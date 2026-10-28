#!/usr/bin/env bash
# Rebuild core/mart atomically; preserve history and raw. Publish exports after verification.
set -euo pipefail
export LC_ALL=C
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS="${MODEL_REPORT_DIR:-$ROOT/model/reports}"
ANSWERS="${MODEL_ANSWER_DIR:-$ROOT/model/answers/results}"
mkdir -p "$REPORTS" "$ANSWERS"
cd "$ROOT"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/capibara-build.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT
mkdir -p "$TMP_DIR/reports" "$TMP_DIR/answers"
bash model/psql.sh -q --csv -f - < model/checks/raw_fingerprint.sql > "$TMP_DIR/raw_before.csv"
python3 model/checks/compare_raw_baseline.py model/checks/raw_baseline.csv "$TMP_DIR/raw_before.csv" "$TMP_DIR/reports/raw_baseline_comparison.json"
{
  for sqlfile in "$ROOT"/model/sql/[0-9][0-9]_*.sql; do
    printf 'Building %s\n' "${sqlfile##*/}" >&2
    cat "$sqlfile"
  done
  cat "$ROOT/model/checks/dq_checks.sql"
} | bash model/psql.sh -q --csv --single-transaction -v product_change_at="${MODEL_PRODUCT_CHANGE_AT:-}" -f - | tee "$TMP_DIR/reports/dq_results.csv"
bash model/psql.sh -q --csv -f - < model/checks/raw_fingerprint.sql > "$TMP_DIR/reports/raw_fingerprint.csv"
if ! cmp "$TMP_DIR/raw_before.csv" "$TMP_DIR/reports/raw_fingerprint.csv"; then
  printf 'FAIL: raw changed during build; exports are not published.\n' >&2
  exit 1
fi
for query in "$ROOT"/model/answers/q[0-9][0-9]_*.sql; do
  name="${query##*/}"
  bash model/psql.sh -q --csv -f - < "$query" > "$TMP_DIR/answers/${name%.sql}.csv"
done
bash model/psql.sh -q -A -t -f - < model/checks/answer_context.sql > "$TMP_DIR/reports/answer_context.json"
python3 model/checks/verify_answers.py "$TMP_DIR/answers" "$TMP_DIR/reports"
bash model/psql.sh -q --csv -f - < model/checks/core_fingerprint.sql > "$TMP_DIR/reports/core_fingerprint.csv"
python3 model/checks/build_summary.py "$TMP_DIR/reports"
cp "$TMP_DIR/reports/"* "$REPORTS/"
cp "$TMP_DIR/answers/"*.csv "$ANSWERS/"
printf 'Build complete; raw unchanged; verified exports: %s\n' "$ANSWERS"
