"""No .env loading, model calls, downloads, production databases or vector data."""
import os

SECRET_KEY = 'isolated-platform-contract-tests'
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'rest_framework',
                  'rest_framework.authtoken', 'users', 'resumes', 'company_reviews', 'career_platform']
AUTH_USER_MODEL = 'users.User'
ROOT_URLCONF = 'career_platform.test_urls'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
if os.getenv('PLATFORM_TEST_MYSQL') == '1':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.mysql', 'NAME': 'platform_ci',
        'USER': 'root', 'PASSWORD': os.environ['MYSQL_TEST_PASSWORD'], 'HOST': '127.0.0.1', 'PORT': '3306'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
TIME_ZONE = 'UTC'
ALLOWED_HOSTS = ['testserver']
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
# Local tests do not upload images; Actions installs Pillow for full image checks.
SILENCED_SYSTEM_CHECKS = ['fields.E210']
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
                 'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated']}
