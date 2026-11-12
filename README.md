# Datheon BookStore Backend API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20(Async)-D71F00.svg?style=flat)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-V2-E92063.svg?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An asynchronous, production-conscious RESTful backend built for the **Datheon Python + FastAPI Backend Development Internship**. This project unites four foundational backend engineering milestones into a single, cohesive, tested, and containerized microservice.

---

## Internship Overview

- **Organization**: [Datheon](https://www.datheon.in/)
- **Program**: [Python + FastAPI Backend Development Internship](https://www.datheon.in/training/catalog/python-fastapi-backend-internship)
- **Repository Name**: `Datheon_FastAPI_Internship`
- **Candidate Track**: Backend Engineering & API Security (B.Tech CSE Graduate)

---

## Completed Internship Tasks

| Task | Title | Key Deliverables & Implementation Highlights |
| :--- | :--- | :--- |
| **Task 1** | **BookStore REST API with Pydantic Validation** | Complete CRUD operations (`/books`), strict Pydantic V2 request/response schemas, ISBN format verification, query filters (title, author, ISBN, price range, publication year), pagination (`limit` & `offset`), HTTP status codes, and interactive Swagger UI documentation. |
| **Task 2** | **User Authentication & RBAC with JWT** | Secure user registration (`/auth/register`), OAuth2 password login (`/auth/login`), profile inspection (`/auth/me`), direct bcrypt password hashing with unique salt, JWT signature creation/verification via PyJWT, Role-Based Access Control (`user` vs `admin`), and an interactive administrative bootstrap script (`scripts/create_admin.py`). |
| **Task 3** | **Database Persistence with SQLAlchemy & SQLite** | Full migration from volatile storage to asynchronous SQLite persistence (`sqlite+aiosqlite`), SQLAlchemy 2.0 async engine and declarative models (`User`, `Book`), relational foreign keys (`created_by_user_id`), ACID transactions, unique constraints, and automated schema generation during application startup. |
| **Task 4** | **Microservice with Background Tasks, Rate Limiting & Docker** | Non-blocking background worker (`BackgroundTasks`) dispatching audit and inventory notifications, IP-based request throttling using SlowAPI (5 attempts/min on auth, 100/min overall), container health check endpoint (`/health`), multi-stage production Dockerfile with non-root security (`appuser`), persistent host volume mounts, and `docker-compose.yml`. |

---

## Architectural Highlights

```
Datheon_FastAPI_Internship/
│
├── app/
│   ├── __init__.py               # Application package root
│   ├── main.py                   # FastAPI instantiation, middleware, lifespan manager
│   ├── config.py                 # Pydantic BaseSettings environment configuration
│   ├── logging_config.py         # Structured logging configuration
│   ├── database.py               # SQLAlchemy 2.0 async engine, declarative Base, session generator
│   ├── models.py                 # User and Book ORM models with constraints & indexes
│   ├── schemas.py                # Pydantic V2 validation & response serialization models
│   ├── security.py               # Bcrypt hashing, JWT encode/decode, OAuth2 scheme
│   ├── dependencies.py           # Reusable route dependencies (get_db, get_current_user, require_admin)
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── books.py              # BookStore catalog CRUD endpoints & filters
│   │   ├── auth.py               # Registration, OAuth2 login, token refresh
│   │   └── users.py              # Administrative user and role management
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── notifications.py      # Decoupled background notification tasks
│   │
│   └── core/
│       ├── __init__.py
│       └── rate_limit.py         # SlowAPI rate limiter & 429 response handler
│
├── scripts/
│   └── create_admin.py           # Secure administrative bootstrap utility
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest async fixtures, test database, auth headers
│   ├── test_books.py             # BookStore CRUD, pagination, filtering tests
│   ├── test_auth.py              # Registration, JWT login, RBAC permission tests
│   ├── test_database.py          # SQLAlchemy persistence & constraint verification
│   └── test_rate_limit.py        # SlowAPI rate limiting & health check verification
│
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git exclusions (caches, virtualenvs, databases)
├── .dockerignore                 # Docker build exclusions
├── Dockerfile                    # Production-ready non-root Docker container
├── docker-compose.yml            # Docker Compose orchestration with persistent volume
├── requirements.txt              # Pinned, tested Python dependencies
├── README.md                     # Comprehensive project documentation
└── LICENSE                       # MIT License
```

---

## Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous ASGI)
- **ASGI Web Server**: [Uvicorn](https://www.uvicorn.org/)
- **Data Validation & Settings**: [Pydantic V2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Database & ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async Engine) with [aiosqlite](https://aiosqlite.omnilib.dev/)
- **Security & Cryptography**: [bcrypt](https://pypi.org/project/bcrypt/) & [PyJWT](https://pyjwt.readthedocs.io/)
- **Rate Limiting**: [SlowAPI](https://slowapi.readthedocs.io/) (Token Bucket / Fixed Window)
- **Automated Testing**: [Pytest](https://pytest.org/), [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio), and [HTTPX](https://www.python-httpx.org/)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

---

## Local Setup & Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12 installed on your system.
- Git installed.
- (Optional) Docker and Docker Compose installed for container execution.

### Step 1: Clone the Repository
```powershell
git clone https://github.com/YOUR_USERNAME/Datheon_FastAPI_Internship.git
cd Datheon_FastAPI_Internship
```

### Step 2: Set Up Virtual Environment

#### On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell blocks script activation, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

#### On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the template `.env.example` into `.env`:
```powershell
Copy-Item .env.example .env
```

Generate a secure 32+ character JWT secret:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Paste this generated secret into `.env` under `JWT_SECRET_KEY`.

---

## Initializing Database & Administrator Account

The application automatically creates required SQLite database tables upon initial startup. To initialize your first administrative user securely without exposing credentials in git:

```powershell
python scripts/create_admin.py
```

You can either accept the environment defaults or enter custom credentials interactively:
- **Default Email**: `admin@datheon.local`
- **Default Password**: `ChangeMeAdmin123!`

---

## Running the Application Locally

Start the asynchronous development server with auto-reload:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Root Welcome**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running with Docker & Docker Compose

The project includes a production-conscious Dockerfile with a non-root `appuser` and persistent volume mounts.

### Build and Launch:
```powershell
docker compose up --build -d
```

### View Live Container Logs:
```powershell
docker compose logs -f backend
```

### Inspect Container Health:
```powershell
docker ps
```
The status column will display `healthy` once the container passes its built-in Python health checks.

### Stop the Container:
```powershell
docker compose down
```
*(Your SQLite database file persists safely inside `./data/datheon_bookstore.db` across container rebuilds).*

---

## API Endpoints Reference

All endpoints are grouped under `/api/v1`:

### 1. Catalog Management (`/api/v1/books`)
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/books` | **Admin Only** | Register a new book (triggers background inventory notification) |
| `GET` | `/api/v1/books` | **Public** | List books with search filters & pagination (`limit`, `offset`) |
| `GET` | `/api/v1/books/{id}` | **Public** | Retrieve detailed metadata for a single book |
| `PUT` | `/api/v1/books/{id}` | **Admin Only** | Update book title, price, description, year, or ISBN |
| `DELETE`| `/api/v1/books/{id}` | **Admin Only** | Permanently delete a book from catalog |

### 2. Authentication & Authorization (`/api/v1/auth`)
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register`| **Public** | Register account (bcrypt hash, rate-limited to 5/min) |
| `POST` | `/api/v1/auth/login` | **Public** | Authenticate credentials & receive JWT token (rate-limited) |
| `GET` | `/api/v1/auth/me` | **Authenticated** | Inspect current user's profile and assigned role |
| `POST` | `/api/v1/auth/refresh` | **Authenticated** | Issue refreshed JWT token for active session |

### 3. User Administration (`/api/v1/users`)
| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | **Admin Only** | View list of all registered users |
| `PATCH`| `/api/v1/users/{id}/role` | **Admin Only** | Change user role (`user` ↔ `admin`) |

---

## Automated Testing Suite

The project includes an end-to-end Pytest suite testing all four tasks against an isolated SQLite test database.

### Run All Tests:
```powershell
pytest -v
```

### Run Specific Test Modules:
```powershell
# Task 1 & 3: Book CRUD, filtering, pagination, and database persistence
pytest -v tests/test_books.py

# Task 2: User registration, login, bcrypt hashing, and RBAC
pytest -v tests/test_auth.py

# Task 3: Database transactions and constraint integrity
pytest -v tests/test_database.py

# Task 4: Rate limiting and OpenAPI docs verification
pytest -v tests/test_rate_limit.py
```

---

## Security Implementation Review

1. **Password Hashing**: Plaintext passwords are never stored. Passwords are salted and hashed using direct `bcrypt.hashpw` with unique salts.
2. **JWT Cryptography**: Signed using HMAC-SHA256 (`HS256`). Payloads include `sub`, `user_id`, `role`, `iat`, and `exp`.
3. **Role-Based Authorization (RBAC)**: Enforced via reusable dependencies (`require_admin`). Unauthorized users receive HTTP `403 Forbidden`.
4. **Rate Limiting**: Protected by SlowAPI to defend against brute-force attacks and credential stuffing.
5. **SQL Injection Defense**: Built entirely on SQLAlchemy 2.0 parameter-binding ORM expressions; zero raw string SQL interpolation.
6. **Data Leak Prevention**: Database models and password hashes are never exposed directly. Output responses are filtered through strictly typed Pydantic models.
7. **Container Hardening**: Docker executes under a non-root system user (`appuser`, UID 1000) with strict layer caching.

---

## Visual Demonstration & Screenshots

> Place your captured screenshots in a `docs/screenshots/` folder and link them below:

### 1. Interactive Swagger Documentation (`/docs`)
![Swagger UI Overview](docs/screenshots/01_swagger_docs.png)

### 2. Admin Authentication & JWT Token Issuance
![JWT Login](docs/screenshots/02_jwt_auth.png)

### 3. Protected Book Creation & Rate Limiting (HTTP 429)
![Rate Limiting](docs/screenshots/03_rate_limiting.png)

### 4. Automated Pytest Execution Results
![Pytest Run](docs/screenshots/04_pytest_results.png)

---

## Demonstration Video Walkthrough

- **LinkedIn Video Walkthrough**: [Link to Your LinkedIn Demonstration Post](https://www.linkedin.com/)
- **Duration**: ~3 minutes
- **Topics Demonstrated**:
  1. Project Architecture & Task Overview
  2. Swagger UI interactive testing
  3. Registering user & obtaining JWT Bearer token
  4. Role-based endpoint protection (User vs Admin)
  5. Background task console logs
  6. Rate limiting triggering HTTP 429
  7. Automated Pytest execution

---

## Future Enhancements
- PostgreSQL dialect migration via `asyncpg` for multi-worker distributed concurrency.
- Redis-backed distributed cache and token blacklist for instant JWT revocation.
- Celery / ARQ worker queue for high-throughput distributed background workloads.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
Project developed for the **Datheon Python + FastAPI Backend Development Internship**.
