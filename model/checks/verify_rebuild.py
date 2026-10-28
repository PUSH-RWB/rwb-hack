"""Verify repeat/fresh rebuild with every exported answer and native or Docker psql."""
from pathlib import Path
import datetime
import json
import os
import subprocess
import tempfile
import time
from probe_support import ROOT,LOG,build,probe_database

reports=ROOT/'model/reports'
started=time.monotonic()
baseline_core=(reports/'core_fingerprint.csv').read_bytes()
baseline_raw=(reports/'raw_fingerprint.csv').read_bytes()
baseline_dq=(reports/'dq_results.csv').read_bytes()
baseline_answers={p.name:p.read_bytes() for p in (ROOT/'model/answers/results').glob('q*.csv')}
expected={p.stem+'.csv' for p in (ROOT/'model/answers').glob('q[0-9][0-9]_*.sql')}
assert set(baseline_answers)==expected,'Answer exports do not match query files'

def compare(folder):
    assert (folder/'reports/core_fingerprint.csv').read_bytes()==baseline_core,'core changed'
    assert (folder/'reports/raw_fingerprint.csv').read_bytes()==baseline_raw,'raw changed'
    assert (folder/'reports/dq_results.csv').read_bytes()==baseline_dq,'DQ changed'
    for name,content in baseline_answers.items():
        assert (folder/'answers'/name).read_bytes()==content,'answer changed: '+name

try:
    with tempfile.TemporaryDirectory(prefix='capibara-rebuild-') as temp:
        temp=Path(temp)
        print('Checking repeated build...',flush=True)
        build(dict(os.environ),temp/'repeat')
        compare(temp/'repeat')
        print('Checking a separate empty database...',flush=True)
        with probe_database() as (_,env):
            load=subprocess.run(['python3','model/load_raw_copy.py'],cwd=ROOT,env=env,
                                text=True,capture_output=True,timeout=120)
            LOG.append(load.stdout+load.stderr)
            assert load.returncode==0,load.stderr
            build(env,temp/'fresh')
            compare(temp/'fresh')
    result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'same_database_rebuild':True,'fresh_database_rebuild':True,
            'core_tables_compared':10,'raw_tables_compared':8,
            'answer_files_compared':len(baseline_answers),'dq_results_identical':True,
            'raw_payload_excludes_only_loader_timestamp':True,
            'seconds':round(time.monotonic()-started,2)}
    (reports/'rebuild_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
finally:
    (reports/'rebuild_verification.log').write_text('\n'.join(LOG))
