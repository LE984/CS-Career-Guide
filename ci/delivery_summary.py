"""Fail closed on selected jobs; describe skipped integration without claiming it passed."""

import argparse
import json
import os
from pathlib import Path


def summarize(needs, environment):
    lines, failures = [], []

    def require(job, expected='success'):
        result = needs.get(job, {}).get('result', 'missing')
        if result != expected:
            failures.append(f'{job}: expected {expected}, got {result}')
        return result

    require('changes')
    outputs = needs.get('changes', {}).get('outputs', {})
    selected = [c for c in ('backend', 'frontend') if outputs.get(c) == 'true']
    require('platform-gates')
    if selected:
        require('delivery-checks')
    for component in ('backend', 'frontend'):
        if component not in selected:
            for suffix in ('test', 'image'):
                require(f'{component}-{suffix}', 'skipped')
            for prefix in ('publish', 'deploy'):
                require(f'{prefix}-{component}', 'skipped')
            lines.append(f'{component}: unselected; no image publication or deployment.')
            continue
        require(component + '-test')
        require(component + '-image')
        publish = outputs.get('publish') == 'true'
        require('publish-' + component, 'success' if publish else 'skipped')
        deploy = (publish and environment.get('SYNC_ENABLED') == 'true'
                  and environment.get('DEPLOY_' + component.upper() + '_ENABLED') == 'true')
        require('deploy-' + component, 'success' if deploy else 'skipped')
        lines.append(f'{component}: image={needs.get(component + "-image", {}).get("result")}; '
                     f'publication={needs.get("publish-" + component, {}).get("result")}; '
                     f'deployment={needs.get("deploy-" + component, {}).get("result")}.')
    require('integration', 'success' if len(selected) == 2 else 'skipped')
    lines.append('Full candidate gateway/auth/static/media/recreation integration: '
                 + ('required; see integration result.' if len(selected) == 2 else
                    'SKIPPED. Component checks use isolated contracts, not a deployed counterpart.'))
    lines.append('Server activation, real AI and browser acceptance are separate evidence. '
                 'Registry publication may trigger an independently enabled Watchtower.')
    return lines, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--needs', required=True)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    lines, failures = summarize(json.loads(args.needs), os.environ)
    with args.summary.open('a', encoding='utf-8') as output:
        output.write('\n'.join(['## Component delivery', '', *lines, '', *failures, '']))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
