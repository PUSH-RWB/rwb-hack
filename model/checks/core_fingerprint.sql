SELECT 'core.dim_date' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.dim_date t
UNION ALL
SELECT 'core.dim_order_status' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.dim_order_status t
UNION ALL
SELECT 'core.dim_geography' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.dim_geography t
UNION ALL
SELECT 'core.dim_customer' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.dim_customer t
UNION ALL
SELECT 'core.dim_seller' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.dim_seller t
UNION ALL
SELECT 'core.dim_product' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.dim_product t
UNION ALL
SELECT 'core.fct_orders' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.fct_orders t
UNION ALL
SELECT 'core.fct_order_items' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.fct_order_items t
UNION ALL
SELECT 'core.fct_payments' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.fct_payments t
UNION ALL
SELECT 'core.fct_reviews' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t))::text),'' ORDER BY md5((to_jsonb(t))::text))) payload_hash FROM core.fct_reviews t
ORDER BY table_name;
