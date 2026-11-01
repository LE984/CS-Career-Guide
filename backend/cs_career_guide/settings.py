import os
from pathlib import Path
from dotenv import load_dotenv
from .env import env, env_bool, env_int, env_list, env_path
from .vector_store import DEFAULT_EMBEDDING_DIMENSION, DEFAULT_LANCEDB_RELATIVE_PATH

# 加载环境变量，指定.env文件路径
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=dotenv_path)

SECRET_KEY = env('SECRET_KEY', required=True)

DEBUG = env_bool('DEBUG', False)

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'career_paths',
    'company_reviews',
    'career_evaluation',
    'users',
    'ai_integration',
    'resumes',
    'career_platform',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cs_career_guide.middleware.ApiTokenRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cs_career_guide.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cs_career_guide.wsgi.application'

# 使用MySQL数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('DATABASE_NAME', required=True),
        'USER': env('DATABASE_USER', required=True),
        'PASSWORD': env('DATABASE_PASSWORD', required=True),
        'HOST': env('DATABASE_HOST', 'localhost'),
        'PORT': env_int('DATABASE_PORT', 3306, minimum=1, maximum=65535),
        'CONN_MAX_AGE': env_int('DATABASE_CONN_MAX_AGE', 0),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': env('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': env('CACHE_LOCATION', 'cs-career-guide'),
        'TIMEOUT': env_int('CACHE_TIMEOUT', 300),
    }
}

SESSION_ENGINE = env('SESSION_ENGINE', 'django.contrib.sessions.backends.db')

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = env('LANGUAGE_CODE', 'zh-hans')

TIME_ZONE = env('TIME_ZONE', 'Asia/Shanghai')

USE_I18N = True

USE_TZ = True

STATIC_URL = env('STATIC_URL', '/static/')
STATIC_ROOT = env_path('STATIC_ROOT', 'staticfiles', base_dir=BASE_DIR)

MEDIA_URL = env('MEDIA_URL', '/media/')
MEDIA_ROOT = env_path('MEDIA_ROOT', 'media', base_dir=BASE_DIR)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', False)
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')
SESSION_COOKIE_SECURE = env_bool('SESSION_COOKIE_SECURE', False)
CSRF_COOKIE_SECURE = env_bool('CSRF_COOKIE_SECURE', False)

# API secrets belong to the backend only. Legacy variable names remain supported.
LLM_API_KEY = env('LLM_API_KEY', '', aliases=('api_key',))
LLM_BASE_URL = env('LLM_BASE_URL', '', aliases=('base_url',))
LLM_MODEL = env('LLM_MODEL', '')
CAREER_REPORT_MODEL = env('CAREER_REPORT_MODEL', '', aliases=('career_report_model',)) or LLM_MODEL
LLM_TIMEOUT = env_int('LLM_TIMEOUT', 120, minimum=1)

ENABLE_TTS = env_bool('ENABLE_TTS', False)
ASR_API_KEY = env('ASR_API_KEY', '') or LLM_API_KEY
ASR_WSS_URL = env('ASR_WSS_URL', '', aliases=('WSS_URL',))
ASR_MODEL = env('ASR_MODEL', '')
TTS_API_KEY = env('TTS_API_KEY', '') or LLM_API_KEY
TTS_WSS_URL = env('TTS_WSS_URL', '', aliases=('WSS_URL',))
TTS_MODEL = env('TTS_MODEL', '')
TTS_VOICE = env('TTS_VOICE', '')

LANCEDB_PATH = env_path('LANCEDB_PATH', DEFAULT_LANCEDB_RELATIVE_PATH, base_dir=BASE_DIR)
EMBEDDING_ENABLED = env_bool('EMBEDDING_ENABLED', True)
EMBEDDING_DIMENSION = env_int('EMBEDDING_DIMENSION', DEFAULT_EMBEDDING_DIMENSION, minimum=1)
EMBEDDING_MODEL = env('EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5')
EMBEDDING_MODEL_PATH = env('EMBEDDING_MODEL_PATH', '')
EMBEDDING_DEVICE = env('EMBEDDING_DEVICE', 'cpu')
EMBEDDING_ALLOW_DOWNLOAD = env_bool('EMBEDDING_ALLOW_DOWNLOAD', True)
SEARCH_MAX_WORKERS = env_int('SEARCH_MAX_WORKERS', 3, minimum=1)
CAREER_REPORT_MAX_WORKERS = env_int('CAREER_REPORT_MAX_WORKERS', 4, minimum=1)
DATABASE_POOL_SIZE = env_int('DATABASE_POOL_SIZE', 5)
DATABASE_MAX_OVERFLOW = env_int('DATABASE_MAX_OVERFLOW', 20)
DATABASE_POOL_TIMEOUT = env_int('DATABASE_POOL_TIMEOUT', 30, minimum=1)
DATABASE_POOL_RECYCLE = env_int('DATABASE_POOL_RECYCLE', 3600, minimum=1)

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}
