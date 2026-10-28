-- Один месяц оформления; все заказы, выручка только согласно dim_order_status.
WITH months AS (
 SELECT month_key FROM core.dim_date
 WHERE date_key >= DATE '2016-09-01' AND date_key < DATE '2018-09-01' GROUP BY month_key
), monthly AS (
 SELECT d.month_key,count(*) order_count,sum(o.item_amount) FILTER (WHERE s.is_revenue) revenue
 FROM core.fct_orders o JOIN core.dim_date d ON d.date_key=o.purchase_date
 JOIN core.dim_order_status s USING(order_status)
 WHERE o.purchase_date >= DATE '2016-09-01' AND o.purchase_date < DATE '2018-09-01'
 GROUP BY d.month_key
)
SELECT m.month_key,coalesce(a.order_count,0) order_count,coalesce(a.revenue,0)::numeric(12,2) revenue
FROM months m LEFT JOIN monthly a USING(month_key) ORDER BY m.month_key;
