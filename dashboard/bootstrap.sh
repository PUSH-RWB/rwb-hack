#!/bin/sh
# Первый запуск: миграции метаданных, администратор, роли, затем сервер.
# Каждый шаг идемпотентен, повторный старт контейнера безопасен.
set -eu
superset db upgrade
superset fab create-admin \
  --username "$SUPERSET_ADMIN_USER" --firstname Capibara --lastname Admin \
  --email admin@capibara.local --password "$SUPERSET_ADMIN_PASSWORD" || true
superset init
exec /usr/bin/run-server.sh
