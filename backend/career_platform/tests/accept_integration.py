"""Actual member services compose end to end; only the external model is a fixture."""
from career_platform.resume.service import ResumeAnalysisService
from career_platform.records.service import PracticeService
from career_platform.rag.service import InterviewRagService
from career_platform.models import AnswerRecord
from resumes.models import Resume
from .accept_support import AcceptanceCase,Gateway
from .helpers import request_id


class IntegrationAcceptance(AcceptanceCase):
    def test_import_analyze_apply_practice_feedback_finish_history(self):
        self.post('catalog/imports/',dict(kind='questions',records=self.fixture_questions(),dry_run=False),True)
        q=self.get('catalog/questions/?topic=集合')['results'][0]
        resume=Resume.objects.create(user=self.user,skills='Java课程项目')
        sid=request_id()
        gateway=Gateway(dict(matches=['Java'],gaps=[],suggestions=[dict(id=sid,field_path='skills',original=resume.skills,suggested='使用Java开发课程项目',reason='明确表述',evidence=[dict(source_id=str(resume.id),field_path='skills',quote=resume.skills)])]))
        records=PracticeService(model_gateway=gateway)
        self.wire(resume=ResumeAnalysisService(model_gateway=gateway),records=records,
                  rag=InterviewRagService(model_gateway=gateway,records=records))
        analysis=self.post('resume-analyses/',dict(jd_text='Java后端',resume_revision=0,request_id=request_id()))
        self.post(f"resume-analyses/{analysis['id']}/apply/",dict(base_revision=0,accepted_suggestion_ids=[sid],request_id=request_id()))
        resume.refresh_from_db();self.assertEqual(resume.skills,'使用Java开发课程项目')
        session=self.post('practice-sessions/',dict(role='Java后端',topic='集合',difficulty='easy',question_ids=[q['id']],jd_text='Java后端',request_id=request_id()))
        gateway.result=dict(answer_quote='随机访问',key_points_covered=['存储结构与访问模式'],missing_points=[],evidence=[dict(source_id=q['id'],field_path='key_points[0]',quote=q['key_points'][0])],follow_up=None)
        self.post(f"practice-sessions/{session['id']}/answers/",dict(question_id=q['id'],answer='数组支持随机访问',request_id=request_id()))
        gateway.result=dict(strengths=['解释随机访问'],gaps=[],next_steps=['练习JVM'])
        self.post(f"practice-sessions/{session['id']}/finish/",dict(request_id=request_id()))
        history=self.get(f"practice-sessions/{session['id']}/")
        self.assertEqual(history['status'],'ended')
        self.assertEqual(history['answers'][0]['answer'],'数组支持随机访问')
        self.assertEqual(AnswerRecord.objects.count(),1)
