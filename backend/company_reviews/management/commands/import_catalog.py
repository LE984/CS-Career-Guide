"""Import catalog JSON files through the same service used by the staff API.

Operator entry point for deploying curated catalog data. It defaults to a
dry-run, validates every record in the batch, writes transactionally, dedupes
by the stable ``dedupe_key`` and reports the index notification status.

Typical use (from the repository root, with the target database configured):

    python backend/manage.py import_catalog \
        data/career-platform/xiaolincoding-questions.json --dry-run

    python backend/manage.py import_catalog \
        data/career-platform/xiaolincoding-questions.json --commit
"""
from __future__ import annotations

import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import PermissionDenied, ValidationError

from career_platform.catalog.service import CatalogService

KINDS = ('companies', 'jobs', 'questions')
MAX_BATCH_SIZE = 1000
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PATH = 'data/career-platform/xiaolincoding-questions.json'


class SystemActor:
    """Management commands are already privileged; this satisfies the staff check."""

    is_staff = True
    is_authenticated = True
    username = 'management-command'


class Command(BaseCommand):
    help = (
        'Import catalog JSON (companies/jobs/questions) idempotently. '
        'Defaults to dry-run; pass --commit to write.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'path', nargs='?', default=None,
            help=f'JSON dataset path (default: {DEFAULT_PATH})',
        )
        parser.add_argument(
            '--kind', choices=('all',) + KINDS, default='all',
            help='Which top-level array to import; all imports companies -> jobs -> questions',
        )
        parser.add_argument(
            '--username', default=None,
            help='Existing staff username to attribute the import to; defaults to the first staff user',
        )
        parser.add_argument(
            '--batch-size', type=int, default=MAX_BATCH_SIZE,
            help=f'Records per transaction (1..{MAX_BATCH_SIZE})',
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--dry-run', dest='dry_run', action='store_true', default=True,
            help='Validate and report counts without writing (default)',
        )
        group.add_argument(
            '--commit', dest='dry_run', action='store_false',
            help='Write the records',
        )

    def handle(self, *args, **options):
        path = self._resolve_path(options['path'])
        if not 1 <= options['batch_size'] <= MAX_BATCH_SIZE:
            raise CommandError(f'--batch-size must be between 1 and {MAX_BATCH_SIZE}')
        try:
            dataset = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            raise CommandError(f'cannot read dataset {path}: {error}') from None
        if not isinstance(dataset, dict):
            raise CommandError('dataset root must be a JSON object')

        kinds = KINDS if options['kind'] == 'all' else (options['kind'],)
        selected = []
        for kind in kinds:
            records = dataset.get(kind)
            if records is None:
                if options['kind'] != 'all':
                    raise CommandError(f'dataset has no top-level {kind!r} array')
                continue
            if not isinstance(records, list) or not records:
                raise CommandError(f'{kind!r} must be a non-empty JSON array')
            selected.append((kind, records))
        if not selected:
            raise CommandError('dataset has no importable companies/jobs/questions arrays')

        actor = self._actor(options['username'])
        service = CatalogService()
        dry_run = options['dry_run']
        if not dry_run:
            self.stdout.write(self.style.WARNING(
                'allowed records become immediately visible to catalog queries and RAG retrieval'
            ))

        totals = {'created': 0, 'updated': 0, 'unchanged': 0}
        notifications = set()
        for kind, records in selected:
            counts = {'created': 0, 'updated': 0, 'unchanged': 0}
            for start in range(0, len(records), options['batch_size']):
                batch = records[start:start + options['batch_size']]
                try:
                    result = service.import_batch(
                        user=actor,
                        data={'kind': kind, 'records': batch, 'dry_run': dry_run},
                    )
                except ValidationError as error:
                    raise CommandError(
                        f'{kind}[{start}:{start + len(batch)}]: {error.detail}'
                    ) from None
                except PermissionDenied as error:
                    raise CommandError(str(error)) from None
                for key in counts:
                    counts[key] += int(result.get(key, 0))
                    totals[key] += int(result.get(key, 0))
                notifications.add(result.get('index_notification', 'unknown'))
            self.stdout.write(
                f'{kind}: records={len(records)} created={counts["created"]} '
                f'updated={counts["updated"]} unchanged={counts["unchanged"]}'
            )

        self.stdout.write(self.style.SUCCESS(
            f'total created={totals["created"]} updated={totals["updated"]} '
            f'unchanged={totals["unchanged"]} dry_run={dry_run}'
        ))
        if dry_run:
            self.stdout.write('dry-run: no database writes were made')
        else:
            self.stdout.write('index_notification=' + ','.join(sorted(str(item) for item in notifications)))

    @staticmethod
    def _resolve_path(raw: str | None) -> Path:
        candidate = Path(raw) if raw else REPO_ROOT / DEFAULT_PATH
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
            if not candidate.is_file():
                candidate = REPO_ROOT / (raw or DEFAULT_PATH)
        candidate = candidate.resolve()
        if not candidate.is_file():
            raise CommandError(f'dataset not found: {candidate}')
        return candidate

    def _actor(self, username: str | None):
        user_model = get_user_model()
        if username:
            user = user_model.objects.filter(username=username, is_staff=True).first()
            if user is None:
                raise CommandError(f'staff user not found: {username}')
            return user
        user = user_model.objects.filter(is_staff=True).order_by('id').first()
        if user is not None:
            return user
        self.stdout.write(self.style.WARNING(
            'no staff user found; using the management-command system actor'
        ))
        return SystemActor()
