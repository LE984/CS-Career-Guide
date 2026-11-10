from career_platform.models import AnswerRecord, PracticeSession
from career_platform.contracts import Evidence, RankedQuestion
from career_platform.records.service import PracticeService
from career_platform.rag.service import InterviewRagService

from .accept_support import AcceptanceCase, Gateway
from .helpers import PREFIX, question, request_id


class StaticRetriever:
    def __init__(self, rows):
        self.rows = rows

    def retrieve(self, **query):
        return self.rows


class RecordsRuntimeTests(AcceptanceCase):
    def test_retrieval_receipt_preserves_ranked_snapshot(self):
        q = question()
        evidence = Evidence(str(q.id), 'key_points[0]', '语义')
        records = PracticeService(model_gateway=Gateway())
        rag = InterviewRagService(
            retriever=StaticRetriever([
                RankedQuestion(str(q.id), q.question, ('语义',), (evidence,), .73)
            ]),
            records=records,
        )
        self.wire(records=records, rag=rag)
        retrieved = self.post('questions/retrieve/', dict(
            role='Java后端', topic='集合', difficulty='easy', request_id=request_id(),
        ))
        session = self.post('practice-sessions/', dict(
            role='Java后端', topic='集合', difficulty='easy',
            question_ids=[str(q.id)], retrieval_id=retrieved['retrieval_id'],
            request_id=request_id(),
        ))
        snapshot = session['presented_questions'][0]
        self.assertEqual(snapshot['score'], .73)
        self.assertEqual(snapshot['evidence'][0], {
            'source_id': str(q.id), 'field_path': 'key_points[0]', 'quote': '语义'
        })
        self.assertEqual(snapshot['retrieval_context']['selection_mode'], 'retrieval_receipt')

    def test_start_is_idempotent_and_history_uses_public_snapshots(self):
        q = question()
        service = PracticeService(model_gateway=Gateway())
        self.wire(records=service)
        rid = request_id()
        body = dict(
            role='Java后端', topic='集合', difficulty='easy',
            question_ids=[str(q.id)], request_id=rid,
        )
        first = self.post('practice-sessions/', body)
        second = self.post('practice-sessions/', body)
        self.assertEqual(first, second)
        self.assertEqual(PracticeSession.objects.count(), 1)
        self.assertEqual(first['answers'], [])
        self.assertNotIn('reference_answer', first['presented_questions'][0])
        listing = self.get('practice-sessions/?role=Java%E5%90%8E%E7%AB%AF')
        self.assertEqual(listing['count'], 1)
        conflict = self.client.post(
            PREFIX + 'practice-sessions/', body | {'role': 'Python后端'}, format='json'
        )
        self.assertEqual(conflict.status_code, 409)

    def test_empty_finish_does_not_call_model(self):
        gateway = Gateway()
        service = PracticeService(model_gateway=gateway)
        self.wire(records=service)
        session = PracticeSession.objects.create(
            user=self.user, request_id=request_id(), status='active',
            presented_questions=[], summary={},
        )
        result = self.post(
            f'practice-sessions/{session.id}/finish/', {'request_id': request_id()}
        )
        self.assertEqual(result['status'], 'ended')
        self.assertEqual(result['summary']['status'], 'failed')
        self.assertEqual(result['summary']['failure_code'], 'NO_ANSWERS')
        self.assertEqual(gateway.calls, [])

    def test_feedback_retry_reuses_answer_and_attempt_key(self):
        session, q = self.session()
        service = PracticeService(model_gateway=Gateway())
        first = service.record_answer(user=self.user, data=dict(
            id=session.id, question_id=q.id, answer='集合语义', request_id=request_id(),
        ))
        service.record_feedback(user=self.user, data=dict(
            id=first['id'], feedback={}, status='failed', failure_code='MODEL_TIMEOUT',
            feedback_request_id=first['feedback_request_id'],
        ))
        retry_id = request_id()
        claimed = service.begin_feedback_retry(user=self.user, data=dict(
            session_id=session.id, id=first['id'], request_id=retry_id,
        ))
        replay = service.begin_feedback_retry(user=self.user, data=dict(
            session_id=session.id, id=first['id'], request_id=retry_id,
        ))
        self.assertTrue(claimed['should_generate_feedback'])
        self.assertFalse(replay['should_generate_feedback'])
        self.assertEqual(AnswerRecord.objects.count(), 1)

    def test_feedback_retry_http_updates_original_record(self):
        session, q = self.session()
        evidence = {'source_id': str(q.id), 'field_path': 'key_points[0]', 'quote': '语义'}
        gateway = Gateway(fail=True)
        records = PracticeService(model_gateway=gateway)
        rag = InterviewRagService(model_gateway=gateway, records=records)
        self.wire(records=records, rag=rag)
        body = {'question_id': str(q.id), 'answer': '集合语义', 'request_id': request_id()}
        failed = self.client.post(
            PREFIX + f'practice-sessions/{session.id}/answers/', body, format='json'
        )
        self.assertIn(failed.status_code, (502, 503, 504))
        answer = AnswerRecord.objects.get()
        gateway.fail = False
        gateway.result = {
            'answer_quote': '集合语义', 'key_points_covered': ['语义'],
            'missing_points': [], 'evidence': [evidence], 'follow_up': None,
        }
        result = self.post(
            f'practice-sessions/{session.id}/answers/{answer.id}/retry-feedback/',
            {'request_id': request_id()},
        )
        answer.refresh_from_db()
        self.assertEqual(result['id'], str(answer.id))
        self.assertEqual(answer.status, 'succeeded')
        self.assertEqual(AnswerRecord.objects.count(), 1)
        self.assertEqual(len(gateway.calls), 2)
