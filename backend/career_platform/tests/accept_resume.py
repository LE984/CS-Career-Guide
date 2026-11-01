from resumes.models import Resume
from career_platform.resume.service import ResumeAnalysisService
from career_platform.models import ResumeAnalysisRun,ResumeApplyReceipt
from .accept_support import AcceptanceCase,Gateway
from .helpers import request_id,PREFIX


class ResumeAcceptance(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.resume=Resume.objects.create(user=self.user,skills='使用Java完成课程项目')
        self.sid=request_id()
        self.suggestion=dict(id=self.sid,field_path='skills',original=self.resume.skills,suggested='使用Java开发课程项目',reason='表述清晰',
            evidence=[dict(source_id=str(self.resume.pk),field_path='skills',quote=self.resume.skills)])
        self.gateway=Gateway(dict(matches=['Java'],gaps=['Redis'],suggestions=[self.suggestion]))
        self.wire(resume=ResumeAnalysisService(model_gateway=self.gateway))

    def analyze(self):
        return self.post('resume-analyses/',dict(jd_text='Java，Redis',resume_revision=self.resume.edit_revision,request_id=request_id()))

    def test_analysis_does_not_change_original_and_application_is_idempotent(self):
        result=self.analyze();self.resume.refresh_from_db()
        self.assertEqual(self.resume.skills,self.suggestion['original'])
        run=ResumeAnalysisRun.objects.get(pk=result['id'])
        self.assertEqual(run.result['suggestions'][0]['evidence'][0]['quote'],self.resume.skills)
        body=dict(base_revision=self.resume.edit_revision,accepted_suggestion_ids=[self.sid],suggestion_edits={self.sid:'使用Java实现课程项目'},request_id=request_id())
        applied=self.post(f"resume-analyses/{run.id}/apply/",body)
        self.resume.refresh_from_db();revision=self.resume.edit_revision
        self.assertEqual(self.resume.skills,'使用Java实现课程项目')
        self.assertEqual(self.post(f"resume-analyses/{run.id}/apply/",body),applied)
        self.resume.refresh_from_db();self.assertEqual(self.resume.edit_revision,revision)
        self.assertEqual(ResumeApplyReceipt.objects.count(),1)

    def test_old_analysis_cannot_overwrite_new_resume_or_cross_user(self):
        result=self.analyze()
        self.resume.skills='新版本';self.resume.save()
        self.post(f"resume-analyses/{result['id']}/apply/",dict(base_revision=0,accepted_suggestion_ids=[self.sid],request_id=request_id()),expected=409)
        self.resume.refresh_from_db();self.assertEqual(self.resume.skills,'新版本')
        self.assertEqual(self.stranger.get(PREFIX+f"resume-analyses/{result['id']}/").status_code,404)

    def test_fabricated_facts_and_timeout_do_not_modify_resume(self):
        self.suggestion['suggested']='精通Redis，提升吞吐50%'
        self.gateway.result['suggestions']=[self.suggestion]
        response=self.client.post(PREFIX+'resume-analyses/',dict(jd_text='Java',resume_revision=0,request_id=request_id()),format='json')
        self.assertIn(response.status_code,(400,422))
        self.assertEqual(ResumeAnalysisRun.objects.count(),0)
        self.gateway.fail=True
        response=self.client.post(PREFIX+'resume-analyses/',dict(jd_text='Java',resume_revision=0,request_id=request_id()),format='json')
        self.assertIn(response.status_code,(502,503,504))
        self.resume.refresh_from_db();self.assertEqual(self.resume.skills,self.suggestion['original'])
        self.assertEqual(ResumeApplyReceipt.objects.count(),0)
