"""Prepare a first gateway cutover while retaining server identities and env interpolation."""

from copy import deepcopy


def prepare(existing, template, frontend_image, backend_image, nginx_path):
    result = deepcopy(existing)
    services = result['services']
    if 'gateway' in services:
        raise ValueError('Gateway is already configured; use component deployment')
    for name, service in services.items():
        if name not in template['services']:
            raise ValueError('Unreviewed server service; refusing topology rewrite')
        managed_env = template['services'][name].get('environment', {})
        if set(service.get('environment', {})) - set(managed_env):
            raise ValueError('Unreviewed server environment keys; refusing topology rewrite')
        if 'environment' in service:
            service['environment'] = deepcopy(managed_env)
    backend, frontend = services['backend'], services['frontend']
    if backend.get('ports'):
        raise ValueError('Backend already has published ports; review before cutover')
    common = set(backend.get('networks', {})) & set(frontend.get('networks', {}))
    if not common or not frontend.get('ports'):
        raise ValueError('Existing frontend ports and a shared application network are required')
    mounts = frontend.get('volumes', [])
    shared = []
    for target in ('/var/www/backend-static', '/var/www/media'):
        selected = [m for m in mounts if m.get('target') == target and m.get('type') == 'volume'
                    and m.get('read_only') is True]
        if len(selected) != 1:
            raise ValueError('Expected existing read-only static/media named volumes')
        shared.append(deepcopy(selected[0]))
    gateway = deepcopy(template['services']['gateway'])
    gateway['networks'] = {name: None for name in sorted(common)}
    gateway['ports'] = deepcopy(frontend.pop('ports'))
    for port in gateway['ports']:
        port['target'] = 8080
    gateway['volumes'] = [
        {'type': 'bind', 'source': nginx_path, 'target': '/etc/nginx/nginx.conf', 'read_only': True},
        *shared]
    frontend.pop('volumes', None)
    frontend.pop('depends_on', None)
    frontend['image'], backend['image'] = frontend_image, backend_image
    services['gateway'] = gateway
    return result
