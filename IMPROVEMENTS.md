# RPL-3.0 (Backend) Improvements

Proposed improvements for the RPL-3.0 backend.
**Scoring:** 1 (Low) to 5 (High). C: Complexity, R: Risk.

## 1. Architecture & Performance
*   **Merge Microservices:** Combine `rpl_users` and `rpl_activities` into one repo. Use FastAPI routers to maintain separation. This reduces DB connection pool overhead and simplifies deployment into a single container.
    *   **C: 4 | R: 4**
*   **Async SQLAlchemy:** Refactor `src/repositories` to use `await session.execute` and `AsyncSession`. Swap `pymysql` for `aiomysql`. This will improve throughput for 200+ concurrent users on cheap hardware.
    *   **C: 5 | R: 4**
*   **Redis Caching:** Implement a `@cached` decorator for common lookups (courses, roles, activities). For 200 concurrent users, this offloads up to 70% of read queries from MySQL.
    *   **C: 3 | R: 2**
*   **Connection Pooling:** Tuned SQLAlchemy `pool_size` and `max_overflow`. Use `pool_pre_ping=True` to prevent the "MySQL has gone away" errors common in long-lived student sessions.
    *   **C: 2 | R: 1**

## 2. Documentation & API
*   **OpenAPI Refinement:** Add `Pydantic` `Field(description=...)` and `Example` to all DTOs. This ensures the `/docs` UI is a live, self-documenting contract for the frontend team.
    *   **C: 2 | R: 1**
*   **ADR & Decision Logs:** Create a `/docs/adr` folder and record the technical rationale for choices like RabbitMQ, the specific C compiler used, and the authentication flow.
    *   **C: 1 | R: 1**
*   **Global Error Handling:** Implement a custom `HTTPException` handler that maps Python exceptions (e.g., SQLAlchemy `NoResultFound`) to consistent JSON error bodies with unique error codes.
    *   **C: 2 | R: 2**

## 3. Testing
*   **Increase Coverage (>80%):** Prioritize the `services` layer where the business logic resides. Use `pytest-cov` to identify untested branches and enforce coverage limits in CI.
    *   **C: 3 | R: 1**
*   **Integration Tests (Testcontainers):** Use `testcontainers-python` to spin up ephemeral MySQL and RabbitMQ containers for each test run, ensuring a clean state and no dependency on pre-existing local DBs.
    *   **C: 4 | R: 3**
*   **Locust Load Testing:** Create a script simulating 200 students browsing and 50 submitting code simultaneously to find the memory/CPU limits of the $5 VPS deployment.
    *   **C: 2 | R: 1**

## 4. Features & AI
*   **Mistake Mapping Table:** Create a new `common_mistakes` DB table linking language-specific regex patterns (from Runner) to localized, student-friendly hints (e.g., "Memory Leak" -> "Make sure to free() your pointers").
    *   **C: 3 | R: 2**
*   **AI Hinting:** Integrate a lightweight LLM (via Ollama or API) that takes failed compilation output and suggests a "hint" (not code) to help students debug their errors.
    *   **C: 4 | R: 3**

## 5. DX & CD
*   **Migration CI Checks:** Add a CI step that runs `alembic upgrade head` on a fresh MySQL Docker instance for every PR, preventing breaking DB migrations from reaching production.
    *   **C: 2 | R: 3**
*   **Environment Validation:** Add a `health_check` on startup that verifies connectivity to MySQL and RabbitMQ. Fail fast with clear error messages if a `.env` variable is missing or invalid.
    *   **C: 2 | R: 2**
