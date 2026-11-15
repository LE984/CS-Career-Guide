"""Validate the xiaolincoding question dataset with the catalog import primitives.

This is an offline, read-only data check. It does not import the Django app
registry, touch a database, or execute any downloaded content.

Usage:
    python data/career-platform/validate_xiaolincoding.py [path] [--report out.json]
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(USE_TZ=True, TIME_ZONE='UTC')

from career_platform.catalog.source import (  # noqa: E402
    PERMISSION_STATUSES,
    QUESTION_DIFFICULTIES,
    RecordInvalid,
    boolean,
    choice,
    datetime_value,
    dedupe_key,
    string_list,
    text,
    url,
)

COMMON_FIELDS = {
    'id', 'source', 'source_url', 'permission_status', 'collected_at',
    'dedupe_key', 'is_demo',
}
QUESTION_FIELDS = {
    'category', 'role', 'topic', 'difficulty', 'question', 'key_points',
    'reference_answer', 'tags',
}


def validate_question(record: dict) -> dict:
    unknown = sorted(set(record) - COMMON_FIELDS - QUESTION_FIELDS)
    if unknown:
        raise RecordInvalid(unknown[0], '不支持的字段')
    values = {'source': text(record.get('source'), 'source', required=True, max_length=255)}
    if 'source_url' in record:
        values['source_url'] = url(record['source_url'], 'source_url')
    if 'permission_status' in record:
        values['permission_status'] = choice(
            record['permission_status'], 'permission_status', PERMISSION_STATUSES, required=True)
    if 'collected_at' in record:
        values['collected_at'] = datetime_value(record['collected_at'], 'collected_at')
    if 'is_demo' in record:
        values['is_demo'] = boolean(record['is_demo'], 'is_demo')
    if 'id' in record:
        try:
            uuid.UUID(str(record['id']))
        except (ValueError, TypeError, AttributeError):
            raise RecordInvalid('id', '必须是 UUID') from None
    category = text(record.get('category'), 'category', required=True, max_length=100)
    role = text(record.get('role'), 'role', required=True, max_length=100)
    topic = text(record.get('topic'), 'topic', required=True, max_length=100)
    difficulty = choice(record.get('difficulty'), 'difficulty', QUESTION_DIFFICULTIES,
                        required=True)
    question = text(record.get('question'), 'question', required=True, max_length=20000)
    key_points = string_list(record.get('key_points'), 'key_points', required=True)
    reference_answer = text(record.get('reference_answer'), 'reference_answer',
                            required=True, max_length=20000)
    values.update(category=category, role=role, topic=topic, difficulty=difficulty,
                  question=question, key_points=key_points,
                  reference_answer=reference_answer)
    if 'tags' in record:
        values['tags'] = string_list(record['tags'], 'tags')
    values['dedupe_key'] = (text(record['dedupe_key'], 'dedupe_key', required=True, max_length=128)
                            if 'dedupe_key' in record
                            else dedupe_key('questions', values['source'], role, topic, question))
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?',
                        default=str(REPO_ROOT / 'data/career-platform/xiaolincoding-questions.json'))
    parser.add_argument('--report', help='可选：把完整校验报告写入该 JSON 文件')
    args = parser.parse_args()

    with open(args.path, encoding='utf-8') as handle:
        dataset = json.load(handle)
    records = dataset.get('questions')
    if not isinstance(records, list):
        print('dataset.questions is missing or not a list', file=sys.stderr)
        return 1

    errors = []
    keys = Counter()
    questions = Counter()
    for index, record in enumerate(records):
        try:
            values = validate_question(record)
            keys[values['dedupe_key']] += 1
            questions[values['question']] += 1
        except RecordInvalid as error:
            errors.append({'index': index, 'field': error.field, 'message': error.message})

    duplicate_keys = [key for key, count in keys.items() if count > 1]
    duplicate_questions = [question for question, count in questions.items() if count > 1]
    report = {
        'records': len(records),
        'valid': len(records) - len(errors),
        'errors': errors,
        'duplicate_dedupe_keys': duplicate_keys,
        'duplicate_questions': duplicate_questions,
        'permission_status': dict(Counter(r.get('permission_status') for r in records)),
        'difficulty': dict(Counter(r.get('difficulty') for r in records)),
        'topics': dict(Counter(r.get('topic') for r in records)),
        'key_points_min': min(len(r['key_points']) for r in records),
        'key_points_max': max(len(r['key_points']) for r in records),
        'answer_len_min': min(len(r['reference_answer']) for r in records),
        'answer_len_max': max(len(r['reference_answer']) for r in records),
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n',
                                     encoding='utf-8')

    # Keep stdout ASCII-only so the command also works in GBK consoles.
    print(json.dumps({
        'records': report['records'],
        'valid': report['valid'],
        'errors': len(errors),
        'duplicate_dedupe_keys': len(duplicate_keys),
        'duplicate_questions': len(duplicate_questions),
    }, ensure_ascii=True))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
