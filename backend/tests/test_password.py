"""演示密码便利功能；仅使用隔离数据库。"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.authtoken.models import Token


class PasswordTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='demo-user', password='old-password')
        self.other = get_user_model().objects.create_user(username='other-user', password='other-password')
        self.token = Token.objects.create(user=self.user)
        self.headers = {'HTTP_AUTHORIZATION': f'Token {self.token.key}'}

    def test_public_reset_revokes_token_and_new_password_logs_in(self):
        response = self.client.post('/api/users/auth/reset-password/', {
            'username': self.user.username, 'new_password': 'new-password',
        }, HTTP_AUTHORIZATION='Token stale')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-password'))
        self.assertNotEqual(self.user.password, 'new-password')
        self.assertFalse(Token.objects.filter(user=self.user).exists())
        self.assertEqual(self.client.get('/api/users/profile/', **self.headers).status_code, 401)
        self.assertEqual(self.client.post('/api/users/auth/login/', {
            'username': self.user.username, 'password': 'old-password',
        }).status_code, 400)
        self.assertEqual(self.client.post('/api/users/auth/login/', {
            'username': self.user.username, 'password': 'new-password',
        }).status_code, 200)

    def test_set_requires_auth_and_only_changes_current_user(self):
        path = '/api/users/profile/set-password/'
        self.assertEqual(self.client.post(path, {'new_password': 'new-password'}).status_code, 401)
        response = self.client.post(path, {
            'new_password': 'new-password', 'username': self.other.username,
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertTrue(self.user.check_password('new-password'))
        self.assertTrue(self.other.check_password('other-password'))
        self.assertEqual(self.client.get('/api/users/profile/', **self.headers).status_code, 200)

    def test_invalid_password_does_not_change_account(self):
        for value in ['', 'short', 'x' * 129, None]:
            for path, data, headers in [
                ('/api/users/auth/reset-password/', {'username': self.user.username, 'new_password': value}, {}),
                ('/api/users/profile/set-password/', {'new_password': value}, self.headers),
            ]:
                with self.subTest(path=path, value=value):
                    self.assertEqual(self.client.post(path, data, content_type='application/json', **headers).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old-password'))
        self.assertTrue(Token.objects.filter(user=self.user).exists())

    def test_missing_unknown_and_disabled_username(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        for username in ['', 'missing', self.user.username]:
            self.assertEqual(self.client.post('/api/users/auth/reset-password/', {
                'username': username, 'new_password': 'new-password',
            }).status_code, 400)
        self.assertEqual(self.client.get('/api/users/auth/reset-password/').status_code, 405)
        self.assertEqual(self.client.post('/api/users/auth/reset-password/extra/').status_code, 401)

    def test_password_whitespace_is_preserved(self):
        response = self.client.post('/api/users/profile/set-password/', {
            'new_password': '  new password  ',
        }, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('  new password  '))
