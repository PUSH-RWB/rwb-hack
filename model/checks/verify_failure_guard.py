"""Inject a non-persistent defect to prove DQ rejects it and rolls back."""
from pathlib import Path
import json
import subprocess
root=Path(__file__).resolve().parents[2]
psql=['bash',str(root/'model/psql.sh'),'-q','--csv','-f','-']
def run(sql):
    return subprocess.run(psql,input=sql,text=True,capture_output=True,cwd=root,timeout=120)
fingerprint=(root/'model/checks/core_fingerprint.sql').read_text()
before=run(fingerprint)
assert before.returncode==0,before.stderr
sql='BEGIN;\nUPDATE core.fct_order_items SET is_revenue=NOT is_revenue WHERE (order_id,order_item_id)=(SELECT order_id,order_item_id FROM core.fct_order_items ORDER BY order_id,order_item_id LIMIT 1);\n'
sql+=(root/'model/checks/dq_checks.sql').read_text()
injected=run(sql)
assert injected.returncode!=0 and 'Core quality checks failed' in injected.stderr,injected.stderr
assert 'item_denormalization,FAIL,1' in injected.stdout,injected.stdout
# No COMMIT was sent; connection closure rolls the whole test transaction back.
after=run(fingerprint)
assert after.returncode==0 and after.stdout==before.stdout,'Rollback changed core'
result={'injected_defect_detected':True,'failed_check':'item_denormalization',
        'failed_check_violations':1,'transaction_rolled_back':True,'all_core_hashes_unchanged':True}
(root/'model/reports/failure_guard_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
