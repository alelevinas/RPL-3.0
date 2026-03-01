# Backend Testing Plan (RPL-3.0)

Testing strategy for the RPL-3.0 microservices (`rpl_activities` and `rpl_users`).

## 1. Unit & Integration Tests (Current)
- **Tool**: `pytest`
- **Scope**: Services, Repositories, Routers.
- **Database**: Uses SQLite in-memory with SQLAlchemy for fast, isolated tests.
- **Status**: ~60% coverage.

## 2. Gaps & Improvements (Target)

### 2.1. AI Hinting Validation
We are missing tests that verify the AI hint generation logic in `SubmissionsService`. 
- **Plan**: Create mock tests for LLM response parsing and edge cases (e.g., empty compiler output).
- **Target**: `rpl_activities/tests/services/test_ai_hints.py`.

### 2.2. Global Error Handling Verification
Ensure all routers properly utilize the standardized `ErrorResponseDTO`.
- **Plan**: Test common error scenarios (404, 403, 500) and verify the JSON body format.

### 2.3. Migration Testing
Verify that Alembic migrations run successfully against a MySQL container.
- **Plan**: Add a CI step that runs `alembic upgrade head` on a fresh MySQL instance.

## 3. GitHub Actions Workflow (`.github/workflows/pytest.yml`)

The workflow must include:
1. **Python Setup**: Python 3.13.
2. **Dependency Installation**: `pip install -r base_requirements.txt -r ...`.
3. **Execution**: `python -m pytest --cov=src`.
4. **Coverage Report**: Fail PR if coverage drops below 60%.

## 4. Test Categories

- **Unit**: Mocking database and external API calls.
- **Integration**: Real database schema (SQLite) + FastAPI `TestClient`.
- **Security**: Verify `Depends(admin_user)` and JWT validation across all endpoints.
