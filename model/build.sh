#!/usr/bin/env bash
# Atomic model rebuild. Raw is read-only. Answers are exported only after checks pass.
set -euo pipefail
export LC_ALL=C
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS="${MODEL_REPORT_DIR:-$ROOT/model/reports}"
ANSWERS="${MODEL_ANSWER_DIR:-$ROOT/model/answers/results}"
mkdir -p "$REPORTS" "$ANSWERS"
cd "$ROOT"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/capibara-build.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT
bash model/psql.sh -q --csv -f - < model/checks/raw_fingerprint.sql > "$TMP_DIR/raw_before.csv"
{
  for sqlfile in "$ROOT"/model/sql/[0-9][0-9]_*.sql; do
    printf 'Building %s\n' "${sqlfile##*/}" >&2
    cat "$sqlfile"
  done
  cat "$ROOT/model/checks/dq_checks.sql"
} | bash model/psql.sh -q --csv --single-transaction -f - | tee "$TMP_DIR/dq_results.csv"
bash model/psql.sh -q --csv -f - < model/checks/raw_fingerprint.sql > "$TMP_DIR/raw_after.csv"
cmp "$TMP_DIR/raw_before.csv" "$TMP_DIR/raw_after.csv"
cp "$TMP_DIR/raw_after.csv" "$REPORTS/raw_fingerprint.csv"
cp "$TMP_DIR/dq_results.csv" "$REPORTS/dq_results.csv"
for query in "$ROOT"/model/answers/q[0-9][0-9]_*.sql; do
  name="${query##*/}"
  bash model/psql.sh -q --csv -f - < "$query" > "$TMP_DIR/${name%.sql}.csv"
  cp "$TMP_DIR/${name%.sql}.csv" "$ANSWERS/${name%.sql}.csv"
done
python3 model/checks/verify_answers.py "$ANSWERS" "$REPORTS"
bash model/psql.sh -q --csv -f - < model/checks/core_fingerprint.sql > "$REPORTS/core_fingerprint.csv"
printf 'Build complete; raw unchanged; answers verified. Results: %s\n' "$ANSWERS"
