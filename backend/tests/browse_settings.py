"""企业招聘隔离测试：内存 SQLite，不加载模型、环境文件或提示词初始化。"""
from django.apps import AppConfig
from .auth_settings import *


class AiTestConfig(AppConfig):
    name = 'ai_integration'
    default_auto_field = 'django.db.models.BigAutoField'


INSTALLED_APPS = [*INSTALLED_APPS, 'tests.browse_settings.AiTestConfig']
MIGRATION_MODULES = {**MIGRATION_MODULES, 'ai_integration': None}
ROOT_URLCONF = 'tests.browse_urls'
