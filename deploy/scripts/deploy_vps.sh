#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/opt/reminder_bot"
cd "$PROJECT_DIR"

cp -n .env.example .env || true

docker compose build
docker compose --profile tools run --rm migrate
docker compose up -d db bot worker

docker compose ps
