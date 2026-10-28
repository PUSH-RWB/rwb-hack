#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${DATABASE_URL:-}" ]]; then
  exec psql -X -v ON_ERROR_STOP=1 "$DATABASE_URL" "$@"
fi
exec docker exec -i "${PG_CONTAINER:-hack_postgres}" psql -X -v ON_ERROR_STOP=1 -U "${PGUSER:-hack}" -d "${PGDATABASE:-marketplace}" "$@"
