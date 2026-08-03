# Rest_project

A full-stack restaurant management application with a **Django** (session-based backend) and **FastAPI** (JWT API layer), sharing a single PostgreSQL database.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   Django        │     │   FastAPI        │
│   (Session      │     │   (JWT API)      │
│    Auth)        │     │                  │
│   localhost:8000│     │   localhost:8000 │
│   /api/*        │     │   /api/*         │
└────────┬────────┘     └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │   PostgreSQL    │
            │   (rest_db)     │
            └─────────────────┘
```

- **Django** serves HTML templates with session-based authentication
- **FastAPI** serves JSON endpoints with JWT token-based authentication
- Both share the same database models and migrate together

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend (Django) | Django 4.2, Python 3.14 |
| API (FastAPI) | FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2 |
| Database | PostgreSQL (via psycopg2-binary) |
| Auth (Django) | Session-based, bcrypt password hashing |
| Auth (FastAPI) | JWT (python-jose), bcrypt |
| Frontend | HTML templates + Flutter mobile app |
| RAG Chatbot | pgvector (PostgreSQL embeddings) + Qdrant vector DB |
| Other | QR codes, Pillow, Arabic l10n (polib) |

## Features

| Feature | Django Views | FastAPI Endpoints |
|---------|-------------|-------------------|
| **Auth** | Register, login, logout | Register, login, JWT token |
| **Home** | Popular items, categories, ratings | Same via JSON |
| **Menu** | List, detail, search, sort, ratings | Same via JSON |
| **Cart** | Add, remove, update items, options | Same via JSON |
| **Order** | Checkout, place order, history, detail | Place order, payment, QR |
| **Reservation** | Create, edit, cancel reservations | Same via JSON |
| **Profile** | Edit profile, settings, password change | Same via JSON |
| **Review** | Create, edit, delete reviews | Same via JSON |
| **Payment** | Add/list payment methods, card masking | Same via JSON |
| **Chat** | RAG chatbot widget (`CHAT_API_URL`) | Same via JSON |

## RAG Chatbot

The project integrates a **mini RAG (Retrieval-Augmented Generation) chatbot** that answers questions about the restaurant (menu items, ordering, reservations, and more) using the project data as its knowledge base.

- Built with **pgvector** — PostgreSQL extension used to store and search the embeddings of the restaurant knowledge base with vector similarity
- Uses **Qdrant** — a dedicated vector database for fast, scalable similarity retrieval
- Retrieves the most relevant documents for a question, then generates a grounded answer from the retrieved context
- Wired into the Django frontend through the `CHAT_API_URL` environment variable (default: `http://localhost:8000/api/v1/nlp/index/answer/1`), injected into templates via the `chat_api_url` context processor

## Setup

### Prerequisites

- Python 3.14+
- PostgreSQL running on `localhost:5432`
- A database named `rest_db`

### Installation

```bash
# Clone the repo
git clone <repo-url>
cd Rest_project

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
cd Rest_project
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your PostgreSQL credentials

# Run Django migrations
python manage.py migrate

# Run Django dev server
python manage.py runserver

# In a separate terminal, run FastAPI
cd api_endpoints
uvicorn main:app --reload --port 8000
```

### Environment Variables (`.env`)

```
DB_NAME=rest_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

## Branch Structure

Each feature has its own branch for isolated development:

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

## Testing

```bash
# Django tests
cd Rest_project
python manage.py test api.tests

# FastAPI tests
python -m pytest api_endpoints/tests/ -v
```

## Docker

```bash
docker compose -f docker/docker-compose.yml up -d
```

## API Endpoints (FastAPI)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login, returns JWT |
| GET | `/api/home` | Optional | Popular items & categories |
| GET | `/api/menu` | No | Menu list (search, sort) |
| GET | `/api/menu/{id}` | No | Menu detail with reviews |
| GET | `/api/cart` | Yes | View cart |
| POST | `/api/cart/add` | Yes | Add item to cart |
| POST | `/api/cart/update/{id}` | Yes | Update cart item |
| DELETE | `/api/cart/remove/{id}` | Yes | Remove cart item |
| POST | `/api/order/place` | Yes | Place order |
| GET | `/api/order/history` | Yes | Order history |
| GET | `/api/order/{id}` | Yes | Order detail |
| POST | `/api/reservation/create` | Yes | Create reservation |
| PUT | `/api/reservation/{id}` | Yes | Update reservation |
| DELETE | `/api/reservation/{id}` | Yes | Cancel reservation |
| GET | `/api/profile` | Yes | Get profile |
| PUT | `/api/profile/edit` | Yes | Update profile |
| POST | `/api/profile/change-password` | Yes | Change password |
| POST | `/api/review/add/{menu_id}` | Yes | Add review |
| PUT | `/api/review/edit/{review_id}` | Yes | Edit review |
| DELETE | `/api/review/delete/{review_id}` | Yes | Delete review |
| GET | `/api/payment/methods` | Yes | List payment methods |
| POST | `/api/payment/add` | Yes | Add payment method |
