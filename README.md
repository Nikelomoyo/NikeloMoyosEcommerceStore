# Everyday

A complete Django + SQLite demo store, with server-rendered HTML, CSS and vanilla JavaScript. Product artwork is bundled locally; there are no external font, image or frontend-library dependencies. Prices are in South African rand. Delivery is free. Payments are simulated: no money is charged and no real orders are fulfilled.

## Requirements

Python 3.10 or newer (Python 3.12 recommended), pip, and a modern browser. Django 5.2 is the LTS release series: https://www.djangoproject.com/download/

## Local setup (Windows PowerShell)

Open a terminal in this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_products
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

If `py` is unavailable, use the installed Python executable, for example:
`& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv`

On macOS/Linux, use `python3 -m venv .venv` and replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

Open http://127.0.0.1:8000/ for the store and http://127.0.0.1:8000/admin/ for administration. Create a customer account through the storefront. No default admin password is provided.

`seed_products` creates 12 products in three categories. It is safe to rerun: existing products, edits and stock counts are preserved. Illustrations are representative; the planter listing excludes the plant shown in its artwork.

## Features and use

- Search product names/descriptions, filter categories, sort and paginate available, in-stock listings.
- View product details, select quantities, add to the session-based bag, update quantities and remove items.
- Register, log in and log out. Anonymous carts survive registration/login; logout clears the session, including the bag.
- Checkout requires authentication. Enter delivery details and choose **Place mock order**.
- View confirmation and past orders under **My orders**. Orders are accessible only to their owner.
- In admin, manage products, categories, stock, uploaded product images and order status. Django also provides user administration.
- Product images uploaded through admin override the local SVG illustrations. Use JPG, PNG or WebP files. Keep uploaded images small (recommended under 5 MB).
- The UI remains usable without JavaScript. JavaScript adds filter auto-submit and a submit-button busy state.

## Tests and checks

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Tests exercise authentication and password validation, cart persistence and quantity limits, CSRF protection, filtering/pagination, server-calculated order totals, product snapshots, stock changes, full rollback, duplicate requests and order privacy.

## How checkout works

The browser submits an opaque session checkout token, quantities already stored in the session and delivery details. Prices and product availability come from the database. The unique order token prevents repeated submissions from creating more than one order. An order is created as the first write inside a transaction, serializing SQLite writers before stock reads. Products are locked where supported, and conditional stock decrements prevent negative stock. All order items and stock changes commit together, or everything rolls back. A successful checkout clears the bag; failures preserve it. Replaying an old successful checkout does not clear a newly filled bag.

SQLite permits a single writer and is intended here for local development. Under contention a request may receive a retry message. For production use PostgreSQL, load-test simultaneous checkouts and implement operational retry/monitoring policies appropriate to your traffic.

Order items store the name and unit price at purchase time. Later product edits or deletion do not alter historical totals. Admin order items and delivery details are read-only to protect these snapshots. Changing order status is informational: cancellation does not automatically restock products, issue refunds or trigger shipment. Handle stock adjustments explicitly in admin. There is no payment, email, tax engine or courier integration.

## Project layout

- `config/`: settings, URL routing and WSGI entry point.
- `store/`: models, forms, session cart, views, URLs, admin, tests and migrations.
- `store/management/commands/seed_products.py`: repeatable sample data.
- `templates/`: Django storefront and authentication templates.
- `static/store/`: CSS, JavaScript and local SVG artwork.
- `media/`: local admin-uploaded images (not committed).

## Before production

The default settings are development-only: DEBUG is enabled, the secret key is public, media is served by Django and SQLite is used. Do not expose the development server to the internet.

1. Set `DJANGO_DEBUG=0`, a long random `DJANGO_SECRET_KEY`, and comma-separated `DJANGO_ALLOWED_HOSTS`. Production startup rejects the development key. Configure `CSRF_TRUSTED_ORIGINS` when your deployment architecture requires it.
2. Replace SQLite with PostgreSQL and configure credentials securely. Back up the database and uploads; test restoration. Do not commit secrets or customer data.
3. Deploy through a production WSGI server (for example Waitress on Windows or Gunicorn on Linux), behind a correctly configured HTTPS reverse proxy. Configure trusted proxy headers only for a proxy you control. Secure cookies, HTTPS redirects and HSTS are enabled when DEBUG is off; validate proxy and HSTS configuration before launch.
4. Run `manage.py collectstatic` and serve static files through the web server/CDN. Serve uploaded media separately with appropriate validation, size limits and non-executable content policies. Enforce upload limits at the proxy.
5. Run `manage.py check --deploy`, maintain supported dependency/security updates, configure logging/monitoring, authentication throttling, password recovery with an email provider, and a data retention policy.
6. Replace mock checkout with a payment provider using signed webhooks and idempotent payment processing before accepting real payments. Add real shipping, taxes, refunds and fulfilment workflows as needed. Never collect or store raw card details.

This project is a functional local demo, not a configured production deployment.

## GitHub and hosted deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the prepared GitHub Actions workflow, Render Blueprint, production settings and deployment process. No cloud resources or repository push are implied by these files. Local setup above is unchanged.
