"""Test the smoke harness failure paths without starting Docker or services."""

import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from demo_smoke import DemoClient, run_demo, verify_profile
from test_host_protection import sandbox_state


class DemoClientTests(unittest.TestCase):
    def test_requests_are_limited_to_runner_loopback(self):
        for url in ('https://127.0.0.1:18080', 'http://example.com', 'http://127.0.0.1/private'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                DemoClient(url)

    def test_failure_does_not_echo_authentication_response(self):
        error = HTTPError('http://127.0.0.1:18080/api/users/auth/register/', 400, 'Bad Request', {},
                          io.BytesIO(b'{"token":"private-response-token","password":"private-password"}'))
        with patch('demo_smoke.urlopen', side_effect=error):
            with self.assertRaises(RuntimeError) as caught:
                DemoClient('http://127.0.0.1:18080').request('/api/users/auth/register/', expected=201)
        self.assertIn('expected HTTP 201, got 400', str(caught.exception))
        self.assertNotIn('private-response-token', str(caught.exception))
        self.assertNotIn('private-password', str(caught.exception))

    def test_profile_verification_rejects_lost_identity_or_data(self):
        expected = {'id': 7, 'username': 'ci_demo_user', 'profile': 'saved-marker'}
        verify_profile(expected, 7, 'ci_demo_user', 'saved-marker')
        for changed in ({'id': 8}, {'username': 'other-user'}, {'profile': ''}):
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                verify_profile({**expected, **changed}, 7, 'ci_demo_user', 'saved-marker')


class StackLifecycleTests(unittest.TestCase):
    def exercise(self, *, same_container=False):
        client = Mock()
        token = 'a' * 40
        user = {'id': 7, 'username': 'ci_demo_0123456789ab'}
        profile = {**user, 'profile': 'ci-persistence-marker'}
        authenticated = {'user': user, 'token': token}
        client.request.side_effect = [
            b'<div id="app"></div>', b'<div id="app"></div>', b'<div id="app"></div>',
            b'body { color: black; }', {'detail': 'Invalid token.'},
            authenticated, authenticated, profile, profile, profile, authenticated, profile, b'<div id="app"></div>',
        ]
        calls = []
        ids = {'backend': 'container-before', 'frontend': 'frontend-before', 'gateway': 'gateway-container'}

        def fake_run(command, **kwargs):
            calls.append(command)
            if command[:2] == ['docker', 'inspect']:
                service = next(c for c, value in ids.items() if value == command[-1])
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(sandbox_state(service)), stderr='')
            output = ''
            if command[-3:-1] == ['ps', '-q']:
                output = ids[command[-1]]
            if command[-3:] == ['rm', '--force', 'backend'] and not same_container:
                ids['backend'] = 'container-after'
            if '--force-recreate' in command and command[-1] == 'frontend':
                ids['frontend'] = 'frontend-after'
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr='')

        with tempfile.TemporaryDirectory() as directory:
            with patch('demo_smoke.DemoClient', return_value=client), \
                    patch('demo_smoke.subprocess.run', side_effect=fake_run), \
                    patch('demo_smoke.secrets.token_hex', side_effect=['0123456789ab', 'marker']), \
                    patch('demo_smoke.secrets.token_urlsafe', return_value='synthetic-test-password'), \
                    patch('builtins.print'):
                if same_container:
                    with self.assertRaisesRegex(RuntimeError, 'newly created backend container'):
                        run_demo('ci-demo-123-1', 'http://127.0.0.1:18080', Path(directory))
                else:
                    run_demo('ci-demo-123-1', 'http://127.0.0.1:18080', Path(directory))
            self.assertTrue((Path(directory) / 'containers.log').is_file())
        self.assertTrue(any(command[-3:] == ['rm', '--force', 'backend'] for command in calls))
        self.assertEqual(calls[-1][-3:], ['down', '--volumes', '--remove-orphans'])
        compose_calls = [command for command in calls if command[:2] == ['docker', 'compose']]
        self.assertTrue(all('--env-file' in command and '/dev/null' in command for command in compose_calls))
        inspections = [command for command in calls if command[:2] == ['docker', 'inspect']]
        self.assertEqual(len(inspections), 3)
        self.assertTrue(all('.Config.Env' not in command[3] for command in inspections))
        self.assertFalse(any('watchtower' in command or 'mysql' in command for command in calls))

    def test_recreation_preserves_data_and_cleans_disposable_resources(self):
        self.exercise()

    def test_reusing_the_original_container_cannot_pass_persistence(self):
        self.exercise(same_container=True)

    def test_cleanup_rejects_a_non_ci_project_before_docker_runs(self):
        with patch('demo_smoke.subprocess.run') as runner:
            with self.assertRaises(ValueError):
                run_demo('production', 'http://127.0.0.1:18080', Path('unused'))
        runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
