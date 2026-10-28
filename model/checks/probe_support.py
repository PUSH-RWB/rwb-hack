"""Isolated PostgreSQL test utilities; credentials come only from the environment."""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from contextlib import contextmanager
import os
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]
LOG=[]

def database_env(name):
    env=dict(os.environ)
    if env.get('DATABASE_URL'):
        url=urlsplit(env['DATABASE_URL'])
        env['DATABASE_URL']=urlunsplit((url.scheme,url.netloc,'/'+name,url.query,url.fragment))
    else:
        env['PGDATABASE']=name
    return env

def execute(sql, env=None, check=True):
    result=subprocess.run(['bash',str(ROOT/'model/psql.sh'),'-q','-A','-t','-c',sql],
                          cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
    LOG.append('SQL: '+sql+'\n'+result.stdout+result.stderr)
    if check and result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result

def scalar(sql,env=None):
    return execute(sql,env).stdout.strip()

def build(env, folder, effective_at=None, success=True):
    env=dict(env)
    folder=Path(folder)
    env['MODEL_REPORT_DIR']=str(folder/'reports')
    env['MODEL_ANSWER_DIR']=str(folder/'answers')
    if effective_at:
        env['MODEL_PRODUCT_CHANGE_AT']=effective_at
    result=subprocess.run(['bash','model/build.sh'],cwd=ROOT,env=env,text=True,
                          capture_output=True,timeout=240)
    LOG.append('BUILD '+str(folder)+'\n'+result.stdout+result.stderr)
    if success and result.returncode:
        raise RuntimeError(result.stdout[-3000:]+'\n'+result.stderr[-5000:])
    if not success and not result.returncode:
        raise AssertionError('Invalid fixture unexpectedly passed')
    return result

@contextmanager
def probe_database(template=None):
    name='rwb_probe_'+uuid.uuid4().hex[:16]
    admin=database_env('postgres')
    clause=' TEMPLATE "'+template+'"' if template else ''
    execute('CREATE DATABASE "'+name+'"'+clause+';',admin)
    try:
        yield name,database_env(name)
    finally:
        # Only the uniquely named database created by this context is removed.
        execute('DROP DATABASE IF EXISTS "'+name+'" WITH (FORCE);',admin)
