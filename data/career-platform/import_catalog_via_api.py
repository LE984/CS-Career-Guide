"""Import catalog JSON through the staff HTTP API.

The token is read from an environment variable and never printed. Requests do
not follow redirects, so the Authorization header cannot be forwarded to a
different host. Defaults to a dry-run; pass --commit to write.

Example (run from the repository root):

    export CATALOG_IMPORT_TOKEN='<staff-token>'
    python data/career-platform/import_catalog_via_api.py \
        data/career-platform/xiaolincoding-questions.json --dry-run
    python data/career-platform/import_catalog_via_api.py \
        data/career-platform/xiaolincoding-questions.json --commit
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

KINDS = ('companies', 'jobs', 'questions')
MAX_BATCH_SIZE = 1000
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = 'data/career-platform/xiaolincoding-questions.json'
DEFAULT_BASE_URL = 'http://123.207.252.243/api'


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(
            req.full_url, code, 'unexpected redirect (refusing to forward the token)',
            headers, fp,
        )


def post(base_url: str, token: str, payload: dict, timeout: int):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    request = urllib.request.Request(
        base_url.rstrip('/') + '/career-platform/catalog/imports/',
        data=body,
        headers={
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8') or '{}'
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as error:
        raw = error.read().decode('utf-8', 'replace')
        try:
            data = json.loads(raw)
        except ValueError:
            data = {'detail': raw}
        return error.code, data


def _resolve_path(raw: str | None) -> Path:
    candidate = Path(raw) if raw else REPO_ROOT / DEFAULT_PATH
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
        if not candidate.is_file():
            candidate = REPO_ROOT / (raw or DEFAULT_PATH)
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise SystemExit(f'dataset not found: {candidate}')
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default=None,
                        help=f'JSON dataset path (default: {DEFAULT_PATH})')
    parser.add_argument('--base-url', default=os.environ.get('CATALOG_IMPORT_BASE_URL', DEFAULT_BASE_URL),
                        help='API base URL, for example https://example.com/api')
    parser.add_argument('--kind', choices=('all',) + KINDS, default='all')
    parser.add_argument('--token-env', default='CATALOG_IMPORT_TOKEN',
                        help='Environment variable holding the staff DRF token')
    parser.add_argument('--batch-size', type=int, default=MAX_BATCH_SIZE)
    parser.add_argument('--timeout', type=int, default=120)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', dest='dry_run', action='store_true', default=True)
    group.add_argument('--commit', dest='dry_run', action='store_false')
    args = parser.parse_args()

    if not 1 <= args.batch_size <= MAX_BATCH_SIZE:
        print(f'--batch-size must be between 1 and {MAX_BATCH_SIZE}', file=sys.stderr)
        return 2
    token = os.environ.get(args.token_env, '').strip()
    if not token:
        print(f'{args.token_env} is not set', file=sys.stderr)
        return 2
    if args.base_url.startswith('http://'):
        print('warning: the token is sent over plain HTTP; use HTTPS outside the demo network',
              file=sys.stderr)

    path = _resolve_path(args.path)
    try:
        dataset = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        print(f'cannot read dataset {path}: {error}', file=sys.stderr)
        return 2
    if not isinstance(dataset, dict):
        print('dataset root must be a JSON object', file=sys.stderr)
        return 2

    kinds = KINDS if args.kind == 'all' else (args.kind,)
    selected = []
    for kind in kinds:
        records = dataset.get(kind)
        if records is None:
            if args.kind != 'all':
                print(f'dataset has no top-level {kind!r} array', file=sys.stderr)
                return 2
            continue
        if not isinstance(records, list) or not records:
            print(f'{kind!r} must be a non-empty JSON array', file=sys.stderr)
            return 2
        selected.append((kind, records))
    if not selected:
        print('dataset has no importable companies/jobs/questions arrays', file=sys.stderr)
        return 2

    for kind, records in selected:
        for start in range(0, len(records), args.batch_size):
            batch = records[start:start + args.batch_size]
            status, response = post(args.base_url, token, {
                'kind': kind, 'records': batch, 'dry_run': args.dry_run,
            }, args.timeout)
            print(f'{kind}[{start}:{start + len(batch)}] status={status} '
                  f'{json.dumps(response, ensure_ascii=False)}')
            if status >= 400:
                return 1
    print('done: dry_run=' + ('true' if args.dry_run else 'false'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
