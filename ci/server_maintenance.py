"""Read-only server inventory over the existing verified deployment SSH channel."""

import argparse
import base64
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile

STAGE = 'start'


def stage(value):
    global STAGE
    STAGE = value


class MaintenanceFailure(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__('Server maintenance operation failed; raw diagnostics withheld')


def import_gateway(payload):
    """Import the exact runner-verified public Nginx image without server Hub access."""
    import hashlib

    archive = base64.b64decode(payload['gateway_archive_b64'], validate=True)
    expected_id = payload['gateway_image_id']
    if (len(archive) > 150 * 1024 * 1024
            or hashlib.sha256(archive).hexdigest() != payload['gateway_archive_sha256']
            or not re.fullmatch(r'sha256:[0-9a-f]{64}', expected_id)):
        raise ValueError('Gateway archive integrity check failed')
    loaded = subprocess.run(['docker', 'load'], input=archive, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=180)
    if loaded.returncode:
        raise MaintenanceFailure('gateway-import-failed')
    image = run(['docker', 'image', 'inspect', 'nginx:1.27-alpine'], json_output=True)[0]
    if image['Id'] != expected_id or image.get('Os') != 'linux' or image.get('Architecture') != 'amd64':
        raise ValueError('Gateway imported image identity does not match runner verification')


def run(command, *, json_output=False):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode:
        diagnostic = result.stderr.lower()
        code = ('registry-timeout' if b'timeout' in diagnostic or b'timed out' in diagnostic else
                'registry-auth' if b'unauthorized' in diagnostic or b'authentication required' in diagnostic else
                'registry-unreachable' if b'connection refused' in diagnostic or b'no such host' in diagnostic else
                'image-missing' if b'manifest unknown' in diagnostic else 'command-failed')
        raise MaintenanceFailure(code)
    return json.loads(result.stdout) if json_output else result.stdout.decode().strip()


def existing_deployment(env_path):
    path = Path(env_path)
    if not path.is_absolute() or path.name != '.env' or path.resolve() != path:
        raise ValueError('Expected an absolute deployment .env path without symlinks')
    info, parent = path.stat(), path.parent.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_uid != os.geteuid() or info.st_mode & 0o077
            or parent.st_uid != os.geteuid() or parent.st_mode & 0o022):
        raise ValueError('Unsafe deployment file or directory ownership/permissions')
    compose = path.parent / 'docker-compose.yml'
    if compose.is_symlink() or not compose.is_file():
        raise ValueError('Expected an existing regular Compose file')
    base = ['docker', 'compose', '--project-directory', str(path.parent),
            '--env-file', str(path), '-f', str(compose)]
    # Expanded environment values stay only inside this process; never emit config.
    config = run([*base, '--profile', '*', 'config', '--format', 'json'], json_output=True)
    return path, base, config


def inventory(env_path):
    path, base, config = existing_deployment(env_path)
    report = {'action': 'audit', 'env_file_read_or_replaced': False, 'services': {},
              'compose_project': config.get('name'), 'deployment_directory_private': True}
    for component in ('backend', 'frontend', 'gateway', 'watchtower'):
        service = config.get('services', {}).get(component)
        if not service:
            report['services'][component] = {'configured': False}
            continue
        ids = run([*base, '--profile', '*', 'ps', '-a', '-q', component]).splitlines()
        containers = run(['docker', 'inspect', *ids], json_output=True) if ids else []
        safe_containers = []
        for container in containers:
            image = run(['docker', 'image', 'inspect', container['Image']], json_output=True)[0]
            safe_containers.append({
                'id': container['Id'], 'name': container['Name'],
                'state': container['State']['Status'],
                'health': container['State'].get('Health', {}).get('Status'),
                'image': container['Config']['Image'], 'image_id': container['Image'],
                'repository_digests': image.get('RepoDigests', []),
                'project': container['Config'].get('Labels', {}).get('com.docker.compose.project'),
                'ports': container['HostConfig'].get('PortBindings', {}),
                'named_volumes': sorted(m['Name'] for m in container.get('Mounts', []) if m['Type'] == 'volume'),
            })
        report['services'][component] = {
            'configured': True, 'containers': safe_containers,
            'environment_keys': sorted(service.get('environment', {})),
            'published_ports': service.get('ports', []),
        }
    report['tools'] = {'compose': run(['docker', 'compose', 'version', '--short']),
                       'python': run(['python3', '--version'])}
    print(json.dumps(report))


def install(env_path, payload):
    """Cut over only frontend/gateway; restore the previous frontend on failure."""
    import contextlib
    from datetime import datetime, timezone
    import fcntl
    import hashlib
    import io
    import shutil
    import time
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    stage('existing-config')
    path, base, existing = existing_deployment(env_path)
    lock_fd = os.open(str(path) + '.ai-sync.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    lock_info = os.fstat(lock_fd)
    if (lock_info.st_uid != os.geteuid() or lock_info.st_mode & 0o077
            or not stat.S_ISREG(lock_info.st_mode) or lock_info.st_nlink != 1):
        os.close(lock_fd)
        raise ValueError('Unsafe deployment lock')
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    candidate = None
    try:
        # Inventory again inside the shared deployment lock.
        path, base, existing = existing_deployment(env_path)
        if 'gateway' in existing['services']:
            raise ValueError('Gateway already installed; use ordinary component activation')
        env_identity = (path.stat().st_ino, path.stat().st_mtime_ns, path.stat().st_size)
        compose_path, nginx_path = path.parent / 'docker-compose.yml', path.parent / 'nginx.conf'
        original_compose = compose_path.read_bytes()
        if nginx_path.is_symlink() or (nginx_path.exists() and not nginx_path.is_file()):
            raise ValueError('Unsafe gateway configuration path')
        original_nginx = nginx_path.read_bytes() if nginx_path.exists() else None
        original_nginx_mode = stat.S_IMODE(nginx_path.stat().st_mode) if nginx_path.exists() else None

        def container(service):
            ids = run([*base, '--profile', '*', 'ps', '-a', '-q', service]).splitlines()
            if len(ids) != 1:
                raise ValueError('Expected one existing application container')
            return run(['docker', 'inspect', ids[0]], json_output=True)[0]

        stage('existing-containers')
        before = {name: container(name) for name in ('backend', 'frontend')}
        project = existing['name']
        for item in before.values():
            if (item['State']['Status'] != 'running'
                    or item['Config'].get('Labels', {}).get('com.docker.compose.project') != project):
                raise ValueError('Existing application project is not running as expected')
        if 'watchtower' in existing['services']:
            watchers = run([*base, '--profile', '*', 'ps', '-q', 'watchtower']).splitlines()
            if watchers:
                run(['docker', 'stop', *watchers])

        def digest(service):
            image = run(['docker', 'image', 'inspect', before[service]['Image']], json_output=True)[0]
            refs = [ref for ref in image.get('RepoDigests', []) if '/cs-career-guide-' + service + '@sha256:' in ref]
            if len(refs) != 1:
                raise ValueError('Existing image needs one unambiguous repository digest')
            return refs[0]

        stage('existing-digests')
        backend_digest, old_frontend_digest = digest('backend'), digest('frontend')
        frontend_digest = payload['frontend_image']
        expected_repo = old_frontend_digest.split('@')[0]
        if not re.fullmatch(re.escape(expected_repo) + r'@sha256:[0-9a-f]{64}', frontend_digest):
            raise ValueError('First frontend image must match the existing repository by digest')
        scope = {'__name__': 'split_topology'}
        exec(compile(payload['topology_source'], 'split_topology', 'exec'), scope)
        topology = scope['prepare'](existing, payload['template'], frontend_digest, backend_digest, str(nginx_path))

        def write_private(target, content):
            descriptor, temporary = tempfile.mkstemp(prefix='.split-write-', dir=target.parent)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(content)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, target)
            finally:
                Path(temporary).unlink(missing_ok=True)

        descriptor, candidate_name = tempfile.mkstemp(prefix='.split-compose-', suffix='.json', dir=path.parent)
        candidate = Path(candidate_name)
        with os.fdopen(descriptor, 'w') as output:
            json.dump(topology, output)
        candidate_base = ['docker', 'compose', '--project-directory', str(path.parent), '--env-file', str(path),
                          '--project-name', project, '-f', str(candidate)]
        stage('candidate-config')
        rendered = run([*candidate_base, '--profile', '*', 'config', '--format', 'json'], json_output=True)
        stage('candidate-environment')
        for name in existing['services']:
            for key, value in existing['services'][name].get('environment', {}).items():
                if rendered['services'][name].get('environment', {}).get(key) != value:
                    raise ValueError('Candidate changes an existing runtime environment value')
        stage('candidate-storage')
        if rendered.get('volumes') != existing.get('volumes') or rendered.get('networks') != existing.get('networks'):
            raise ValueError('Candidate changed existing network or volume identities')
        stage('pull-images')
        if payload.get('gateway_archive_b64'):
            stage('import-gateway')
            import_gateway(payload)
            stage('pull-frontend')
            run([*candidate_base, 'pull', 'frontend'])
        else:
            run([*candidate_base, 'pull', 'frontend', 'gateway'])
        stage('backup')
        if ((path.stat().st_ino, path.stat().st_mtime_ns, path.stat().st_size) != env_identity
                or compose_path.read_bytes() != original_compose):
            raise ValueError('Deployment configuration changed during preparation')

        backup = Path(tempfile.mkdtemp(prefix='.split-backup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S-'), dir=path.parent))
        write_private(backup / 'docker-compose.yml', original_compose)
        if original_nginx is not None:
            write_private(backup / 'nginx.conf', original_nginx)
        pins = {}
        for component in ('backend', 'frontend'):
            target = path.parent / f'docker-compose.{component}-image.json'
            if target.is_symlink():
                raise ValueError('Unexpected symlink at component pin path')
            pins[component] = target.read_bytes() if target.exists() else None
            if pins[component] is not None:
                write_private(backup / target.name, pins[component])
        tools = backup / 'tools' / 'ci'
        tools.mkdir(parents=True, mode=0o700)
        for name, source in payload['helpers'].items():
            if name not in ('sync_runtime_env.py', 'deploy_component.py'):
                raise ValueError('Unexpected helper file')
            write_private(tools / name, source.encode())
        write_private(backup / 'rollback-reference.json', json.dumps({
            'backend': backend_digest, 'frontend': old_frontend_digest,
            'backend_container': before['backend']['Id'], 'project': project}).encode())

        def probe():
            ports = rendered['services']['gateway']['ports']
            local = [p for p in ports if p.get('protocol', 'tcp') == 'tcp'
                     and p.get('host_ip', '') in ('', '0.0.0.0', '127.0.0.1', '::')]
            if not local:
                raise ValueError('No reviewed localhost-accessible gateway port')
            port = next((p for p in local if str(p['published']) == '48080'), local[0])['published']
            root = 'http://127.0.0.1:' + str(port)
            checks = (('/', 200, True), ('/login', 200, True), ('/static/admin/css/base.css', 200, False),
                      ('/api/users/profile/', 401, False), ('/media/split-check-nonexistent', 404, False))
            for route, expected, spa in checks:
                request = Request(root + route)
                try:
                    response = urlopen(request, timeout=10)
                except HTTPError as error:
                    response = error
                with response:
                    body = response.read()
                    if response.status != expected or (spa and b'<div id="app"></div>' not in body):
                        raise ValueError('Gateway read-only HTTP verification failed')
            return [route for route, _, _ in checks]

        current_base = [*candidate_base[:-1], str(compose_path)]
        try:
            write_private(nginx_path, payload['nginx'].encode())
            nginx_path.chmod(0o644)  # Public config must be readable by container UID 10001.
            write_private(compose_path, candidate.read_bytes())
            for component, image in (('backend', backend_digest), ('frontend', frontend_digest)):
                write_private(path.parent / f'docker-compose.{component}-image.json',
                              json.dumps({'services': {component: {'image': image}}}).encode())
            stage('activate-gateway')
            run([*current_base, 'up', '-d', '--no-deps', '--no-build', '--pull', 'never',
                 '--force-recreate', '--wait', '--wait-timeout', '180', 'frontend', 'gateway'])
            stage('verify-gateway')
            routes = probe()
            gateway_before = container('gateway')['Id']
            frontend_before = container('frontend')['Id']
            # Exercise the exact installed single-service activation path once.
            helper = {'__name__': 'sync_runtime_env'}
            exec(compile(payload['helpers']['sync_runtime_env.py'], 'sync_runtime_env', 'exec'), helper)
            # The component helper takes this same flock itself. Release our
            # descriptor while it owns the activation, then resume the cutover lock.
            stage('verify-frontend-recreation')
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    helper['apply_remote'](str(path), {}, 'frontend', frontend_digest)
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
            routes = probe()
            if (container('backend')['Id'] != before['backend']['Id']
                    or container('gateway')['Id'] != gateway_before
                    or container('frontend')['Id'] == frontend_before
                    or (path.stat().st_ino, path.stat().st_mtime_ns, path.stat().st_size) != env_identity):
                raise ValueError('Single frontend activation changed protected runtime state')
        except Exception:
            # Restore only files and containers changed by this cutover; keep Watchtower stopped.
            gateway_ids = run([*current_base, 'ps', '-a', '-q', 'gateway']).splitlines()
            if gateway_ids:
                run(['docker', 'rm', '-f', *gateway_ids])
            write_private(compose_path, original_compose)
            if original_nginx is None:
                nginx_path.unlink(missing_ok=True)
            else:
                write_private(nginx_path, original_nginx)
                nginx_path.chmod(original_nginx_mode)
            for component, previous in pins.items():
                target = path.parent / f'docker-compose.{component}-image.json'
                if previous is None:
                    target.unlink(missing_ok=True)
                else:
                    write_private(target, previous)
            rollback_pin = backup / 'rollback-frontend.json'
            write_private(rollback_pin, json.dumps({'services': {'frontend': {'image': old_frontend_digest}}}).encode())
            run([*current_base, '-f', str(rollback_pin), 'up', '-d', '--no-deps', '--no-build', '--pull', 'never',
                 '--force-recreate', '--wait', '--wait-timeout', '180', 'frontend'])
            raise MaintenanceFailure('cutover-failed-frontend-restored') from None
        report = {'action': 'install', 'success': True, 'project': project,
                  'backend_container_unchanged': True, 'env_file_unchanged': True,
                  'frontend_image': frontend_digest, 'backend_image': backend_digest,
                  'gateway_container': gateway_before, 'http_checks': routes,
                  'single_frontend_activation_verified': True, 'database_migrations': False,
                  'real_model': False, 'backup_directory': backup.name,
                  'tools_relative_path': str(tools.relative_to(path.parent))}
        write_private(backup / 'result.json', json.dumps(report, indent=2).encode())
        print(json.dumps(report))
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)
        os.close(lock_fd)


def remote(action, frontend_image=''):
    stage('verified-ssh')
    required = ('DEPLOY_SSH_HOST', 'DEPLOY_SSH_USER', 'DEPLOY_ENV_PATH',
                'DEPLOY_SSH_KEY', 'DEPLOY_SSH_KNOWN_HOSTS')
    if any(not os.environ.get(key, '').strip() for key in required):
        raise ValueError('Deployment SSH configuration is incomplete')
    host, user = os.environ['DEPLOY_SSH_HOST'], os.environ['DEPLOY_SSH_USER']
    port = os.environ.get('DEPLOY_SSH_PORT') or '22'
    if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*', host)
            or not re.fullmatch(r'[a-z_][a-z0-9_-]*', user)
            or not port.isdigit() or not 1 <= int(port) <= 65535):
        raise ValueError('Invalid deployment SSH coordinates')
    source = base64.b64encode(Path(__file__).read_bytes()).decode('ascii')
    bootstrap = f"import base64;exec(compile(base64.b64decode('{source}'),'server-maintenance','exec'))"
    command = shlex.join(['python3', '-c', bootstrap, '--remote', '--action', action,
                          '--env-path', os.environ['DEPLOY_ENV_PATH']])
    payload = b''
    if action == 'install':
        import hashlib
        import yaml
        root = Path(__file__).resolve().parents[1]
        stage('runner-gateway-image')
        run(['docker', 'pull', '--platform', 'linux/amd64', 'nginx:1.27-alpine'])
        gateway = run(['docker', 'image', 'inspect', 'nginx:1.27-alpine'], json_output=True)[0]
        with tempfile.TemporaryDirectory(prefix='gateway-export-') as archive_dir:
            archive_path = Path(archive_dir) / 'gateway.tar'
            run(['docker', 'save', '--output', str(archive_path), 'nginx:1.27-alpine'])
            archive = archive_path.read_bytes()
        payload = json.dumps({
            'frontend_image': frontend_image,
            'topology_source': (root / 'ci/split_topology.py').read_text(),
            'template': yaml.safe_load((root / 'deploy/docker-compose.yml').read_text()),
            'nginx': (root / 'deploy/nginx.conf').read_text(),
            'helpers': {name: (root / 'ci' / name).read_text()
                        for name in ('sync_runtime_env.py', 'deploy_component.py')},
            'gateway_archive_b64': base64.b64encode(archive).decode('ascii'),
            'gateway_archive_sha256': hashlib.sha256(archive).hexdigest(),
            'gateway_image_id': gateway['Id'],
        }).encode()
    stage('verified-ssh')
    with tempfile.TemporaryDirectory(prefix='split-maintenance-') as directory:
        os.chmod(directory, 0o700)
        key, known = Path(directory) / 'identity', Path(directory) / 'known_hosts'
        for target, content in ((key, os.environ['DEPLOY_SSH_KEY']),
                                (known, os.environ['DEPLOY_SSH_KNOWN_HOSTS'])):
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as output:
                output.write(content.rstrip('\r\n') + '\n')
        result = subprocess.run([
            'ssh', '-F', '/dev/null', '-T', '-i', str(key), '-p', port,
            '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', f'UserKnownHostsFile={known}',
            '-o', 'GlobalKnownHostsFile=/dev/null', '-o', 'ConnectTimeout=15',
            '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
            f'{user}@{host}', command], input=payload, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=1200)
        if result.returncode:
            try:
                failure = json.loads(result.stdout)
            except (ValueError, TypeError):
                raise MaintenanceFailure('ssh-command-failed') from None
            if (set(failure) == {'success', 'stage', 'failure'} and failure['success'] is False
                    and all(isinstance(failure[key], str) and re.fullmatch(r'[a-z-]{1,80}', failure[key])
                            for key in ('stage', 'failure'))):
                stage(failure['stage'])
                raise MaintenanceFailure(failure['failure'])
            raise MaintenanceFailure('ssh-command-failed')
        report = json.loads(result.stdout)
    output = Path('output/server-maintenance')
    output.mkdir(parents=True, exist_ok=True)
    (output / f'{action}.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('audit', 'install'), default='audit')
    parser.add_argument('--frontend-image', default='')
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--env-path')
    args = parser.parse_args()
    if args.remote:
        if args.action == 'install':
            install(args.env_path, json.load(sys.stdin))
        else:
            inventory(args.env_path)
    else:
        remote(args.action, args.frontend_image)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'success': False, 'stage': STAGE,
                          'failure': error.code if isinstance(error, MaintenanceFailure) else 'validation-or-runtime'}))
        raise SystemExit(1)
