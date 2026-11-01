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
import tempfile


def run(command, *, json_output=False):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    if result.returncode:
        raise RuntimeError('Server inventory command failed; raw diagnostics withheld')
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


def remote(action):
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
            f'{user}@{host}', command], input=b'', stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=600)
        if result.returncode:
            raise RuntimeError('Verified SSH inventory failed; raw diagnostics withheld')
        report = json.loads(result.stdout)
    output = Path('output/server-maintenance')
    output.mkdir(parents=True, exist_ok=True)
    (output / f'{action}.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=('audit',), default='audit')
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--env-path')
    args = parser.parse_args()
    if args.remote:
        inventory(args.env_path)
    else:
        remote(args.action)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Server maintenance failed; raw configuration/SSH diagnostics withheld')
