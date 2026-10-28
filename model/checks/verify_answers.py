"""Independent acceptance checks on actual query CSV outputs, standard library only."""
import csv
import json
from decimal import Decimal
from pathlib import Path
import sys

answers=Path(sys.argv[1]); reports=Path(sys.argv[2])
def read(stem):
    with (answers/(stem+'.csv')).open(newline='') as handle:
        return list(csv.DictReader(handle))
q1=read('q01_monthly_revenue'); q2=read('q02_top_sellers'); q3=read('q03_average_order_value')[0]
q4=read('q04_repeat_customers')[0]; q5=read('q05_category_revenue')
checks={
 'q1_24_months':len(q1)==24,
 'q1_empty_month':[(r['month_key'],r['order_count'],r['revenue']) for r in q1 if Decimal(r['revenue'])==0]==[('2016-11','0','0.00')],
 'q1_total':sum(Decimal(r['revenue']) for r in q1)==Decimal('13221498.11'),
 'q2_ten_sellers':len(q2)==10,
 'q2_top_seller':q2[0]=={'seller_id':'4869f7a5dfa277a7dca6462dcf3b52b2','city':'guariba','state':'SP','order_count':'1124','units':'1148','revenue':'226987.93'},
 'q3_average':Decimal(q3['average_order_value'])==Decimal('159.88'),
 'q3_lines_units':Decimal(q3['average_lines_per_order'])==Decimal('1.1422') and Decimal(q3['average_units_per_order'])==Decimal('1.1422'),
 'q3_orders':int(q3['order_count'])==96478,
 'q4_buyers_repeat':q4=={'customers':'96096','repeat_customers':'2997','repeat_percentage':'3.12'},
 'q5_categories':len(q5)==74 and any(r['category_name_pt']=='__unknown__' for r in q5),
 'q5_top':q5[0]['category_name_pt']=='beleza_saude' and Decimal(q5[0]['revenue'])==Decimal('1233131.72') and Decimal(q5[0]['revenue_share_percentage'])==Decimal('9.33'),
 'q5_total':sum(Decimal(r['revenue']) for r in q5)==Decimal('13221498.11'),
}
(reports/'answer_verification.json').write_text(json.dumps(checks,indent=2)+'\n')
assert all(checks.values()),[name for name,passed in checks.items() if not passed]
print('All 12 acceptance checks for five core-only answers passed.')
