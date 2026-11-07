# Image for the `api` and `ingest` services. Same image, different command.
FROM python:3.11.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependency metadata first, so a source change does not reinstall the world.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev,api]"

COPY rules ./rules
COPY tools ./tools
COPY tests ./tests
COPY docs ./docs

# The schema is built by `docker compose run --rm api alembic upgrade head`,
# never by hand — see docs/ENGINEERING.md.
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

# Files outside the Python tree that some tests read, so `python -m pytest`
# passes inside the image as well (the `docker` job in CI). Without them seven
# tests failed in the image and nowhere else, and the job was red on every
# push from 2026-08-20 to 2026-10-29. The configuration examples, the ignore
# list the public check relies on, and the two search-screen files the
# syntax-contract test reads. Small, public, and never read at run time.
COPY .env.example .gitignore .denylist.example ./
COPY deploy/server.env.example ./deploy/server.env.example
COPY web/src/screens/search/syntax.ts web/src/screens/search/Search.tsx ./web/src/screens/search/

EXPOSE 8000

CMD ["uvicorn", "murfulu.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
