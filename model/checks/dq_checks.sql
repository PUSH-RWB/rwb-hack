-- Проверки читают raw только для сверки; ответы на вопросы обращаются исключительно к core.
-- MODEL: строгий FAIL. SOURCE: аномалия источника. SNAPSHOT: контроль исходной выгрузки; расхождение WARN.
CREATE OR REPLACE TEMP VIEW dq_results AS
WITH checks AS (
SELECT 'rows_fct_orders' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-99441) FROM core.fct_orders)::bigint violations,'99441' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'raw_conservation_fct_orders' check_name,'MODEL' defect_type,(SELECT abs((SELECT count(*) FROM core.fct_orders)-(SELECT count(*) FROM raw.orders)))::bigint violations,'0' expected,'Ни одна исходная запись не потеряна' explanation
UNION ALL
SELECT 'rows_fct_order_items' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-112650) FROM core.fct_order_items)::bigint violations,'112650' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'raw_conservation_fct_order_items' check_name,'MODEL' defect_type,(SELECT abs((SELECT count(*) FROM core.fct_order_items)-(SELECT count(*) FROM raw.order_items)))::bigint violations,'0' expected,'Ни одна исходная запись не потеряна' explanation
UNION ALL
SELECT 'rows_fct_payments' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-103886) FROM core.fct_payments)::bigint violations,'103886' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'raw_conservation_fct_payments' check_name,'MODEL' defect_type,(SELECT abs((SELECT count(*) FROM core.fct_payments)-(SELECT count(*) FROM raw.order_payments)))::bigint violations,'0' expected,'Ни одна исходная запись не потеряна' explanation
UNION ALL
SELECT 'rows_fct_reviews' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-99224) FROM core.fct_reviews)::bigint violations,'99224' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'raw_conservation_fct_reviews' check_name,'MODEL' defect_type,(SELECT abs((SELECT count(*) FROM core.fct_reviews)-(SELECT count(*) FROM raw.order_reviews)))::bigint violations,'0' expected,'Ни одна исходная запись не потеряна' explanation
UNION ALL
SELECT 'rows_dim_customer' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-96096) FROM core.dim_customer)::bigint violations,'96096' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'rows_dim_seller' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-3095) FROM core.dim_seller)::bigint violations,'3095' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'rows_dim_product' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-32951) FROM core.dim_product)::bigint violations,'32951' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'rows_dim_geography' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-15080) FROM core.dim_geography)::bigint violations,'15080' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'rows_dim_date' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-1826) FROM core.dim_date)::bigint violations,'1826' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'rows_dim_order_status' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-8) FROM core.dim_order_status)::bigint violations,'8' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'unique_dim_date' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT date_key FROM core.dim_date GROUP BY date_key HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_dim_order_status' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT order_status FROM core.dim_order_status GROUP BY order_status HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_dim_geography' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT zip_code_prefix FROM core.dim_geography GROUP BY zip_code_prefix HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_dim_customer' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT customer_unique_id FROM core.dim_customer GROUP BY customer_unique_id HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_dim_seller' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT seller_id FROM core.dim_seller GROUP BY seller_id HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_dim_product' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT product_key FROM core.dim_product GROUP BY product_key HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_fct_orders' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT order_id FROM core.fct_orders GROUP BY order_id HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_fct_order_items' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT order_id,order_item_id FROM core.fct_order_items GROUP BY order_id,order_item_id HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_fct_payments' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT order_id,payment_sequential FROM core.fct_payments GROUP BY order_id,payment_sequential HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'unique_fct_reviews' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT order_id,review_id FROM core.fct_reviews GROUP BY order_id,review_id HAVING count(*)>1) x)::bigint violations,'0' expected,'Уникальность объявленного первичного ключа' explanation
UNION ALL
SELECT 'fk_fct_orders_customer_unique_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_orders c LEFT JOIN core.dim_customer p ON c.customer_unique_id=p.customer_unique_id WHERE c.customer_unique_id IS NOT NULL AND p.customer_unique_id IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_orders_purchase_date' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_orders c LEFT JOIN core.dim_date p ON c.purchase_date=p.date_key WHERE c.purchase_date IS NOT NULL AND p.date_key IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_orders_order_status' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_orders c LEFT JOIN core.dim_order_status p ON c.order_status=p.order_status WHERE c.order_status IS NOT NULL AND p.order_status IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_orders_customer_zip_code_prefix' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_orders c LEFT JOIN core.dim_geography p ON c.customer_zip_code_prefix=p.zip_code_prefix WHERE c.customer_zip_code_prefix IS NOT NULL AND p.zip_code_prefix IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_order_items_order_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items c LEFT JOIN core.fct_orders p ON c.order_id=p.order_id WHERE c.order_id IS NOT NULL AND p.order_id IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_order_items_product_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items c LEFT JOIN core.dim_product p ON c.product_key=p.product_key AND c.product_id=p.product_id WHERE p.product_key IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_order_items_seller_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items c LEFT JOIN core.dim_seller p ON c.seller_id=p.seller_id WHERE c.seller_id IS NOT NULL AND p.seller_id IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_order_items_customer_unique_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items c LEFT JOIN core.dim_customer p ON c.customer_unique_id=p.customer_unique_id WHERE c.customer_unique_id IS NOT NULL AND p.customer_unique_id IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_order_items_purchase_date' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items c LEFT JOIN core.dim_date p ON c.purchase_date=p.date_key WHERE c.purchase_date IS NOT NULL AND p.date_key IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_order_items_order_status' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items c LEFT JOIN core.dim_order_status p ON c.order_status=p.order_status WHERE c.order_status IS NOT NULL AND p.order_status IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_payments_order_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_payments c LEFT JOIN core.fct_orders p ON c.order_id=p.order_id WHERE c.order_id IS NOT NULL AND p.order_id IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_fct_reviews_order_id' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_reviews c LEFT JOIN core.fct_orders p ON c.order_id=p.order_id WHERE c.order_id IS NOT NULL AND p.order_id IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'fk_dim_seller_zip_code_prefix' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.dim_seller c LEFT JOIN core.dim_geography p ON c.zip_code_prefix=p.zip_code_prefix WHERE c.zip_code_prefix IS NOT NULL AND p.zip_code_prefix IS NULL)::bigint violations,'0' expected,'Ссылочная целостность' explanation
UNION ALL
SELECT 'sum_item_amount' check_name,'MODEL' defect_type,(SELECT CASE WHEN (SELECT sum(item_amount) FROM core.fct_orders) IS NOT DISTINCT FROM (SELECT sum(price) FROM core.fct_order_items) THEN 0 ELSE 1 END)::bigint violations,'0' expected,'Денежная свёртка совпадает с деталью' explanation
UNION ALL
SELECT 'raw_sum_price' check_name,'MODEL' defect_type,(SELECT CASE WHEN (SELECT sum(price) FROM core.fct_order_items) IS NOT DISTINCT FROM (SELECT sum(nullif(trim(price),'')::numeric(12,2)) FROM raw.order_items) THEN 0 ELSE 1 END)::bigint violations,'0' expected,'Сумма сохранена относительно raw' explanation
UNION ALL
SELECT 'sum_freight_amount' check_name,'MODEL' defect_type,(SELECT CASE WHEN (SELECT sum(freight_amount) FROM core.fct_orders) IS NOT DISTINCT FROM (SELECT sum(freight_value) FROM core.fct_order_items) THEN 0 ELSE 1 END)::bigint violations,'0' expected,'Денежная свёртка совпадает с деталью' explanation
UNION ALL
SELECT 'raw_sum_freight_value' check_name,'MODEL' defect_type,(SELECT CASE WHEN (SELECT sum(freight_value) FROM core.fct_order_items) IS NOT DISTINCT FROM (SELECT sum(nullif(trim(freight_value),'')::numeric(12,2)) FROM raw.order_items) THEN 0 ELSE 1 END)::bigint violations,'0' expected,'Сумма сохранена относительно raw' explanation
UNION ALL
SELECT 'payment_sums' check_name,'MODEL' defect_type,(SELECT CASE WHEN (SELECT sum(payment_amount) FROM core.fct_orders) IS NOT DISTINCT FROM (SELECT sum(payment_value) FROM core.fct_payments) AND (SELECT sum(payment_value) FROM core.fct_payments) IS NOT DISTINCT FROM (SELECT sum(nullif(trim(payment_value),'')::numeric(12,2)) FROM raw.order_payments) THEN 0 ELSE 1 END)::bigint violations,'0' expected,'Сохранность платежей и их свёрток' explanation
UNION ALL
SELECT 'review_counts' check_name,'MODEL' defect_type,(SELECT abs((SELECT sum(review_count) FROM core.fct_orders)-(SELECT count(*) FROM core.fct_reviews)))::bigint violations,'0' expected,'Сохранность отзывов в свёртке' explanation
UNION ALL
SELECT 'revenue' check_name,'SNAPSHOT' defect_type,(SELECT CASE WHEN sum(item_amount)=13221498.11 THEN 0 ELSE 1 END FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue)::bigint violations,'13221498.11' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'order_value_identity' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_orders WHERE order_amount IS DISTINCT FROM item_amount+freight_amount)::bigint violations,'0' expected,'Чек = товары + доставка, включая семантику NULL' explanation
UNION ALL
SELECT 'item_denormalization' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items i JOIN core.fct_orders o USING(order_id) JOIN core.dim_order_status s ON s.order_status=o.order_status WHERE i.purchase_date IS DISTINCT FROM o.purchase_date OR i.order_status IS DISTINCT FROM o.order_status OR i.customer_unique_id IS DISTINCT FROM o.customer_unique_id OR i.is_revenue IS DISTINCT FROM s.is_revenue)::bigint violations,'0' expected,'Денормализованные поля согласованы с заказом и статусом' explanation
UNION ALL
SELECT 'missing_money_is_null' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_orders WHERE (NOT has_items AND (item_amount IS NOT NULL OR freight_amount IS NOT NULL OR order_amount IS NOT NULL)) OR (NOT has_payments AND payment_amount IS NOT NULL))::bigint violations,'0' expected,'Неизвестные суммы не заменены нулём' explanation
UNION ALL
SELECT 'categories' check_name,'SNAPSHOT' defect_type,(SELECT CASE WHEN count(DISTINCT category_name_pt)=74 AND count(*) FILTER(WHERE category_name_pt='__unknown__')=610 THEN 0 ELSE 1 END FROM core.dim_product)::bigint violations,'74; unknown products=610' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'category_translation' check_name,'SNAPSHOT' defect_type,(SELECT abs(count(*)-13) FROM core.dim_product WHERE has_category AND category_name_en IS NULL)::bigint violations,'13' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'delivery_before_purchase' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders WHERE delivered_customer_at<purchase_at)::bigint violations,'0' expected,'Даты не переставляются автоматически' explanation
UNION ALL
SELECT 'delivered_without_date' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue AND delivered_customer_at IS NULL)::bigint violations,'8' expected,'Ожидаемая аномалия источника; заказ сохранён' explanation
UNION ALL
SELECT 'chronology_flags' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders WHERE has_chronology_anomaly)::bigint violations,'WARN' expected,'Нарушения хронологии помечены, исходные даты сохранены' explanation
UNION ALL
SELECT 'orders_without_items' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders WHERE NOT has_items)::bigint violations,'775' expected,'Заказы без товарных позиций сохранены' explanation
UNION ALL
SELECT 'orders_without_payments' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders WHERE NOT has_payments)::bigint violations,'1' expected,'Отсутствующий платёж не равен нулевому' explanation
UNION ALL
SELECT 'orders_without_reviews' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders WHERE NOT has_reviews)::bigint violations,'768' expected,'Отзыв необязателен' explanation
UNION ALL
SELECT 'delivered_payment_gap' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue AND (payment_amount IS NULL OR payment_delta<>0))::bigint violations,'goods+freight minus payments = 2001.88' expected,'Разница общих сумм включает заказ без платежа; сумма известных индивидуальных разниц отличается' explanation
UNION ALL
SELECT 'payment_gap_control' check_name,'SNAPSHOT' defect_type,(SELECT CASE WHEN sum(order_amount)-sum(payment_amount)=2001.88 THEN 0 ELSE 1 END FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue)::bigint violations,'2001.88' expected,'Ожидание исходного снимка; при новых данных пересмотреть эталон, не исправлять модель' explanation
UNION ALL
SELECT 'geography_ambiguity' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.dim_geography WHERE state_variant_count>1)::bigint violations,'33' expected,'Префикс не гарантирует единственный штат; исходные адреса сохранены' explanation
UNION ALL
SELECT 'zero_installments' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_payments WHERE payment_installments=0)::bigint violations,'2' expected,'Нулевые installments сохраняются; payment_value не умножается' explanation
UNION ALL
SELECT 'product_version_intervals' check_name,'MODEL' defect_type,(SELECT count(*) FROM (SELECT product_id,valid_from,valid_to,lead(valid_from) OVER(PARTITION BY product_id ORDER BY valid_from) next_from FROM core.dim_product) v WHERE (next_from IS NOT NULL AND valid_to IS DISTINCT FROM next_from) OR (next_from IS NULL AND valid_to IS NOT NULL))::bigint violations,'0' expected,'Версии без пересечений и разрывов, последняя открыта' explanation
UNION ALL
SELECT 'item_product_asof' check_name,'MODEL' defect_type,(SELECT count(*) FROM core.fct_order_items i JOIN core.fct_orders o USING(order_id) JOIN core.dim_product p USING(product_key) WHERE i.product_id<>p.product_id OR o.purchase_at<p.valid_from OR (p.valid_to IS NOT NULL AND o.purchase_at>=p.valid_to))::bigint violations,'0' expected,'Позиция ссылается на версию, действовавшую при оформлении' explanation
UNION ALL
SELECT 'product_history_conservation' check_name,'MODEL' defect_type,(SELECT abs((SELECT count(*) FROM history.product_versions)-(SELECT count(*) FROM core.dim_product)))::bigint violations,'0' expected,'Пересборка не теряет сохранённые версии' explanation
UNION ALL
SELECT 'unknown_order_status' check_name,'SNAPSHOT' defect_type,(SELECT count(*) FROM core.dim_order_status WHERE order_status NOT IN ('delivered','shipped','canceled','unavailable','invoiced','processing','created','approved'))::bigint violations,'0' expected,'Новые статусы не включены в выручку; требуется классификация человеком' explanation
UNION ALL
SELECT 'non_revenue_with_delivery_date' check_name,'SOURCE' defect_type,(SELECT count(*) FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE NOT s.is_revenue AND delivered_customer_at IS NOT NULL)::bigint violations,'WARN' expected,'Для Q7/Q10 используем фактическую дату вручения; противоречивый статус виден отдельно' explanation
UNION ALL
SELECT 'mart_order_grain' check_name,'MODEL' defect_type,(SELECT abs((SELECT count(*) FROM mart.order_metrics)-(SELECT count(*) FROM core.fct_orders)))::bigint violations,'0' expected,'Витрина не размножает и не теряет заказы' explanation
)
SELECT check_name,CASE WHEN violations=0 THEN 'PASS' WHEN defect_type IN ('SOURCE','SNAPSHOT') THEN 'WARN' ELSE 'FAIL' END status,
 violations,defect_type,expected,explanation FROM checks;
SELECT * FROM dq_results ORDER BY CASE status WHEN 'FAIL' THEN 0 WHEN 'WARN' THEN 1 ELSE 2 END,check_name;
DO $assert$
BEGIN
 IF EXISTS(SELECT 1 FROM dq_results WHERE status='FAIL') THEN
  RAISE EXCEPTION 'Core quality checks failed; transaction rolled back';
 END IF;
END $assert$;
