"""Check production settings and real static serving without requiring a cloud database."""
import os
from pathlib import Path
import secrets
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.production'
os.environ['DJANGO_DEBUG'] = '0'
os.environ.setdefault('DJANGO_SECRET_KEY', secrets.token_urlsafe(64))
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,testserver')
os.environ.setdefault('DATABASE_URL', 'postgresql://validation:validation@localhost:5432/validation')

with tempfile.TemporaryDirectory() as media:
    os.environ.setdefault('DJANGO_MEDIA_ROOT', media)
    import django
    django.setup()
    from django.core.management import call_command
    from django.test import Client
    call_command('collectstatic', interactive=False, verbosity=0)
    call_command('check', deploy=True, fail_level='WARNING')
    client = Client()
    for path, kind in [('/static/store/style.css', 'text/css'),
                       ('/static/store/app.js', 'javascript'),
                       ('/static/store/hero.svg', 'image/svg+xml')]:
        response = client.get(path, secure=True)
        assert response.status_code == 200, (path, response.status_code)
        assert kind in response['Content-Type'], (path, response['Content-Type'])
        response.close()
    print('Production security checks and CSS/JS/SVG serving passed.')
