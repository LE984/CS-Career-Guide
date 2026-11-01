"""Keep registry updates disabled until the first split deployment is coordinated."""

import argparse
import os
from pathlib import Path
import re


def publication_allowed(environment):
    return (environment.get('RELEASE_ENABLED') == 'true'
            and environment.get('GITHUB_REF') == 'refs/heads/master'
            and environment.get('GITHUB_REPOSITORY') == 'vacontinuejatotired/CS-Career-Guide'
            and environment.get('GITHUB_EVENT_NAME') in ('push', 'workflow_dispatch'))


def outputs(environment):
    tag = environment.get('EXTRA_TAG', '')
    if tag and not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._-]{0,127}', tag):
        raise ValueError('extra_tag contains invalid characters')
    return f'publish={str(publication_allowed(environment)).lower()}\nextra_tag={tag}\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('a', encoding='utf-8') as output:
        output.write(outputs(os.environ))


if __name__ == '__main__':
    main()
