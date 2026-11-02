"""使用 tests.auth_settings 在内存 SQLite 中验证性别字段契约。"""

import json

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.authtoken.models import Token


class UserGenderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='gender-test', password='test-password')
        cls.token = Token.objects.create(user=cls.user)

    def update(self, payload):
        return self.client.put('/api/users/profile/', json.dumps(payload), content_type='application/json',
                               HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_profile_accepts_male_and_female(self):
        for gender in ['男', '女']:
            with self.subTest(gender=gender):
                response = self.update({'gender': gender})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['gender'], gender)
                self.user.refresh_from_db()
                self.assertEqual(self.user.gender, gender)

    def test_empty_legacy_payloads_are_stored_as_null(self):
        for gender in ['', None]:
            with self.subTest(gender=gender):
                self.update({'gender': '女'})
                response = self.update({'gender': gender})
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.json()['gender'])
                self.user.refresh_from_db()
                self.assertIsNone(self.user.gender)

    def test_removed_option_and_unknown_values_are_rejected(self):
        self.update({'gender': '男'})
        for gender in ['暂不填写', 'invalid']:
            with self.subTest(gender=gender):
                response = self.update({'gender': gender})
                self.assertEqual(response.status_code, 400)
                self.assertIn('gender', response.json())
                self.user.refresh_from_db()
                self.assertEqual(self.user.gender, '男')

    def test_omitted_gender_preserves_existing_value(self):
        self.update({'gender': '女'})
        self.assertEqual(self.update({'major': '计算机'}).status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.gender, '女')

    def test_database_rejects_removed_and_invalid_values(self):
        for gender in ['', '暂不填写', 'invalid']:
            with self.subTest(gender=gender), self.assertRaises(IntegrityError), transaction.atomic():
                get_user_model().objects.filter(pk=self.user.pk).update(gender=gender)

    def test_registration_still_allows_no_gender(self):
        response = self.client.post('/api/users/auth/register/', json.dumps({
            'username': 'new-without-gender', 'password': 'test-password', 'confirm_password': 'test-password',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(get_user_model().objects.get(username='new-without-gender').gender)
