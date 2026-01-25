# AGENTS.md

Project guidance for AI coding agents (Codex) working in this Django repository.

## North Star
Make **safe, minimal, reviewable** changes that follow existing Django patterns, keep tests passing, and avoid breaking migrations, security, or settings.

---

## First steps (always)
1. **Restate the goal** in 1–2 sentences.
2. Propose a **short plan** (3–6 bullets).
3. Identify the correct Django project:
   - look for `manage.py`
   - find the settings module (e.g. `<project_name>/settings.py` or `<project_name>/settings/`)

---

## How to run this repo (auto-detect tooling)
Prefer the tool implied by repo files:

### Python environment / dependency tool
- If `uv.lock` exists → use `uv` (preferred):
  - `uv sync`
  - `uv run python manage.py <cmd>`
- If `poetry.lock` exists → use `poetry`:
  - `poetry install`
  - `poetry run python manage.py <cmd>`
- If `Pipfile.lock` exists → use `pipenv`:
  - `pipenv install --dev`
  - `pipenv run python manage.py <cmd>`
- Else if `requirements.txt` exists → use `venv + pip`:
  - `python -m venv .venv`
  - `source .venv/bin/activate` (or Windows equivalent)
  - `pip install -r requirements.txt`

If none apply, inspect `pyproject.toml` and follow existing docs/CI.

---

## Standard Django commands (use as appropriate)
- Sanity check:
  - `python manage.py check`
- Run locally:
  - `python manage.py runserver`
- Tests:
  - `python manage.py test`
  - If repo uses pytest (look for `pytest.ini`, `pyproject.toml` pytest config, or `pytest-django`):
    - `pytest -q`
- Migrations:
  - Create: `python manage.py makemigrations`
  - Apply: `python manage.py migrate`
  - CI-style check (when available/appropriate):
    - `python manage.py makemigrations --check --dry-run`
- Static (if relevant):
  - `python manage.py collectstatic --noinput`

> Prefer running the narrowest relevant checks first (lint/typecheck), then tests.

---

## Coding standards (Django-specific)

### Project structure & conventions
- Keep Django concerns separated:
  - Models: data + constraints
  - Views/ViewSets: request/response + orchestration
  - Forms/Serializers: validation + transformation
  - Services/Selectors (if project uses them): business logic / query composition
- Avoid “fat views” and “fat models” when complexity grows; follow existing project pattern.

### ORM & performance
- Avoid N+1 queries:
  - use `select_related()` / `prefetch_related()` where appropriate
- Prefer `exists()` over `count()` when you only need existence.
- Use `transaction.atomic()` for multi-step writes that must succeed/fail together.
- Use database constraints (unique, indexes) when appropriate—coordinate with migrations.

### Migrations (high importance)
- **Never edit applied migrations** in shared branches.
- Keep migrations small and reviewable.
- For data migrations:
  - make them reversible when feasible
  - avoid loading huge tables into memory
  - use `apps.get_model()` (historical models), not direct imports
- If you add/modify fields that can lock large tables, call it out explicitly.

### Settings & configuration
- Do not hardcode secrets. Use environment variables and existing settings patterns.
- Don’t disable security middleware/settings (CSRF, auth, SECURE_* flags) unless explicitly instructed.
- Respect existing environment splitting (`settings/base.py`, `settings/dev.py`, etc.) if present.

### Security & privacy
- Never log secrets, tokens, passwords, session IDs, or personal data.
- Use Django protections:
  - CSRF for session-based POSTs
  - permissions/authorization checks for sensitive views/APIs
  - parameterized queries for raw SQL (avoid raw SQL unless necessary)
- If modifying auth/permissions, add tests for allowed/denied cases.

### Timezones & datetimes
- Use timezone-aware datetimes (`django.utils.timezone.now()`).
- Don’t mix naive/aware datetimes.

---

## API behavior & backward compatibility
- If changing externally visible behavior (URLs, serializers, templates, admin behavior):
  - update tests
  - update docs (README / docs)
  - note any migration or rollout steps

If this repo uses DRF:
- Keep permission classes explicit.
- Prefer consistent serializer validation (`validate_…`, `validate`, field validators).
- Pagination/filtering should follow existing settings.

---

## Testing guidance
- Bug fix workflow:
  1. Add regression test (when practical)
  2. Fix the bug
  3. Ensure tests pass
- Use factories/fixtures the repo already uses (Factory Boy, model_bakery, fixtures, etc.).
- If a test suite is slow or flaky, note it and suggest a follow-up.

---

## Dependency policy
- Prefer existing dependencies already used in the repo.
- Ask before adding new runtime dependencies.
- If adding a dependency is necessary, explain:
  - why existing libs aren’t enough
  - alternatives considered
  - maintenance/security implications

---

## “Ask first” changes (require explicit approval)
- New runtime dependencies or major lockfile changes
- Auth/permissions/security-sensitive code paths
- Database schema changes that affect large tables / production risk
- Background job behavior (Celery/RQ) that could impact queues/throughput
- Breaking public API/URL changes

---

## What to include in the final response
When finishing a task, report:
- **Summary** (what changed and why)
- **Files changed**
- **Commands run** (lint/typecheck/tests/migrations) + results
- **Migration notes** (if any): created? applied? backwards compatibility?
- **Risks / follow-ups / assumptions**

---

## Repo-specific notes (optional, fill in)
- Django project module: `<e.g., config or mysite>`
- Local env file pattern: `<e.g., .env, .env.local>`
- DB: `<e.g., PostgreSQL via Docker>`
- Task queue: `<e.g., Celery + Redis>`
- Lint/format: `<e.g., ruff + black>`
- Typecheck: `<e.g., mypy + django-stubs>`
