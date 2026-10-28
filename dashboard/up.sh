#!/usr/bin/env bash
# Поднимает Superset и создаёт в нём 10 дашбордов по схеме core. Безопасно запускать повторно.
# Нужно: Docker, собранная модель (bash model/setup.sh && bash model/build.sh).
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  sed "s|^SUPERSET_SECRET_KEY=.*|SUPERSET_SECRET_KEY=$(openssl rand -base64 42 | tr -d '\n')|" .env.example > .env
  echo "создан dashboard/.env со случайным SECRET_KEY"
fi
docker compose up -d --build --wait --wait-timeout 240
python3 provision.py
echo
echo "Готово: http://127.0.0.1:8088   логин и пароль: admin / admin (только локально)"
