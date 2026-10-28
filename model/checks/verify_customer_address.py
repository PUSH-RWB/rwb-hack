"""Prove a new address does not overwrite any original order address."""
from pathlib import Path
import datetime
import json
import subprocess
import tempfile
from probe_support import ROOT,LOG,build,execute,scalar,probe_database

main=scalar('SELECT current_database();')
address_sql="""SELECT md5(string_agg(md5(to_jsonb(a)::text),'' ORDER BY order_id)) FROM (
SELECT order_id,source_customer_id,customer_unique_id,customer_zip_code_prefix,customer_city_source,customer_state_source
FROM core.fct_orders WHERE order_id<>md5('address_probe_order')) a;"""
before=scalar(address_sql)
raw_before=(ROOT/'model/reports/raw_fingerprint.csv').read_bytes()
try:
    with tempfile.TemporaryDirectory(prefix='capibara-address-') as temp:
        with probe_database(template=main) as (_,env):
            execute("""INSERT INTO raw.customers(customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state,_source_file)
SELECT md5('address_probe_customer'),customer_unique_id,'99999','probe_city','RJ','address_fixture'
FROM raw.customers ORDER BY customer_id LIMIT 1;
INSERT INTO raw.orders(order_id,customer_id,order_status,order_purchase_timestamp,order_estimated_delivery_date,_source_file)
VALUES(md5('address_probe_order'),md5('address_probe_customer'),'created','2020-01-02 10:00:00','2020-01-07 10:00:00','address_fixture');""",env)
            build(env,Path(temp))
            assert scalar(address_sql,env)==before,'An original order address changed'
            assert scalar("SELECT customer_zip_code_prefix='99999' AND customer_city_source='probe_city' AND customer_state_source='RJ' FROM core.fct_orders WHERE order_id=md5('address_probe_order');",env)=='t'
            assert scalar("SELECT count(DISTINCT customer_zip_code_prefix)>1 FROM core.fct_orders WHERE customer_unique_id=(SELECT customer_unique_id FROM core.fct_orders WHERE order_id=md5('address_probe_order'));",env)=='t'
    after=subprocess.run(['bash','model/psql.sh','-q','--csv','-f','-'],input=(ROOT/'model/checks/raw_fingerprint.sql').read_text(),cwd=ROOT,text=True,capture_output=True,check=True,timeout=90).stdout.encode()
    assert after==raw_before,'Main raw changed'
    result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'all_original_order_addresses_unchanged':True,'new_order_has_new_address':True,
            'same_person_has_both_addresses':True,'main_raw_fingerprint_unchanged':True}
    (ROOT/'model/reports/customer_address_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
finally:
    (ROOT/'model/reports/customer_address_verification.log').write_text('\n'.join(LOG))
