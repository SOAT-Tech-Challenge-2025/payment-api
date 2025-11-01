FROM python:3.14-alpine AS builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apk add --no-cache gcc g++ musl-dev

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --only=main --no-root

FROM python:3.14-alpine AS runtime

ARG USER_UID=1000
ARG VERSION=1.0.0

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

LABEL author="SOAT Team"
LABEL version=${VERSION}
LABEL description="SOAT Tech Challenge FIAP - Payment API"

RUN apk add --no-cache libstdc++

RUN adduser soat --home /app --uid ${USER_UID} --disabled-password

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

USER soat

COPY --chown=${USER_UID}:${USER_UID} ./docker-entrypoint ./docker-entrypoint
COPY --chown=${USER_UID}:${USER_UID} ./payment_api ./payment_api
COPY --chown=${USER_UID}:${USER_UID} ./logging.ini ./logging.ini

EXPOSE 8000

ENTRYPOINT ["sh", "/app/docker-entrypoint/start_api.sh"]
