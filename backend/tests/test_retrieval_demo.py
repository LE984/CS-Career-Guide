"""登录用户的独立演示接口；禁止数据库访问，执行真实文本检索。"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'career_platform.test_settings'

import django
django.setup()

from django.test import SimpleTestCase
from rest_framework.test import APIClient
from career_platform.rag.demo import DEMO_QUESTIONS
from career_platform.rag.service import InterviewRagService
from career_platform import composition


class RetrievalDemoTests(SimpleTestCase):
    path = '/api/career-platform/questions/demo-retrieve/'

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(SimpleNamespace(pk=123, is_authenticated=True))
        self.body = dict(query='集合', role='Java后端', topic='集合', difficulty='easy', top_k=5)

    def post(self, **changes):
        return self.client.post(self.path, self.body | changes, format='json')

    def test_authentication_required(self):
        self.assertEqual(APIClient().post(self.path, self.body, format='json').status_code, 401)

    def test_real_strategy_filters_and_marks_demo_without_database(self):
        response = self.post()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['is_demo'])
        self.assertEqual(response.data['count'], 3)
        eligible = {q['id'] for q in DEMO_QUESTIONS if q['permission_status'] == 'allowed'
                    and q['role'] == 'Java后端' and q['topic'] == '集合' and q['difficulty'] == 'easy'}
        self.assertEqual({r['question_id'] for r in response.data['results']}, eligible)
        self.assertTrue(all(r['is_demo'] for r in response.data['results']))

    def test_query_changes_ranking_top_k_and_unknown_topic_is_empty(self):
        response = self.post(query='ArrayList', top_k=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('ArrayList', response.data['results'][0]['question'])
        self.assertEqual(self.post(topic='不存在的知识点').data['results'], [])

    def test_sources_resolve_to_demo_material_and_restricted_never_leaks(self):
        source = {q['id']: q for q in DEMO_QUESTIONS}
        for query in ('集合', '待审核', '受限'):
            for result in self.post(query=query).data['results']:
                original = source[result['question_id']]
                self.assertEqual(original['permission_status'], 'allowed')
                evidence = next(e for e in result['evidence'] if e['field_path'] == 'source')
                self.assertEqual(evidence['quote'], original['source'])

    def test_input_validation_and_unsupported_methods(self):
        for body in ({'top_k': 21}, {'query': 'x' * 501}, {'difficulty': 'other'}, {'question_ids': []}):
            response = self.post(**body)
            self.assertEqual(response.status_code, 400, response.data)
            self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
        self.assertEqual(self.client.get(self.path).status_code, 405)

    def test_regular_retrieval_is_isolated_from_demo_material(self):
        retriever = Mock()
        retriever.retrieve.return_value = []
        service = InterviewRagService(retriever=retriever)
        with patch.dict(composition.services, rag=service):
            response = self.client.post('/api/career-platform/questions/retrieve/', {
                'role': 'Java后端', 'request_id': 'de000000-0000-4000-8000-000000000001',
            }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['results'], [])
        self.assertEqual(response.data['count'], 0)
        self.assertIn('retrieval_id', response.data)
        self.assertNotIn('is_demo', response.data)
        retriever.retrieve.assert_called_once_with(
            query='Java后端', role='Java后端', topic='', difficulty='easy', top_k=5,
        )
        # 正式检索无命中不得补演示题；演示入口仍保留原有独立材料。
        self.assertEqual(self.post().data['count'], 3)
