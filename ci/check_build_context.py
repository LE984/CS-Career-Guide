"""Runner-only Dockerignore probe using synthetic files and a scratch COPY export."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def sentinel_paths(component):
    common = ['.env.ci-delivery-probe', '.ci-delivery-probe/.env', 'ci-delivery-probe.pem']
    return common + (['ci-delivery-probe.sqlite3', 'media/.ci-delivery-probe',
                      'ai_integration/lancedb/.ci-delivery-probe'] if component == 'backend'
                     else ['node_modules/.ci-delivery-probe'])


def verify_export(directory, component):
    for relative in sentinel_paths(component):
        if (directory / relative).exists():
            raise RuntimeError('Docker context includes an environment, credential or runtime-data probe')
    for relative in ('Dockerfile', '.env.example', 'requirements-runtime.txt' if component == 'backend' else 'package-lock.json'):
        if not (directory / relative).is_file():
            raise RuntimeError('Required source is missing from the Docker build context')


def check_context(component):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Docker context export is restricted to the Actions runner')
    root = Path(__file__).resolve().parents[1] / component
    created, directories = [], []
    try:
        for relative in sentinel_paths(component):
            target = root / relative
            missing = []
            parent = target.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for parent in reversed(missing):
                parent.mkdir()
                directories.append(parent)
            # Never replace an existing file, even on an ostensibly clean runner.
            with target.open('xb') as output:
                output.write(b'synthetic-build-context-probe-only\n')
            created.append(target)
        with tempfile.TemporaryDirectory(prefix='context-probe-') as directory:
            temporary = Path(directory)
            dockerfile = temporary / 'Dockerfile'
            dockerfile.write_text('FROM scratch\nCOPY . /\n', encoding='utf-8')
            destination = temporary / 'export'
            result = subprocess.run(['docker', 'buildx', 'build', '--file', str(dockerfile),
                                     '--output', 'type=local,dest=' + str(destination), str(root)],
                                    capture_output=True, timeout=180)
            if result.returncode:
                raise RuntimeError('Scratch context export failed on the runner')
            verify_export(destination, component)
        print(f'{component} Docker context excludes synthetic env/key/runtime probes')
    finally:
        for path in reversed(created):
            path.unlink()
        for directory in reversed(directories):
            directory.rmdir()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', choices=('backend', 'frontend'), required=True)
    check_context(parser.parse_args().component)
