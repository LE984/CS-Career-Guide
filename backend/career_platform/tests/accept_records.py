from career_platform.records.service import PracticeService
from career_platform.models import AnswerRecord,PracticeSession
from .accept_support import AcceptanceCase,Gateway
from .helpers import request_id,PREFIX


class RecordsAcceptance(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.gateway=Gateway(dict(strengths=['引用了集合语义'],gaps=['需举例'],next_steps=['练习集合']))
        self.service=PracticeService(model_gateway=self.gateway)
        self.wire(records=self.service)

    def test_snapshots_idempotency_and_history(self):
        session,q=self.session()
        body=dict(id=session.id,question_id=q.id,question_snapshot=session.presented_questions[0],answer='集合语义',request_id=request_id())
        first=self.service.record_answer(user=self.user,data=body)
        second=self.service.record_answer(user=self.user,data=body)
        self.assertEqual(first['id'],second['id'])
        self.assertEqual(AnswerRecord.objects.count(),1)
        q.question='已修改';q.save()
        result=self.get(f'practice-sessions/{session.id}/')
        self.assertEqual(result['answers'][0]['question_snapshot']['question'],'解释集合接口')
        self.assertEqual(result['answers'][0]['answer'],'集合语义')
        self.assertEqual(self.stranger.get(PREFIX+f'practice-sessions/{session.id}/').status_code,404)
        q.delete()
        self.assertEqual(self.get(f'practice-sessions/{session.id}/')['answers'][0]['question_snapshot']['question'],'解释集合接口')

    def test_finish_once_then_reject_answers(self):
        session,q=self.session()
        self.service.record_answer(user=self.user,data=dict(id=session.id,question_id=q.id,question_snapshot=session.presented_questions[0],answer='集合语义',request_id=request_id()))
        body=dict(request_id=request_id())
        first=self.post(f'practice-sessions/{session.id}/finish/',body)
        self.assertEqual(self.post(f'practice-sessions/{session.id}/finish/',body),first)
        self.assertEqual(len(self.gateway.calls),1)
        session.refresh_from_db();self.assertEqual(session.status,'ended');self.assertIsNotNone(session.ended_at)
        from rest_framework.exceptions import APIException
        with self.assertRaises(APIException) as error:
            self.service.record_answer(user=self.user,data=dict(id=session.id,question_id=q.id,answer='迟到回答',request_id=request_id()))
        self.assertEqual(error.exception.status_code,409)

    def test_summary_failure_preserves_answers_and_requires_explicit_retry(self):
        session,q=self.session();self.gateway.fail=True
        self.service.record_answer(user=self.user,data=dict(id=session.id,question_id=q.id,question_snapshot=session.presented_questions[0],answer='保留真实回答',request_id=request_id()))
        # Finish acknowledges a persisted end even when summary generation fails.
        self.post(f'practice-sessions/{session.id}/finish/',dict(request_id=request_id()))
        session.refresh_from_db();self.assertEqual(session.summary['status'],'failed')
        self.assertEqual(session.answers.get().answer,'保留真实回答')
        self.post(f'practice-sessions/{session.id}/finish/',dict(request_id=request_id()))
        self.assertEqual(len(self.gateway.calls),1)
        self.gateway.fail=False
        self.post(f'practice-sessions/{session.id}/finish/',dict(request_id=request_id(),retry_summary=True))
        self.assertEqual(len(self.gateway.calls),2)
