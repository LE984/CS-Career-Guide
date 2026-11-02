"""隔离验证历史性别清理、数据库约束与迁移状态。"""

from pathlib import Path
import subprocess
import sys
import unittest


class UserGenderMigrationTests(unittest.TestCase):
    def test_existing_profiles_are_preserved_and_removed_option_is_cleared(self):
        source = '''
from django.conf import settings
settings.configure(SECRET_KEY='isolated-gender-test', AUTH_USER_MODEL='users.User',
    INSTALLED_APPS=['django.contrib.auth', 'django.contrib.contenttypes', 'users'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField', USE_TZ=True)
import django
django.setup()
from django.core.management import call_command
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
before = [('users', '0012_user_career_goal_user_other_skills_user_profile_and_more')]
after = [('users', '0013_normalize_gender_choices')]
executor = MigrationExecutor(connection)
executor.migrate(before)
User = executor.loader.project_state(before).apps.get_model('users', 'User')
for i, gender in enumerate(['男', '女', '', None, '暂不填写']):
    User.objects.create(username=f'test-{i}', gender=gender, school='保留学校')
unknown = User.objects.create(username='unknown', gender='unexpected')
try:
    MigrationExecutor(connection).migrate(after)
except RuntimeError:
    pass
else:
    raise AssertionError('Unknown historical values must not be silently deleted')
assert User.objects.get(username='unknown').gender == 'unexpected'
assert User.objects.get(username='test-4').gender == '暂不填写'
unknown.delete()
executor = MigrationExecutor(connection)
executor.migrate(after)
User = executor.loader.project_state(after).apps.get_model('users', 'User')
assert list(User.objects.order_by('id').values_list('gender', flat=True)) == ['男', '女', None, None, None]
assert User.objects.filter(school='保留学校').count() == 5
for gender in ['', '暂不填写', 'unexpected']:
    try:
        with transaction.atomic():
            User.objects.filter(username='test-0').update(gender=gender)
    except IntegrityError:
        pass
    else:
        raise AssertionError('Database must reject invalid gender values')
call_command('makemigrations', 'users', check=True, dry_run=True, verbosity=0)
MigrationExecutor(connection).migrate(before)
assert User.objects.count() == 5
assert User.objects.filter(gender__isnull=True).count() == 3
'''
        result = subprocess.run([sys.executable, '-c', source],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
