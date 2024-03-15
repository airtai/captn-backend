#!/usr/bin/bash


if [[ -z "${NUM_WORKERS}" ]]; then
  NUM_WORKERS=1
fi

echo NUM_WORKERS set to $NUM_WORKERS

cat <<< "$CLIENT_SECRET" > client_secret.json

prisma migrate deploy
prisma generate

uvicorn application:app --port $PORT --workers=$NUM_WORKERS --proxy-headers --lifespan on
