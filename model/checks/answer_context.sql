-- Control totals from the current model, independent of baseline constants.
WITH winner AS (
 SELECT product_id, count(*) units, count(DISTINCT price) price_variants
 FROM core.fct_order_items WHERE is_revenue GROUP BY product_id
 ORDER BY price_variants DESC, product_id LIMIT 1
), states AS (
 SELECT customer_state_source, count(*) n FROM core.fct_orders
 WHERE delivered_customer_at IS NOT NULL GROUP BY customer_state_source HAVING count(*) >= 500
), rated_pairs AS (
 SELECT DISTINCT r.order_id, r.review_score FROM core.fct_reviews r
 JOIN core.fct_orders o USING(order_id) WHERE o.delivered_customer_at IS NOT NULL
)
SELECT jsonb_build_object(
 'orders', (SELECT count(*) FROM core.fct_orders),
 'statuses', (SELECT count(*) FROM core.dim_order_status),
 'without_items', (SELECT count(*) FROM core.fct_orders WHERE NOT has_items),
 'revenue', (SELECT coalesce(sum(price),0) FROM core.fct_order_items WHERE is_revenue),
 'monthly_revenue', (SELECT coalesce(sum(o.item_amount),0) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue AND purchase_date >= DATE '2016-09-01' AND purchase_date < DATE '2018-09-01'),
 'revenue_orders', (SELECT count(*) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue),
 'priced_orders', (SELECT count(order_amount) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue),
 'order_amount', (SELECT sum(order_amount) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue),
 'revenue_sellers', (SELECT count(DISTINCT seller_id) FROM core.fct_order_items WHERE is_revenue),
 'winner', (SELECT to_jsonb(winner) FROM winner),
 'delivery_states', (SELECT coalesce(jsonb_agg(customer_state_source ORDER BY customer_state_source),'[]'::jsonb) FROM states),
 'delivery_orders', (SELECT coalesce(sum(n),0) FROM states),
 'customers', (SELECT count(*) FROM core.dim_customer),
 'repeat_customers', (SELECT count(*) FROM (SELECT customer_unique_id FROM core.fct_orders GROUP BY customer_unique_id HAVING count(*)>=2) x),
 'revenue_categories', (SELECT coalesce(jsonb_agg(category_name_pt ORDER BY category_name_pt),'[]'::jsonb) FROM (SELECT DISTINCT p.category_name_pt FROM core.fct_order_items i JOIN core.dim_product p USING(product_key) WHERE i.is_revenue) c),
 'payments', (SELECT count(*) FROM core.fct_payments),
 'payments_2018', (SELECT count(*) FROM core.fct_payments p JOIN core.fct_orders o USING(order_id) WHERE purchase_date >= DATE '2018-01-01' AND purchase_date < DATE '2019-01-01'),
 'payment_amount_2018', (SELECT coalesce(sum(payment_value),0) FROM core.fct_payments p JOIN core.fct_orders o USING(order_id) WHERE purchase_date >= DATE '2018-01-01' AND purchase_date < DATE '2019-01-01'),
 'rated_pairs', (SELECT count(*) FROM rated_pairs)
);
