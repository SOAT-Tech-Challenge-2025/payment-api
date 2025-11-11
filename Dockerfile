# Base stage
FROM python:3.14-alpine AS base

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apk add --no-cache gcc g++ musl-dev
RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Production builder
FROM base AS prod-builder

RUN poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Development builder
FROM base AS dev-builder

RUN poetry install --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Production runtime
FROM python:3.14-alpine AS production

ARG USER_UID=1000
ARG VERSION=1.0.0

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

LABEL author="SOAT Team"
LABEL version=${VERSION}
LABEL description="SOAT Tech Challenge FIAP - Payment API"

RUN apk add --no-cache libstdc++
RUN adduser soat --home /app --uid ${USER_UID} --disabled-password

WORKDIR /app

COPY --from=prod-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

USER soat

COPY --chown=${USER_UID}:${USER_UID} ./docker-entrypoint ./docker-entrypoint
COPY --chown=${USER_UID}:${USER_UID} ./payment_api ./payment_api
COPY --chown=${USER_UID}:${USER_UID} ./logging.ini ./logging.ini
COPY --chown=${USER_UID}:${USER_UID} ./alembic.ini ./alembic.ini

EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker-entrypoint/start_api.sh"]

# Development/Test runtime
FROM python:3.14-alpine AS development

ARG USER_UID=1000
ARG VERSION=1.0.0-dev

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

LABEL author="SOAT Team"
LABEL version=${VERSION}
LABEL description="SOAT Tech Challenge FIAP - Payment API - Development"

RUN apk add --no-cache libstdc++
RUN adduser soat --home /app --uid ${USER_UID} --disabled-password

WORKDIR /app

COPY --from=dev-builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

USER soat

COPY --chown=${USER_UID}:${USER_UID} ./docker-entrypoint ./docker-entrypoint
COPY --chown=${USER_UID}:${USER_UID} ./payment_api ./payment_api
COPY --chown=${USER_UID}:${USER_UID} ./tests ./tests
COPY --chown=${USER_UID}:${USER_UID} ./logging.ini ./logging.ini
COPY --chown=${USER_UID}:${USER_UID} ./pytest.ini ./pytest.ini
COPY --chown=${USER_UID}:${USER_UID} ./alembic.ini ./alembic.ini
COPY --chown=${USER_UID}:${USER_UID} ./pyproject.toml ./pyproject.toml

EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker-entrypoint/start_api.sh"]
