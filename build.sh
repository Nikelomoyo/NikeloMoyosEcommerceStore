#!/usr/bin/env bash
set -o errexit
python -m pip install -r requirements-production.txt
python manage.py collectstatic --no-input
python manage.py check --deploy --fail-level WARNING
