from career_platform.rag.service import InterviewRagService
from career_platform.records.service import PracticeService
from career_platform.contracts import RankedQuestion,Evidence
from career_platform.models import AnswerRecord
from .accept_support import AcceptanceCase,Gateway
from .helpers import request_id,PREFIX


class Retriever:
    def __init__(self, rows): self.rows=rows;self.calls=[]
    def retrieve(self, **query):
        self.calls.append(query)
        return self.rows


class RagAcceptance(AcceptanceCase):
    def setUp(self):
        super().setUp()
        self.session_row,self.q=self.session()
        self.evidence=dict(source_id=str(self.q.id),field_path='key_points[0]',quote='语义')
        self.retriever=Retriever([RankedQuestion(str(self.q.id),self.q.question,('语义',),(Evidence(**self.evidence),),.7)])
        self.gateway=Gateway(dict(answer_quote='集合语义',key_points_covered=['语义'],missing_points=[],evidence=[self.evidence],follow_up=None))
        self.records=PracticeService(model_gateway=self.gateway)
        self.wire(rag=InterviewRagService(retriever=self.retriever,model_gateway=self.gateway,records=self.records))

    def test_retrieval_constraints_source_and_empty_result(self):
        body=dict(role='Java后端',topic='集合',difficulty='easy',request_id=request_id())
        result=self.post('questions/retrieve/',body)
        self.assertEqual(result['results'][0]['question_id'],str(self.q.id))
        self.assertEqual(result['results'][0]['evidence'][0],self.evidence)
        for key in ('role','topic','difficulty'):
            self.assertEqual(self.retriever.calls[0][key],body[key])
        self.retriever.rows=[]
        self.assertEqual(self.post('questions/retrieve/',body)['results'],[])

    def test_feedback_uses_real_answer_and_persists_once(self):
        body=dict(question_id=str(self.q.id),answer='集合语义',request_id=request_id())
        path=f'practice-sessions/{self.session_row.id}/answers/'
        self.post(path,body);self.post(path,body)
        self.assertEqual(AnswerRecord.objects.count(),1)
        self.assertEqual(len(self.gateway.calls),1)
        row=AnswerRecord.objects.get()
        self.assertEqual(row.answer,'集合语义')
        self.assertIn(row.feedback['answer_quote'],row.answer)
        self.assertEqual(row.feedback['evidence'][0],self.evidence)

    def test_model_failure_preserves_answer_and_unissued_question_is_rejected(self):
        self.gateway.fail=True
        body=dict(question_id=str(self.q.id),answer='不能丢失的回答',request_id=request_id())
        response=self.client.post(PREFIX+f'practice-sessions/{self.session_row.id}/answers/',body,format='json')
        self.assertIn(response.status_code,(502,503,504))
        row=AnswerRecord.objects.get();self.assertEqual(row.answer,body['answer']);self.assertEqual(row.status,'failed')
        body.update(question_id=request_id(),request_id=request_id())
        self.post(f'practice-sessions/{self.session_row.id}/answers/',body,expected=400)
        self.assertEqual(AnswerRecord.objects.count(),1)
