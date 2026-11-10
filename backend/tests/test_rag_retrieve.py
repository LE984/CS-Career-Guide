"""正式检索编排的离线测试；不接数据库、模型或生产题库。"""
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'career_platform.test_settings')
import django
from django.apps import apps
if not apps.ready:
    django.setup()
from django.core.cache import cache
from rest_framework.exceptions import NotFound
from career_platform.errors import ModelUnavailable
from career_platform.rag.service import InterviewRagService
from career_platform.rag.retrieval import TextRetrievalStrategy
from test_text_retrieval import question


class RetrieveServiceTests(unittest.TestCase):
    def setUp(self):
        cache.clear()
        self.user = SimpleNamespace(pk=123)
        self.model = Mock()
        self.records = Mock()
        self.service = InterviewRagService(
            retriever=TextRetrievalStrategy([question()]),
            model_gateway=self.model, records=self.records,
        )
        self.data = dict(role='Java 后端', topic='集合', request_id='test-only')

    def tearDown(self):
        self.assertEqual(self.model.mock_calls, [])
        self.assertEqual(self.records.mock_calls, [])

    def test_real_strategy_and_json_evidence(self):
        result = self.service.retrieve(user=self.user, data=self.data)
        self.assertEqual(result['count'], 1)
        row = result['results'][0]
        self.assertEqual(row['question_id'], str(question()['id']))
        self.assertEqual(row['question'], question()['question'])
        self.assertEqual(row['key_points'], question()['key_points'])
        self.assertEqual(row['origin'], 'catalog')
        self.assertTrue(any(e['field_path'] == 'source' for e in row['evidence']))
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_normalized_arguments_and_jd_priority(self):
        spy = Mock()
        spy.retrieve.return_value = []
        self.service.retriever = spy
        self.service.retrieve(user=self.user, data=dict(
            self.data, role=' Java 后端 ', topic=' 集合 ', jd_text=' List 与 Set ',
            difficulty='medium', top_k=2,
        ))
        spy.retrieve.assert_called_once_with(
            query='List 与 Set', role='Java 后端', topic='集合',
            difficulty='medium', top_k=2,
        )

    def test_no_topic_uses_role_and_defaults(self):
        spy = Mock()
        spy.retrieve.return_value = []
        self.service.retriever = spy
        self.service.retrieve(user=self.user, data={'role': ' Java 后端 ', 'jd_text': ' '})
        spy.retrieve.assert_called_once_with(
            query='Java 后端', role='Java 后端', topic='', difficulty='easy', top_k=5,
        )

    def test_no_match_is_explicit(self):
        result = self.service.retrieve(user=self.user, data=dict(self.data, topic='火星地质'))
        self.assertEqual(result['results'], [])
        self.assertEqual(result['count'], 0)
        self.assertTrue(result['message'])

    def test_permissions_and_conditions_still_filter(self):
        self.service.retriever = TextRetrievalStrategy([
            question(1), question(2, permission_status='pending'),
            question(3, permission_status='restricted'), question(4, role='Python 后端'),
            question(5, difficulty='hard'), question(6, topic='并发'),
        ])
        result = self.service.retrieve(user=self.user, data=self.data)
        self.assertEqual([r['question_id'] for r in result['results']], [str(question()['id'])])

    def test_top_k_is_forwarded(self):
        self.service.retriever = TextRetrievalStrategy([question(1), question(2)])
        result = self.service.retrieve(user=self.user, data=dict(self.data, top_k=1))
        self.assertEqual(result['count'], 1)

    def test_missing_dependency_stays_unavailable(self):
        with self.assertRaises(ModelUnavailable):
            InterviewRagService().retrieve(user=self.user, data=self.data)

    def test_job_resolution_not_silently_ignored(self):
        spy = Mock()
        self.service.retriever = spy
        with patch('career_platform.rag.service.Job') as jobs:
            jobs.objects.filter.return_value.first.return_value = None
            with self.assertRaises(NotFound):
                self.service.retrieve(user=self.user, data=dict(self.data, job_id=12))
        spy.retrieve.assert_not_called()

    def test_adapter_failure_not_disguised_as_empty(self):
        self.service.retriever = Mock()
        self.service.retriever.retrieve.side_effect = RuntimeError('offline adapter unavailable')
        with self.assertRaises(RuntimeError):
            self.service.retrieve(user=self.user, data=self.data)

    def test_input_not_mutated_and_no_session_authorization(self):
        original = self.data.copy()
        result = self.service.retrieve(user=self.user, data=self.data)
        self.assertEqual(self.data, original)
        self.assertNotIn('session_id', result)
        self.assertNotIn('presented_questions', result)
        key = f"career-platform:retrieval:{self.user.pk}:{result['retrieval_id']}"
        self.assertEqual(cache.get(key)['results'], result['results'])
        result['results'][0]['question'] = 'client change'
        self.assertNotEqual(cache.get(key)['results'][0]['question'], 'client change')
        self.assertIsNone(cache.get(f"career-platform:retrieval:999:{result['retrieval_id']}"))


if __name__ == '__main__':
    unittest.main()
