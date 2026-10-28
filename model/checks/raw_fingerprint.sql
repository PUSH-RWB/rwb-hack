SELECT 'raw.orders' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.orders t
UNION ALL
SELECT 'raw.order_items' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.order_items t
UNION ALL
SELECT 'raw.order_payments' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.order_payments t
UNION ALL
SELECT 'raw.order_reviews' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.order_reviews t
UNION ALL
SELECT 'raw.products' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.products t
UNION ALL
SELECT 'raw.sellers' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.sellers t
UNION ALL
SELECT 'raw.customers' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.customers t
UNION ALL
SELECT 'raw.product_category_translation' table_name,count(*) row_count,md5(string_agg(md5((to_jsonb(t)-'_loaded_at')::text),'' ORDER BY md5((to_jsonb(t)-'_loaded_at')::text))) payload_hash FROM raw.product_category_translation t
ORDER BY table_name;
