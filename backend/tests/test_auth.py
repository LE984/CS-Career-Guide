"""Run: python -m django test tests.test_auth --settings=tests.auth_settings"""

import ast
import json
import logging
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory

from tests.auth_urls import DefaultPermissionProbe, stream_events
from cs_career_guide.middleware import ApiTokenRequiredMiddleware


class ExistingFrontendContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='api-contract', password='test-password')
        cls.token = Token.objects.create(user=cls.user)

    def test_frontend_paths_resolve_to_existing_business_actions(self):
        from django.urls import resolve
        for path, view_class, action in [
            ('/api/resumes/my/', 'ResumeViewSet', 'my'),
            ('/api/resumes/upload_avatar/', 'ResumeViewSet', 'upload_avatar'),
            ('/api/resumes/delete_avatar/', 'ResumeViewSet', 'delete_avatar'),
            ('/api/company-reviews/company-info/', 'CompanyInfoViewSet', 'list'),
        ]:
            with self.subTest(path=path):
                callback = resolve(path).func
                self.assertEqual(callback.cls.__name__, view_class)
                self.assertIn(action, callback.actions.values())

    def test_resume_save_reload_and_clear_round_trip(self):
        headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}
        payload = {
            'name': 'API contract', 'skills': 'Java',
            'education': [{'school': 'Test university', 'major': 'Computer science', 'period': '2023-2027'}],
            'projects': [{'name': 'Test project', 'role': 'Developer', 'period': '2026', 'description': 'Real API test'}],
        }
        saved = self.client.post('/api/resumes/my/', json.dumps(payload), content_type='application/json', **headers)
        self.assertEqual(saved.status_code, 200, saved.content)
        loaded = self.client.get('/api/resumes/my/', **headers).json()
        self.assertEqual(loaded['name'], payload['name'])
        self.assertEqual(loaded['projects'][0]['name'], 'Test project')
        # A second save includes IDs returned by the real nested serializers.
        loaded.update(skills='', education=[], projects=[])
        updated = self.client.post('/api/resumes/my/', json.dumps(loaded), content_type='application/json', **headers)
        self.assertEqual(updated.status_code, 200, updated.content)
        reloaded = self.client.get('/api/resumes/my/', **headers).json()
        self.assertEqual(reloaded['education'], [])
        self.assertEqual(reloaded['projects'], [])
        self.assertEqual(reloaded['skills'], '')


class ApiAuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='auth-test', password='test-password')
        cls.token = Token.objects.create(user=cls.user)

    def headers(self):
        return {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    def test_all_business_methods_reject_missing_invalid_and_malformed_tokens(self):
        paths = [
            '/api/career-paths/', '/api/company-reviews/companies/',
            '/api/company-reviews/companies/1/', '/api/company-reviews/companies/submit/',
            '/api/company-reviews/company-info/', '/api/company-reviews/job-fairs/',
            '/api/career-evaluation/computer-careers/', '/api/resumes/my/',
            '/api/ai/llm/chat/', '/api/career-report/', '/api/users/profile/',
            '/api/users/auth/logout/', '/api/future-probe/', '/api/unknown-new-endpoint/',
            '/api/users/auth/login/extra/', '/api/users/auth/register/extra/',
        ]
        for path in paths:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD']:
                for authorization in [None, 'Token forged', 'Bearer forged', 'Token', 'Token a b', 'Token ☃']:
                    with self.subTest(path=path, method=method, authorization=authorization):
                        headers = {} if authorization is None else {'HTTP_AUTHORIZATION': authorization}
                        response = self.client.generic(method, path, **headers)
                        self.assertEqual(response.status_code, 401)
                        self.assertEqual(response['WWW-Authenticate'], 'Token')
                        if method != 'HEAD':
                            self.assertIn('detail', response.json())

    def test_valid_token_sets_identity_for_django_and_drf_views(self):
        response = self.client.get('/api/identity-probe/', **self.headers())
        self.assertEqual(response.json(), {'user': self.user.username, 'auth': self.token.key})
        response = self.client.get('/api/users/profile/', **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], self.user.username)
        response = self.client.get('/api/default-probe/', **self.headers())
        self.assertEqual(response.json(), {'user': self.user.username})

    def test_real_company_and_career_views_preserve_authenticated_user(self):
        for path in ['/api/company-reviews/companies/', '/api/company-reviews/company-info/',
                     '/api/company-reviews/job-fairs/', '/api/career-evaluation/computer-careers/']:
            # Stop before database queries against the legacy unmanaged company tables.
            from django.urls import resolve
            view = resolve(path).func.cls
            instance = view()
            instance.action_map = {'get': 'list'}
            request = instance.initialize_request(APIRequestFactory().get(path, **self.headers()))
            self.assertTrue(request.user.is_authenticated)
            self.assertEqual(request.user.pk, self.user.pk)

    def test_inactive_and_revoked_tokens_are_rejected(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        self.assertEqual(self.client.get('/api/users/profile/', **self.headers()).status_code, 401)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.token.delete()
        self.assertEqual(self.client.get('/api/users/profile/', **self.headers()).status_code, 401)

    def test_login_register_work_even_with_stale_authorization(self):
        for path, data, expected in [
            ('/api/users/auth/login/', {'username': 'auth-test', 'password': 'test-password'}, 200),
            ('/api/users/auth/register/', {'username': 'registered-test', 'password': 'test-password',
                                           'confirm_password': 'test-password'}, 201),
        ]:
            response = self.client.post(path, data=json.dumps(data), content_type='application/json',
                                        HTTP_AUTHORIZATION='Token stale-token')
            self.assertEqual(response.status_code, expected)
            self.assertIn('token', response.json())
            self.assertIn('user', response.json())
        response = self.client.post('/api/users/auth/login/', {'username': 'auth-test', 'password': 'bad'})
        self.assertEqual(response.status_code, 400)

    def test_logout_revokes_token(self):
        self.assertEqual(self.client.post('/api/users/auth/logout/', **self.headers()).status_code, 200)
        self.assertEqual(self.client.get('/api/users/profile/', **self.headers()).status_code, 401)

    def test_new_api_is_denied_despite_explicit_anonymous_override(self):
        self.assertEqual(self.client.get('/api/future-probe/').status_code, 401)
        self.assertEqual(self.client.get('/api/future-probe/', **self.headers()).status_code, 200)

    def test_drf_default_also_requires_auth_without_middleware(self):
        response = DefaultPermissionProbe.as_view()(APIRequestFactory().get('/api/default-probe/'))
        self.assertEqual(response.status_code, 401)

    def test_stream_is_not_consumed_by_middleware(self):
        stream_events.clear()
        response = self.client.post('/api/ai/llm/chat/', **self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(stream_events, [])
        self.assertEqual(list(response.streaming_content), [b'data: auth-test\n\n', b'data: [DONE]\n\n'])
        self.assertEqual(stream_events, ['started'])

    def test_real_django_chat_function_is_guarded_and_still_returns_a_lazy_stream(self):
        # Execute the actual view without importing optional AI libraries. Its
        # model boundary is mocked; never iterate its paid-model generator.
        source = Path(__file__).resolve().parents[1] / 'ai_integration/langgraph_views.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'llm_chat')
        conversations = Mock()
        conversations.get_or_create.return_value = (SimpleNamespace(context_aware=False), True)
        namespace = {
            'csrf_exempt': csrf_exempt, 'JsonResponse': JsonResponse,
            'StreamingHttpResponse': StreamingHttpResponse, 'time': time, 'json': json,
            'logger': Mock(spec=logging.Logger), 'AIConversation': SimpleNamespace(objects=conversations),
        }
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
        protected_view = ApiTokenRequiredMiddleware(namespace['llm_chat'])
        for headers in [{}, {'HTTP_AUTHORIZATION': 'Token fake'}]:
            request = APIRequestFactory().post('/api/ai/llm/chat/', {'message': 'test'}, format='json', **headers)
            self.assertEqual(protected_view(request).status_code, 401)
        conversations.get_or_create.assert_not_called()
        request = APIRequestFactory().post('/api/ai/llm/chat/', {
            'message': 'test', 'session_id': 'test-session',
        }, format='json', **self.headers())
        response = protected_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(request.user.pk, self.user.pk)
        self.assertEqual(response['Content-Type'], 'text/event-stream; charset=utf-8')
        response.close()

    def test_cors_preflight_and_plain_options_do_not_run_view(self):
        stream_events.clear()
        response = self.client.options('/api/ai/llm/chat/', HTTP_ORIGIN='https://ui.test',
                                       HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                                       HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'https://ui.test')
        self.assertIn('authorization', response['Access-Control-Allow-Headers'])
        self.assertEqual(self.client.options('/api/ai/llm/chat/').status_code, 204)
        self.assertEqual(stream_events, [])

    def test_admin_and_static_resources_keep_existing_behavior(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 200)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(self.client.get('/static/probe.css').status_code, 200)
        # A Django session cannot replace the API token.
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/api/users/profile/').status_code, 401)

    def test_csrf_enabled_client_can_use_token_api(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/api/users/auth/login/', {
            'username': 'auth-test', 'password': 'test-password',
        }).status_code, 200)
        self.assertEqual(client.post('/api/ai/llm/chat/', **self.headers()).status_code, 200)

    def test_only_auth_views_declare_anonymous_permissions(self):
        backend = Path(__file__).resolve().parents[1]
        for folder in ['ai_integration', 'company_reviews', 'career_evaluation', 'career_paths', 'resumes']:
            for path in (backend / folder).glob('*views.py'):
                tree = ast.parse(path.read_text(encoding='utf-8-sig'))
                self.assertFalse(any(isinstance(node, ast.Name) and node.id == 'AllowAny'
                                     for node in ast.walk(tree)), str(path))
