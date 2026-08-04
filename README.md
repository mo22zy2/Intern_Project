# Rest_project 🍽️

A full-stack restaurant management platform with **two backends sharing one PostgreSQL database** — a **Django** app (session-based auth, server-rendered HTML) and a **FastAPI** service (JWT auth, JSON API) — plus a **Flutter mobile client** and a **RAG-powered chatbot**.

## Project Knowledge Graph

> **Live & interactive:** every file, module, and relationship in this repo is indexed into a navigable knowledge graph — **explore it at [Rest_project Knowledge Graph](https://mo22zy2.github.io/Django-Eats-Intern-Project/)** (deployed to GitHub Pages; no setup needed). The community overview below shows the ~135 module clusters (bubble size = files in the cluster); click the image to open the full interactive graph. A local copy also lives at [`graphify-out/graph.html`](graphify-out/graph.html).

<p align="center">
  <a href="https://mo22zy2.github.io/Django-Eats-Intern-Project/">
    <img src="graphify-out/graph-preview.svg" alt="Rest_project knowledge graph — community overview" width="100%">
  </a>
</p>

## Badges

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?style=flat-square&logo=django&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=flat-square&logo=flutter&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-Session%20%2B%20JWT-6a0dad?style=flat-square)
![i18n](https://img.shields.io/badge/i18n-English%20%2F%20Arabic-8b0000?style=flat-square)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Knowledge Graph](#knowledge-graph)
- [Project Structure](#project-structure)
- [RAG Chatbot](#rag-chatbot)
- [Telegram Notifications](#telegram-notifications)
- [Security](#security)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Mobile App (Flutter)](#mobile-app-flutter)
- [Admin Dashboard](#admin-dashboard)
- [Testing](#testing)
- [Docker](#docker)
- [API Endpoints (FastAPI)](#api-endpoints-fastapi)
- [Branch Structure](#branch-structure)
- [Contributing](#contributing)

## Features

| Feature | Django Views | FastAPI Endpoints |
|---------|-------------|-------------------|
| **Auth** | Register, login (rate-limited), logout | Register, login, JWT token |
| **Home** | Popular items, categories, ratings | Same via JSON |
| **Menu** | List, detail, search, sort, ratings | Same via JSON |
| **Cart** | Add, remove, update items, options | Same via JSON |
| **Order** | Checkout, place order, history, detail, QR | Place order, payment, QR |
| **Reservation** | Create, edit, cancel (double-booking guarded) | Same via JSON |
| **Profile** | Edit profile, settings, password change | Same via JSON |
| **Review** | Create, edit, delete (purchase-gated) | Same via JSON |
| **Payment** | Add/list payment methods, card masking | Same via JSON |
| **Chat** | RAG chatbot widget (`CHAT_API_URL`) | Same via JSON |
| **Admin** | Dashboard, orders, menu, inventory, users, reports | Superuser-only management endpoints |
| **Notify** | Telegram notifications on order/reservation/inventory/review events | — |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Django        │     │   FastAPI        │     │   Flutter App   │
│   (Session      │     │   (JWT API)      │     │   (mobile)      │
│    Auth)        │     │                  │     │                 │
│   localhost:8070│     │   localhost:8071 │     │  → FastAPI:8071 │
│   HTML pages    │     │   /auth, /menu,  │     │                 │
│                 │     │   /cart, /orders │     │                 │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                       │
         └───────────┬───────────┘                       │
                     │                                   │
            ┌────────▼────────┐                          │
            │   PostgreSQL    │◄─────────────────────────┘
            │   (rest_db)     │
            └─────────────────┘
```

- **Django** serves HTML templates with session-based authentication (port **8070**).
- **FastAPI** serves JSON endpoints with JWT token-based authentication (port **8071** — never share 8070).
- Both backends read/write the **same PostgreSQL database** and share the Django service layer (`api/services/`). FastAPI reuses Django's ORM via `django.setup()` and keeps SQLAlchemy mirror models in sync with Django's schema.
- The **Flutter app** talks to FastAPI on port 8071 by default (`10.0.2.2:8071` on the Android emulator, `localhost:8071` elsewhere).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend (Django) | Django 4.2, Python 3.14 |
| API (FastAPI) | FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2 |
| Database | PostgreSQL (via psycopg2-binary) |
| Auth (Django) | Session-based, bcrypt password hashing |
| Auth (FastAPI) | JWT (python-jose), bcrypt |
| Frontend (Web) | HTML templates + Bootstrap-style CSS (RTL-aware, Arabic-ready) |
| Frontend (Mobile) | Flutter (`frontend/rest_project/`) |
| RAG Chatbot | pgvector (PostgreSQL embeddings) + Qdrant vector DB |
| Notifications | Telegram bot (webhook + signals) |
| Other | QR codes, Pillow, Arabic l10n (polib) |

## Knowledge Graph

The repository is indexed into a **queryable knowledge graph** (community detection, god-node analysis, and an honest EXTRACTED / INFERRED / AMBIGUOUS audit trail):

- **Live interactive visualization:** <https://mo22zy2.github.io/Django-Eats-Intern-Project/> (GitHub Pages; updated from the `gh-pages` branch).
- **Local copy:** [`graphify-out/graph.html`](graphify-out/graph.html) — open in any browser, no server needed.
- **Community overview:** [`graphify-out/graph-preview.svg`](graphify-out/graph-preview.svg) — static snapshot for READMEs/docs.
- **Raw graph data:** `graphify-out/graph.json`.
- **Audit report:** `graphify-out/GRAPH_REPORT.md`.

> **How to query it:** install `graphify` (`uv tool install graphifyy`) and run `graphify query "Why does AuthProvider bridge the Flutter auth flow to the cart?"` from the repo root. Rebuild after changes with `graphify --update` (or `graphify . --no-viz` for a fresh full build). The `graphify-out/` folder is git-ignored except for `graph.html` and `graph-preview.svg`.

## Project Structure

```
Rest_project/               # Django project root
├── Rest_project/           # Django project config (settings, urls, wsgi)
│   ├── settings.py         # PostgreSQL, i18n, static/media, security headers
│   └── urls.py             # i18n_patterns (EN + AR)
├── api/                    # Django app
│   ├── models.py           # All Django ORM models (User, Menu, Order, ...)
│   ├── services/           # Business logic shared with FastAPI
│   ├── views/              # Session-auth view functions
│   ├── templates/          # HTML templates (auth, menu, cart, dashboard, ...)
│   ├── signals.py          # Telegram/notification hooks on domain events
│   └── tests/              # Django TestCase suites
├── api_endpoints/          # FastAPI app
│   ├── main.py             # App + lifespan (django.setup())
│   ├── models.py           # SQLAlchemy mirror of Django tables
│   ├── schemas.py          # Pydantic request/response models
│   ├── routers/            # /auth, /menu, /cart, /orders, /admin, ...
│   ├── auth_utils.py       # JWT helpers (env-driven SECRET_KEY)
│   └── tests/              # pytest + TestClient suites
├── frontend/rest_project/  # Flutter mobile app
├── static/                 # CSS, JS
├── locale/                 # Translation files (ar/)
└── graphify-out/           # Knowledge graph outputs (git-ignored)
```

## RAG Chatbot

The project integrates a **mini RAG (Retrieval-Augmented Generation) chatbot** that answers questions about the restaurant (menu items, ordering, reservations, and more) using the project data as its knowledge base.

- **pgvector** — PostgreSQL extension storing the restaurant knowledge-base embeddings for vector similarity search.
- **Qdrant** — a dedicated vector database for fast, scalable similarity retrieval.
- Retrieves the most relevant documents for a question, then generates a grounded answer from the retrieved context.
- Wired into the Django frontend through the `CHAT_API_URL` environment variable (default: `http://localhost:8081/api/v1/nlp/index/answer/1`), injected into templates via the `chat_api_url` context processor.

## Telegram Notifications

Domain events automatically trigger Telegram notifications via Django signals (`api/signals.py`):

- **New orders** — a message with order details is sent to staff.
- **New reservations** and **cancellations** — staff are notified.
- **Low inventory** — staff are alerted when stock drops below the threshold.
- **New reviews** — staff get notified about newly published ratings.

Set `TELEGRAM_BOT_TOKEN` (and optionally `TELEGRAM_WEBHOOK_SECRET`) in `.env`; run `python manage.py set_telegram_webhook` to wire up the bot webhook.

## Security

- **Secrets from environment only** — `DJANGO_SECRET_KEY`, `JWT_SECRET_KEY`, and `DB_PASSWORD` are read from `.env`; no hardcoded defaults (settings raise `ImproperlyConfigured` when a required secret is missing in production).
- **Login rate-limiting** — 5 failed attempts per username lock the account for 5 minutes (`api/services/auth_service.py`).
- **Active-user enforcement** — FastAPI `get_current_user` rejects inactive accounts.
- **CORS allowlist** — origins configured via `CORS_ORIGINS` (no wildcard in production).
- **Security headers** — HSTS, `X-Content-Type-Options`, `X-Frame-Options`, secure/HTTP-only cookies, and SSL redirect enabled when `DJANGO_DEBUG=False`.
- **Input validation** — cart quantities must be positive integers, order/reservation/admin operations validate stock, ownership, and status transitions; CSRF-protected POST forms.
- **Whitenoise** — served static files, manifest-compressed in production.
- **`.env` is git-ignored** — real credentials never land in version control.

## Setup

### Prerequisites

- Python 3.14+
- PostgreSQL running on `localhost:5432`
- A database named `rest_db`
- (Optional) Flutter SDK for the mobile app

### Installation

```bash
# Clone the repo
git clone https://github.com/mo22zy2/Django-Eats-Intern-Project.git
cd Django-Eats-Intern-Project

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r Rest_project/requirements.txt

# Configure environment
cd Rest_project
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
# Edit .env with your PostgreSQL credentials and secrets

# Run Django migrations
python manage.py migrate

# (Optional) Seed the menu from data/menu.json (categories, items, extras)
python manage.py import_menu_json data/menu.json

# Run Django dev server (port 8070)
python manage.py runserver 8070

# In a separate terminal, run FastAPI on a different port (8071) —
# both backends default to 8070, so they cannot share it.
uvicorn api_endpoints.main:app --reload --port 8071

# (Optional) Run the Flutter app — see "Mobile App (Flutter)"
```

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DB_NAME` | `rest_db` | ✅ | PostgreSQL database name |
| `DB_USER` | `postgres` | ✅ | PostgreSQL user |
| `DB_PASSWORD` | — | ✅ | PostgreSQL password (no default) |
| `DB_PORT` | `5432` | — | PostgreSQL port |
| `DB_HOST` | `127.0.0.1` | — | PostgreSQL host |
| `DJANGO_SECRET_KEY` | — | ✅ (prod) | Django secret — required when `DJANGO_DEBUG=False` |
| `DJANGO_DEBUG` | `False` | — | Django debug mode (`True` in dev) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | — | Comma-separated allowed hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost,http://127.0.0.1` | — | CSRF-trusted origins |
| `JWT_SECRET_KEY` | — | ✅ (prod) | FastAPI JWT signing key |
| `CORS_ORIGINS` | `http://localhost:8070,...` | — | Comma-separated CORS allowlist |
| `CHAT_API_URL` | `http://localhost:8081/api/v1/nlp/index/answer/1` | — | RAG chatbot endpoint |
| `BASE_URL` | `http://localhost:8070` | — | Base URL for QR codes / links |
| `TELEGRAM_BOT_TOKEN` | — | — | Telegram bot token for notifications |
| `TELEGRAM_WEBHOOK_SECRET` | — | — | Secret for Telegram webhook verification |

`DJANGO_SECRET_KEY` and `JWT_SECRET_KEY` are required in production — `DJANGO_SECRET_KEY` must be set whenever `DJANGO_DEBUG=False` (settings raise `ImproperlyConfigured` otherwise).

## Mobile App (Flutter)

The mobile client lives in `frontend/rest_project/` and talks to the FastAPI backend.

```bash
cd frontend/rest_project
flutter pub get
flutter run --web-port 8072   # Android emulator targets http://10.0.2.2:8071 by default
```

- The API base URL is resolved at runtime: `API_BASE_URL` env var override → Android emulator (`10.0.2.2:8071`) → `localhost:8071`.
- Internet permission and cleartext-traffic allowances are preconfigured for Android and iOS.
- Auth state is initialized before the first frame; cart and auth providers wrap the widget tree.
- Run the test suite with `flutter test` (see [Testing](#testing)).

## Admin Dashboard

Staff users (`is_staff=True`) get a full management dashboard served by Django under `/dashboard` (orders, menu, categories, customizations, inventory, users, reservations, reports) and a matching set of FastAPI admin endpoints under `/admin` (superuser-only for sensitive toggles like `toggle-staff` / `toggle-active`).

```bash
# Create a staff superuser
python manage.py createsuperuser
# then mark the account as staff: python manage.py shell -> user.is_staff = True; user.save()
```

## Testing

```bash
# Django tests (224 tests)
cd Rest_project
python manage.py test api.tests -v 1

# FastAPI tests (160 tests)
python -m pytest api_endpoints/tests/ -q

# Flutter tests
cd ../frontend/rest_project
flutter test
```

`pytest`, `httpx` (the FastAPI `TestClient` dependency), and `whitenoise` are included in `requirements.txt`. FastAPI tests mock the database and override dependencies; the `api/tests/__init__.py` package applies a `BaseContext.__copy__` workaround required on Python 3.9+ / Django 4.2 (see the code comment).

## Docker

> Note: the compose file currently defines **MongoDB only**, which is not used at runtime — the application stores everything in PostgreSQL. The Django and FastAPI backends are not containerized.

```bash
docker compose -f docker/docker-compose.yml up -d
```

## API Endpoints (FastAPI)

FastAPI routers use `prefix="/auth"` style — there is no `/api` prefix. Run FastAPI on port 8071 (Django owns 8070). Endpoints:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login, returns JWT |
| GET | `/` | Optional | Popular items & categories |
| GET | `/menu` | No | Menu list (search, sort) |
| GET | `/menu/{item_id}` | No | Menu detail with reviews |
| GET | `/cart` | Yes | View cart |
| POST | `/cart/add/{item_id}` | Yes | Add item to cart |
| PUT | `/cart/update/{item_id}` | Yes | Update cart item |
| DELETE | `/cart/remove/{item_id}` | Yes | Remove cart item |
| POST | `/orders/checkout/place` | Yes | Place order |
| GET | `/orders` | Yes | Order history |
| GET | `/orders/{order_id}` | Yes | Order detail |
| POST | `/reservations/new` | Yes | Create reservation |
| PUT | `/reservations/{reservation_id}/edit` | Yes | Update reservation |
| DELETE | `/reservations/{reservation_id}/cancel` | Yes | Cancel reservation |
| GET | `/profile` | Yes | Get profile |
| PUT | `/profile/edit` | Yes | Update profile |
| POST | `/profile/change-password` | Yes | Change password |
| POST | `/reviews/add/{menu_id}` | Yes | Add review |
| PUT | `/reviews/{review_id}/edit` | Yes | Edit review |
| DELETE | `/reviews/{review_id}/delete` | Yes | Delete review |
| GET | `/payment-methods` | Yes | List payment methods |
| POST | `/payment-methods/add` | Yes | Add payment method |

Admin endpoints (staff only) live under `/admin` (`/admin/dashboard`, `/admin/orders`, `/admin/reservations`, `/admin/menu`, `/admin/categories`, `/admin/inventory`, `/admin/users`, `/admin/reports/...`).

## Branch Structure

Each feature was developed on its own branch for isolated development:

| Branch | Feature |
|--------|---------|
| `feature/auth` | Authentication (register, login, logout, JWT) |
| `feature/home` | Homepage with popular items and categories |
| `feature/menu` | Menu browsing, search, sort, detail |
| `feature/cart` | Shopping cart management |
| `feature/order` | Order checkout, payment, history |
| `feature/reservation` | Table reservations |
| `feature/profile` | User profile and settings |
| `feature/review` | Menu item reviews and ratings |
| `feature/payment` | Payment method management |
| `feature/tests` | Test suites for Django and FastAPI |
| `feature/frontend` | Flutter mobile app |
| `feature/docker` | Docker compose for services |

## Contributing

1. Fork the repository and create a feature branch (`git checkout -b feature/my-feature`).
2. Make your changes and run the relevant test suite (see [Testing](#testing)).
3. Keep commits focused and use conventional commit messages (`feat:`, `fix:`, `docs:`, `chore:`).
4. Open a pull request describing the change and how it was tested.
