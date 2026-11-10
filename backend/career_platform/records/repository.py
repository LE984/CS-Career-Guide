import copy
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from company_reviews.models import Job
from resumes.models import Resume

from ..errors import Conflict
from ..models import AnswerRecord, InterviewQuestion, PracticeSession


SUMMARY_EMPTY = {
    'status': 'pending', 'strengths': [], 'gaps': [], 'next_steps': [],
    'failure_code': '', 'prompt_version': 'v1',
}


def _iso(value):
    if value is None:
        return None
    text = value.isoformat()
    return text[:-6] + 'Z' if text.endswith('+00:00') else text


def _uuid_text(value):
    return str(value) if value is not None else None


def _attempt(log, request_id):
    key = str(request_id)
    return next((item for item in log or [] if item.get('request_id') == key), None)


def _append_attempt(log, request_id, status='pending', failure_code=''):
    rows = copy.deepcopy(log or [])
    rows.append({
        'request_id': str(request_id), 'status': status,
        'started_at': _iso(timezone.now()), 'completed_at': None,
        'failure_code': failure_code,
    })
    return rows


def _complete_attempt(log, request_id, status, failure_code=''):
    rows = copy.deepcopy(log or [])
    key = str(request_id)
    for item in rows:
        if item.get('request_id') == key:
            item.update(status=status, completed_at=_iso(timezone.now()), failure_code=failure_code)
            break
    return rows


def _attempt_limit():
    return int(getattr(settings, 'PRACTICE_MAX_MODEL_ATTEMPTS', 5))


def _attempt_timeout():
    return int(getattr(settings, 'LLM_TIMEOUT', 120)) + int(
        getattr(settings, 'PRACTICE_ATTEMPT_GRACE_SECONDS', 30)
    )


class DjangoPracticeRepository:
    def _start_payload(self, data):
        return {
            'role': data.get('role', ''),
            'topic': data.get('topic', ''),
            'difficulty': data.get('difficulty', 'easy'),
            'job_id': data.get('job_id'),
            'jd_text': data.get('jd_text', ''),
            'question_ids': [str(value) for value in data.get('question_ids') or []],
            'retrieval_id': str(data.get('retrieval_id') or ''),
        }

    def _same_start(self, session, data):
        return (session.filters or {}).get('request_payload') == self._start_payload(data)

    def _job_snapshot(self, job, jd_text):
        if job is None:
            return {
                'id': None, 'title': '', 'company': '', 'description': jd_text or '',
                'requirements': '', 'skills': [], 'city': '', 'source': '',
                'source_url': '', 'permission_status': '', 'collected_at': None,
                'is_demo': False, 'jd_source': 'input' if jd_text else 'none',
            }
        return {
            'id': job.id, 'title': job.title, 'company': job.company.name,
            'description': job.description or job.requirements or '',
            'requirements': job.requirements or '', 'skills': copy.deepcopy(job.skills or []),
            'city': job.city or '', 'source': job.source or '', 'source_url': job.source_url or '',
            'permission_status': job.permission_status, 'collected_at': _iso(job.collected_at),
            'is_demo': bool(job.is_demo), 'jd_source': 'job',
        }

    def _resume_snapshot(self, user):
        resume = Resume.objects.filter(user=user).first()
        if resume is None:
            return {}

        def rows(manager, fields):
            return [
                {field: getattr(item, field) for field in fields}
                for item in manager.all().order_by('id')
            ]

        return {
            'id': resume.id, 'edit_revision': resume.edit_revision,
            'target_position': resume.target_position or '', 'skills': resume.skills or '',
            'self_evaluation': resume.self_evaluation or '',
            'educations': rows(resume.education, ('school', 'major', 'period', 'description')),
            'experiences': rows(resume.experience, ('company', 'position', 'period', 'description')),
            'projects': rows(resume.projects, ('name', 'role', 'period', 'url', 'description')),
            'certificates': rows(resume.certificates, ('name', 'issuer', 'period', 'description')),
            'awards': rows(resume.awards, ('name', 'issuer', 'period', 'description')),
        }

    def _question_snapshot(self, question, *, score=None, retrieval_context=None):
        question_id = str(question.id)
        evidence = [{'source_id': question_id, 'field_path': 'source', 'quote': question.source}]
        if question.source_url:
            evidence.append({'source_id': question_id, 'field_path': 'source_url', 'quote': question.source_url})
        evidence.extend(
            {'source_id': question_id, 'field_path': f'key_points[{index}]', 'quote': point}
            for index, point in enumerate(question.key_points or [])
        )
        return {
            'question_id': question_id, 'question': question.question,
            'key_points': copy.deepcopy(question.key_points or []), 'evidence': evidence,
            'source': question.source, 'source_url': question.source_url or '',
            'permission_status': question.permission_status,
            'collected_at': _iso(question.collected_at), 'role': question.role,
            'topic': question.topic, 'difficulty': question.difficulty,
            'origin': 'catalog', 'score': score,
            'retrieval_context': copy.deepcopy(retrieval_context or {}),
        }

    def public_question_snapshot(self, snapshot):
        allowed = {
            'question_id', 'question', 'key_points', 'evidence', 'source', 'source_url',
            'permission_status', 'collected_at', 'role', 'topic', 'difficulty',
            'origin', 'score', 'retrieval_context',
        }
        return {key: copy.deepcopy(value) for key, value in (snapshot or {}).items() if key in allowed}

    def serialize_answer(self, answer, *, internal=False):
        result = {
            'id': str(answer.id), 'question_id': answer.question_key,
            'question_snapshot': self.public_question_snapshot(answer.question_snapshot),
            'answer': answer.answer, 'status': answer.status,
            'failure_code': answer.failure_code, 'feedback': copy.deepcopy(answer.feedback or {}),
            'created_at': _iso(answer.created_at), 'updated_at': _iso(answer.updated_at),
        }
        if internal:
            result['feedback_request_id'] = _uuid_text(answer.feedback_request_id)
        return result

    def serialize_session(self, session, *, include_answers=True):
        summary = copy.deepcopy(SUMMARY_EMPTY)
        summary.update(copy.deepcopy(session.summary or {}))
        result = {
            'id': str(session.id), 'status': session.status,
            'created_at': _iso(session.created_at), 'ended_at': _iso(session.ended_at),
            'role': session.role or (session.filters or {}).get('role', ''),
            'topic': session.topic or (session.filters or {}).get('topic', ''),
            'difficulty': session.difficulty or (session.filters or {}).get('difficulty', ''),
            'filters': {key: copy.deepcopy(value) for key, value in (session.filters or {}).items() if key != 'request_payload'},
            'job_snapshot': copy.deepcopy(session.job_snapshot or {}),
            'resume_snapshot': copy.deepcopy(session.resume_snapshot or {}),
            'presented_questions': [self.public_question_snapshot(item) for item in session.presented_questions or []],
            'summary': summary,
        }
        if include_answers:
            result['answers'] = [self.serialize_answer(item) for item in session.answers.all().order_by('created_at', 'id')]
        return result

    def start(self, *, user, data):
        existing = PracticeSession.objects.filter(user=user, request_id=data['request_id']).first()
        if existing is not None:
            if not self._same_start(existing, data):
                raise Conflict()
            return self.serialize_session(existing)

        payload = self._start_payload(data)
        if payload['job_id'] and payload['jd_text']:
            raise ValidationError({'jd_text': 'job_id 与 jd_text 不能同时提供'})
        if not payload['question_ids']:
            raise ValidationError({'question_ids': '至少选择一道题目'})
        if len(set(payload['question_ids'])) != len(payload['question_ids']):
            raise ValidationError({'question_ids': '题目不能重复'})

        job = None
        if payload['job_id']:
            job = Job.objects.select_related('company').filter(pk=payload['job_id']).first()
            if job is None:
                raise NotFound()
            if job.permission_status != 'allowed':
                raise ValidationError({'job_id': '岗位来源未获允许'})

        context = {
            'role': payload['role'], 'topic': payload['topic'],
            'difficulty': payload['difficulty'], 'selection_mode': 'explicit_ids',
        }
        if payload['retrieval_id']:
            receipt = cache.get(f"career-platform:retrieval:{user.pk}:{payload['retrieval_id']}")
            if not receipt:
                raise Conflict('检索结果已过期，请重新检索')
            for field in ('role', 'topic', 'difficulty'):
                if str(receipt.get(field, '')) != str(payload[field]):
                    raise Conflict('检索条件与会话条件不一致')
            available = {str(item.get('question_id')): item for item in receipt.get('results', [])}
            if any(key not in available for key in payload['question_ids']):
                raise ValidationError({'question_ids': '所选题目不属于本次检索结果'})
            presented = [copy.deepcopy(available[key]) for key in payload['question_ids']]
            context = copy.deepcopy(receipt.get('context') or context)
            context['selection_mode'] = 'retrieval_receipt'
            for item in presented:
                item['retrieval_context'] = copy.deepcopy(context)
        else:
            questions = {str(item.id): item for item in InterviewQuestion.objects.filter(id__in=payload['question_ids'])}
            if len(questions) != len(payload['question_ids']):
                raise NotFound()
            ordered = [questions[key] for key in payload['question_ids']]
            if any(item.permission_status != 'allowed' for item in ordered):
                raise ValidationError({'question_ids': '题目来源未获允许'})
            for item in ordered:
                if payload['role'] and item.role != payload['role']:
                    raise ValidationError({'question_ids': '题目岗位方向与会话不一致'})
                if payload['topic'] and item.topic != payload['topic']:
                    raise ValidationError({'question_ids': '题目知识点与会话不一致'})
                if payload['difficulty'] and item.difficulty != payload['difficulty']:
                    raise ValidationError({'question_ids': '题目难度与会话不一致'})
            presented = [self._question_snapshot(item, retrieval_context=context) for item in ordered]
        job_snapshot = self._job_snapshot(job, payload['jd_text'])
        filters = {
            'role': payload['role'], 'topic': payload['topic'], 'difficulty': payload['difficulty'],
            'job_id': payload['job_id'], 'jd_source': job_snapshot['jd_source'],
            'question_ids': payload['question_ids'], 'selection_mode': 'explicit_ids',
            'request_payload': payload,
        }
        try:
            with transaction.atomic():
                session = PracticeSession.objects.create(
                    user=user, request_id=data['request_id'], status='active', job=job,
                    role=payload['role'], topic=payload['topic'], difficulty=payload['difficulty'],
                    job_title=job_snapshot.get('title') or payload['role'],
                    job_snapshot=job_snapshot, resume_snapshot=self._resume_snapshot(user),
                    filters=filters, presented_questions=presented,
                    summary=copy.deepcopy(SUMMARY_EMPTY),
                )
        except IntegrityError:
            session = PracticeSession.objects.get(user=user, request_id=data['request_id'])
            if not self._same_start(session, data):
                raise Conflict()
        return self.serialize_session(session)

    def list_sessions(self, *, user, data):
        queryset = PracticeSession.objects.filter(user=user)
        if data.get('role'):
            queryset = queryset.filter(role=data['role'])
        if data.get('topic'):
            queryset = queryset.filter(topic=data['topic'])
        if data.get('difficulty'):
            queryset = queryset.filter(difficulty=data['difficulty'])
        if data.get('q'):
            queryset = queryset.filter(Q(job_title__icontains=data['q']) | Q(role__icontains=data['q']))
        queryset = queryset.annotate(answer_count=Count('answers')).order_by('-created_at', '-id')
        count = queryset.count()
        page, page_size = data.get('page', 1), data.get('page_size', 20)
        rows = queryset[(page - 1) * page_size: page * page_size]
        results = [{
            'id': str(item.id), 'status': item.status,
            'created_at': _iso(item.created_at), 'ended_at': _iso(item.ended_at),
            'role': item.role, 'topic': item.topic, 'difficulty': item.difficulty,
            'job_title': item.job_title, 'answer_count': item.answer_count,
            'summary_status': (item.summary or {}).get('status', 'pending'),
        } for item in rows]
        return {'count': count, 'page': page, 'page_size': page_size, 'results': results}

    def get_session(self, *, user, session_id):
        session = PracticeSession.objects.filter(user=user, pk=session_id).first()
        if session is None:
            raise NotFound()
        return self.serialize_session(session)

    def record_answer(self, *, user, data):
        session_id = data['id']
        request_id = data['request_id']
        question_key = str(data['question_id'])
        with transaction.atomic():
            session = PracticeSession.objects.select_for_update().filter(user=user, pk=session_id).first()
            if session is None:
                raise NotFound()
            existing = AnswerRecord.objects.filter(session=session, request_id=request_id).first()
            if existing is not None:
                if existing.question_key != question_key or existing.answer != data['answer']:
                    raise Conflict()
                result = self.serialize_answer(existing, internal=True)
                result['should_generate_feedback'] = False
                return result
            if session.status != 'active':
                raise Conflict('会话已结束，不能继续回答')
            snapshot = next(
                (item for item in session.presented_questions or [] if str(item.get('question_id')) == question_key),
                None,
            )
            if snapshot is None:
                raise ValidationError({'question_id': '题目未在本次会话中下发'})
            supplied = data.get('question_snapshot')
            if supplied and (
                str(supplied.get('question_id')) != question_key
                or supplied.get('question') != snapshot.get('question')
            ):
                raise ValidationError({'question_snapshot': '题目快照与会话不一致'})
            if AnswerRecord.objects.filter(session=session, question_key=question_key).exists():
                raise Conflict('该题已提交回答')
            question = InterviewQuestion.objects.filter(pk=question_key).first()
            answer = AnswerRecord.objects.create(
                session=session, question=question, question_key=question_key,
                question_snapshot=copy.deepcopy(snapshot), request_id=request_id,
                answer=data['answer'], status='received', feedback_request_id=request_id,
                feedback_started_at=timezone.now(),
                feedback_attempt_log=_append_attempt([], request_id),
            )
            result = self.serialize_answer(answer, internal=True)
            result['should_generate_feedback'] = True
            return result

    def record_feedback(self, *, user, data):
        with transaction.atomic():
            answer = (
                AnswerRecord.objects.select_for_update().select_related('session')
                .filter(pk=data['id'], session__user=user).first()
            )
            if answer is None:
                raise NotFound()
            attempt_id = str(data.get('feedback_request_id') or answer.feedback_request_id)
            if str(answer.feedback_request_id) != attempt_id:
                return self.serialize_answer(answer, internal=True)
            status = data.get('status')
            if status not in {'succeeded', 'failed'}:
                raise ValidationError({'status': '不支持的反馈状态'})
            feedback = copy.deepcopy(data.get('feedback') or {})
            failure_code = data.get('failure_code') or ''
            if status == 'succeeded':
                quote = feedback.get('answer_quote')
                if not isinstance(quote, str) or quote not in answer.answer:
                    raise ValidationError({'feedback': 'answer_quote 必须来自真实回答'})
                for field in ('key_points_covered', 'missing_points', 'evidence'):
                    if not isinstance(feedback.get(field, []), list):
                        raise ValidationError({'feedback': f'{field} 必须是列表'})
                failure_code = ''
            answer.status = status
            answer.feedback = feedback if status == 'succeeded' else {}
            answer.failure_code = failure_code
            answer.feedback_attempt_log = _complete_attempt(
                answer.feedback_attempt_log, attempt_id, status, failure_code
            )
            answer.save(update_fields=[
                'status', 'feedback', 'failure_code', 'feedback_attempt_log', 'updated_at'
            ])
            return self.serialize_answer(answer, internal=True)

    def begin_feedback_retry(self, *, user, data):
        request_id = data['request_id']
        with transaction.atomic():
            answer = (
                AnswerRecord.objects.select_for_update().select_related('session')
                .filter(pk=data['id'], session_id=data['session_id'], session__user=user).first()
            )
            if answer is None:
                raise NotFound()
            if answer.status == 'succeeded':
                result = self.serialize_answer(answer, internal=True)
                result['should_generate_feedback'] = False
                return result
            if _attempt(answer.feedback_attempt_log, request_id):
                result = self.serialize_answer(answer, internal=True)
                result['should_generate_feedback'] = False
                return result
            if len(answer.feedback_attempt_log or []) >= _attempt_limit():
                raise Conflict('反馈重试次数已达上限')
            if answer.status == 'received':
                timeout = _attempt_timeout()
                if not answer.feedback_started_at or timezone.now() - answer.feedback_started_at <= timedelta(seconds=timeout):
                    result = self.serialize_answer(answer, internal=True)
                    result['should_generate_feedback'] = False
                    return result
                answer.feedback_attempt_log = _complete_attempt(
                    answer.feedback_attempt_log, answer.feedback_request_id,
                    'failed', 'FEEDBACK_ATTEMPT_EXPIRED'
                )
            elif answer.status != 'failed':
                raise Conflict('当前反馈状态不允许重试')
            answer.status = 'received'
            answer.failure_code = ''
            answer.feedback_request_id = request_id
            answer.feedback_started_at = timezone.now()
            answer.feedback_attempt_log = _append_attempt(answer.feedback_attempt_log, request_id)
            answer.save(update_fields=[
                'status', 'failure_code', 'feedback_request_id', 'feedback_started_at',
                'feedback_attempt_log', 'updated_at'
            ])
            result = self.serialize_answer(answer, internal=True)
            result['should_generate_feedback'] = True
            return result

    def begin_finish(self, *, user, data):
        request_id = data['request_id']
        retry = data.get('retry_summary', False)
        with transaction.atomic():
            session = PracticeSession.objects.select_for_update().filter(user=user, pk=data['id']).first()
            if session is None:
                raise NotFound()
            if session.status == 'active':
                session.status = 'ended'
                session.ended_at = timezone.now()
                session.finish_request_id = request_id
                if not session.answers.exists():
                    summary = copy.deepcopy(SUMMARY_EMPTY)
                    summary.update(status='failed', failure_code='NO_ANSWERS')
                    session.summary = summary
                    session.save(update_fields=['status', 'ended_at', 'finish_request_id', 'summary', 'updated_at'])
                    return self.serialize_session(session), False, None
                session.summary_request_id = request_id
                session.summary_started_at = timezone.now()
                session.summary = copy.deepcopy(SUMMARY_EMPTY)
                session.summary_attempt_log = _append_attempt(session.summary_attempt_log, request_id)
                session.save(update_fields=[
                    'status', 'ended_at', 'finish_request_id', 'summary_request_id',
                    'summary_started_at', 'summary', 'summary_attempt_log', 'updated_at'
                ])
                return self.serialize_session(session), True, str(request_id)

            if not retry:
                return self.serialize_session(session), False, None
            if _attempt(session.summary_attempt_log, request_id):
                return self.serialize_session(session), False, None
            if len(session.summary_attempt_log or []) >= _attempt_limit():
                raise Conflict('总结重试次数已达上限')
            summary_status = (session.summary or {}).get('status')
            if summary_status == 'succeeded' or (session.summary or {}).get('failure_code') == 'NO_ANSWERS':
                return self.serialize_session(session), False, None
            if summary_status == 'pending':
                timeout = _attempt_timeout()
                if not session.summary_started_at or timezone.now() - session.summary_started_at <= timedelta(seconds=timeout):
                    return self.serialize_session(session), False, None
                session.summary_attempt_log = _complete_attempt(
                    session.summary_attempt_log, session.summary_request_id, 'failed', 'SUMMARY_ATTEMPT_EXPIRED'
                )
            elif summary_status != 'failed':
                return self.serialize_session(session), False, None
            session.summary_request_id = request_id
            session.summary_started_at = timezone.now()
            session.summary = copy.deepcopy(SUMMARY_EMPTY)
            session.summary_attempt_log = _append_attempt(session.summary_attempt_log, request_id)
            session.save(update_fields=[
                'summary_request_id', 'summary_started_at', 'summary',
                'summary_attempt_log', 'updated_at'
            ])
            return self.serialize_session(session), True, str(request_id)

    def summary_payload(self, *, user, session_id):
        session = PracticeSession.objects.filter(user=user, pk=session_id).first()
        if session is None:
            raise NotFound()
        return {
            'session': {
                'role': session.role, 'topic': session.topic,
                'difficulty': session.difficulty, 'job_snapshot': copy.deepcopy(session.job_snapshot or {}),
            },
            'answers': [
                {
                    'question': self.public_question_snapshot(item.question_snapshot),
                    'answer': item.answer, 'feedback': copy.deepcopy(item.feedback or {}),
                    'feedback_status': item.status,
                }
                for item in session.answers.all().order_by('created_at', 'id')
            ],
        }

    def complete_summary(self, *, user, session_id, request_id, result=None, failure_code=''):
        with transaction.atomic():
            session = PracticeSession.objects.select_for_update().filter(user=user, pk=session_id).first()
            if session is None:
                raise NotFound()
            if str(session.summary_request_id) != str(request_id):
                return self.serialize_session(session)
            summary = copy.deepcopy(SUMMARY_EMPTY)
            if failure_code:
                summary.update(status='failed', failure_code=failure_code)
                status = 'failed'
            else:
                summary.update(status='succeeded', **copy.deepcopy(result or {}))
                status = 'succeeded'
            session.summary = summary
            session.summary_attempt_log = _complete_attempt(
                session.summary_attempt_log, request_id, status, failure_code
            )
            session.save(update_fields=['summary', 'summary_attempt_log', 'updated_at'])
            return self.serialize_session(session)
