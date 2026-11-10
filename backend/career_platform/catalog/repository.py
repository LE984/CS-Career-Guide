"""ORM repository for the catalog module.

Queries only expose records whose permission status is ``allowed``. Imports are
transactional and deduplicated by the stable key produced by CatalogService.
"""
from __future__ import annotations

from datetime import timezone as dt_timezone

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from company_reviews.models import Company, Job

from ..models import InterviewQuestion


def _iso(value):
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, dt_timezone.utc)
    return value.astimezone(dt_timezone.utc).isoformat()


def _money(value):
    return None if value is None else str(value)


def _company_row(obj: Company) -> dict:
    return {
        'id': obj.id,
        'name': obj.name,
        'city': obj.city,
        'scale': obj.scale,
        'nature': obj.nature,
        'ranking': obj.ranking,
        'avg_salary': _money(obj.avg_salary),
        'industry': obj.industry,
        'website': obj.website,
        'public_profile': obj.public_profile,
        'description': obj.description,
        'warning_info': obj.warning_info,
        'source': obj.source,
        'source_url': obj.source_url,
        'permission_status': obj.permission_status,
        'collected_at': _iso(obj.collected_at),
        'verified_at': _iso(obj.verified_at),
        'is_demo': obj.is_demo,
        'dedupe_key': obj.dedupe_key,
        'created_at': _iso(obj.created_at),
        'updated_at': _iso(obj.updated_at),
    }


def _job_row(obj: Job) -> dict:
    return {
        'id': obj.id,
        'company_id': obj.company_id,
        'company': {'id': obj.company_id, 'name': obj.company.name, 'city': obj.company.city},
        'title': obj.title,
        'salary_min': _money(obj.salary_min),
        'salary_max': _money(obj.salary_max),
        'city': obj.city,
        'experience': obj.experience,
        'education': obj.education,
        'description': obj.description,
        'requirements': obj.requirements,
        'skills': obj.skills or [],
        'source': obj.source,
        'source_url': obj.source_url,
        'permission_status': obj.permission_status,
        'collected_at': _iso(obj.collected_at),
        'valid_until': _iso(obj.valid_until),
        'is_demo': obj.is_demo,
        'dedupe_key': obj.dedupe_key,
        'created_at': _iso(obj.created_at),
    }


def _question_row(obj: InterviewQuestion) -> dict:
    return {
        'id': str(obj.id),
        'category': obj.category,
        'role': obj.role,
        'topic': obj.topic,
        'difficulty': obj.difficulty,
        'question': obj.question,
        'key_points': obj.key_points or [],
        'reference_answer': obj.reference_answer,
        'source': obj.source,
        'source_url': obj.source_url,
        'permission_status': obj.permission_status,
        'collected_at': _iso(obj.collected_at),
        'tags': obj.tags or [],
        'is_demo': obj.is_demo,
        'dedupe_key': obj.dedupe_key,
        'created_at': _iso(obj.created_at),
        'updated_at': _iso(obj.updated_at),
    }


class DjangoCatalogRepository:
    row_serializers = {
        'companies': _company_row,
        'jobs': _job_row,
        'questions': _question_row,
    }
    models = {
        'companies': Company,
        'jobs': Job,
        'questions': InterviewQuestion,
    }

    # -- public queries ---------------------------------------------------
    def companies(self, data: dict) -> dict:
        queryset = Company.objects.filter(permission_status='allowed')
        city = data.get('city')
        if city:
            queryset = queryset.filter(city__iexact=city)
        query = data.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(industry__icontains=query)
                | Q(description__icontains=query)
                | Q(public_profile__icontains=query)
            )
        return self._page(queryset.order_by('created_at', 'id'), data, 'companies')

    def jobs(self, data: dict) -> dict:
        queryset = Job.objects.select_related('company').filter(permission_status='allowed')
        now = timezone.now()
        queryset = queryset.filter(Q(valid_until__isnull=True) | Q(valid_until__gte=now))
        city = data.get('city')
        if city:
            queryset = queryset.filter(
                Q(city__iexact=city) | Q(company__city__iexact=city)
            )
        role = data.get('role')
        if role:
            queryset = queryset.filter(
                Q(title__icontains=role)
                | Q(description__icontains=role)
                | Q(requirements__icontains=role)
            )
        query = data.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(requirements__icontains=query)
                | Q(company__name__icontains=query)
            )
        return self._page(queryset.order_by('created_at', 'id'), data, 'jobs')

    def questions(self, data: dict) -> dict:
        queryset = InterviewQuestion.objects.filter(permission_status='allowed')
        role = data.get('role')
        if role:
            queryset = queryset.filter(role=role)
        topic = data.get('topic')
        if topic:
            queryset = queryset.filter(topic=topic)
        difficulty = data.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        query = data.get('q')
        if query:
            queryset = queryset.filter(
                Q(question__icontains=query)
                | Q(reference_answer__icontains=query)
                | Q(topic__icontains=query)
                | Q(category__icontains=query)
                | Q(role__icontains=query)
            )
        return self._page(queryset.order_by('created_at', 'id'), data, 'questions')

    # -- import support ---------------------------------------------------
    def resolve_company(self, *, company_id=None, name=None, city=None):
        if company_id is not None:
            company = Company.objects.filter(pk=company_id).first()
            if company is None:
                raise LookupError('company_id')
            if name and company.name != name:
                raise LookupError('company')
            return company
        if name:
            queryset = Company.objects.filter(name=name)
            if city:
                queryset = queryset.filter(city__iexact=city)
            company = queryset.order_by('id').first()
            if company is None:
                raise LookupError('company')
            return company
        raise LookupError('company_id')

    def preview(self, kind: str, records: list[dict]) -> dict:
        model = self.models[kind]
        rows, counts = [], {'created': 0, 'updated': 0, 'unchanged': 0}
        planned: dict[str, dict] = {}
        for index, values in enumerate(records):
            key = values['dedupe_key']
            if key in planned:
                action = 'updated' if planned[key]['values'] != values else 'unchanged'
                row_id = planned[key]['id']
            else:
                existing = model.objects.filter(dedupe_key=key).first()
                if existing is None:
                    action = 'created'
                    row_id = None
                elif self._would_change(existing, values):
                    action = 'updated'
                    row_id = self._row_id(kind, existing.pk)
                else:
                    action = 'unchanged'
                    row_id = self._row_id(kind, existing.pk)
            planned[key] = {'values': values, 'id': row_id}
            counts[action] += 1
            rows.append({'index': index, 'id': row_id, 'action': action})
        return {'kind': kind, 'dry_run': True, **counts, 'records': rows}

    def save_batch(self, kind: str, records: list[dict]) -> dict:
        model = self.models[kind]
        rows, counts = [], {'created': 0, 'updated': 0, 'unchanged': 0}
        allowed_ids: list[str] = []
        with transaction.atomic():
            for index, values in enumerate(records):
                existing = (model.objects.select_for_update()
                            .filter(dedupe_key=values['dedupe_key']).first())
                if existing is None:
                    create_values = dict(values)
                    create_values.setdefault('collected_at', timezone.now())
                    obj = model.objects.create(**create_values)
                    action = 'created'
                else:
                    changed = self._apply(existing, values)
                    if changed:
                        existing.save()
                    action = 'updated' if changed else 'unchanged'
                    obj = existing
                counts[action] += 1
                rows.append({'index': index, 'id': self._row_id(kind, obj.pk),
                             'action': action})
                if (kind == 'questions' and action in ('created', 'updated')
                        and obj.permission_status == 'allowed'):
                    allowed_ids.append(str(obj.pk))
        return {
            'kind': kind,
            'dry_run': False,
            **counts,
            'records': rows,
            '_allowed_question_ids': allowed_ids,
        }

    # -- internals --------------------------------------------------------
    @staticmethod
    def _row_id(kind: str, pk):
        return str(pk) if kind == 'questions' else pk

    @staticmethod
    def _apply(obj, values: dict) -> bool:
        changed = False
        for field, value in values.items():
            if field == 'dedupe_key':
                continue
            if getattr(obj, field) != value:
                setattr(obj, field, value)
                changed = True
        return changed

    @staticmethod
    def _would_change(obj, values: dict) -> bool:
        return any(field != 'dedupe_key' and getattr(obj, field) != value
                   for field, value in values.items())

    def _page(self, queryset, data: dict, kind: str) -> dict:
        page = int(data.get('page', 1))
        page_size = int(data.get('page_size', 20))
        offset = (page - 1) * page_size
        rows = list(queryset[offset:offset + page_size])
        serialize = self.row_serializers[kind]
        return {
            'count': queryset.count(),
            'page': page,
            'page_size': page_size,
            'results': [serialize(row) for row in rows],
        }
