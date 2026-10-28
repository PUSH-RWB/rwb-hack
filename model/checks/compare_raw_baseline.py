"""Compare immutable source baseline with a current raw payload fingerprint."""
import csv
import json
from pathlib import Path
import sys

baseline, current, output = map(Path, sys.argv[1:4])
def read(path):
    with path.open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    return {r['table_name']: {'rows': int(r['row_count']), 'hash': r['payload_hash']} for r in rows}
old, new = read(baseline), read(current)
changed = [dict(table=name, expected=old.get(name), actual=new.get(name))
           for name in sorted(set(old) | set(new)) if old.get(name) != new.get(name)]
output.write_text(json.dumps({'changed': bool(changed), 'tables': changed}, indent=2) + '\n')
if changed:
    print('WARNING: source data changed relative to baseline; original control values require review.')
    for item in changed:
        print('  Changed:', item['table'], 'rows', item['expected'], '->', item['actual'])
else:
    print('Source data match the original baseline.')
