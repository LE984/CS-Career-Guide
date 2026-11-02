from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.authtoken.models import Token

from ai_integration.models import SeniorAdvice
from ai_integration.serializers import SeniorAdviceSerializer
from career_evaluation.models import ComputerCareer
from career_evaluation.views import ComputerCareerViewSet


class CompanyBrowseTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='browse-test', password='test-only')
        cls.token = Token.objects.create(user=cls.user).key
        ComputerCareer.objects.bulk_create([
            ComputerCareer(position_name=f'岗位 {i}', company_name='目标企业' if i == 1204 else '示例企业',
                           address='长沙' if i % 2 else '北京', salary_range='10K', industry='软件',
                           update_date=date(2026, 1, 1) + timedelta(days=1205-i), position_details='Vue 开发',
                           position_source_url='https://example.com/jobs') for i in range(1205)
        ])
        SeniorAdvice.objects.bulk_create([
            SeniorAdvice(company='目标企业' if i % 3 == 0 else '示例企业', position=f'岗位 {i}', senior_name='测试学长',
                         graduation_year='2025', current_company='', salary_info='', advice='测试建议',
                         rating=1+i%5, user=cls.user, is_approved=True) for i in range(61)
        ])
        SeniorAdvice.objects.create(company='未审核', position='岗位', senior_name='测试', graduation_year='2025',
                                   advice='不可出现在公开列表', rating=5, is_approved=False)

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token}')

    def test_jobs_are_bounded_and_use_stable_record_order(self):
        request = APIRequestFactory().get('/api/career-evaluation/computer-careers/', {'page': 2, 'page_size': 10})
        force_authenticate(request, self.user)
        with CaptureQueriesContext(connection) as queries:
            response = ComputerCareerViewSet.as_view({'get': 'list'})(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1205)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['results'][0]['position_name'], '岗位 10')
        self.assertEqual(len(queries), 2)
        self.assertIn('LIMIT 10 OFFSET 10', queries[-1]['sql'])

    def test_job_search_includes_records_beyond_first_hundred(self):
        response = self.client.get('/api/career-evaluation/computer-careers/', {'search': '目标企业'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['position_name'], '岗位 1204')

    def test_jobs_preserve_address_filter_and_bound_page_size(self):
        response = self.client.get('/api/career-evaluation/computer-careers/', {'address': '长沙', 'page_size': 9999})
        self.assertEqual(len(response.data['results']), 100)
        self.assertTrue(all(row['address'] == '长沙' for row in response.data['results']))
        self.assertEqual(self.client.get('/api/career-evaluation/computer-careers/', {'page': 999999}).status_code, 404)

    def test_advice_pages_are_distinct_and_limited(self):
        first = self.client.get('/api/ai/senior-advice/').data
        second = self.client.get('/api/ai/senior-advice/', {'page': 2}).data
        self.assertEqual(first['count'], 61)
        self.assertEqual(len(first['results']), 10)
        self.assertFalse(set(row['id'] for row in first['results']) & set(row['id'] for row in second['results']))
        self.assertEqual(len(self.client.get('/api/ai/senior-advice/', {'page_size': 9999}).data['results']), 50)

    def test_advice_search_sort_and_empty_response(self):
        data = self.client.get('/api/ai/senior-advice/', {'search': '目标企业', 'ordering': 'rating'}).data
        self.assertEqual(data['count'], 21)
        ratings = [row['rating'] for row in data['results']]
        self.assertEqual(ratings, sorted(ratings, reverse=True))
        self.assertTrue(all(row['company'] == '目标企业' for row in data['results']))
        empty = self.client.get('/api/ai/senior-advice/', {'search': '不存在'}).data
        self.assertEqual(empty['count'], 0)
        self.assertEqual(empty['results'], [])

    def test_invalid_advice_query_and_page_are_errors(self):
        self.assertEqual(self.client.get('/api/ai/senior-advice/', {'ordering': 'invalid'}).status_code, 400)
        self.assertEqual(self.client.get('/api/ai/senior-advice/', {'page': 9999}).status_code, 404)

    def test_optional_form_fields_can_be_empty_or_omitted(self):
        body = {'company': '测试公司', 'position': '开发', 'senior_name': '测试', 'graduation_year': '2025',
                'advice': '有效建议', 'rating': 4, 'pros': ['导师指导'], 'cons': []}
        for extra in ({}, {'current_company': '', 'salary_info': ''}):
            response = self.client.post('/api/ai/senior-advice/', {**body, **extra}, format='json')
            self.assertEqual(response.status_code, 201)
            self.assertTrue(response.data['success'])
            self.assertIn('message', response.data)
            row = SeniorAdvice.objects.get(pk=response.data['data']['id'])
            self.assertEqual(row.current_company, '')
            self.assertEqual(row.salary_info, '')
            self.assertFalse(row.is_approved)
            self.assertEqual(row.user, self.user)

    def test_field_validation_returns_actionable_errors(self):
        response = self.client.post('/api/ai/senior-advice/', {'rating': 10, 'graduation_year': 'oops'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('rating', response.data['errors'])
        self.assertIn('graduation_year', response.data['errors'])
        self.assertIn('company', response.data['errors'])
        self.assertFalse(SeniorAdviceSerializer(data={'rating': float('nan')}).is_valid())

    def test_database_failure_does_not_look_like_empty_data_or_leak_details(self):
        cases = [
            ('career_evaluation.views.ComputerCareerViewSet.get_queryset', '/api/career-evaluation/computer-careers/', 'JOBS_UNAVAILABLE'),
            ('company_reviews.views.JobFairViewSet.get_queryset', '/api/company-reviews/job-fairs/', 'JOB_FAIRS_UNAVAILABLE'),
            ('ai_integration.senior_advice_views.SeniorAdvice.objects.filter', '/api/ai/senior-advice/', 'ADVICE_UNAVAILABLE'),
        ]
        for target, url, code in cases:
            with patch(target, side_effect=DatabaseError('private connection details')):
                response = self.client.get(url)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.data['code'], code)
            self.assertNotIn('private connection details', str(response.data))

    def test_new_advice_endpoint_still_requires_authentication(self):
        self.client.credentials()
        response = self.client.get('/api/ai/senior-advice/')
        self.assertEqual(response.status_code, 401)
