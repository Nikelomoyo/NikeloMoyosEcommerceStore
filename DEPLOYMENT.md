# Free Render internship demo

Deploy this repository as a Render Blueprint using render.yaml. It requests one free Python web service and one free PostgreSQL database, both in Frankfurt, with no paid disk.

1. Upload the complete source tree to the GitHub repository root. manage.py, config/, store/, templates/ and static/ must be at the same level as render.yaml.
2. In Render, create a Blueprint from https://github.com/Nikelomoyo/NikeloMoyosEcommerceStore and authorize repository access when prompted.
3. Verify that both resource plans are Free, then deploy. Render generates DJANGO_SECRET_KEY and wires DATABASE_URL automatically.
4. Wait for a successful deploy and open the assigned HTTPS URL. Check /health/, register a customer, add a product and place a mock order. No real payment is charged.

Build: bash build.sh installs production requirements, collects static files and runs Django deployment checks. Start: bash start.sh migrates PostgreSQL, seeds sample products without overwriting existing stock and launches Gunicorn.

Free-tier limits: Render sleeps the web service after 15 minutes idle; it can take about a minute to wake. The free PostgreSQL database expires after 30 days. Users and orders persist in PostgreSQL until that expiry. Admin-uploaded images use temporary storage and disappear on restart; bundled product illustrations remain available. Use this setup for assessment, not real customer transactions.

Local development uses SQLite and manage.py runserver. GitHub Actions tests SQLite and PostgreSQL. Local checks: manage.py test, manage.py makemigrations --check --dry-run, and scripts/check_production.py after installing requirements-production.txt. Gunicorn runs on Render Linux, not Windows.

Never upload .venv/, db.sqlite3, media/, staticfiles/, .env or real secrets. The clean everyday-upload-ready folder excludes these files.

Documentation: https://render.com/docs/free and https://render.com/docs/deploy-django