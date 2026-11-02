#!/bin/sh
set -eu

export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-cs_career_guide.settings}"

python manage.py collectstatic --noinput --settings="$DJANGO_SETTINGS_MODULE"
python manage.py migrate --noinput --settings="$DJANGO_SETTINGS_MODULE"

WORKERS="$(python -c 'import os; override=os.getenv("GUNICORN_WORKERS", "").strip(); value=int(override) if override else min(2*(os.cpu_count() or 1)+1, 4); print(value)')"
TIMEOUT="${GUNICORN_TIMEOUT:-300}"

exec gunicorn cs_career_guide.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$WORKERS" \
  --timeout "$TIMEOUT" \
  --access-logfile - \
  --error-logfile -