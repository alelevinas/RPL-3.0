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

1.  **Install dependencies:**
    ```bash
    pip install -r base_requirements.txt -r rpl_activities/extra_requirements.txt -r rpl_users/extra_requirements.txt
    ```

2.  **Start Users API:**
    ```bash
    uvicorn rpl_users.src.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir rpl_users/src
    ```

3.  **Start Activities API:**
    ```bash
    uvicorn rpl_activities.src.main:app --host 0.0.0.0 --port 8001 --reload --reload-dir rpl_activities/src
    ```

## Database Migrations

Use Alembic to manage database changes:

```bash
# In RPL-3.0/
alembic upgrade head
```

## AI Hinting

The backend includes an AI-powered hinting engine that assists students on failed submissions.
Configure `OPENAI_API_KEY` or `OLLAMA_URL` in the `.env` file to activate.

## Testing

Run tests with `pytest`:

```bash
python -m pytest
```
