"""Member 1: traceable job, company and interview-question catalog.

Imports validate every record before writing, deduplicate by a stable key, and
only expose ``allowed`` records through the public queries. Question index
notification is scheduled after the database transaction commits.
"""
from __future__ import annotations

import logging
import uuid

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..composition_base import UnavailableService
from .repository import DjangoCatalogRepository
from .source import (
    PERMISSION_STATUSES,
    QUESTION_DIFFICULTIES,
    JsonSourceAdapter,
    RecordInvalid,
    boolean,
    choice,
    datetime_value,
    decimal,
    dedupe_key,
    string_list,
    text,
    url,
)

logger = logging.getLogger(__name__)

COMMON_FIELDS = {
    'id', 'source', 'source_url', 'permission_status', 'collected_at',
    'dedupe_key', 'is_demo',
}
COMPANY_FIELDS = {
    'name', 'city', 'scale', 'nature', 'ranking', 'avg_salary', 'industry',
    'website', 'public_profile', 'description', 'warning_info', 'verified_at',
}
JOB_FIELDS = {
    'company_id', 'company', 'title', 'salary_min', 'salary_max', 'city',
    'experience', 'education', 'description', 'requirements', 'skills',
    'valid_until',
}
QUESTION_FIELDS = {
    'category', 'role', 'topic', 'difficulty', 'question', 'key_points',
    'reference_answer', 'tags',
}
COMPANY_SCALES = ('small', 'medium', 'large', 'enterprise')
COMPANY_NATURES = ('private', 'state', 'foreign', 'joint', 'startup')
COMPANY_RANKINGS = ('red', 'normal', 'black')

QUERY_FILTERS = {
    'companies': ('city',),
    'jobs': ('city', 'role'),
    'questions': ('role', 'topic', 'difficulty'),
}


class CatalogService(UnavailableService):
    def __init__(self, *, source_adapter=None, index_notifier=None, repository=None):
        super().__init__('catalog')
        self.source_adapter = source_adapter or JsonSourceAdapter()
        self.index_notifier = index_notifier
        self.repository = repository or DjangoCatalogRepository()

    # -- public queries ---------------------------------------------------
    def companies(self, *, user, data: dict) -> dict:
        self._reject_unsupported_filters('companies', data)
        return self.repository.companies(data)

    def jobs(self, *, user, data: dict) -> dict:
        self._reject_unsupported_filters('jobs', data)
        return self.repository.jobs(data)

    def questions(self, *, user, data: dict) -> dict:
        self._reject_unsupported_filters('questions', data)
        return self.repository.questions(data)

    # -- import -----------------------------------------------------------
    def import_batch(self, *, user, data: dict) -> dict:
        if not getattr(user, 'is_staff', False):
            raise PermissionDenied('仅管理员可以导入目录数据')

        kind = data['kind']
        records = data['records']
        dry_run = bool(data.get('dry_run', True))
        validators = {
            'companies': self._validate_company,
            'jobs': self._validate_job,
            'questions': self._validate_question,
        }
        if kind not in validators:
            raise ValidationError({'kind': '不支持的导入类型'})
        validator = validators[kind]

        canonical, errors = [], {}
        for index, raw in enumerate(records):
            try:
                normalized = self._adapt(kind, raw)
                if not isinstance(normalized, dict):
                    raise RecordInvalid('record', '必须是对象')
                canonical.append(validator(normalized))
            except RecordInvalid as error:
                errors[f'records[{index}].{error.field}'] = error.message
        if errors:
            raise ValidationError(errors)

        if dry_run:
            return self.repository.preview(kind, canonical)

        result = self.repository.save_batch(kind, canonical)
        allowed_ids = result.pop('_allowed_question_ids', [])
        if allowed_ids and self.index_notifier is not None:
            transaction.on_commit(lambda: self._notify_index(allowed_ids))
            result['index_notification'] = 'scheduled'
        elif allowed_ids:
            result['index_notification'] = 'not_configured'
        else:
            result['index_notification'] = 'not_required'
        return result

    # -- validation -------------------------------------------------------
    def _adapt(self, kind: str, raw):
        adapter = self.source_adapter
        for name in ('normalize', 'adapt'):
            method = getattr(adapter, name, None)
            if callable(method):
                return method(kind=kind, record=raw)
        if callable(adapter):
            return adapter(kind, raw)
        raise TypeError('source_adapter 必须提供 normalize/adapt 方法或可调用')

    def _common(self, record: dict) -> dict:
        values = {'source': text(record.get('source'), 'source', required=True, max_length=255)}
        if 'source_url' in record:
            values['source_url'] = url(record['source_url'], 'source_url')
        if 'permission_status' in record:
            values['permission_status'] = choice(
                record['permission_status'], 'permission_status', PERMISSION_STATUSES,
                required=True)
        if 'collected_at' in record:
            values['collected_at'] = datetime_value(record['collected_at'], 'collected_at')
        if 'is_demo' in record:
            values['is_demo'] = boolean(record['is_demo'], 'is_demo')
        return values

    def _reject_unknown(self, record: dict, allowed: set[str]):
        unknown = sorted(set(record) - COMMON_FIELDS - allowed)
        if unknown:
            raise RecordInvalid(unknown[0], '不支持的字段')

    @staticmethod
    def _dedupe_value(record: dict, kind: str, *parts: str) -> str:
        if 'dedupe_key' in record:
            return text(record['dedupe_key'], 'dedupe_key', required=True, max_length=128)
        return dedupe_key(kind, *parts)

    def _validate_company(self, record: dict) -> dict:
        self._reject_unknown(record, COMPANY_FIELDS)
        values = self._common(record)
        name = text(record.get('name'), 'name', required=True, max_length=255)
        city = text(record.get('city'), 'city', required=True, max_length=100)
        values.update(name=name, city=city)
        if 'scale' in record:
            values['scale'] = choice(record['scale'], 'scale', COMPANY_SCALES)
        if 'nature' in record:
            values['nature'] = choice(record['nature'], 'nature', COMPANY_NATURES)
        if 'ranking' in record:
            values['ranking'] = choice(record['ranking'], 'ranking', COMPANY_RANKINGS)
        if 'avg_salary' in record:
            values['avg_salary'] = decimal(record['avg_salary'], 'avg_salary')
        if 'industry' in record:
            values['industry'] = text(record['industry'], 'industry', max_length=100,
                                      allow_blank=True)
        if 'website' in record:
            values['website'] = url(record['website'], 'website')
        if 'public_profile' in record:
            values['public_profile'] = text(
                record['public_profile'], 'public_profile', max_length=20000, allow_blank=True)
        if 'description' in record:
            values['description'] = text(
                record['description'], 'description', max_length=20000, allow_blank=True)
        if 'warning_info' in record:
            values['warning_info'] = text(
                record['warning_info'], 'warning_info', max_length=20000, allow_blank=True)
        if 'verified_at' in record:
            values['verified_at'] = datetime_value(record['verified_at'], 'verified_at')
        values['dedupe_key'] = self._dedupe_value(record, 'companies', values['source'], name, city)
        return values

    def _validate_job(self, record: dict) -> dict:
        self._reject_unknown(record, JOB_FIELDS)
        values = self._common(record)
        title = text(record.get('title'), 'title', required=True, max_length=255)

        company_id = record.get('company_id')
        company_name = record.get('company')
        if company_id is not None and (isinstance(company_id, bool) or not isinstance(company_id, int)
                                       or company_id < 1):
            raise RecordInvalid('company_id', '必须是正整数')
        if company_name is not None:
            company_name = text(company_name, 'company', required=True, max_length=255)
        if company_id is None and company_name is None:
            raise RecordInvalid('company_id', '必须提供 company_id 或 company')
        try:
            company = self.repository.resolve_company(
                company_id=company_id, name=company_name,
                city=text(record['city'], 'city', max_length=100, allow_blank=True)
                if 'city' in record else None,
            )
        except LookupError as error:
            field = 'company_id' if str(error) == 'company_id' else 'company'
            raise RecordInvalid(field, '企业不存在，请先导入企业') from None

        city = (text(record['city'], 'city', max_length=100, allow_blank=True)
                if 'city' in record else '') or company.city
        values.update(company_id=company.id, title=title, city=city)

        salary_min = decimal(record.get('salary_min'), 'salary_min') if 'salary_min' in record else None
        salary_max = decimal(record.get('salary_max'), 'salary_max') if 'salary_max' in record else None
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise RecordInvalid('salary_max', '不能小于最低薪资')
        if 'salary_min' in record:
            values['salary_min'] = salary_min
        if 'salary_max' in record:
            values['salary_max'] = salary_max

        for field, max_length in (('experience', 100), ('education', 100)):
            if field in record:
                values[field] = text(record[field], field, max_length=max_length, allow_blank=True)

        description = (text(record['description'], 'description', max_length=20000,
                            allow_blank=True) if 'description' in record else '')
        requirements = (text(record['requirements'], 'requirements', max_length=20000,
                             allow_blank=True) if 'requirements' in record else '')
        if not description and requirements:
            description = requirements
        if not requirements and description:
            requirements = description
        if not description and not requirements:
            raise RecordInvalid('description', 'description 与 requirements 至少提供一项')
        values['description'] = description
        values['requirements'] = requirements

        if 'skills' in record:
            values['skills'] = string_list(record['skills'], 'skills')
        if 'valid_until' in record:
            values['valid_until'] = datetime_value(record['valid_until'], 'valid_until')

        values['dedupe_key'] = self._dedupe_value(
            record, 'jobs', values['source'], str(company.id), title, city)
        return values

    def _validate_question(self, record: dict) -> dict:
        self._reject_unknown(record, QUESTION_FIELDS)
        if 'id' in record:
            try:
                uuid.UUID(str(record['id']))
            except (ValueError, TypeError, AttributeError):
                raise RecordInvalid('id', '必须是 UUID') from None
        values = self._common(record)
        category = text(record.get('category'), 'category', required=True, max_length=100)
        role = text(record.get('role'), 'role', required=True, max_length=100)
        topic = text(record.get('topic'), 'topic', required=True, max_length=100)
        difficulty = choice(record.get('difficulty'), 'difficulty', QUESTION_DIFFICULTIES,
                            required=True)
        question = text(record.get('question'), 'question', required=True, max_length=20000)
        key_points = string_list(record.get('key_points'), 'key_points', required=True)
        reference_answer = text(
            record.get('reference_answer'), 'reference_answer', required=True, max_length=20000)
        values.update(category=category, role=role, topic=topic, difficulty=difficulty,
                      question=question, key_points=key_points,
                      reference_answer=reference_answer)
        if 'tags' in record:
            values['tags'] = string_list(record['tags'], 'tags')
        values['dedupe_key'] = self._dedupe_value(
            record, 'questions', values['source'], role, topic, question)
        return values

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _reject_unsupported_filters(kind: str, data: dict):
        allowed = set(QUERY_FILTERS[kind]) | {'page', 'page_size', 'q'}
        unsupported = sorted(set(data) - allowed)
        if unsupported:
            field = unsupported[0]
            raise ValidationError({field: f'{kind} 查询不支持该筛选条件'})

    def _notify_index(self, ids: list[str]):
        """Notify the optional question index after commit; the DB is authoritative."""
        notifier = self.index_notifier
        try:
            if hasattr(notifier, 'notify'):
                notifier.notify(kind='questions', ids=ids)
            else:
                notifier(kind='questions', ids=ids)
        except Exception:  # index failures must not roll back committed catalog data
            logger.exception('题库索引通知失败，数据已提交，索引需重试')
