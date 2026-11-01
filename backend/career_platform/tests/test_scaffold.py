import uuid
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from career_platform.models import ResumeAnalysisRun, PracticeSession, EvaluationRun, AnswerRecord, InterviewQuestion
from career_platform.composition import build_services
from .helpers import client, request_id, company, question, PREFIX

class ScaffoldTests(TestCase):
    def setUp(self):
        self.user,self.client=client()
        self.admin,self.staff=client(True,'staff')

    def test_public_and_admin_permissions(self):
        response=APIClient().get(PREFIX+'catalog/jobs/')
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.data['code'],'UNAUTHENTICATED')
        for path,method in [('catalog/imports/','post'),('evaluation-runs/','get')]:
            self.assertEqual(getattr(self.client,method)(PREFIX+path,{},format='json').status_code,403)

    def test_valid_business_requests_are_unavailable_without_writes(self):
        # Always exercise the real unavailable adapter. Implemented modules are
        # tested separately by immutable complete suites; do not pin them to 501.
        from unittest.mock import patch
        from career_platform.composition_base import UnavailableService
        from career_platform import composition
        patcher=patch.dict(composition.services,{key:UnavailableService(key) for key in composition.services})
        patcher.start()
        self.addCleanup(patcher.stop)
        cases=[('catalog/companies/',self.client,'get',{}),('catalog/jobs/',self.client,'get',{}),('catalog/questions/',self.client,'get',{}),
            ('catalog/imports/',self.staff,'post',{'kind':'questions','records':[{'test':True}]}),
            ('resume-analyses/',self.client,'post',{'jd_text':'Java工程师','resume_revision':0,'request_id':request_id()}),
            ('practice-sessions/',self.client,'post',{'role':'Java后端','request_id':request_id()}),
            ('questions/retrieve/',self.client,'post',{'role':'Java后端','request_id':request_id()}),
            ('evaluation-runs/',self.staff,'post',{'task':'question','strategy':'tfidf','dataset_version':'fixture-v1','request_id':request_id()})]
        for path,c,method,data in cases:
            with self.subTest(path=path):
                response=getattr(c,method)(PREFIX+path,data,format='json')
                self.assertEqual(response.status_code,501,response.data)
                self.assertEqual(response.data['code'],'FEATURE_NOT_IMPLEMENTED')
                self.assertEqual(set(response.data),{'code','message','details'})
        for model in (ResumeAnalysisRun,PracticeSession,EvaluationRun,InterviewQuestion):
            self.assertEqual(model.objects.count(),0)
        self.assertEqual(set(build_services()),{'catalog','evaluation','resume','rag','records'})

    def test_input_validation_rejects_owner_injection(self):
        response=self.client.post(PREFIX+'resume-analyses/',{'user':self.admin.pk},format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.data['code'],'VALIDATION_ERROR')
        self.assertEqual(self.client.get(PREFIX+'catalog/jobs/?page_size=101').status_code,400)

    def test_private_ids_are_scoped_before_service(self):
        run=ResumeAnalysisRun.objects.create(user=self.user,request_id=uuid.uuid4(),base_revision=0,jd_text='Java')
        self.assertEqual(self.staff.get(PREFIX+f'resume-analyses/{run.pk}/').status_code,404)
        from unittest.mock import patch
        from career_platform.composition_base import UnavailableService
        from career_platform import composition
        with patch.dict(composition.services,resume=UnavailableService('resume')):
            self.assertEqual(self.client.get(PREFIX+f'resume-analyses/{run.pk}/').status_code,501)
        session=PracticeSession.objects.create(user=self.user,request_id=uuid.uuid4())
        answer={'question_id':request_id(),'request_id':request_id(),'answer':'真实回答'}
        self.assertEqual(self.staff.post(PREFIX+f'practice-sessions/{session.pk}/answers/',answer,format='json').status_code,404)

    def test_resume_version_and_legacy_save(self):
        for body in [{'name':'测试姓名'},{'skills':'Java','education':[{'school':'测试学校','period':'2026'}]}]:
            response=self.client.post('/api/resumes/my/',body,format='json')
            self.assertEqual(response.status_code,200,response.data)
        revision=response.data['edit_revision']
        self.assertGreater(revision,0)
        response=self.client.post('/api/resumes/my/',{'name':'新姓名','edit_revision':999},format='json')
        self.assertEqual(response.data['edit_revision'],revision+1)

    def test_legacy_catalog_writes_require_staff(self):
        c=company()
        self.assertEqual(self.client.patch(f'/api/company-reviews/companies/{c.pk}/',{'name':'篡改'},format='json').status_code,403)
        self.assertEqual(self.staff.patch(f'/api/company-reviews/companies/{c.pk}/',{'name':'管理员修改'},format='json').status_code,200)

    def test_real_migrations_snapshots_and_uniqueness(self):
        company()
        q=question()
        rid=uuid.uuid4()
        session=PracticeSession.objects.create(user=self.user,request_id=rid,job_snapshot={'title':'历史岗位'})
        record=AnswerRecord.objects.create(session=session,question=q,request_id=uuid.uuid4(),question_snapshot={'question':q.question},answer='原回答')
        q.question='新题'
        q.save()
        record.refresh_from_db()
        self.assertEqual(record.question_snapshot['question'],'解释集合接口')
        with self.assertRaises(IntegrityError), transaction.atomic():
            PracticeSession.objects.create(user=self.user,request_id=rid)
        call_command('makemigrations','company_reviews','resumes','career_platform',check=True,dry_run=True,verbosity=0)
