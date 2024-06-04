#!/usr/bin/env bash

docker build --progress=plain --build-arg PORT=9000 -t ghcr.io/airtai/captn-backend:dev .

mkdir -p grafana_data loki_data prometheus_data

docker-compose up -d

echo "All docker containers started. Grafana is running on http://localhost:3000/d/custom-observability/custom-observability?orgId=1&refresh=5s"

echo "To stop the containers, run 'docker-compose down'"
