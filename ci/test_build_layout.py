"""Check source/layout boundaries without a Docker daemon or reading real environment files."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildLayoutTests(unittest.TestCase):
    def test_each_dockerfile_uses_only_its_own_context(self):
        for component in ('backend', 'frontend'):
            text = (ROOT / component / 'Dockerfile').read_text()
            copies = [line for line in text.splitlines() if line.startswith(('COPY ', 'ADD '))]
            self.assertTrue(copies)
            self.assertFalse(any('../' in line for line in copies))
            self.assertFalse(any('COPY ' + component + '/' in line for line in copies))
        self.assertFalse((ROOT / 'Dockerfile.frontend').exists())
        self.assertFalse((ROOT / 'Dockerfile.backend').exists())

    def test_dependency_forwarding_and_original_utf16_source_remain_supported(self):
        self.assertEqual((ROOT / 'requirements.txt').read_text(encoding='utf-16').strip(), '-r backend/requirements.txt')
        self.assertEqual((ROOT / 'requirements-runtime.txt').read_text().strip(), '-r backend/requirements-runtime.txt')
        source = (ROOT / 'backend/requirements.txt').read_bytes()
        self.assertTrue(source.startswith((b'\xff\xfe', b'\xfe\xff')))
        self.assertIn('django', source.decode('utf-16').lower())

    def test_context_filters_exclude_env_credentials_and_runtime_data(self):
        for component in ('backend', 'frontend'):
            patterns = (ROOT / component / '.dockerignore').read_text().splitlines()
            for required in ('.env', '.env.*', '**/.env', '**/.env.*', '**/*.pem', '**/*.key'):
                self.assertIn(required, patterns)
            self.assertIn('!.env.example', patterns)
        backend = (ROOT / 'backend/.dockerignore').read_text().splitlines()
        for required in ('media', 'staticfiles', 'ai_integration/lancedb', '**/*.sqlite*', '.runtime'):
            self.assertIn(required, backend)
        frontend = (ROOT / 'frontend/.dockerignore').read_text().splitlines()
        for public_asset in ('!public/models/d51675667acfc8a42b8e40d4c3e9799a.glb',
                             '!public/models/vad', '!public/models/vad/**'):
            self.assertIn(public_asset, frontend)

    def test_frontend_nginx_has_no_upstream_and_gateway_owns_streaming_and_files(self):
        static = (ROOT / 'frontend/nginx.conf').read_text()
        self.assertNotIn('proxy_pass', static)
        self.assertNotIn('resolver ', static)
        self.assertIn('try_files $uri $uri/ /index.html', static)
        gateway = (ROOT / 'deploy/nginx.conf').read_text()
        for expected in ('resolver 127.0.0.11 valid=5s', 'proxy_pass $backend$request_uri',
                         'proxy_pass $frontend$request_uri', 'proxy_buffering off',
                         'proxy_read_timeout 300s', 'alias /var/www/backend-static/', 'alias /var/www/media/'):
            self.assertIn(expected, gateway)
        for name in ('client_body', 'proxy', 'fastcgi', 'uwsgi', 'scgi'):
            self.assertIn(name + '_temp_path /tmp/', gateway)
        self.assertNotIn('/var/log/nginx/', gateway)

    def test_company_api_default_keeps_the_legacy_path(self):
        dockerfile = (ROOT / 'frontend/Dockerfile').read_text()
        self.assertIn('ARG VITE_COMPANY_API_BASE_URL=/company-api', dockerfile)


if __name__ == '__main__':
    unittest.main()
