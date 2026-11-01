"""Exercise cutover, rollback and the nested deployment lock with synthetic files only."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import server_maintenance


@unittest.skipUnless(hasattr(os, 'geteuid'), 'POSIX cutover filesystem and locks')
class ServerCutoverTests(unittest.TestCase):
    def exercise(self, failure=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            env = root / '.env'
            env.write_bytes(b'SECRET_KEY=synthetic-value\n')
            env.chmod(0o600)
            identity = env.stat().st_ino
            compose = root / 'docker-compose.yml'
            compose.write_bytes(b'original-compose-fixture')
            mounts = [{'type': 'volume', 'source': name, 'target': target, 'read_only': True}
                      for name, target in [('static', '/var/www/backend-static'), ('media', '/var/www/media')]]
            config = {'name': 'fixture', 'networks': {'app': {'name': 'fixture-net'}},
                      'volumes': {'static': {'name': 'fixture-static'}, 'media': {'name': 'fixture-media'}},
                      'services': {
                          'backend': {'networks': {'app': {}}, 'environment': {}},
                          'frontend': {'networks': {'app': {}}, 'volumes': mounts,
                                       'ports': [{'target': 8080, 'published': '48080'}]}}}
            template = {'services': {'backend': {'environment': {}}, 'frontend': {},
                                     'gateway': {'image': 'nginx:fixture'}}}
            state = {'installed': False, 'rollback': False, 'commands': []}

            def inspected(service):
                identifier = service
                if service == 'frontend' and state['installed']:
                    identifier = 'new-frontend-2' if (root / 'reapplied').exists() else 'new-frontend-1'
                return {'Id': identifier, 'Image': service, 'State': {'Status': 'running'},
                        'Config': {'Labels': {'com.docker.compose.project': 'fixture'}}}

            def run(command, **kwargs):
                state['commands'].append(command)
                if command[:3] == ['docker', 'image', 'inspect']:
                    return [{'RepoDigests': ['registry.example/demo/cs-career-guide-' + command[-1]
                                              + '@sha256:' + 'a' * 64]}]
                if command[:2] == ['docker', 'inspect']:
                    return [inspected(command[-1])]
                if 'ps' in command:
                    service = command[-1]
                    return '' if service == 'gateway' and not state['installed'] else service
                if 'config' in command:
                    rendered = json.loads(Path(command[command.index('-f') + 1]).read_text())
                    if failure == 'environment':
                        config['services']['backend']['environment']['SYNTHETIC'] = 'original'
                    return rendered
                if 'pull' in command and failure == 'pull':
                    raise RuntimeError('synthetic pull failure')
                if 'up' in command:
                    if command[-1] == 'gateway':
                        state['installed'] = True
                        if failure == 'cutover':
                            raise RuntimeError('synthetic cutover failure')
                    elif command[-1] == 'frontend':
                        state['rollback'] = True
                        state['installed'] = False
                return ''

            helper = '''def apply_remote(env_path, *args):
    import fcntl
    from pathlib import Path
    with open(env_path + '.ai-sync.lock', 'r+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        Path(env_path).with_name('reapplied').touch()
'''
            payload = {'template': template, 'nginx': 'public-fixture-config',
                       'frontend_image': 'registry.example/demo/cs-career-guide-frontend@sha256:' + 'b' * 64,
                       'topology_source': (Path(__file__).parent / 'split_topology.py').read_text(),
                       'helpers': {'sync_runtime_env.py': helper, 'deploy_component.py': '# fixture'}}

            class Response:
                def __init__(self, request):
                    self.status = 401 if '/api/' in request.full_url else 404 if '/media/' in request.full_url else 200

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def read(self):
                    return b'<div id="app"></div>'

            output = io.StringIO()
            with patch('server_maintenance.existing_deployment', return_value=(env, ['compose'], config)), \
                    patch('server_maintenance.run', side_effect=run), \
                    patch('urllib.request.urlopen', side_effect=lambda request, **kwargs: Response(request)), \
                    contextlib.redirect_stdout(output):
                if failure:
                    with self.assertRaises((RuntimeError, ValueError)):
                        server_maintenance.install(str(env), payload)
                else:
                    server_maintenance.install(str(env), payload)
            self.assertEqual(env.read_bytes(), b'SECRET_KEY=synthetic-value\n')
            self.assertEqual(env.stat().st_ino, identity)
            self.assertEqual(list(root.glob('.split-compose-*')), [])
            self.assertNotIn('synthetic-value', output.getvalue())
            for command in state['commands']:
                if 'up' in command:
                    self.assertNotIn('backend', command[command.index('up') + 1:])
            if failure:
                self.assertEqual(compose.read_bytes(), b'original-compose-fixture')
                self.assertEqual(state['rollback'], failure == 'cutover')
            else:
                report = json.loads(output.getvalue())
                self.assertTrue(report['backend_container_unchanged'])
                self.assertTrue(report['single_frontend_activation_verified'])
                self.assertEqual((root / 'nginx.conf').stat().st_mode & 0o777, 0o644)

    def test_success_preserves_env_and_backend_and_exercises_component_lock(self):
        self.exercise()

    def test_pull_failure_does_not_change_server_files(self):
        self.exercise('pull')

    def test_cutover_failure_restores_previous_frontend_without_touching_backend(self):
        self.exercise('cutover')

    def test_changed_environment_is_rejected_before_cutover(self):
        self.exercise('environment')


if __name__ == '__main__':
    unittest.main()
