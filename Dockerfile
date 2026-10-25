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

EXPOSE 8000

CMD ["uvicorn", "murfulu.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
