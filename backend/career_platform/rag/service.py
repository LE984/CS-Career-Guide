import copy
import uuid

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import NotFound, ValidationError

from company_reviews.models import Job

from ..errors import InvalidModelOutput, ModelTimeout, ModelUnavailable


class InterviewRagService:
    def __init__(self, *, retriever=None, model_gateway=None, records=None):
        self.retriever = retriever
        self.model_gateway = model_gateway
        self.records = records

    def demo_retrieve(self, *, user, data: dict) -> dict:
        from .demo import retrieve_demo
        return retrieve_demo(data)

    def retrieve(self, *, user, data: dict) -> dict:
        if self.retriever is None:
            raise ModelUnavailable('题库检索服务暂时不可用')
        if data.get('job_id') and data.get('jd_text'):
            raise ValidationError({'jd_text': 'job_id 与 jd_text 不能同时提供'})
        query = data.get('jd_text') or ''
        if data.get('job_id'):
            job = Job.objects.filter(pk=data['job_id']).first()
            if job is None:
                raise NotFound()
            if job.permission_status != 'allowed':
                raise ValidationError({'job_id': '岗位来源未获允许'})
            query = job.description or job.requirements or ''
        query = query or data.get('topic') or data.get('role') or ''
        try:
            rows = self.retriever.retrieve(
                query=query, role=data.get('role', ''), topic=data.get('topic', ''),
                difficulty=data.get('difficulty', 'easy'), top_k=data.get('top_k', 5),
            )
        except ValueError as exc:
            raise ValidationError({'query': str(exc)}) from exc
        results = [self._ranked_question(item) for item in rows]
        retrieval_id = str(uuid.uuid4())
        context = {
            'query': query, 'role': data.get('role', ''), 'topic': data.get('topic', ''),
            'difficulty': data.get('difficulty', 'easy'), 'top_k': data.get('top_k', 5),
            'request_id': str(data.get('request_id')),
        }
        for item in results:
            item.update(
                role=context['role'], topic=context['topic'], difficulty=context['difficulty'],
                permission_status='allowed', collected_at=None,
                source=next((e['quote'] for e in item['evidence'] if e['field_path'] == 'source'), ''),
                source_url=next((e['quote'] for e in item['evidence'] if e['field_path'] == 'source_url'), ''),
            )
        cache.set(
            f'career-platform:retrieval:{user.pk}:{retrieval_id}',
            dict(context=context, results=copy.deepcopy(results),
                 role=context['role'], topic=context['topic'], difficulty=context['difficulty']),
            timeout=int(getattr(settings, 'PRACTICE_RETRIEVAL_TTL', 900)),
        )
        return {'count': len(results), 'results': results, 'retrieval_id': retrieval_id}

    def answer(self, *, user, data: dict) -> dict:
        if self.records is None:
            raise ModelUnavailable('练习记录服务暂时不可用')
        record = self.records.record_answer(user=user, data=data)
        if not record.pop('should_generate_feedback', False):
            record.pop('feedback_request_id', None)
            return record
        return self._generate_feedback(user=user, record=record)

    def retry_feedback(self, *, user, data: dict) -> dict:
        if self.records is None:
            raise ModelUnavailable('练习记录服务暂时不可用')
        record = self.records.begin_feedback_retry(user=user, data=data)
        if not record.pop('should_generate_feedback', False):
            record.pop('feedback_request_id', None)
            return record
        return self._generate_feedback(user=user, record=record)

    def _generate_feedback(self, *, user, record):
        attempt_id = record.get('feedback_request_id')
        if self.model_gateway is None:
            self.records.record_feedback(user=user, data={
                'id': record['id'], 'feedback': {}, 'status': 'failed',
                'failure_code': 'MODEL_UNAVAILABLE', 'feedback_request_id': attempt_id,
            })
            raise ModelUnavailable()
        try:
            feedback = self.model_gateway.generate(
                system=(
                    '你是面试逐题反馈助手。仅依据真实回答、题目参考要点和证据，'
                    '返回 answer_quote、key_points_covered、missing_points、evidence、follow_up。'
                ),
                payload={
                    'question': copy.deepcopy(record['question_snapshot']),
                    'answer': record['answer'],
                },
            )
        except TimeoutError as exc:
            self.records.record_feedback(user=user, data={
                'id': record['id'], 'feedback': {}, 'status': 'failed',
                'failure_code': 'MODEL_TIMEOUT', 'feedback_request_id': attempt_id,
            })
            raise ModelTimeout() from exc
        except ValueError as exc:
            self.records.record_feedback(user=user, data={
                'id': record['id'], 'feedback': {}, 'status': 'failed',
                'failure_code': 'INVALID_MODEL_OUTPUT', 'feedback_request_id': attempt_id,
            })
            raise InvalidModelOutput() from exc
        except Exception as exc:
            self.records.record_feedback(user=user, data={
                'id': record['id'], 'feedback': {}, 'status': 'failed',
                'failure_code': 'MODEL_UNAVAILABLE', 'feedback_request_id': attempt_id,
            })
            raise ModelUnavailable() from exc
        if not self._valid_feedback(feedback, record):
            self.records.record_feedback(user=user, data={
                'id': record['id'], 'feedback': {}, 'status': 'failed',
                'failure_code': 'INVALID_MODEL_OUTPUT', 'feedback_request_id': attempt_id,
            })
            raise InvalidModelOutput()
        result = self.records.record_feedback(user=user, data={
            'id': record['id'], 'feedback': feedback, 'status': 'succeeded',
            'failure_code': '', 'feedback_request_id': attempt_id,
        })
        result.pop('feedback_request_id', None)
        return result

    @staticmethod
    def _valid_feedback(feedback, record):
        if not isinstance(feedback, dict):
            return False
        quote = feedback.get('answer_quote')
        if not isinstance(quote, str) or quote not in record['answer']:
            return False
        for field in ('key_points_covered', 'missing_points', 'evidence'):
            if not isinstance(feedback.get(field, []), list):
                return False
        allowed = {
            (str(item.get('source_id')), item.get('field_path'), item.get('quote'))
            for item in record['question_snapshot'].get('evidence', [])
        }
        for evidence in feedback.get('evidence', []):
            if not isinstance(evidence, dict):
                return False
            key = (str(evidence.get('source_id')), evidence.get('field_path'), evidence.get('quote'))
            if key not in allowed:
                return False
        follow_up = feedback.get('follow_up')
        return follow_up is None or isinstance(follow_up, str)

    @staticmethod
    def _ranked_question(item):
        evidence = [
            {'source_id': value.source_id, 'field_path': value.field_path, 'quote': value.quote}
            for value in item.evidence if value.field_path != 'reference_answer'
        ]
        return {
            'question_id': item.question_id, 'question': item.question,
            'key_points': list(item.key_points), 'evidence': evidence,
            'score': item.score, 'origin': item.origin,
        }
