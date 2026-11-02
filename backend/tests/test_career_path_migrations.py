"""Verify fresh installs can migrate the actual career_paths application."""

from pathlib import Path
import subprocess
import sys
import unittest


class CareerPathMigrationTests(unittest.TestCase):
    def test_fresh_database_can_store_and_read_assessment_result(self):
        source = '''
from django.conf import settings
settings.configure(SECRET_KEY='isolated-migration-test', INSTALLED_APPS=['career_paths'],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    DEFAULT_AUTO_FIELD='django.db.models.BigAutoField', USE_TZ=True)
import django
django.setup()
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
executor = MigrationExecutor(connection)
assert ('career_paths', '0001_initial') in executor.loader.graph.leaf_nodes()
executor.migrate(executor.loader.graph.leaf_nodes())
from career_paths.models import CareerPath, CareerAssessment, AssessmentResult
CareerPath.objects.create(path_type='employment', title='就业', description='测试', preparation_advice='测试')
CareerAssessment.objects.create(question='隔离测试题', options=['A'], path_weights={'A': {'employment': 1}})
AssessmentResult.objects.create(session_id='isolated-test', answers={'1': 'A'}, recommended_path='employment', confidence_score=1)
assert CareerPath.objects.get(path_type='employment').title == '就业'
assert CareerAssessment.objects.count() == 1
assert AssessmentResult.objects.get(session_id='isolated-test').confidence_score == 1
call_command('makemigrations', 'career_paths', check=True, dry_run=True, verbosity=0)
'''
        result = subprocess.run([sys.executable, '-c', source],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
