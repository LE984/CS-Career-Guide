import os
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class SqliteSettingsTests(unittest.TestCase):
    def load(self, **overrides):
        values = {
            'SECRET_KEY': 'deploy-test-only-key',
            **overrides,
        }
        with patch.dict(os.environ, values, clear=True), patch('dotenv.load_dotenv'):
            return runpy.run_module('cs_career_guide.settings_sqlite')

    def test_sqlite_does_not_require_a_database_server(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'demo.sqlite3'
            config = self.load(DB_PATH=str(db), STATIC_ROOT=str(Path(directory) / 'static'),
                               MEDIA_ROOT=str(Path(directory) / 'media'))
            database = config['DATABASES']['default']
            self.assertEqual(database['ENGINE'], 'django.db.backends.sqlite3')
            self.assertEqual(database['NAME'], str(db))
            self.assertNotIn('HOST', database)

    def test_writable_paths_can_be_overridden(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.load(
                DB_PATH=str(root / 'db.sqlite3'),
                STATIC_ROOT=str(root / 'static'),
                MEDIA_ROOT=str(root / 'media'),
            )
            self.assertEqual(config['STATIC_ROOT'], root / 'static')
            self.assertEqual(config['MEDIA_ROOT'], root / 'media')
            self.assertTrue((root / 'static').is_dir())
            self.assertTrue((root / 'media').is_dir())

    def test_blank_optional_mysql_credentials_do_not_break_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.load(
                DATABASE_NAME='', DATABASE_USER='', DATABASE_PASSWORD='',
                DB_PATH=str(root / 'demo.sqlite3'),
                STATIC_ROOT=str(root / 'static'), MEDIA_ROOT=str(root / 'media'),
                LANCEDB_PATH=str(root / 'lancedb'),
            )
            self.assertEqual(config['DATABASES']['default']['ENGINE'], 'django.db.backends.sqlite3')
            self.assertEqual(config['DATABASES']['default']['NAME'], str(root / 'demo.sqlite3'))

    def test_sqlite_settings_only_pass_supported_connection_options(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.load(
                DB_PATH=str(root / 'demo.sqlite3'),
                STATIC_ROOT=str(root / 'static'),
                MEDIA_ROOT=str(root / 'media'),
                LANCEDB_PATH=str(root / 'lancedb'),
            )
            self.assertEqual(config['DATABASES']['default']['OPTIONS'], {'timeout': 20})


class DeployFileTests(unittest.TestCase):
    def test_compose_uses_two_acr_repositories_and_optional_mysql(self):
        text = (BACKEND_DIR.parent / 'deploy' / 'docker-compose.yml').read_text(encoding='utf-8')
        self.assertIn('cs-career-guide-backend', text)
        self.assertIn('cs-career-guide-frontend', text)
        self.assertIn('profiles: ["mysql"]', text)

    def test_watchtower_can_check_registry_with_mounted_credentials(self):
        text = (BACKEND_DIR.parent / 'deploy' / 'docker-compose.yml').read_text(encoding='utf-8')
        watchtower = text.split('\n  watchtower:\n', 1)[1].split('\n  mysql:\n', 1)[0]
        self.assertIn('network_mode: bridge', watchtower)
        self.assertIn('DOCKER_CONFIG: /config', watchtower)
        self.assertIn(':/config:ro', watchtower)
        self.assertIn('--interval 30 --label-enable', watchtower)
        self.assertNotIn('ports:', watchtower)

    def test_image_excludes_large_optional_dependencies(self):
        runtime = (BACKEND_DIR / 'requirements-runtime.txt').read_text(encoding='utf-8')
        for name in ('torch', 'sentence-transformers', 'transformers'):
            self.assertNotIn(name, runtime.lower())


if __name__ == '__main__':
    unittest.main()
