"""Offline regression checks: no SSH, Docker daemon or real credentials."""

import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from sync_runtime_env import AI_KEYS, apply_remote, merge_env, sync, validate_image


ROOT = Path(__file__).resolve().parents[1]
IMAGES = {c: 'registry.invalid/demo/cs-career-guide-' + c + '@sha256:' + 'a' * 64
          for c in ('backend', 'frontend')}
VALUES = {'LLM_API_KEY': 'fake-$KEY#only', 'LLM_BASE_URL': 'https://example.invalid/v1',
          'LLM_MODEL': 'test-model', 'ENABLE_TTS': 'True'}


class MergeTests(unittest.TestCase):
    def test_only_ai_keys_change_and_merge_is_idempotent(self):
        host = b'# host settings\r\nSECRET_KEY="host-secret"\r\nDATABASE_PASSWORD=host-only\r\nWEB_PORT=127.0.0.1:48080\r\nCUSTOM_FLAG=keep\r\n'
        original = host + b'LLM_API_KEY=old\r\n'
        merged = merge_env(original, VALUES)
        self.assertTrue(merged.startswith(host))
        self.assertIn(b"LLM_API_KEY='fake-$KEY#only'\r\n", merged)
        self.assertNotIn(b'LLM_API_KEY=old', merged)
        self.assertEqual(merge_env(merged, VALUES), merged)

    def test_missing_optional_values_preserve_existing_server_settings(self):
        original = b'ASR_API_KEY=server-asr\nENABLE_TTS=False\n'
        values = {k: v for k, v in VALUES.items() if k != 'ENABLE_TTS'}
        self.assertTrue(merge_env(original, values).startswith(original))

    def test_rejects_protected_keys_injection_duplicates_and_multiline(self):
        cases = [
            (b'SECRET_KEY=keep\n', {**VALUES, 'SECRET_KEY': 'overwrite'}),
            (b'', {**VALUES, 'LLM_API_KEY': 'bad\nSECRET_KEY=overwrite'}),
            (b'', {**VALUES, 'LLM_API_KEY': "bad'quote"}),
            (b'', {**VALUES, 'LLM_API_KEY': 'bad\\escape'}),
            (b'', {**VALUES, 'LLM_API_KEY': ''}),
            (b'LLM_MODEL=a\nexport LLM_MODEL=b\n', VALUES),
            (b'PRIVATE="first\nLLM_MODEL=inside\nlast"\n', VALUES),
        ]
        for original, values in cases:
            with self.subTest(original=original), self.assertRaises(ValueError):
                merge_env(original, values)

    def test_export_and_comments_and_quoted_host_values(self):
        original = b"# comment\nOTHER='host # value' # trailing\nexport LLM_MODEL=old\n"
        self.assertIn(b"OTHER='host # value' # trailing\n", merge_env(original, VALUES))
        self.assertIn(b"LLM_MODEL='test-model'\n", merge_env(original, VALUES))


class TransportTests(unittest.TestCase):
    def test_verified_ssh_and_secrets_only_in_stdin_with_private_temporary_files(self):
        environment = {'DEPLOY_IMAGE': IMAGES['backend'], **VALUES, 'DEPLOY_SSH_HOST': 'server.invalid', 'DEPLOY_SSH_PORT': '2222',
                       'DEPLOY_SSH_USER': 'deployer', 'DEPLOY_ENV_PATH': '/srv/career/.env',
                       'DEPLOY_SSH_KEY': 'fake-private-key', 'DEPLOY_SSH_KNOWN_HOSTS': 'fake-known-host'}
        def run(command, **kwargs):
            self.assertIn('StrictHostKeyChecking=yes', command)
            self.assertIn('IdentitiesOnly=yes', command)
            self.assertIn('/dev/null', command)
            self.assertNotIn(VALUES['LLM_API_KEY'], ' '.join(command))
            self.assertEqual(json.loads(kwargs['input']), VALUES)
            key = Path(command[command.index('-i') + 1])
            self.assertEqual(key.read_text().strip(), 'fake-private-key')
            if os.name != 'nt':
                self.assertEqual(key.stat().st_mode & 0o777, 0o600)
            return subprocess.CompletedProcess(command, 0)
        with patch.dict(os.environ, environment, clear=True), patch('sync_runtime_env.subprocess.run', side_effect=run), patch('sys.stdout', new_callable=io.StringIO):
            sync()

    def test_frontend_transport_ignores_all_model_secrets_and_uses_published_digest(self):
        environment = {**VALUES, 'DEPLOY_COMPONENT': 'frontend', 'DEPLOY_IMAGE': IMAGES['frontend'],
                       'DEPLOY_SSH_HOST': 'server.invalid', 'DEPLOY_SSH_USER': 'deployer',
                       'DEPLOY_ENV_PATH': '/srv/career/.env', 'DEPLOY_SSH_KEY': 'fake-private-key',
                       'DEPLOY_SSH_KNOWN_HOSTS': 'fake-known-host'}
        with patch.dict(os.environ, environment, clear=True), patch('sync_runtime_env.subprocess.run') as run, patch('builtins.print'):
            run.return_value = subprocess.CompletedProcess([], 0)
            sync()
        self.assertEqual(json.loads(run.call_args.kwargs['input']), {})
        self.assertTrue(run.call_args.args[0][-1].endswith('frontend ' + IMAGES['frontend']))

    def test_wrong_component_or_mutable_image_is_rejected(self):
        for image in ('registry.invalid/demo/cs-career-guide-frontend:latest', IMAGES['backend'],
                      'bad; command', IMAGES['frontend'] + '\n'):
            with self.subTest(image=image), self.assertRaises(ValueError):
                validate_image('frontend', image)

    def test_missing_secrets_fail_before_network(self):
        with patch.dict(os.environ, {}, clear=True), patch('sync_runtime_env.subprocess.run') as run:
            with self.assertRaises(ValueError):
                sync()
            run.assert_not_called()


@unittest.skipIf(os.name == 'nt', 'Remote atomic update requires Linux fcntl and POSIX permissions')
class RemoteTests(unittest.TestCase):
    def prepare(self, directory):
        path = Path(directory) / '.env'
        path.write_bytes(b'SECRET_KEY=host-only\nDATABASE_PASSWORD=keep\n')
        path.chmod(0o600)
        (path.parent / 'docker-compose.yml').write_text('services: {}')
        other = path.parent / 'docker-compose.frontend-image.json'
        other.write_bytes(b'{"services":{"frontend":{"image":"old-frontend-pin"}}}')
        other.chmod(0o600)
        return path

    def test_symlink_hardlink_and_public_permissions_rejected_without_compose(self):
        for kind in ('symlink', 'hardlink', 'public'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                path = self.prepare(directory)
                original = path.read_bytes()
                if kind == 'public':
                    path.chmod(0o644)
                elif kind == 'symlink':
                    path.rename(path.parent / 'actual-env')
                    path.symlink_to(path.parent / 'actual-env')
                else:
                    os.link(path, path.parent / 'linked-env')
                with patch('sync_runtime_env.compose_run') as compose, self.assertRaises(ValueError):
                    apply_remote(str(path), VALUES, 'backend', IMAGES['backend'])
                compose.assert_not_called()
                self.assertEqual(path.read_bytes(), original)

    def config(self, values=None, component='backend', topology=True):
        return {'services': {'backend': {'environment': VALUES if values is None else values,
                                        'image': IMAGES['backend'], 'networks': {'app-net': {}},
                                        **({} if topology else {'ports': [{'target': 8000}]})},
                             'frontend': {'image': IMAGES['frontend'], 'networks': {'app-net': {}},
                                          **({} if topology else {'ports': ['80:8080']})},
                             'gateway': {'networks': {'app-net': {}},
                                         'ports': [{'target': 8080}],
                                         'volumes': [{'type': 'bind',
                                             'source': str(Path('/tmp') / 'nginx.conf'),
                                             'target': '/etc/nginx/nginx.conf', 'read_only': True}]}}}

    def real_topology(self, path, values=None):
        config = self.config(values)
        config['services']['gateway']['volumes'][0]['source'] = str(path.parent / 'nginx.conf')
        return config

    def test_validate_pull_replace_recreate_and_preserve_other_component(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.prepare(directory)
            other = path.parent / 'docker-compose.frontend-image.json'
            other_bytes = other.read_bytes()
            calls = []
            def compose(command, **kwargs):
                calls.append(command)
                if 'config' in command:
                    return self.real_topology(path)
                if 'pull' in command:
                    self.assertNotIn(b'LLM_MODEL', path.read_bytes())
                if 'up' in command:
                    self.assertIn(b"LLM_MODEL='test-model'", path.read_bytes())
                    for flag in ('--wait', '--no-deps', '--no-build'):
                        self.assertIn(flag, command)
                    self.assertEqual(command[command.index('--pull') + 1], 'never')
                    self.assertEqual(command[-1], 'backend')
            with patch('sync_runtime_env.compose_run', side_effect=compose), patch('builtins.print'):
                apply_remote(str(path), VALUES, 'backend', IMAGES['backend'])
            self.assertEqual(len(calls), 3)
            self.assertEqual(calls[1][-2:], ['pull', 'backend'])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(other.read_bytes(), other_bytes)
            overlay = path.parent / 'docker-compose.backend-image.json'
            self.assertEqual(json.loads(overlay.read_text())['services']['backend']['image'], IMAGES['backend'])
            self.assertEqual(overlay.stat().st_mode & 0o777, 0o600)
            self.assertFalse(list(path.parent.glob('.ai-env-*')))
            self.assertFalse(list(path.parent.glob('.component-image-*')))

    def test_frontend_never_replaces_env_or_receives_ai_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.prepare(directory)
            original, inode = path.read_bytes(), path.stat().st_ino
            calls = []
            def compose(command, **kwargs):
                calls.append(command)
                return self.real_topology(path) if 'config' in command else None
            with patch('sync_runtime_env.compose_run', side_effect=compose), patch('builtins.print'):
                apply_remote(str(path), {}, 'frontend', IMAGES['frontend'])
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(path.stat().st_ino, inode)
            self.assertFalse(list(path.parent.glob('.ai-env-*')))
            self.assertEqual(calls[1][-2:], ['pull', 'frontend'])
            self.assertEqual(calls[2][-1], 'frontend')
            self.assertIn('--no-deps', calls[2])
            with self.assertRaises(ValueError):
                apply_remote(str(path), VALUES, 'frontend', IMAGES['frontend'])

    def test_mapping_topology_or_pull_failure_preserves_files_and_removes_candidates(self):
        for failure in ('mapping', 'topology', 'pull'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                path = self.prepare(directory)
                original = path.read_bytes()
                def compose(command, **kwargs):
                    if 'config' in command:
                        return (self.real_topology(path, values={} if failure == 'mapping' else VALUES)
                                if failure != 'topology' else self.config(VALUES, topology=False))
                    raise RuntimeError('fake pull failure')
                with patch('sync_runtime_env.compose_run', side_effect=compose), self.assertRaises((ValueError, RuntimeError)):
                    apply_remote(str(path), VALUES, 'backend', IMAGES['backend'])
                self.assertEqual(path.read_bytes(), original)
                self.assertFalse((path.parent / 'docker-compose.backend-image.json').exists())
                self.assertFalse(list(path.parent.glob('.ai-env-*')))
                self.assertFalse(list(path.parent.glob('.component-image-*')))

    def test_activation_failure_keeps_new_env_and_pin_without_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.prepare(directory)
            def compose(command, **kwargs):
                if 'config' in command:
                    return self.real_topology(path)
                if 'up' in command:
                    raise RuntimeError('fake unhealthy service')
            with patch('sync_runtime_env.compose_run', side_effect=compose), self.assertRaises(RuntimeError):
                apply_remote(str(path), VALUES, 'backend', IMAGES['backend'])
            self.assertIn(b'SECRET_KEY=host-only\n', path.read_bytes())
            self.assertIn(b"LLM_MODEL='test-model'", path.read_bytes())
            self.assertTrue((path.parent / 'docker-compose.backend-image.json').exists())
            self.assertFalse(list(path.parent.glob('.ai-env-*')))
            self.assertFalse(list(path.parent.glob('.component-image-*')))

    def test_concurrent_env_edit_or_unsafe_pin_is_rejected(self):
        for failure in ('concurrent', 'public-pin', 'symlink-pin'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                path = self.prepare(directory)
                if failure == 'public-pin':
                    pin = path.parent / 'docker-compose.backend-image.json'
                    pin.write_text('{}')
                    pin.chmod(0o644)
                if failure == 'symlink-pin':
                    (path.parent / 'docker-compose.backend-image.json').symlink_to(path)
                calls = []
                def compose(command, **kwargs):
                    calls.append(command)
                    if 'config' in command:
                        return self.real_topology(path)
                    if 'pull' in command:
                        path.write_bytes(b'concurrent=keep\n')
                with patch('sync_runtime_env.compose_run', side_effect=compose), self.assertRaises(ValueError):
                    apply_remote(str(path), VALUES, 'backend', IMAGES['backend'])
                self.assertFalse(any('up' in c for c in calls))
                if failure == 'concurrent':
                    self.assertEqual(path.read_bytes(), b'concurrent=keep\n')
                self.assertFalse(list(path.parent.glob('.ai-env-*')))
                self.assertFalse(list(path.parent.glob('.component-image-*')))

    def test_backend_rollback_does_not_merge_ai_or_modify_env(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.prepare(directory)
            original, inode = path.read_bytes(), path.stat().st_ino
            with patch('sync_runtime_env.compose_run', side_effect=lambda cmd, **kw: self.real_topology(path) if 'config' in cmd else None), patch('builtins.print'):
                apply_remote(str(path), {}, 'backend', IMAGES['backend'])
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(path.stat().st_ino, inode)

    def test_invalid_payload_is_rejected_before_docker(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.prepare(directory)
            for values in (None, [], ['LLM_MODEL']):
                with self.subTest(values=values), patch('sync_runtime_env.compose_run') as compose:
                    with self.assertRaises(ValueError):
                        apply_remote(str(path), values, 'backend', IMAGES['backend'])
                    compose.assert_not_called()

    def test_gateway_ports_mount_and_network_must_match_split_topology(self):
        for failure in ('mount', 'network', 'port', 'backend-port'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                path = self.prepare(directory)
                config = self.real_topology(path)
                if failure == 'mount': config['services']['gateway']['volumes'] = []
                elif failure == 'network': config['services']['gateway']['networks'] = {'other': {}}
                elif failure == 'port': config['services']['gateway']['ports'] = [{'target': 80}]
                else: config['services']['backend']['ports'] = [{'target': 8000}]
                with patch('sync_runtime_env.compose_run', return_value=config) as compose:
                    with self.assertRaises(ValueError):
                        apply_remote(str(path), {}, 'frontend', IMAGES['frontend'])
                self.assertEqual(compose.call_count, 1)



class WorkflowTests(unittest.TestCase):
    def test_deployment_is_gated_per_component_and_frontend_receives_no_ai_settings(self):
        workflow = yaml.safe_load((ROOT / '.github/workflows/ci-cd.yml').read_text())
        for component in ('backend', 'frontend'):
            job = workflow['jobs']['deploy-' + component]
            self.assertEqual(job['needs'], ['publish-' + component])
            for guard in ("needs.publish-" + component + ".result == 'success'", "refs/heads/master",
                          "vars.DEPLOY_ENV_SYNC_ENABLED == 'true'",
                          "vars.DEPLOY_" + component.upper() + "_ENABLED == 'true'"):
                self.assertIn(guard, job['if'])
            step = job['steps'][-1]
            self.assertEqual(step['env']['DEPLOY_COMPONENT'], component)
            self.assertEqual(step['env']['DEPLOY_IMAGE'], '${{ needs.publish-' + component + '.outputs.image }}')
            for name in ('DEPLOY_SSH_HOST', 'DEPLOY_SSH_USER', 'DEPLOY_SSH_PORT', 'DEPLOY_ENV_PATH', 'DEPLOY_SSH_KEY', 'DEPLOY_SSH_KNOWN_HOSTS'):
                self.assertEqual(step['env'][name], '${{ secrets.' + name + ' }}')
            self.assertEqual(set(AI_KEYS) & set(step['env']), set(AI_KEYS) if component == 'backend' else set())
        compose = yaml.safe_load((ROOT / 'deploy/docker-compose.yml').read_text())
        self.assertTrue(set(AI_KEYS).issubset(compose['services']['backend']['environment']))


if __name__ == '__main__':
    unittest.main()
