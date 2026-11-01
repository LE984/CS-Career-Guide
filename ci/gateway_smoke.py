"""Runner-only gateway protocol and forced-IP-change checks with synthetic upstreams."""

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen


def run_probe(project, backend_image):
    if not re.fullmatch(r'ci-gateway-\d+-\d+', project):
        raise ValueError('Disposable CI gateway project name required')
    root = Path(__file__).resolve().parents[1]
    fixture = (root / 'ci/gateway_fixture.py').read_text(encoding='utf-8')
    network = project + '-net'
    names = {c: project + '-' + c for c in ('backend', 'frontend', 'gateway')}

    def docker(*args, check=True):
        result = subprocess.run(['docker', *args], text=True, capture_output=True, timeout=120)
        if check and result.returncode:
            raise RuntimeError(f'Gateway probe Docker {args[0]} failed')
        return result.stdout.strip()

    def upstream(component, address):
        return docker('run', '-d', '--name', names[component], '--network', network,
                      '--ip', address, '--network-alias', component,
                      '--entrypoint', 'python', backend_image, '-u', '-c', fixture,
                      '8000' if component == 'backend' else '8080', component + '-' + address)

    def response(path):
        request = Request('http://127.0.0.1:18081' + path,
                          headers={'Authorization': 'Token synthetic-probe', 'Cookie': 'probe=only'})
        with urlopen(request, timeout=8) as result:
            return json.load(result)

    def wait_for(path, label):
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            try:
                result = response(path)
                if result['label'] == label:
                    return result
            except (OSError, ValueError):
                pass
            time.sleep(1)
        raise RuntimeError('Gateway did not resolve the expected upstream address')

    with tempfile.TemporaryDirectory(prefix=project) as directory:
        data = Path(directory)
        data.chmod(0o755)
        (data / 'probe.txt').write_bytes(b'gateway-file-probe')
        try:
            # Explicit subnet makes the old/new addresses deterministic on the isolated runner.
            docker('network', 'create', '--subnet', '172.30.87.0/24', network)
            backend = upstream('backend', '172.30.87.10')
            frontend = upstream('frontend', '172.30.87.20')
            gateway = docker('run', '-d', '--name', names['gateway'], '--network', network,
                '--user', '10001:10001', '--read-only', '--cap-drop', 'ALL',
                '--security-opt', 'no-new-privileges:true', '--tmpfs', '/tmp:rw,size=32m,mode=1777',
                '-v', str(root / 'deploy/nginx.conf') + ':/etc/nginx/nginx.conf:ro',
                '-v', str(data) + ':/var/www/backend-static:ro',
                '-v', str(data) + ':/var/www/media:ro', '-p', '127.0.0.1:18081:8080',
                '--entrypoint', 'nginx', 'nginx:1.27-alpine', '-g', 'daemon off;')
            wait_for('/login?from=probe', 'frontend-172.30.87.20')
            result = wait_for('/api/probe/?value=one%20two', 'backend-172.30.87.10')
            if (result['path'] != '/api/probe/?value=one%20two'
                    or result['authorization'] != 'Token synthetic-probe'
                    or result['cookie'] != 'probe=only' or result['host'] != '127.0.0.1'):
                raise RuntimeError('Gateway changed the path, query, credentials or host header')
            for path in ('/static/probe.txt', '/media/probe.txt'):
                with urlopen('http://127.0.0.1:18081' + path, timeout=8) as response_file:
                    if response_file.read() != b'gateway-file-probe':
                        raise RuntimeError('Gateway did not serve the shared file')
            start = time.monotonic()
            with urlopen('http://127.0.0.1:18081/api/ai/llm/chat/?probe=sse', timeout=8) as stream:
                first = stream.readline()
                if first != b'event: token\n' or time.monotonic() - start >= 2.5:
                    raise RuntimeError('Gateway buffered the first synthetic SSE event')
                if b'event: done' not in stream.read():
                    raise RuntimeError('Gateway lost the final synthetic SSE event')
            # Explicitly choose new IPs; a normal recreation might reuse its old IP and hide caching bugs.
            for component, address, path in (('backend', '172.30.87.11', '/api/probe/'),
                                              ('frontend', '172.30.87.21', '/login')):
                other = 'frontend' if component == 'backend' else 'backend'
                other_before = docker('inspect', '--format', '{{.Id}}', names[other])
                docker('rm', '-f', names[component])
                upstream(component, address)
                wait_for(path, component + '-' + address)
                if (docker('inspect', '--format', '{{.Id}}', names['gateway']) != gateway
                        or docker('inspect', '--format', '{{.Id}}', names[other]) != other_before):
                    raise RuntimeError('Recreating one upstream changed another container')
            print('Synthetic gateway checks passed: auth headers/query, files, unbuffered SSE and both forced IP changes')
        finally:
            for name in names.values():
                docker('rm', '-f', name, check=False)
            docker('network', 'rm', network, check=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--backend-image', required=True)
    args = parser.parse_args()
    run_probe(args.project, args.backend_image)
