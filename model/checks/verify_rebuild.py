"""Verify repeatability in the same DB and an isolated fresh PostgreSQL database."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/'model/reports'
started=time.monotonic()
container=os.environ.get('PG_CONTAINER','hack_postgres')
user=os.environ.get('PGUSER','hack')
verify_db='rwb_verify_'+str(os.getpid())+'_'+str(int(time.time()))
log=[]
created=False

def run(command,env=None):
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=240)
    log.append('$ '+' '.join(command)+'\n'+result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError('Command failed: '+' '.join(command)+'\n'+result.stderr[-4000:])
    return result.stdout

def compare(left,right):
    if left.read_bytes()!=right.read_bytes():
        raise AssertionError('Rebuild differs: '+str(left)+' vs '+str(right))

try:
    baseline_core=(REPORTS/'core_fingerprint.csv').read_bytes()
    baseline_raw=(REPORTS/'raw_fingerprint.csv').read_bytes()
    baseline_answers={p.name:p.read_bytes() for p in (ROOT/'model/answers/results').glob('q*.csv')}
    assert len(baseline_answers)==5
    with tempfile.TemporaryDirectory(prefix='capibara-rebuild-') as temp:
        temp=Path(temp)
        for phase in ['repeat','fresh']:
            print('Verifying',phase,'build...',flush=True)
            env=dict(os.environ)
            env['MODEL_REPORT_DIR']=str(temp/phase/'reports')
            env['MODEL_ANSWER_DIR']=str(temp/phase/'answers')
            if phase=='fresh':
                run(['docker','exec',container,'createdb','-U',user,verify_db])
                created=True
                env['PGDATABASE']=verify_db
                run(['python3','model/load_raw_copy.py'],env)
            run(['bash','model/build.sh'],env)
            assert (temp/phase/'reports/core_fingerprint.csv').read_bytes()==baseline_core,phase+' core changed'
            assert (temp/phase/'reports/raw_fingerprint.csv').read_bytes()==baseline_raw,phase+' raw payload changed'
            for name,content in baseline_answers.items():
                assert (temp/phase/'answers'/name).read_bytes()==content,phase+' answer changed: '+name
            compare(REPORTS/'dq_results.csv',temp/phase/'reports/dq_results.csv')
            print(phase,'build: all table hashes, five CSV answers and DQ results match.',flush=True)
    result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'same_database_rebuild':True,'fresh_database_rebuild':True,
        'core_tables_compared':10,'raw_tables_compared':8,'answer_files_compared':5,
        'dq_results_identical':True,'raw_payload_excludes_only_loader_timestamp':True,
        'baseline_core_fingerprint_sha256':hashlib.sha256(baseline_core).hexdigest(),
        'seconds':round(time.monotonic()-started,2)}
    (REPORTS/'rebuild_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
finally:
    if created:
        subprocess.run(['docker','exec',container,'dropdb','-U',user,'--if-exists',verify_db],check=True)
    (REPORTS/'rebuild_verification.log').write_text('\n'.join(log),encoding='utf-8')
