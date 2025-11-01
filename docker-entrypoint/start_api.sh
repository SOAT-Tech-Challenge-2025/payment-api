#!/bin/sh

gunicorn payment_api.entrypoints.api:app -w ${GUNICORN_WORKERS:-4} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --log-config logging.ini
