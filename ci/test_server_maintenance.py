import contextlib
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import server_maintenance


class ServerMaintenanceTests(unittest.TestCase):
    def test_gateway_mirror_never_changes_application_tags_and_verifies_digest(self):
        repository = 'registry.example/demo/cs-career-guide-frontend'
        image = {'Id': 'sha256:' + 'a' * 64, 'Os': 'linux', 'Architecture': 'amd64',
                 'RootFS': {'Layers': ['sha256:' + 'e' * 64]},
                 'Config': {'Entrypoint': ['/docker-entrypoint.sh'], 'Cmd': ['nginx'], 'User': ''}}
        with patch('server_maintenance.run', side_effect=[
                [image], '', 'digest: sha256:' + 'b' * 64, '', [image]]) as run:
            reference, identity, fingerprint = server_maintenance.publish_gateway(repository + '@sha256:' + 'c' * 64)
        self.assertEqual(reference, repository + '@sha256:' + 'b' * 64)
        self.assertEqual(identity, image['Id'])
        tag = run.call_args_list[1].args[0][-1]
        self.assertEqual(tag, repository + ':gateway-nginx-' + 'a' * 64)
        self.assertNotIn(':latest', str(run.call_args_list))
        changed = dict(image, RootFS={'Layers': ['sha256:' + 'd' * 64]})
        with patch('server_maintenance.run', side_effect=[
                [image], '', 'digest: sha256:' + 'b' * 64, '', [changed]]), self.assertRaises(ValueError):
            server_maintenance.publish_gateway(repository + '@sha256:' + 'c' * 64)

    def test_engine_specific_image_id_does_not_change_content_identity(self):
        image = {'Id': 'sha256:' + 'a' * 64, 'Os': 'linux', 'Architecture': 'amd64',
                 'RootFS': {'Layers': ['sha256:' + 'e' * 64]}, 'Config': {'Cmd': ['nginx']}}
        other_engine = dict(image, Id='sha256:' + 'b' * 64)
        self.assertEqual(server_maintenance.image_fingerprint(image), server_maintenance.image_fingerprint(other_engine))
        other_engine['Config'] = {'Cmd': ['unreviewed-command']}
        self.assertNotEqual(server_maintenance.image_fingerprint(image), server_maintenance.image_fingerprint(other_engine))

    def test_gateway_import_checks_archive_and_loaded_image_identity(self):
        archive = b'synthetic-unit-test-archive'
        payload = {'gateway_archive_b64': base64.b64encode(archive).decode(),
                   'gateway_archive_sha256': hashlib.sha256(archive).hexdigest(),
                   'gateway_image_id': 'sha256:' + 'a' * 64}
        image = {'Id': payload['gateway_image_id'], 'Os': 'linux', 'Architecture': 'amd64'}
        with patch('server_maintenance.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as load, \
                patch('server_maintenance.run', return_value=[image]):
            server_maintenance.import_gateway(payload)
        self.assertEqual(load.call_args.kwargs['input'], archive)
        payload['gateway_archive_sha256'] = 'bad-checksum'
        with patch('server_maintenance.subprocess.run') as load, self.assertRaises(ValueError):
            server_maintenance.import_gateway(payload)
        load.assert_not_called()

    def test_compressed_gateway_transport_loads_original_archive(self):
        archive = b'synthetic-unit-test-archive' * 500
        packed = server_maintenance.pack_gateway_archive(archive)
        self.assertLess(len(packed), len(archive))
        payload = {'gateway_archive_b64': base64.b64encode(packed).decode(),
                   'gateway_archive_sha256': hashlib.sha256(packed).hexdigest(),
                   'gateway_image_id': 'sha256:' + 'a' * 64}
        image = {'Id': payload['gateway_image_id'], 'Os': 'linux', 'Architecture': 'amd64'}
        with patch('server_maintenance.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as load, \
                patch('server_maintenance.run', return_value=[image]):
            server_maintenance.import_gateway(payload)
        self.assertEqual(load.call_args.kwargs['input'], archive)

    def test_audit_emits_only_selected_metadata_and_never_environment_values(self):
        config = {'name': 'fixture', 'services': {
            'backend': {'environment': {'SECRET_KEY': 'synthetic-hidden-value'}},
            'frontend': {'environment': {}}}}
        container = {'Id': 'container-id', 'Image': 'image-id', 'Name': '/fixture',
                     'State': {'Status': 'running'}, 'HostConfig': {'PortBindings': {}},
                     'Config': {'Image': 'fixture:old', 'Env': ['SECRET_KEY=synthetic-hidden-value'],
                                'Labels': {'com.docker.compose.project': 'fixture'}}, 'Mounts': []}

        def run(command, **kwargs):
            if command[:3] == ['docker', 'image', 'inspect']:
                return [{'RepoDigests': ['example.invalid/demo/image@sha256:abc']}]
            if command[:2] == ['docker', 'inspect']:
                return [container]
            if 'ps' in command:
                return 'container-id'
            return 'fixture-version'

        output = io.StringIO()
        with patch('server_maintenance.existing_deployment', return_value=(Path('/fixture/.env'), ['compose'], config)), \
                patch('server_maintenance.run', side_effect=run), contextlib.redirect_stdout(output):
            server_maintenance.inventory('/fixture/.env')
        self.assertNotIn('synthetic-hidden-value', output.getvalue())
        report = json.loads(output.getvalue())
        self.assertFalse(report['env_file_read_or_replaced'])
        self.assertEqual(report['services']['backend']['environment_keys'], ['SECRET_KEY'])
        self.assertFalse(report['services']['gateway']['configured'])

    def test_command_failures_hide_raw_diagnostics(self):
        result = subprocess.CompletedProcess([], 1, b'', b'synthetic-hidden-value')
        with patch('server_maintenance.subprocess.run', return_value=result):
            with self.assertRaises(RuntimeError) as error:
                server_maintenance.run(['fixture'])
        self.assertNotIn('synthetic-hidden-value', str(error.exception))

    @unittest.skipUnless(hasattr(__import__('os'), 'geteuid'), 'POSIX deployment permissions')
    def test_audit_refuses_public_env_before_invoking_compose(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env'
            path.write_text('SECRET_KEY=synthetic-hidden-value')
            path.chmod(0o644)
            with patch('server_maintenance.run') as run, self.assertRaises(ValueError):
                server_maintenance.existing_deployment(str(path))
            run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
