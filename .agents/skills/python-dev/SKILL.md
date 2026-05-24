---
name: python-dev
description: Python development standards for modern codebases. Use when writing, reviewing, debugging, refactoring, hardening, or setting up Python projects, pyproject.toml, uv, pytest, ruff, mypy, CI/CD, Docker, FastAPI, CLI tools, async code, logging, typing, or security checks.
---

# Python Development Skill

Use this skill to make professional, maintainable, tested, typed, and secure Python changes. Prefer existing project conventions over generic defaults; use the defaults below when starting a new project or when a repository has no clear convention.

## Trigger Signals

Use this skill for tasks mentioning:

- `python`, `.py`, `pyproject.toml`, `.python-version`, `requirements.txt`, `uv.lock`
- `uv`, `pip`, `venv`, packaging, dependency management, lockfiles
- `pytest`, `ruff`, `mypy`, `coverage`, `bandit`, `pip-audit`, pre-commit
- FastAPI, Pydantic, CLI tools, async Python, Dockerized Python apps, Python CI/CD
- Python debugging, typing, logging, config, file handling, security, performance

Do not apply this skill to non-Python work unless the user explicitly asks for Python guidance.

## Agent Workflow

1. Inspect the existing project first: package layout, Python version, dependency manager, tooling config, tests, CI, and style.
2. Preserve existing conventions unless they are unsafe, broken, or the user asks to modernize them.
3. Make the smallest correct change; avoid broad refactors and unrelated formatting.
4. Keep runtime behavior explicit, observable, and testable.
5. Add or update tests for changed behavior, especially bug fixes and security-sensitive paths.
6. Run the relevant quality gates: format, lint, type check, tests, and security checks when applicable.
7. Report what changed, why it changed, and how it was validated.

## Core Principles

| Principle | Practical rule |
|---|---|
| Readability first | Clear names, small functions, simple control flow |
| Explicit over implicit | Visible configuration, typed boundaries, no hidden side effects |
| Minimal change | Fix the issue without opportunistic rewrites |
| Reproducibility | Pin Python version, commit lockfiles, use deterministic tooling |
| Testability | Isolate pure logic from I/O and external systems |
| Security by default | Validate input, avoid shell/SQL injection, never leak secrets |
| Automation | Prefer CI, pre-commit, and repeatable commands over manual checks |

## Quick Start

For new projects, prefer `uv`:

```bash
uv init --app
uv add requests
uv add --dev pytest pytest-cov ruff mypy pip-audit bandit
uv run pytest
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pip-audit
uv run bandit -r src
```

Standard-library fallback:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Rules:

- Never install project dependencies globally.
- Use `python -m pip`, not bare `pip`, when using pip directly.
- Keep `pyproject.toml` as the source of truth for project metadata and tool config.
- Commit lockfiles when the selected tooling supports them.

## Python Version

- Prefer Python `3.13` or `3.14` for new projects.
- Prefer `3.14` for new internal tools if dependencies support it.
- Record the chosen version consistently in `.python-version`, `pyproject.toml`, CI, Dockerfile, and README.
- Do not start new projects on Python `3.10` or older without a concrete compatibility requirement.

## Project Structure

Prefer `src/` layout for applications and libraries:

```text
my-python-app/
  .github/workflows/ci.yml
  src/my_python_app/
    __init__.py
    __main__.py
    config.py
    service.py
  tests/
    conftest.py
    test_service.py
  .python-version
  .gitignore
  pyproject.toml
  uv.lock
```

Use `src/` layout to prevent accidental local imports and expose packaging issues early.

## Naming

| Object | Convention | Example |
|---|---|---|
| Package/module | `snake_case` | `order_service.py` |
| Function | `snake_case` | `calculate_total()` |
| Variable | `snake_case` | `user_id` |
| Class | `PascalCase` | `OrderService` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private helper | leading `_` | `_parse_date()` |

## `pyproject.toml` Baseline

Use this as a starting point for new projects; adapt to the repository if it already has tool config.

```toml
[project]
name = "my-python-app"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=9",
  "pytest-cov>=7",
  "ruff>=0.15",
  "mypy>=2.1",
  "pip-audit>=2.10",
  "bandit>=1.8",
]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.13"
strict = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
show_missing = true
fail_under = 80

[tool.bandit]
exclude_dirs = ["tests", ".venv"]
```

## Type Hints and Data Modeling

- Always annotate new public functions and always specify return types.
- Avoid `Any`; if unavoidable, keep it localized and explain why.
- Prefer `dataclass`, `TypedDict`, or Pydantic models over untyped nested dictionaries.
- Use `Decimal`, not `float`, for money.
- Treat the type checker as a safety net, not as a replacement for tests.

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str


def calculate_total(unit_price: Decimal, quantity: int) -> Decimal:
    return unit_price * quantity


def find_user(user_id: str) -> User | None:
    ...
```

## Testing

Use `pytest` by default.

Test strategy:

- Many fast unit tests.
- Some integration tests around boundaries.
- Few end-to-end tests.

Test design rules:

- Add a regression test before or with every bug fix.
- Use names like `test_<unit>_<expected_behavior>`.
- Follow Arrange, Act, Assert.
- Test happy paths, error paths, boundary values, empty inputs, and external failures.
- Keep tests deterministic and independent.
- Mock external boundaries only: HTTP, DB, email, time, randomness, filesystem as needed.
- Do not mock core business logic.

```python
from pathlib import Path
from typing import Iterator
import tempfile

import pytest


@pytest.fixture
def temp_workdir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory)


@pytest.mark.parametrize(
    ("price", "quantity", "expected"),
    [(10.0, 1, 10.0), (10.0, 3, 30.0), (0.0, 5, 0.0)],
)
def test_calculate_total_returns_price_times_quantity(
    price: float,
    quantity: int,
    expected: float,
) -> None:
    assert calculate_total(price, quantity) == expected
```

Async tests:

```python
import pytest


@pytest.mark.asyncio
async def test_fetch_user_name_returns_name() -> None:
    result = await fetch_user_name("u-123")
    assert result == "Alice"
```

Coverage guidance: use coverage as a signal. Meaningful assertions at 80% are better than high coverage with weak tests.

## Formatting, Linting, and Type Checking

Prefer repository commands if they exist. Otherwise use:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src
uv run pytest --cov=src --cov-branch --cov-report=term-missing
```

Use `ruff check --fix .` only when fixes are clearly safe and scoped to the task.

## Exceptions and Logging

Rules:

- Catch only exceptions you can handle meaningfully.
- Use specific exception types.
- Use `raise ... from exc` when adding context.
- Use context managers or `finally` for cleanup.
- Never silently swallow exceptions with `except: pass`.
- Never log passwords, tokens, cookies, authorization headers, or personal data.
- Use `logging`, not `print`, for runtime events.
- Use `%s` formatting in logging calls, not f-strings.
- In server/container apps, log to stdout/stderr.

```python
import logging

logger = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    """Raised when application configuration is invalid."""


try:
    result = risky_operation()
except TimeoutError as exc:
    logger.warning("Operation timed out: %s", exc)
    raise RuntimeError("external service timed out") from exc
```

## Configuration and Secrets

- Keep configuration outside code: environment variables, config files, or typed settings models.
- Add `.env` and `.env.*` to `.gitignore`; keep `.env.example` without real secrets.
- Use a secrets manager or CI/CD secrets in production.
- Validate required configuration at startup and fail fast with clear errors.

```python
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_url: str
    log_level: str = "INFO"


def load_settings() -> Settings:
    return Settings(
        api_url=os.environ["API_URL"],
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
```

## Files and Paths

- Use `pathlib.Path`, not string concatenation.
- Set text encoding explicitly, usually `encoding="utf-8"`.
- Resolve and restrict user-controlled paths to prevent path traversal.
- Avoid relying on the current working directory unless it is part of the interface.

```python
from pathlib import Path
import json

config_path = Path(__file__).resolve().parent / "config.json"
config = json.loads(config_path.read_text(encoding="utf-8"))

output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

## CLI, Web APIs, and Async

CLI tools:

- Prefer `argparse` for standard-library compatibility unless the project already uses Click, Typer, or another framework.
- Keep parsing separate from business logic so it can be tested directly.
- Return useful exit codes and user-facing error messages.

Web APIs:

- Use typed request and response models.
- Provide a `/health` endpoint.
- Separate authentication from authorization.
- Validate input at boundaries and never expose stack traces to clients.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class UserCreate(BaseModel):
    name: str
    email: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/users")
def create_user(user: UserCreate) -> dict[str, str]:
    return {"id": "u-123", "name": user.name}
```

Async:

- Use `async def` only for I/O-bound work that actually awaits.
- Keep the async stack consistent; do not call blocking I/O from async paths.
- Use `pytest-asyncio` or the repository's existing async test framework.
- Async is not faster for CPU-bound code.

## Security Baseline

Must-follow rules:

- Validate all external input at HTTP, CLI, file, environment, queue, and database boundaries.
- Use parameterized queries; never build SQL with string concatenation or f-strings.
- Avoid `shell=True`; pass subprocess arguments as a list.
- Use `secrets` for tokens and passwords; never use `random` for security-sensitive values.
- Never deserialize untrusted data with `pickle`, `marshal`, or unsafe YAML loaders.
- Never log secrets or authorization material.
- Do not store plaintext passwords; use Argon2, bcrypt, or PBKDF2 via established libraries.

```python
# SQL: good
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# Shell: good
subprocess.run(["convert", filename, "output.png"], check=True)

# Path traversal protection
base_dir = Path("/srv/uploads").resolve()
requested = (base_dir / user_filename).resolve()
if not requested.is_relative_to(base_dir):
    raise ValueError("invalid path")
```

Security tooling:

```bash
uv run pip-audit
uv run bandit -r src
```

## Docker

```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip && python -m pip install .

USER 1000

CMD ["python", "-m", "my_python_app"]
```

`.dockerignore`:

```text
.venv
.git
__pycache__
.pytest_cache
.ruff_cache
.mypy_cache
*.pyc
.env
```

Rules:

- Pin a concrete base image; never use `python:latest`.
- Do not bake secrets into image layers.
- Run as non-root where feasible.
- Keep build context small with `.dockerignore`.

## CI/CD

Minimum quality gates for Python projects:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest --cov=src --cov-branch
uv run pip-audit
uv run bandit -r src
```

GitHub Actions baseline:

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --all-extras --dev
      - run: uv run ruff format --check .
      - run: uv run ruff check .
      - run: uv run mypy src
      - run: uv run pytest --cov=src --cov-branch
      - run: uv run pip-audit
      - run: uv run bandit -r src
```

CI rules:

- Run on every pull request.
- Test the same Python version as production.
- For reusable libraries, test a version matrix.
- Cache only when it is safe and does not hide dependency issues.

## Pre-commit

Use pre-commit when the repository already uses it or when setting up a new project with automated local checks.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.14
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
```

## Debugging and Performance

Debugging loop:

1. Reproduce the issue.
2. Isolate the smallest failing case.
3. Form a hypothesis.
4. Verify with debugger, logs, or targeted tests.
5. Implement the fix.
6. Add a regression test.

Useful baseline:

```python
breakpoint()
```

Performance rule: measure first, optimize second. Prefer simple timing or profilers before changing algorithms or adding caches.

```python
from time import perf_counter

start = perf_counter()
run_operation()
elapsed = perf_counter() - start
```

## Documentation

- Update README, CLI help, API docs, or config examples when behavior or setup changes.
- Keep examples runnable and free of real secrets.
- Document operational assumptions: required env vars, external services, database migrations, and scheduled jobs.

## Common Anti-Patterns

| Anti-pattern | Problem | Better |
|---|---|---|
| Global dependency installs | Non-reproducible environment | `uv`, venv, lockfile |
| Missing Python version | CI/local/prod drift | `.python-version`, `pyproject.toml`, CI, Docker |
| No lockfile | Surprise dependency changes | Commit supported lockfiles |
| Huge functions or god modules | Hard to test and review | Small cohesive units |
| Mutable default arguments | Shared state bugs | Use `None` sentinel |
| Bare `except` or `except Exception: pass` | Hidden failures | Specific handling and logging |
| `Any` everywhere | Type checker becomes useless | Concrete types at boundaries |
| Tests relying on network/time/order | Flaky tests | Mock boundaries and control time |
| SQL or shell string interpolation | Injection risk | Parameterized SQL, subprocess arg lists |
| Secret leakage in code/logs | Credential compromise | Secret managers and redaction |
| `python:latest` Docker image | Non-reproducible builds | Pin a concrete version |

## Review Checklist

- Does the change preserve project conventions and avoid unrelated refactoring?
- Is behavior covered by tests, including failure and boundary cases?
- Are public functions typed and type-checkable?
- Are external inputs validated at boundaries?
- Are secrets absent from code, logs, examples, tests, and diffs?
- Are file paths safe, resolved where needed, and using explicit encodings?
- Are dependencies justified, pinned or locked, and audited where relevant?
- Are Docker and CI using the same supported Python version?

## Definition of Done

A Python change is complete only when:

- Code is implemented with minimal, focused changes.
- Tests are added or updated, or omission is explicitly justified.
- Formatting and linting pass.
- Type checking passes, or deviations are documented.
- Security impact is checked.
- Documentation, config, CI, or Docker files are updated when affected.
- Validation commands and any remaining risks are reported.
