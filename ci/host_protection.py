"""Validate the running demo's host-facing permissions without reading its environment."""

from pathlib import Path


def verify_sandbox(service, state):
    host = state['host']

    def require(condition, message):
        if not condition:
            raise RuntimeError(f'{service} sandbox check failed: {message}')

    require(state.get('user') == '10001:10001', 'unexpected application user')
    require(host.get('ReadonlyRootfs') is True, 'root filesystem must be read-only')
    require(host.get('Privileged') is False, 'privileged containers are forbidden')
    require(host.get('Init') is True, 'an init process is required')
    require(host.get('NetworkMode') != 'host', 'host networking is forbidden')
    require(set(host.get('CapDrop') or []) == {'ALL'}, 'all capabilities must be dropped')
    require(not host.get('CapAdd'), 'additional capabilities are forbidden')
    require(any(option in ('no-new-privileges', 'no-new-privileges:true')
                for option in host.get('SecurityOpt') or []), 'privilege escalation must be disabled')
    require(host.get('Memory', 0) > 0, 'memory limit is missing')
    require(host.get('MemorySwap') == host['Memory'], 'additional swap must be disabled')
    require(host.get('NanoCpus', 0) > 0, 'CPU limit is missing')
    require((host.get('PidsLimit') or 0) > 0, 'process limit is missing')
    logging = host.get('LogConfig', {})
    require(logging.get('Type') == 'local', 'bounded local logging is required')
    require(logging.get('Config', {}).get('max-size') == '5m', 'log size limit is missing')
    require(logging.get('Config', {}).get('max-file') == '3', 'log file count limit is missing')
    require(not host.get('Devices'), 'host device access is forbidden')

    destinations = {
        'backend': {'/data', '/data/staticfiles', '/data/media', '/tmp'},
        'frontend': {'/tmp', '/var/cache/nginx'},
        'gateway': {'/etc/nginx/nginx.conf', '/var/www/backend-static', '/var/www/media', '/tmp'},
    }[service]
    for mount in state.get('mounts', []):
        if service == 'gateway' and mount.get('Destination') == '/etc/nginx/nginx.conf':
            require(mount.get('Type') == 'bind' and mount.get('RW') is False,
                    'gateway config must be a read-only bind mount')
            require(Path(mount.get('Source', '')).resolve() ==
                    (Path(__file__).resolve().parents[1] / 'deploy/nginx.conf').resolve(),
                    'gateway may bind only the reviewed config file')
        else:
            require(mount.get('Type') in ('volume', 'tmpfs'), 'application host bind mounts are forbidden')
        require(mount.get('Destination') in destinations, 'unexpected writable or mounted path')
        if service == 'gateway' and mount.get('Type') == 'volume':
            require(mount.get('RW') is False, 'gateway data volumes must be read-only')
    for bindings in (host.get('PortBindings') or {}).values():
        require(service == 'gateway', 'only the gateway may publish ports')
        for binding in bindings or []:
            require(binding.get('HostIp') == '127.0.0.1', 'CI publishes ports only on loopback')
