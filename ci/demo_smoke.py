"""Exercise the real demo stack on a GitHub Actions runner using disposable volumes."""

import argparse
import json
import re
import secrets
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from host_protection import verify_sandbox


class DemoClient:
    def __init__(self, base_url):
        url = urlsplit(base_url)
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.path not in ('', '/'):
            raise ValueError('Demo smoke requests must target the runner loopback address.')
        self.base_url = base_url.rstrip('/')

    def request(self, path, *, method='GET', data=None, token=None, expected=200, as_json=True):
        headers = {}
        body = None
        if data is not None:
            headers['Content-Type'] = 'application/json'
            body = json.dumps(data).encode('utf-8')
        if token:
            headers['Authorization'] = f'Token {token}'
        request = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        with response:
            if response.status != expected:
                # Never echo request credentials, tokens or response bodies into CI logs.
                raise RuntimeError(f'{method} {path}: expected HTTP {expected}, got {response.status}')
            result = response.read()
        return json.loads(result) if as_json else result

    def wait_until_ready(self, timeout=180):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                result = self.request('/api/users/profile/', expected=401)
                if isinstance(result, dict) and 'detail' in result:
                    return
            except (OSError, URLError, RuntimeError, ValueError):
                pass
            time.sleep(2)
        raise RuntimeError('Nginx did not proxy the real Django authentication response within the timeout.')

    def wait_for_spa(self, timeout=40):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if b'<div id="app"></div>' in self.request('/login', as_json=False):
                    return
            except (OSError, URLError, RuntimeError):
                pass
            time.sleep(1)
        raise RuntimeError('Gateway did not resolve the recreated frontend')


def verify_profile(profile, user_id, username, marker):
    if (profile.get('id'), profile.get('username'), profile.get('profile')) != (user_id, username, marker):
        raise RuntimeError('The authenticated user identity or saved profile marker did not survive.')


def run_demo(project, base_url, logs_dir):
    if not re.fullmatch(r'ci-demo-\d+-\d+', project):
        raise ValueError('A unique ci-demo-<run-id>-<attempt> project is required for disposable cleanup.')
    client = DemoClient(base_url)
    root = Path(__file__).resolve().parents[1]
    command = [
        'docker', 'compose', '--env-file', '/dev/null', '--project-name', project,
        '-f', str(root / 'deploy' / 'docker-compose.yml'),
        '-f', str(root / 'ci' / 'docker-compose.smoke.yml'),
    ]

    def compose(*arguments, check=True):
        result = subprocess.run(command + list(arguments), text=True, capture_output=True, check=False)
        if check and result.returncode:
            raise RuntimeError(f'Compose {arguments[0]} failed with exit code {result.returncode}: {result.stderr.strip()}')
        return result

    logs_dir.mkdir(parents=True, exist_ok=True)
    try:
        compose('up', '--detach', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '180',
                'backend', 'frontend', 'gateway')
        before = None
        for service in ('backend', 'frontend', 'gateway'):
            container = compose('ps', '-q', service).stdout.strip()
            if not container:
                raise RuntimeError(f'{service} container ID is missing for sandbox verification.')
            # Deliberately exclude Config.Env and all application credentials.
            template = '{"user":{{json .Config.User}},"host":{{json .HostConfig}},"mounts":{{json .Mounts}}}'
            inspected = subprocess.run(['docker', 'inspect', '--format', template, container],
                                       text=True, capture_output=True, check=False)
            if inspected.returncode:
                raise RuntimeError(f'{service} sandbox inspection failed.')
            verify_sandbox(service, json.loads(inspected.stdout))
            if service == 'backend':
                before = container
        print('Running sandbox verified: non-root users, read-only roots, dropped capabilities, bounded CPU/memory/PIDs/logs and only the reviewed read-only gateway config bind.', flush=True)
        client.wait_until_ready()
        for path in ('/', '/login', '/register'):
            if b'<div id="app"></div>' not in client.request(path, as_json=False):
                raise RuntimeError(f'{path} did not serve the Vue application.')
        if not client.request('/static/admin/css/base.css', as_json=False):
            raise RuntimeError('Nginx did not serve the backend collected static file.')
        client.request('/api/users/profile/', token='invalid-ci-token', expected=401)

        username = 'ci_demo_' + secrets.token_hex(6)
        password = secrets.token_urlsafe(24)
        marker = 'ci-persistence-' + secrets.token_hex(8)
        credentials = {'username': username, 'password': password}
        registered = client.request('/api/users/auth/register/', method='POST', expected=201,
                                    data={**credentials, 'confirm_password': password})
        user_id = registered['user']['id']
        token = registered['token']
        if not isinstance(token, str) or not re.fullmatch(r'[0-9a-f]{40}', token):
            raise RuntimeError('Registration did not return a valid authentication token.')
        logged_in = client.request('/api/users/auth/login/', method='POST', data=credentials)
        if logged_in['user']['id'] != user_id or logged_in['token'] != token:
            raise RuntimeError('Registration and login did not resolve to the same user and token.')
        updated = client.request('/api/users/profile/', method='PUT', token=token, data={'profile': marker})
        verify_profile(updated, user_id, username, marker)
        verify_profile(client.request('/api/users/profile/', token=token), user_id, username, marker)
        print('Real Nginx/Django integration passed: SPA routes, shared static files, auth rejection, registration, login and profile update.', flush=True)

        frontend_before = compose('ps', '-q', 'frontend').stdout.strip()
        gateway_before = compose('ps', '-q', 'gateway').stdout.strip()
        compose('stop', 'backend')
        compose('rm', '--force', 'backend')
        compose('up', '--detach', '--no-deps', '--no-build', '--pull', 'never', 'backend')
        after = compose('ps', '-q', 'backend').stdout.strip()
        if not after or after == before:
            raise RuntimeError('Persistence verification requires a newly created backend container.')
        if (compose('ps', '-q', 'frontend').stdout.strip() != frontend_before
                or compose('ps', '-q', 'gateway').stdout.strip() != gateway_before):
            raise RuntimeError('Backend recreation changed the frontend or gateway container')
        client.wait_until_ready()
        verify_profile(client.request('/api/users/profile/', token=token), user_id, username, marker)
        logged_in = client.request('/api/users/auth/login/', method='POST', data=credentials)
        if logged_in['user']['id'] != user_id or logged_in['token'] != token:
            raise RuntimeError('The saved account, password or token did not survive backend recreation.')
        verify_profile(client.request('/api/users/profile/', token=logged_in['token']), user_id, username, marker)
        compose('up', '--detach', '--no-deps', '--no-build', '--pull', 'never',
                '--force-recreate', '--wait', 'frontend')
        frontend_after = compose('ps', '-q', 'frontend').stdout.strip()
        if not frontend_after or frontend_after == frontend_before:
            raise RuntimeError('Frontend independence check requires a newly created frontend')
        if (compose('ps', '-q', 'backend').stdout.strip() != after
                or compose('ps', '-q', 'gateway').stdout.strip() != gateway_before):
            raise RuntimeError('Frontend recreation changed the backend or gateway container')
        client.wait_until_ready()
        client.wait_for_spa()
        print('SQLite volume persistence passed: new backend container retained the user, password, original token and profile marker.', flush=True)
    finally:
        for arguments, filename in [
            (('logs', '--no-color', 'backend', 'frontend', 'gateway'), 'containers.log'),
            (('ps', '--all'), 'compose-status.log'),
        ]:
            result = compose(*arguments, check=False)
            (logs_dir / filename).write_text(result.stdout + result.stderr, encoding='utf-8')
        compose('down', '--volumes', '--remove-orphans')
        print('Disposable CI containers, network and volumes removed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--base-url', default='http://127.0.0.1:18080')
    parser.add_argument('--logs-dir', required=True, type=Path)
    arguments = parser.parse_args()
    run_demo(arguments.project, arguments.base_url, arguments.logs_dir)
