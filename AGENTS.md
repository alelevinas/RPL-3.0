# RPL-3.0 Backend

## What This Is

Two FastAPI microservices in one repo:
- **rpl_users**: Authentication, user management, course enrollment (port 8000)
- **rpl_activities**: Activities, submissions, test execution, file management (port 8001)

## Project Structure

```
RPL-3.0/
├── base_requirements.txt          # Shared Python deps
├── pytest.ini                     # Test configuration
├── rpl_users/
│   ├── src/
│   │   ├── main.py                # FastAPI app entry point
│   │   ├── routers/               # API endpoints
│   │   ├── services/              # Business logic
│   │   ├── repositories/          # DB access (SQLAlchemy)
│   │   ├── dtos/                  # Pydantic request/response models
│   │   ├── deps/                  # Dependencies (auth, db)
│   │   └── config/                # Environment config
│   └── tests/
│       ├── conftest.py            # Fixtures (in-memory SQLite)
│       └── controller/            # API endpoint tests
├── rpl_activities/
│   ├── src/                       # Same structure as rpl_users
│   └── tests/
│       ├── conftest.py
│       └── controller/
└── migrations/                    # Alembic DB migrations
```

## Code Patterns

- **Service layer**: Business logic in `src/services/`, called by routers.
- **Repository layer**: SQLAlchemy queries in `src/repositories/`.
- **Models**: SQLAlchemy ORM models in `src/repositories/models/`.
- **DTOs**: Pydantic models in `src/dtos/` for request validation and response serialization.
- **Auth**: JWT-based auth in `src/deps/auth.py`. Course-level RBAC with roles (admin, teacher, student).
- **DB sessions**: Injected via FastAPI dependency `get_db_session`.
- **Message queue**: Activities API publishes submission jobs to RabbitMQ via `src/deps/mq_sender.py`.

## Running

```bash
# Tests (uses SQLite in-memory, no external deps needed)
python -m pytest

# Dev servers
fastapi run rpl_users/src/main.py --port 8000
fastapi run rpl_activities/src/main.py --port 8001
```

## Testing Conventions

- Tests use `TestClient` from FastAPI with SQLite in-memory databases.
- Each test function gets a fresh DB via fixtures in `conftest.py`.
- Activities tests import user fixtures from `rpl_users/tests/conftest.py` for cross-service test data.
- Test files are in `tests/controller/` and follow `test_<resource>.py` naming.

## Formatting and Linting

- **Formatter**: black (line-length 110, skip string normalization)
- **Linter**: flake8 (config in `.flake8`, max-line-length 88, many rules relaxed)

## Dependencies on Other Repos

- **RPL-3.0-web** calls both APIs via REST.
- **RPL-3.0-runner** receives jobs from Activities API via RabbitMQ and posts results back via HTTP.
- API key auth for runner callbacks: `RUNNER_API_KEY` env var.

## Agent Tasks

Useful work an agent can do:
- **Extend test coverage**: Many endpoints have basic tests; edge cases, error paths, and authorization checks need more coverage.
- **Add type hints**: Some service functions lack return type annotations.
- **Dependency updates**: Check for newer compatible versions of FastAPI, SQLAlchemy, Pydantic.
- **Add API documentation**: FastAPI auto-generates OpenAPI docs, but endpoint descriptions and examples can be improved.
- **Database migrations**: When modifying models, create Alembic migrations in `migrations/`.
