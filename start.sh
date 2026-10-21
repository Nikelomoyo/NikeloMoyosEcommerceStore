#!/usr/bin/env bash
set -o errexit
python manage.py migrate --no-input
# Idempotent: existing products and stock counts are preserved.
python manage.py seed_products
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --threads 2 --timeout 60 --access-logfile - --error-logfile -
