"""Run the production cutover function on disposable runner containers and synthetic env."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import yaml

import server_maintenance


def run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode:
        raise RuntimeError('Disposable cutover command failed: ' + command[0])
    return result.stdout.decode().strip()


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Docker cutover smoke only runs on Actions')
    root = Path(__file__).resolve().parents[1]
    project = 'ci-cutover-' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT']
    registry = project + '-registry'
    template = yaml.safe_load((root / 'deploy/docker-compose.yml').read_text())
    environment = dict(os.environ)
    base = None
    with tempfile.TemporaryDirectory(prefix=project) as directory:
        parent = Path(directory)
        try:
            run(['docker', 'run', '-d', '--name', registry, '-p', '127.0.0.1:15000:5000', 'registry:2'])
            time.sleep(2)
            images = {}
            for component in ('backend', 'frontend'):
                tag = '127.0.0.1:15000/demo/cs-career-guide-' + component + ':fixture'
                run(['docker', 'tag', os.environ['SMOKE_' + component.upper() + '_IMAGE'], tag])
                run(['docker', 'push', tag])
                metadata = json.loads(run(['docker', 'image', 'inspect', tag]))[0]
                images[component] = next(ref for ref in metadata['RepoDigests'] if ref.startswith('127.0.0.1:15000/'))
            os.environ.update(ACR_REGISTRY='127.0.0.1:15000', ACR_NAMESPACE='demo',
                              BACKEND_IMAGE=images['backend'], FRONTEND_IMAGE=images['frontend'],
                              SECRET_KEY='ci-cutover-only-key', WEB_PORT='127.0.0.1:18080')
            legacy = yaml.safe_load((root / 'deploy/docker-compose.yml').read_text())
            legacy['services'].pop('gateway')
            for component in ('backend', 'frontend', 'watchtower', 'mysql'):
                legacy['services'][component]['container_name'] = project + '-' + component
            legacy['networks']['app-net']['name'] = project + '-net'
            frontend = legacy['services']['frontend']
            frontend['ports'] = ['127.0.0.1:18080:8080']
            frontend['volumes'] = ['backend-static:/var/www/backend-static:ro', 'media:/var/www/media:ro']
            frontend['depends_on'] = {'backend': {'condition': 'service_healthy'}}
            compose = parent / 'docker-compose.yml'
            compose.write_text(yaml.safe_dump(legacy), encoding='utf-8')
            env = parent / '.env'
            env.write_text('SECRET_KEY=ci-cutover-only-key\nCOMPOSE_PROJECT_NAME=' + project + '\n', encoding='utf-8')
            env.chmod(0o600)
            base = ['docker', 'compose', '--project-directory', directory, '--env-file', str(env),
                    '-p', project, '-f', str(compose)]
            run([*base, 'up', '-d', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '180', 'backend', 'frontend'])
            gateway_reference, gateway_id, fingerprint = server_maintenance.publish_gateway(images['frontend'])
            server_maintenance.install(str(env), {
                'template': template, 'frontend_image': images['frontend'],
                'topology_source': (root / 'ci/split_topology.py').read_text(),
                'nginx': (root / 'deploy/nginx.conf').read_text(),
                'helpers': {name: (root / 'ci' / name).read_text() for name in ('sync_runtime_env.py', 'deploy_component.py')},
                'gateway_image': gateway_reference,
                'gateway_image_id': gateway_id,
                'gateway_fingerprint': fingerprint,
            })
            print('Disposable real cutover passed: backend/env retained, gateway routes and single frontend activation verified.')
        finally:
            if base:
                # Only this generated ci-cutover project owns these disposable volumes.
                subprocess.run([*base, 'down', '--volumes', '--remove-orphans'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['docker', 'rm', '-f', registry], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.environ.clear()
            os.environ.update(environment)


if __name__ == '__main__':
    main()
