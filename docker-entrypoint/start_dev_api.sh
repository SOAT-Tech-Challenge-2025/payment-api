#!/bin/sh

uvicorn --log-level trace --reload --host 0.0.0.0 --port 8000 payment_api.entrypoints.api:app --log-config logging.ini
