-- Один человек = customer_unique_id; все статусы. Это не когортное удержание.
WITH purchases AS (
 SELECT customer_unique_id,count(*) order_count FROM core.fct_orders GROUP BY customer_unique_id
)
SELECT count(*) customers,count(*) FILTER (WHERE p.order_count>=2) repeat_customers,
 round(100.0*count(*) FILTER (WHERE p.order_count>=2)/nullif(count(*),0),2) repeat_percentage
FROM core.dim_customer c LEFT JOIN purchases p USING(customer_unique_id);
