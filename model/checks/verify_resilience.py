"""Probe changed inputs/history in disposable DBs; never mutate the main raw."""
from pathlib import Path
import datetime
import json
import os
import tempfile
import time
from probe_support import ROOT, LOG, build, execute, scalar, probe_database

PRODUCT='437c05a395e9e47f9762e677a7068ce7'
started=time.monotonic()
results={}
main=scalar('SELECT current_database();')
assert main and '"' not in main
main_raw_before=(ROOT/'model/reports/raw_fingerprint.csv').read_bytes()
baseline={p.name:p.read_bytes() for p in (ROOT/'model/answers/results').glob('q*.csv')}

def literal(value):
    return "'"+value.replace("'","''")+"'"

def add_order(at,prefix,move=False):
    at=literal(at)+'::timestamp'
    who="(SELECT customer_unique_id FROM raw.customers ORDER BY customer_id LIMIT 1)" if move else "md5('"+prefix+"person')"
    return f"""
INSERT INTO raw.customers(customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state,_source_file)
VALUES(md5('{prefix}customer'),{who},'99999','probe_city','RJ','resilience_fixture');
INSERT INTO raw.orders(order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date,_source_file)
VALUES(md5('{prefix}order'),md5('{prefix}customer'),'delivered',({at})::text,({at}+interval '5 minutes')::text,({at}+interval '1 day')::text,({at}+interval '3 days')::text,({at}+interval '5 days')::text,'resilience_fixture');
INSERT INTO raw.order_items(order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value,_source_file)
SELECT md5('{prefix}order'),'1',product_id,seller_id,({at}+interval '2 days')::text,'44.98','5.00','resilience_fixture'
FROM raw.order_items WHERE product_id='{PRODUCT}' ORDER BY order_id,order_item_id LIMIT 1;
INSERT INTO raw.order_payments(order_id,payment_sequential,payment_type,payment_installments,payment_value,_source_file)
VALUES(md5('{prefix}order'),'1','credit_card','1','49.98','resilience_fixture');
INSERT INTO raw.order_reviews(review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp,_source_file)
VALUES(md5('{prefix}review'),md5('{prefix}order'),'5','','',({at}+interval '4 days')::text,({at}+interval '4 days 1 hour')::text,'resilience_fixture');
"""

def summary(folder):
    data=json.loads((folder/'reports/build_summary.json').read_text())
    assert data['model_checks']['FAIL']==0 and data['answer_checks']['FAIL']==0,data
    assert data['source_changed'],data
    return data

def answers_same(folder):
    for name,content in baseline.items():
        assert (folder/'answers'/name).read_bytes()==content,name

try:
    with tempfile.TemporaryDirectory(prefix='capibara-probes-') as tmp:
        tmp=Path(tmp)
        scenarios={
          'future_date':"""UPDATE raw.orders SET
order_purchase_timestamp=(order_purchase_timestamp::timestamp+interval '5 years')::text,
order_approved_at=(nullif(order_approved_at,'')::timestamp+interval '5 years')::text,
order_delivered_carrier_date=(nullif(order_delivered_carrier_date,'')::timestamp+interval '5 years')::text,
order_delivered_customer_date=(nullif(order_delivered_customer_date,'')::timestamp+interval '5 years')::text,
order_estimated_delivery_date=(nullif(order_estimated_delivery_date,'')::timestamp+interval '5 years')::text
WHERE order_id=(SELECT order_id FROM raw.orders WHERE order_status='delivered' ORDER BY order_id LIMIT 1);""",
          'new_order':add_order('2018-07-01 10:00:00','new_order_'),
          'unknown_status':"UPDATE raw.orders SET order_status='awaiting_pickup' WHERE order_id=(SELECT order_id FROM raw.orders WHERE order_status='shipped' ORDER BY order_id LIMIT 1);"
        }
        for name,mutation in scenarios.items():
            print('Checking',name,flush=True)
            with probe_database(template=main) as (_,env):
                execute(mutation,env)
                folder=tmp/name
                build(env,folder)
                data=summary(folder)
                if name=='future_date':
                    assert scalar("SELECT max(date_key)>=DATE '2022-12-31' FROM core.dim_date;",env)=='t'
                if name=='unknown_status':
                    assert scalar("SELECT NOT is_revenue AND NOT is_terminal AND NOT is_canceled AND NOT is_shipped_out FROM core.dim_order_status WHERE order_status='awaiting_pickup';",env)=='t'
                    assert scalar('SELECT sum(price) FROM core.fct_order_items WHERE is_revenue;',env)=='13221498.11'
                results[name]={'passed':True,**data}
        print('Checking product history, interval boundary and customer move...',flush=True)
        with probe_database(template=main) as (_,env):
            old_category=scalar("SELECT category_name_pt FROM core.dim_product WHERE product_id='"+PRODUCT+"' AND is_current;",env)
            historical_sql="""SELECT md5(string_agg(to_jsonb(t)::text,'' ORDER BY t.order_id,t.order_item_id))
FROM (SELECT i.order_id,i.order_item_id,i.price,p.category_name_pt
FROM core.fct_order_items i JOIN core.fct_orders o USING(order_id) JOIN core.dim_product p USING(product_key)
WHERE o.purchase_at<TIMESTAMP '2018-11-01') t;"""
            past_before=scalar(historical_sql,env)
            execute("UPDATE raw.products SET product_category_name='probe_new_category' WHERE product_id='"+PRODUCT+"';",env)
            first=tmp/'category_change'
            build(env,first,effective_at='2018-11-01 00:00:00')
            summary(first)
            answers_same(first)
            assert scalar("SELECT count(*) FROM core.dim_product WHERE product_id='"+PRODUCT+"';",env)=='2'
            assert scalar(historical_sql,env)==past_before
            # Exactly at the boundary and after it must select the new version.
            execute(add_order('2018-11-01 00:00:00','boundary_')+add_order('2018-11-02 10:00:00','after_')+add_order('2018-11-03 10:00:00','move_',move=True),env)
            second=tmp/'new_sales_and_move'
            build(env,second,effective_at='2018-11-01 00:00:00')
            summary(second)
            assert scalar("SELECT count(*) FROM core.fct_order_items i JOIN core.dim_product p USING(product_key) WHERE i.order_id IN (md5('boundary_order'),md5('after_order')) AND p.category_name_pt='probe_new_category';",env)=='2'
            assert scalar(historical_sql,env)==past_before
            assert scalar("SELECT count(DISTINCT customer_zip_code_prefix)>1 FROM core.fct_orders WHERE customer_unique_id=(SELECT customer_unique_id FROM raw.customers WHERE customer_id=md5('move_customer'));",env)=='t'
            repeated=tmp/'history_repeat'
            build(env,repeated,effective_at='2018-11-01 00:00:00')
            assert (second/'reports/core_fingerprint.csv').read_bytes()==(repeated/'reports/core_fingerprint.csv').read_bytes()
            execute("UPDATE raw.products SET product_category_name="+literal(old_category)+" WHERE product_id='"+PRODUCT+"';",env)
            third=tmp/'category_return'
            build(env,third,effective_at='2019-01-01 00:00:00')
            summary(third)
            assert scalar("SELECT count(*) FROM core.dim_product WHERE product_id='"+PRODUCT+"';",env)=='3'
            assert scalar(historical_sql,env)==past_before
            before_core=(third/'reports/core_fingerprint.csv').read_text()
            history_hash_sql="SELECT md5(string_agg(to_jsonb(t)::text,'' ORDER BY product_key)) FROM history.product_versions t;"
            before_history=scalar(history_hash_sql,env)
            execute("UPDATE raw.products SET product_category_name='probe_illegal_backdate' WHERE product_id='"+PRODUCT+"';",env)
            failed=build(env,tmp/'backdate_rejected',effective_at='2018-01-01',success=False)
            assert 'Product change must be later' in failed.stderr or 'Backdated product change' in failed.stderr,failed.stderr
            # Compare CSV using the same formatter as build.sh.
            import subprocess
            after=subprocess.run(['bash','model/psql.sh','-q','--csv','-f','-'],input=(ROOT/'model/checks/core_fingerprint.sql').read_text(),cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=90).stdout
            assert after==before_core,'Failed build changed core'
            assert scalar(history_hash_sql,env)==before_history,'Failed build changed persistent history'
            results['category_history']={'passed':True,'old_answers_byte_identical_after_change':True,
               'past_attribution_unchanged':True,'boundary_uses_new_version':True,
               'new_sales_use_new_version':True,'repeat_idempotent':True,
               'return_to_previous_category_creates_third_version':True,
               'backdated_change_rejected_and_rolled_back':True}
            results['customer_move']={'passed':True,'old_and_new_order_addresses_preserved':True}
    import subprocess
    raw_after=subprocess.run(['bash','model/psql.sh','-q','--csv','-f','-'],input=(ROOT/'model/checks/raw_fingerprint.sql').read_text(),cwd=ROOT,text=True,capture_output=True,check=True,timeout=90).stdout.encode()
    assert raw_after==main_raw_before,'Main raw changed during isolated tests'
    result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'main_raw_not_modified':True,'tests':results,'seconds':round(time.monotonic()-started,2)}
    (ROOT/'model/reports/resilience_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
finally:
    (ROOT/'model/reports/resilience_verification.log').write_text('\n'.join(LOG))
