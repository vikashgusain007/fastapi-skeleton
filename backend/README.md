# FastAPI Clean Architecture Production Boilerplate

A production-ready, highly-scalable, and secure FastAPI backend boilerplate designed using modern software engineering best practices. Suitable for enterprise applications, SaaS products, and high-throughput microservices.

---

## Architecture & Features

This project strictly adheres to **SOLID Principles** and **Clean Architecture**:
* **Controller Layer (`app/api/`)**: Defines REST endpoints, processes request validations, and formats JSON responses.
* **Service Layer (`app/services/`)**: Encapulates all core business logic (e.g. registration rules, hashing, token signing).
* **Repository Layer (`app/repositories/`)**: Abstracts data layer transactions. Decouples ORM engines from services.
* **Database Model (`app/db/`)**: SQLAlchemy 2.0 Declarative models utilizing UUID4 keys and connection pool configurations.

### Feature Integrations:
1. **JWT Session Authentication**: Full Access & Refresh token rotation workflow.
2. **Role-Based Access Control (RBAC)**: Custom FastAPI dependency injecting user authentication checks against database-backed roles (`admin`, `user`).
3. **Redis Caching & Sliding Window Rate Limiting**: Production-grade sliding-window rate limiter safeguarding APIs from traffic abuse.
4. **Structured JSON Logging**: Centralized logs intercepted from Uvicorn, SQLAlchemy, and FastAPI standard logging libraries, serialized to JSON via `Loguru`.
5. **Background Jobs with Celery**: Multi-worker architecture using Redis broker for async executions (e.g., mail dispatching, PDF reporting).
6. **Observability**: Prometheus instrumentation (`/metrics`) and OpenTelemetry trace collection pipeline integration.
7. **Production Dockerization**: Two-stage minimal Dockerfile running under an unprivileged non-root user.

---

## Project Directory Layout

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py          # Register, Login, Refresh endpoints
│   │   │   ├── users.py         # /me Profile, RBAC verification
│   │   │   └── health.py        # System diagnostic checks (DB & Redis)
│   │   └── router.py            # Aggregate version 1 router
│   ├── core/
│   │   ├── config.py            # Pydantic v2 Settings configuration
│   │   ├── security.py          # Password hashing (bcrypt) & JWT management
│   │   ├── logging.py           # Structured JSON logs config (Loguru)
│   │   └── dependencies.py      # Common FastAPI dependencies (DB, Redis, RBAC)
│   ├── db/
│   │   ├── session.py           # Async engine & session factories
│   │   ├── base.py              # DeclarativeBase, UUIDs, & Timestamps
│   │   └── models/
│   │       └── user.py          # User DB schemas
│   ├── schemas/                 # Pydantic validation models
│   ├── services/                # Business logic services
│   ├── repositories/            # DB access abstraction (Repository Pattern)
│   ├── middleware/              # Logging, Rate limiting, Security headers
│   ├── tasks/                   # Celery configurations and background tasks
│   └── main.py                  # Entrypoint initializing App & Lifespans
├── tests/                       # Pytest verification suites (80%+ coverage)
├── alembic/                     # DB migration scripts
├── requirements.txt             # Python packages
├── pyproject.toml               # Linter/Formatter settings (Ruff, Black)
├── docker-compose.yml           # Multi-container local execution stack
├── Dockerfile                   # Multi-stage production container configuration
└── README.md                    # Startup & API Guides
```

---

## Local Development Setup

### 1. Prerequisites
Ensure you have the following installed:
* Python 3.12+
* Docker & Docker Compose
* PostgreSQL client libraries (`libpq-dev` / `postgresql`)

### 2. Configure Environment Variables
Create a local `.env` file inside the `backend/` directory (copied from `.env.example`):
```bash
cp .env.example .env
```
*Modify any credentials, keys, or endpoints inside `.env` to suit your local setup.*

### 3. Setup Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Running with Docker Compose

To boot up the complete environment including **FastAPI**, **PostgreSQL**, **Redis**, and the **Celery background worker**, execute:
```bash
docker compose up --build
```

### Services launched:
* **FastAPI web server**: http://localhost:8000
* **PostgreSQL database**: localhost:5432
* **Redis cache/broker**: localhost:6379
* **Celery worker**: Monitored by celery core cli

---

## Database Migrations (Alembic)

When starting the stack, apply migrations to the database:

```bash
# Generate a migration autodetecting model changes
alembic revision --autogenerate -m "initial_schema"

# Upgrade database to head revision
alembic upgrade head
```

---

## API Documentation & Observability

Once the application is running, you can access the interactive Swagger/OpenAPI docs:
* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### System Health
* **Endpoint**: `GET http://localhost:8000/health` (also mapped to `GET http://localhost:8000/api/v1/health`)
* **Format**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "redis": "connected"
  }
  ```

### Observability Metrics
* **Prometheus Metrics Path**: `GET http://localhost:8000/metrics`
* **OTel Collector Destination**: Default targets `http://localhost:4317` (can be customized via `OTEL_EXPORTER_OTLP_ENDPOINT` environment parameter).

---

## Running Automated Tests

A comprehensive testing suite with 80%+ coverage is configured using **Pytest** and an in-memory async SQLite engine.

To run the unit/integration tests:
```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

---

## Code Quality Checkups

Format and lint specifications are managed via **Black** and **Ruff**:
```bash
# Run Ruff linting check
ruff check app/

# Run Black formatting check
black --check app/

# Run Static Type verification with MyPy
mypy app/
```
