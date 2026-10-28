"""Compact machine-readable and console build result."""
import csv
import json
from pathlib import Path
import sys
reports=Path(sys.argv[1])
with (reports/'dq_results.csv').open(newline='') as handle:
    dq=list(csv.DictReader(handle))
counts={s:sum(r['status']==s for r in dq) for s in ['PASS','WARN','FAIL']}
answers=json.loads((reports/'answer_verification_details.json').read_text())
raw=json.loads((reports/'raw_baseline_comparison.json').read_text())
result={'model_checks':counts,'answer_checks':answers['summary'],
        'snapshot_answer_mismatches':sum(c['kind']=='SNAPSHOT' and c['status']!='PASS' for c in answers['checks']),
        'source_changed':raw['changed'],'changed_tables':[r['table'] for r in raw['tables']]}
(reports/'build_summary.json').write_text(json.dumps(result,indent=2)+'\n')
print('\nBUILD SUMMARY')
print('Model:',counts,'Answers:',answers['summary'])
print('Original-source controls differing:',result['snapshot_answer_mismatches'])
print('Source changed:',result['source_changed'],result['changed_tables'])
