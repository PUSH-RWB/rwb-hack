#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
docker compose -f docker-compose.yml -f model/docker-compose.local.yml up -d --wait --wait-timeout 120 postgres
python3 model/load_raw_copy.py
