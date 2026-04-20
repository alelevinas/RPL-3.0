# RPL-3.0 (Backend)

The RPL-3.0 backend consists of two primary microservices built with FastAPI and SQLAlchemy.

## Services

- **RPL Users API (Port 8000):** Manages users, roles, and courses.
- **RPL Activities API (Port 8001):** Manages activities, categories, and student submissions.

## Setup

### Prerequisites

- MySQL 8.4
- RabbitMQ 3.13
- Python 3.13

### Local Development

Requires `.env` files in `rpl_users/` and `rpl_activities/` — see the workspace [README](../README.md) for the full setup guide including infrastructure and DB seeding.

1.  **Install dependencies:**
    ```bash
    pyenv exec pip install -r base_requirements.txt \
      -r rpl_activities/extra_requirements.txt \
      -r rpl_users/extra_requirements.txt
    ```

2.  **Start Users API:**
    ```bash
    pyenv exec python -m dotenv -f rpl_users/.env run -- \
      python -m uvicorn rpl_users.src.main:app \
      --host 0.0.0.0 --port 8000 --reload --reload-dir rpl_users/src
    ```

3.  **Start Activities API:**
    ```bash
    pyenv exec python -m dotenv -f rpl_activities/.env run -- \
      python -m uvicorn rpl_activities.src.main:app \
      --host 0.0.0.0 --port 8001 --reload --reload-dir rpl_activities/src
    ```

## Database

Schema is managed via SQLAlchemy ORM models. On a fresh database, use `create_all()` (see workspace README). The legacy Alembic scripts under `migrations/` target an existing production database and should not be run on a fresh local setup.

## AI Hinting

The backend includes an AI-powered hinting engine that assists students on failed submissions.
Configure `OPENAI_API_KEY` or `OLLAMA_URL` in the `.env` file to activate.

## Testing

Run tests with `pytest`:

```bash
python -m pytest
```
