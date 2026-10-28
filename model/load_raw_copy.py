"""Initial loading only: server-side COPY, no psycopg dependency, no reload of populated raw."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PSQL = ['bash', str(ROOT / 'model/psql.sh'), '-q', '-A', '-t']
def query(sql):
    completed = subprocess.run(PSQL, input=sql, text=True, capture_output=True, check=True)
    return completed.stdout.strip()

module = ast.parse((ROOT / 'scripts/load_raw.py').read_text())
mapping = next(ast.literal_eval(node.value) for node in module.body
               if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'MAPPING' for t in node.targets))
manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
for entry in manifest['files']:
    assert hashlib.sha256((ROOT / 'data' / entry['file']).read_bytes()).hexdigest() == entry['sha256'], entry['file']
for filename, table, columns in mapping:
    with (ROOT / 'data' / filename).open(encoding='utf-8-sig', newline='') as handle:
        assert next(csv.reader(handle)) == columns, filename

existing = int(query("SELECT count(*) FROM pg_tables WHERE schemaname='raw';"))
if existing == 0:
    query('CREATE SCHEMA IF NOT EXISTS raw;\n' + (ROOT / 'scripts/init/02_raw_ddl.sql').read_text())
elif existing != 8:
    raise SystemExit('Raw has an unexpected table set; refusing to modify it.')
counts_sql = ' UNION ALL '.join("SELECT '" + table + "',count(*) FROM " + table for _, table, _ in mapping) + ';'
counts = dict(line.split('|') for line in query(counts_sql).splitlines())
expected = dict(zip([table for _, table, _ in mapping], [99441,112650,103886,99224,32951,3095,99441,71]))
if any(int(value) for value in counts.values()):
    if any(int(counts[table]) != count for table, count in expected.items()):
        raise SystemExit('Raw is populated with unexpected row counts; refusing to reload it.')
    print('Existing raw preserved: 550759 rows. No COPY or UPDATE performed.')
else:
    statements = ['BEGIN;']
    for filename, table, columns in mapping:
        cols = ','.join(columns)
        statements += [f'CREATE TEMP TABLE incoming (LIKE {table}) ON COMMIT DROP;',
            f"COPY incoming ({cols}) FROM '/data/{filename}' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');",
            f"INSERT INTO {table} ({cols},_source_file) SELECT {cols},'{filename}' FROM incoming;",
            'DROP TABLE incoming;']
    statements.append('COMMIT;')
    query('\n'.join(statements))
    counts = dict(line.split('|') for line in query(counts_sql).splitlines())
assert all(int(counts[table]) == count for table, count in expected.items()), counts
print(json.dumps({'raw_counts':counts,'total_rows':sum(map(int,counts.values()))},indent=2))
