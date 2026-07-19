# ERRORS & SOLUTIONS

## Project Analysis Report

---

## 🔴 CRITICAL (Will crash at runtime)

### 1. Infinite Recursion — `login` view shadows imported `login`

**File:** `Rest_project/api/views/auth_views.py:61`

```python
from django.contrib.auth import login, logout, authenticate  # line 1

def login (request):  # line 61 — shadows the imported `login`
    ...
    login(request=request, user=user)  # line 70 — calls ITSELF → RecursionError
```

**Solution:** Rename the view function (e.g., `login_view`) or change the import:

```python
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout

def login_view(request):
    ...
    auth_login(request=request, user=user)
```

Then update `api/urls.py`:
```python
path("login/", auth_views.login_view, name="login"),
```

---

### 2. Infinite Recursion — `logout` view shadows imported `logout`

**File:** `Rest_project/api/views/auth_views.py:80`

```python
def logout (request):  # shadows imported `logout`
    logout(request=request)  # calls ITSELF → RecursionError
```

**Solution:** Same as above — rename to `logout_view` or use `auth_logout`.

---

### 3. Missing Login Template

**File:** `Rest_project/api/views/auth_views.py:77`

```python
return render(request, "auth/login.html")
```

**File missing:** `Rest_project/api/templates/auth/login.html` does not exist.

**Solution:** Create `Rest_project/api/templates/auth/login.html`:

```html
{% extends "auth/master.html" %}
{% block title %}Login{% endblock %}
{% block content %}
<div>Login Page</div>
<form method="POST">
    {% csrf_token %}
    <input type="text" name="username" placeholder="Username">
    <input type="password" name="password" placeholder="Password">
    <button type="submit">Login</button>
</form>
{% endblock %}
```

---

## 🟠 HIGH (Will cause errors or major issues)

### 4. Unresolved Git Merge Conflict in `.gitignore`

**File:** `.gitignore` (root)

```
<<<<<<< HEAD
.env
db.sqlite3
=======
.env
>>>>>>> 6290620e6854033e9c1d73c3585906dac93b1530
```

**Solution:** Resolve the conflict — remove markers and keep what you need:

```
.env
db.sqlite3
```

---

### 5. Typo in `api/.gitignore`

**File:** `Rest_project/api/.gitignore:1`

```
__pycahce__
```

**Solution:** Fix the typo:

```
__pycache__
```

---

### 6. No Dependency Manifest (`requirements.txt`)

**Problem:** No `requirements.txt`, `Pipfile`, or `pyproject.toml` exists. The project depends on:
- `django`
- `djongo` (MongoDB connector)
- `pymongo`
- `python-dotenv` (optional)

**Solution:** Create `Rest_project/requirements.txt`:

```
django>=3.1,<3.3
djongo==1.3.6
pymongo==3.12.3
python-dotenv
```

> ⚠️ **Important:** `djongo` only supports Django 3.1–3.2. **See Issue #9.**

---

### 7. Hardcoded `SECRET_KEY` & `DEBUG = True`

**File:** `Rest_project/Rest_project/settings.py:12-15`

```python
SECRET_KEY = 'django-insecure-l-rpqb9@m15#wis%hzd35_892_blss&sjmwv&4k(!o5i&lmva5'
DEBUG = True
```

**Solution:** Use environment variables:

```python
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-dev-only-key')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
```

---

### 8. `djongo` + Django Version Incompatibility

**File:** `Rest_project/Rest_project/settings.py:68` and migrations (`0001_initial.py:1`)

- Migration generated with **Django 3.1.12**
- Project settings reference features from **Django 4.2**
- `djongo` only supports Django up to **3.2**

**Solution:** Either:
- **Option A:** Pin Django to `>=3.1,<3.3` and use `djongo==1.3.6`
- **Option B:** Switch from djongo to `pymongo` + `mongoengine` for newer Django
- **Option C:** Migrate from MongoDB to PostgreSQL/SQLite with native Django support

---

### 9. `ALLOWED_HOSTS = []`

**File:** `Rest_project/Rest_project/settings.py:17`

**Problem:** Will reject all requests when `DEBUG=False`.

**Solution:**
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.yourdomain.com']
```

---

## 🟡 MEDIUM

### 10. Missing Static File (`homepage/css/style.css`)

**Files:** `api/templates/master.html:17` and `auth/master.html:14`

```html
<link rel="stylesheet" href="{% static 'homepage/css/style.css' %}">
```

**Solution:** Create the file or remove the reference, then configure static files:

```python
# settings.py
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Then create `Rest_project/static/homepage/css/style.css`.

---

### 11. Malformed HTML — Bare `>` Character

**File:** `api/templates/master.html:51`

```html
>                                       <!-- BARE '>' -->
```

**Solution:** Remove the stray `>` character.

---

### 12. Typo in Brand Name

**File:** `api/templates/auth/master.html:20`

```html
<a href="/" class="nav-logo">Restraunt</a>
```

**Solution:** Fix spelling:
```html
<a href="/" class="nav-logo">Restaurant</a>
```

---

### 13. Wrong Base Template in `register.html`

**File:** `api/templates/auth/register.html:1`

```html
{% extends "master.html" %}
```

This extends the main app master (with nav links for authenticated users), not the auth-specific master.

**Solution:** Change to:
```html
{% extends "auth/master.html" %}
```

---

### 14. `.env` File Is Ignored by Settings

**File:** `Rest_project/.env` exists with:
```
MONGODB_URL="mongodb://admin:admin@localhost:8001"
MONGODB_DATABASE="Rest-DB"
```

But `settings.py` hardcodes values instead of reading from `.env`.

**Solution:**
```python
import os
from dotenv import load_dotenv
load_dotenv()

DATABASES = {
    "default": {
        "ENGINE": "djongo",
        "NAME": os.environ.get("MONGODB_DATABASE", "restaurant_db"),
        "CLIENT": {
            "host": os.environ.get("MONGODB_URL", "mongodb://admin:admin@localhost:8001/restaurant_db?authSource=admin")
        },
    }
}
```

---

### 15. No Models Registered in Admin

**File:** `api/admin.py`

```python
from django.contrib import admin
# Register your models here.
```

**Solution:** Register all models:

```python
from django.contrib import admin
from .models import User, Address, UserSettings, Category, Inventory, Menu, \
    MenuCustomizationOption, Cart, CartItem, Order, OrderItem, \
    ReservationSystem, PaymentMethod, Payment

admin.site.register(User)
admin.site.register(Address)
admin.site.register(UserSettings)
admin.site.register(Category)
admin.site.register(Inventory)
admin.site.register(Menu)
admin.site.register(MenuCustomizationOption)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(ReservationSystem)
admin.site.register(PaymentMethod)
admin.site.register(Payment)
```

---

### 16. No Tests Implemented

**File:** `api/tests/test_models.py`

**Solution:** Write at least basic model tests:

```python
from django.test import TestCase
from api.models import User, Category

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.assertEqual(user.role, "customer")

class CategoryModelTest(TestCase):
    def test_category_creation(self):
        cat = Category.objects.create(category_name="Main Course")
        self.assertEqual(str(cat), "Main Course")
```

---

### 17. Incomplete Docker Compose (No Django Service)

**File:** `docker/docker-compose.yml`

Only MongoDB is defined. The Django app is not containerized.

**Solution:** Add a Django service:

```yaml
services:
  mongodb:
    image: mongo:7-jammy
    container_name: mongodb
    ports:
      - "8001:27017"
    volumes:
      - ./mongodb:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD}
    networks:
      - backend
    restart: always

  django-app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: restaurant-django
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://admin:admin@mongodb:27017
    depends_on:
      - mongodb
    networks:
      - backend
    command: python manage.py runserver 0.0.0.0:8000

networks:
  backend:
```

(Also create a `Dockerfile` in the `docker/` directory.)

---

## 🟢 LOW

| # | Issue | File | Fix |
|---|-------|------|-----|
| 18 | Typo: `Registeration` → `Registration` | `api/templates/auth/register.html:7` | Fix spelling |
| 19 | Empty `frontend/` directory | `frontend/` | Remove or populate |
| 20 | SQLite `db.sqlite3` committed | `Rest_project/db.sqlite3` | Add to `.gitignore` and remove from tracking: `git rm --cached db.sqlite3` |
| 21 | Migration uses `AutoField` but settings define `BigAutoField` | `settings.py:116` / `0001_initial.py` | Regenerate migrations or change setting to `AutoField` |
| 22 | PEP 8 spacing: `def login (request):` | `auth_views.py:61` | Change to `def login_view(request):` |
| 23 | PEP 8 spacing: `user =authenticate(...` | `auth_views.py:66` | Add space: `user = authenticate(...` |
| 24 | PEP 8 spacing: `render(request,"auth/..."` | `auth_views.py:77` | Add space: `render(request, "auth/..."` |
| 25 | No validation for required POST fields | `auth_views.py:13-20` | Add checks for missing fields |
| 26 | Migration generated with Django 3.1.12 but project uses 4.x | `migrations/0001_initial.py` | Align Django version (see Issue #9) |
| 27 | MongoDB data files potentially tracked in git | `docker/mongodb/` | Ensure `docker/.gitignore` includes `mongodb/` |

---

## ✅ Suggested Fix Order (Priority)

1. **Fix infinite recursion** in `auth_views.py` (#1, #2) — app won't run without this
2. **Create `auth/login.html`** (#3) — login view crashes without it
3. **Resolve `.gitignore` merge conflict** (#4) — git operations are broken
4. **Fix `api/.gitignore` typo** (#5) — `__pycache__` directories won't be ignored
5. **Create `requirements.txt`** (#6) — pinned versions for reproducibility
6. **Fix Django version / djongo compatibility** (#9) — database won't work otherwise
7. **Use env vars for secrets & debug** (#7) — security hardening
8. **Fix missing static files** (#10) — UI will have no styles
9. **Fix HTML typo (`>` & `Restraunt`)** (#11, #12) — visual bugs
10. **Fix register template inheritance** (#13) — wrong layout
11. **Read `.env` in settings** (#14) — config is unused
12. **Remaining low-severity items** (#18–27)
