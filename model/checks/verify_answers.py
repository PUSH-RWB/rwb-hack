"""Strict current-data invariants plus source-aware controls of the original snapshot."""
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys

answers, reports = map(Path, sys.argv[1:3])
context = json.loads((reports / 'answer_context.json').read_text())
source_file = reports / 'raw_baseline_comparison.json'
source_changed = json.loads(source_file.read_text())['changed'] if source_file.exists() else False
checks = []

def read(stem):
    with (answers / (stem + '.csv')).open(newline='') as handle:
        return list(csv.DictReader(handle))

def number(value):
    return Decimal(str(value)) if value not in ('', None) else None

def total(rows, field):
    return sum((number(row[field]) or Decimal(0) for row in rows), Decimal(0))

def check(name, expected, actual, kind='SNAPSHOT'):
    passed = expected == actual
    status = 'PASS' if passed else ('WARN' if kind == 'SNAPSHOT' and source_changed else 'FAIL')
    checks.append(dict(name=name, kind=kind, status=status, expected=expected, actual=actual))

q1 = read('q01_monthly_revenue')
q2 = read('q02_top_sellers')
q3 = read('q03_average_order_value')[0]
q4 = read('q04_repeat_customers')[0]
q5 = read('q05_category_revenue')
q6 = read('q06_product_price_history')
q7 = read('q07_delivery_by_state')
q8 = read('q08_order_statuses')
q9s = read('q09_payments_by_state_2018')
q9m = read('q09_payment_methods')
q10 = read('q10_reviews_and_delivery')

check('q1_24_months', 24, len(q1), 'MODEL')
check('q1_empty_month', [('2016-11', '0', '0.00')], [(r['month_key'], r['order_count'], r['revenue']) for r in q1 if number(r['revenue']) == 0])
check('q1_total', Decimal('13221498.11'), total(q1, 'revenue'))
check('q1_current_revenue', number(context['monthly_revenue']), total(q1, 'revenue'), 'MODEL')
check('q2_ten_sellers', 10, len(q2))
check('q2_current_seller_count', min(10, context['revenue_sellers']), len(q2), 'MODEL')
check('q2_top_seller', {'seller_id': '4869f7a5dfa277a7dca6462dcf3b52b2', 'city': 'guariba', 'state': 'SP', 'order_count': '1124', 'units': '1148', 'revenue': '226987.93'}, q2[0] if q2 else None)
check('q3_average', Decimal('159.88'), number(q3['average_order_value']))
check('q3_lines_units', [Decimal('1.1422'), Decimal('1.1422')], [number(q3['average_lines_per_order']), number(q3['average_units_per_order'])])
check('q3_orders', 96478, int(q3['order_count']))
check('q3_current_orders', context['revenue_orders'], int(q3['order_count']), 'MODEL')
expected_average = ((number(context['order_amount']) / context['priced_orders']).quantize(Decimal('.01'), rounding=ROUND_HALF_UP) if context['priced_orders'] else None)
check('q3_current_average', expected_average, number(q3['average_order_value']), 'MODEL')
check('q4_buyers_repeat', {'customers': '96096', 'repeat_customers': '2997', 'repeat_percentage': '3.12'}, q4)
check('q5_categories', 74, len(q5))
check('q5_top', ['beleza_saude', Decimal('1233131.72'), Decimal('9.33')], [q5[0]['category_name_pt'], number(q5[0]['revenue']), number(q5[0]['revenue_share_percentage'])] if q5 else None)
check('q5_total', Decimal('13221498.11'), total(q5, 'revenue'))
check('q5_current_revenue', number(context['revenue']), total(q5, 'revenue'), 'MODEL')
winner = context['winner'] or {'units': 0, 'price_variants': 0}
check('q6_winner_prices', 31, len({r['price'] for r in q6}))
check('q6_units', 151, int(total(q6, 'units')))
check('q6_current_units', winner['units'], int(total(q6, 'units')), 'MODEL')
check('q6_current_prices', winner['price_variants'], len({r['price'] for r in q6}), 'MODEL')
check('q6_unique_date_price', len(q6), len({(r['sale_date'], r['price']) for r in q6}), 'MODEL')
check('q7_states', 17, len(q7))
sp = next((r for r in q7 if r['state'] == 'SP'), None)
check('q7_sp', ['40495', '8.76', '4.49'], [sp['order_count'], sp['average_delivery_days'], sp['late_percentage']] if sp else None)
check('q7_minimum_orders', True, all(int(r['order_count']) >= 500 for r in q7), 'MODEL')
check('q7_current_states', sorted(s or '' for s in context['delivery_states']), sorted(r['state'] for r in q7), 'MODEL')
check('q7_current_orders', int(context['delivery_orders']), int(total(q7, 'order_count')), 'MODEL')
check('q8_orders', 99441, int(total(q8, 'order_count')))
check('q8_without_items', 775, int(total(q8, 'orders_without_items')))
check('q8_current_orders', context['orders'], int(total(q8, 'order_count')), 'MODEL')
check('q8_current_without_items', context['without_items'], int(total(q8, 'orders_without_items')), 'MODEL')
check('q8_current_statuses', context['statuses'], len({r['order_status'] for r in q8}), 'MODEL')
check('q9_states_2018', 56015, int(total(q9s, 'payment_count')))
check('q9_methods_all_period', 103886, int(total(q9m, 'payment_count')))
check('q9_current_states_count', context['payments_2018'], int(total(q9s, 'payment_count')), 'MODEL')
check('q9_current_states_amount', number(context['payment_amount_2018']), total(q9s, 'payment_amount'), 'MODEL')
check('q9_current_methods_count', context['payments'], int(total(q9m, 'payment_count')), 'MODEL')
credit = next((r for r in q9m if r['payment_type'] == 'credit_card'), None)
check('q9_credit_card', ['76795', '3.51'], [credit['payment_count'], credit['average_installments']] if credit else None)
check('q10_scores', [1, 2, 3, 4, 5], [int(r['review_score']) for r in q10], 'MODEL')
check('q10_current_memberships', context['rated_pairs'], int(total(q10, 'order_count')), 'MODEL')
check('q10_baseline_counts', [9384, 2938, 7943, 18943, 56811], [int(r['order_count']) for r in q10])
check('q4_current_customers', context['customers'], int(q4['customers']), 'MODEL')
check('q4_current_repeat', context['repeat_customers'], int(q4['repeat_customers']), 'MODEL')
check('q5_current_categories', context['revenue_categories'], sorted(r['category_name_pt'] for r in q5), 'MODEL')
check('q10_baseline_days', ['21.31','16.65','14.26','12.31','10.68'], [r['average_delivery_days'] for r in q10])
check('q10_baseline_late', ['36.58','18.86','8.79','3.44','1.86'], [r['late_percentage'] for r in q10])
for label,rows,keys in [('q2',q2,['seller_id']),('q5',q5,['category_name_pt']),('q7',q7,['state']),('q8',q8,['order_status']),('q9states',q9s,['state']),('q9methods',q9m,['payment_type'])]:
    check(label+'_unique_groups',len(rows),len({tuple(r[k] for k in keys) for r in rows}),'MODEL')
for label,rows,key in [('q7',q7,'late_percentage'),('q8',q8,'share_percentage'),('q10',q10,'late_percentage')]:
    check(label+'_valid_percentages',True,all(number(r[key]) is None or 0<=number(r[key])<=100 for r in rows),'MODEL')
if context['orders']:
    check('q8_current_percentages',True,all(number(r['share_percentage'])==(Decimal(100)*int(r['order_count'])/context['orders']).quantize(Decimal('.01'),rounding=ROUND_HALF_UP) for r in q8),'MODEL')
summary = {status: sum(c['status'] == status for c in checks) for status in ['PASS', 'WARN', 'FAIL']}
(reports / 'answer_verification.json').write_text(json.dumps({c['name']: c['status'] == 'PASS' for c in checks}, indent=2) + '\n')
(reports / 'answer_verification_details.json').write_text(json.dumps({'source_changed': source_changed, 'summary': summary, 'checks': checks}, indent=2, default=str) + '\n')
for c in checks:
    print(f"{c['status']} {c['name']}: expected={c['expected']}; actual={c['actual']}")
if summary['WARN']:
    print('WARNING: source data differ from baseline; original snapshot controls require review.')
print('Answer checks:', summary)
if summary['FAIL']:
    raise SystemExit('Answer checks failed: ' + ', '.join(c['name'] for c in checks if c['status'] == 'FAIL'))
