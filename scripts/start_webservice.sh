#!/usr/bin/bash


if [[ -z "${NUM_WORKERS}" ]]; then
  NUM_WORKERS=2
fi

echo NUM_WORKERS set to $NUM_WORKERS

prisma migrate deploy

uvicorn application:app --port $PORT --host 0.0.0.0 --workers=$NUM_WORKERS --proxy-headers
