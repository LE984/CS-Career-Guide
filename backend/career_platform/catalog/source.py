"""JSON source adapter and canonical value helpers for the catalog importer.

The adapter only maps input records into canonical Python values. Validation,
permission checks, persistence and index notification stay in the service and
repository layers so that a future source can reuse the same pipeline.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, time, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django.utils import timezone as django_timezone
from django.utils.dateparse import parse_date, parse_datetime

KINDS = ('companies', 'jobs', 'questions')
QUESTION_DIFFICULTIES = ('easy', 'medium', 'hard')
PERMISSION_STATUSES = ('pending', 'allowed', 'restricted')


class RecordInvalid(ValueError):
    """A single imported record is invalid; the message names the field."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f'{field}: {message}')


def text(value, field: str, *, required: bool = False, max_length: int | None = None,
         allow_blank: bool = False) -> str:
    if value is None:
        if required:
            raise RecordInvalid(field, '必填')
        return ''
    if not isinstance(value, str):
        raise RecordInvalid(field, '必须是字符串')
    cleaned = value.strip()
    if not cleaned and (required or not allow_blank):
        raise RecordInvalid(field, '不能为空')
    if max_length is not None and len(cleaned) > max_length:
        raise RecordInvalid(field, f'不能超过 {max_length} 个字符')
    return cleaned


def choice(value, field: str, allowed: tuple[str, ...], *, required: bool = False):
    if value is None:
        if required:
            raise RecordInvalid(field, '必填')
        return None
    if not isinstance(value, str):
        raise RecordInvalid(field, '必须是字符串')
    cleaned = value.strip().lower()
    if cleaned not in allowed:
        raise RecordInvalid(field, f'必须是 {"/".join(allowed)} 之一')
    return cleaned


def boolean(value, field: str) -> bool:
    if not isinstance(value, bool):
        raise RecordInvalid(field, '必须是布尔值')
    return value


def decimal(value, field: str, *, max_digits: int = 10, decimal_places: int = 2):
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        raise RecordInvalid(field, '必须是数字')
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise RecordInvalid(field, '必须是数字') from None
    if not parsed.is_finite():
        raise RecordInvalid(field, '必须是有限数字')
    if parsed < 0:
        raise RecordInvalid(field, '不能为负数')
    if parsed.as_tuple().exponent < -decimal_places:
        raise RecordInvalid(field, f'最多保留 {decimal_places} 位小数')
    integer_digits = len(parsed.as_tuple().digits) + parsed.as_tuple().exponent
    if integer_digits > max_digits - decimal_places:
        raise RecordInvalid(field, f'整数部分不能超过 {max_digits - decimal_places} 位')
    return parsed


def string_list(value, field: str, *, required: bool = False, max_items: int = 100,
                max_item_length: int = 1000) -> list[str]:
    if value is None:
        if required:
            raise RecordInvalid(field, '必填')
        return []
    if isinstance(value, str):
        parts = re.split(r'[,，]', value)
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        raise RecordInvalid(field, '必须是字符串数组')
    result: list[str] = []
    for item in parts:
        if not isinstance(item, str):
            raise RecordInvalid(field, '数组元素必须是字符串')
        cleaned = item.strip()
        if not cleaned:
            continue
        if len(cleaned) > max_item_length:
            raise RecordInvalid(field, f'单个元素不能超过 {max_item_length} 个字符')
        result.append(cleaned)
    if required and not result:
        raise RecordInvalid(field, '至少需要一项')
    if len(result) > max_items:
        raise RecordInvalid(field, f'最多 {max_items} 项')
    return result


def url(value, field: str) -> str:
    cleaned = text(value, field, allow_blank=True, max_length=1000)
    if not cleaned:
        return ''
    parsed = urlparse(cleaned)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise RecordInvalid(field, '必须是 http 或 https 地址')
    return cleaned


def datetime_value(value, field: str):
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        raw = value.strip()
        parsed = parse_datetime(raw)
        if parsed is None:
            parsed_date = parse_date(raw)
            if parsed_date is None:
                raise RecordInvalid(field, '必须是 ISO8601 日期或时间')
            parsed = datetime.combine(parsed_date, time.min)
    else:
        raise RecordInvalid(field, '必须是 ISO8601 日期或时间')
    if django_timezone.is_naive(parsed):
        parsed = django_timezone.make_aware(parsed, timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalized_text(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip().lower()


def dedupe_key(kind: str, *parts: str) -> str:
    """Stable, non-random key for records that do not supply one."""
    payload = '|'.join([kind, *(_normalized_text(str(part)) for part in parts)])
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


class JsonSourceAdapter:
    """Return a defensive copy; field validation is intentionally separate."""

    def normalize(self, *, kind: str, record):
        if not isinstance(record, dict):
            raise RecordInvalid('record', '必须是对象')
        return dict(record)
