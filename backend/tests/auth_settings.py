"""Isolated auth tests: never load .env, MySQL, AI apps or project vector data."""

import os
import runpy
from unittest.mock import patch

with patch.dict(os.environ, {
    'SECRET_KEY': 'auth-tests-only-signing-key',
    'DATABASE_NAME': 'unused', 'DATABASE_USER': 'unused',
    'DATABASE_PASSWORD': 'unused',
}, clear=True), patch('dotenv.load_dotenv'):
    _config = runpy.run_module('cs_career_guide.settings')

globals().update({key: value for key, value in _config.items() if key.isupper()})
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'ai_integration']
ROOT_URLCONF = 'tests.auth_urls'
ALLOWED_HOSTS = ['testserver']
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CORS_ALLOWED_ORIGINS = ['https://ui.test']
CORS_ALLOW_ALL_ORIGINS = False
# Only the temporary database is initialized by Django's test runner.
MIGRATION_MODULES = {'users': None, 'career_paths': None, 'career_evaluation': None,
                     'company_reviews': None, 'resumes': None, 'career_platform': None}
SILENCED_SYSTEM_CHECKS = ['fields.E210']  # ImageField requires Pillow only for uploads.
