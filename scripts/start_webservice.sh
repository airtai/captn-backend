#!/usr/bin/bash


if [[ -z "${NUM_WORKERS}" ]]; then
  NUM_WORKERS=1
fi

echo NUM_WORKERS set to $NUM_WORKERS

cat <<< "$CLIENT_SECRET" > client_secret.json

prisma migrate deploy
prisma generate

uvicorn application:app --port $PORT --host 0.0.0.0 --workers=$NUM_WORKERS --proxy-headers --lifespan on --log-config uvicorn-log-config.json
