import json
import unittest

from split_topology import prepare


class SplitTopologyTests(unittest.TestCase):
    def fixture(self):
        existing = {'name': 'existing-project', 'networks': {'app': {'name': 'existing-net'}},
                    'volumes': {'static': {'name': 'existing-static'}, 'media': {'name': 'existing-media'}},
                    'services': {
                        'backend': {'image': 'old-backend', 'networks': {'app': {}},
                                    'environment': {'SECRET_KEY': 'synthetic-hidden-value'},
                                    'volumes': [{'type': 'volume', 'source': 'db', 'target': '/data'}]},
                        'frontend': {'image': 'old-frontend', 'networks': {'app': {}},
                                     'ports': [{'target': 8080, 'published': '80', 'host_ip': '0.0.0.0', 'protocol': 'tcp'}],
                                     'depends_on': {'backend': {'condition': 'service_healthy'}},
                                     'volumes': [{'type': 'volume', 'source': source, 'target': target, 'read_only': True}
                                                 for source, target in [('static', '/var/www/backend-static'),
                                                                        ('media', '/var/www/media')]]}}}
        template = {'services': {'backend': {'environment': {'SECRET_KEY': '${SECRET_KEY:?required}'}},
                                 'frontend': {}, 'gateway': {'image': 'nginx:fixture', 'read_only': True}}}
        return existing, template

    def test_cutover_preserves_server_ports_named_volumes_and_backend_configuration(self):
        existing, template = self.fixture()
        result = prepare(existing, template, 'new-frontend', 'pinned-backend', '/srv/fixture/nginx.conf')
        self.assertEqual(result['name'], existing['name'])
        self.assertEqual(result['volumes'], existing['volumes'])
        self.assertEqual(result['networks'], existing['networks'])
        self.assertEqual(result['services']['gateway']['ports'], existing['services']['frontend']['ports'])
        self.assertEqual(result['services']['backend']['volumes'], existing['services']['backend']['volumes'])
        for field in ('ports', 'volumes', 'depends_on'):
            self.assertNotIn(field, result['services']['frontend'])
        self.assertNotIn('synthetic-hidden-value', json.dumps(result))
        self.assertEqual(existing['services']['frontend']['image'], 'old-frontend')

    def test_unreviewed_environment_or_missing_mounts_are_rejected(self):
        for mutation in ('environment', 'volumes'):
            existing, template = self.fixture()
            if mutation == 'environment':
                existing['services']['backend']['environment']['UNREVIEWED'] = 'hidden'
            else:
                existing['services']['frontend']['volumes'] = []
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                prepare(existing, template, 'new', 'old', '/srv/fixture/nginx.conf')


if __name__ == '__main__':
    unittest.main()
