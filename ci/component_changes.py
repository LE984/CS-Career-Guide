"""Classify changed paths without coupling frontend releases to backend releases."""

import argparse
from pathlib import Path

COMPONENTS = ('backend', 'frontend')


def classify(paths, selected=None):
    if selected:
        if selected not in (*COMPONENTS, 'all'):
            raise ValueError('Unsupported component')
        return set(COMPONENTS) if selected == 'all' else {selected}
    result = set()
    for path in paths:
        path = path.strip()
        if not path or path == 'README.md' or path.startswith('docs/'):
            continue
        if path.startswith('frontend/'):
            result.add('frontend')
        elif path.startswith('backend/'):
            result.add('backend')
        else:
            # Shared delivery files and unknown paths fail closed to both checks.
            result.update(COMPONENTS)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paths', type=Path, required=True)
    parser.add_argument('--component', choices=(*COMPONENTS, 'all'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    changed = classify(args.paths.read_text(encoding='utf-8').splitlines(), args.component)
    with args.output.open('a', encoding='utf-8') as output:
        for component in COMPONENTS:
            output.write(f'{component}={str(component in changed).lower()}\n')
        output.write(f'code={str(bool(changed)).lower()}\n')


if __name__ == '__main__':
    main()
