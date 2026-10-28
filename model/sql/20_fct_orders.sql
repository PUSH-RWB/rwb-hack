-- Таблица: core.fct_orders
-- Гранулярность: один заказ всех статусов
-- PK: order_id
-- FK: customer_unique_id, purchase_date, order_status, customer_zip_code_prefix -> измерения
-- Ожидаемые строки: 99441
-- Назначение: Основа заказов; свёртки заполняются 24_order_rollups.sql в той же транзакции
-- Пропуски: Деньги без дочерних записей NULL; даты не восстанавливаются; is_late NULL без дат
DROP TABLE IF EXISTS core.fct_orders CASCADE;
CREATE TABLE core.fct_orders (
 order_id text PRIMARY KEY, source_customer_id text NOT NULL,
 customer_unique_id text NOT NULL REFERENCES core.dim_customer,
 customer_zip_code_prefix text REFERENCES core.dim_geography,
 customer_city_source text, customer_state_source text,
 order_status text NOT NULL REFERENCES core.dim_order_status,
 purchase_at timestamp NOT NULL, purchase_date date NOT NULL REFERENCES core.dim_date,
 approved_at timestamp, delivered_carrier_at timestamp, delivered_customer_at timestamp, estimated_delivery_at timestamp,
 delivery_days numeric(12,4), estimate_days integer, delay_days integer, is_late boolean,
 has_chronology_anomaly boolean NOT NULL,
 item_count integer NOT NULL DEFAULT 0, seller_count integer NOT NULL DEFAULT 0,
 item_amount numeric(12,2), freight_amount numeric(12,2), order_amount numeric(12,2),
 payment_count integer NOT NULL DEFAULT 0, payment_amount numeric(12,2), payment_delta numeric(12,2),
 review_count integer NOT NULL DEFAULT 0, review_score_avg numeric(8,4),
 has_items boolean NOT NULL DEFAULT false, has_payments boolean NOT NULL DEFAULT false, has_reviews boolean NOT NULL DEFAULT false
);
WITH typed AS (
 SELECT nullif(trim(o.order_id),'') order_id, nullif(trim(o.customer_id),'') source_customer_id,
 nullif(trim(c.customer_unique_id),'') customer_unique_id,
 nullif(trim(c.customer_zip_code_prefix),'') zip, nullif(trim(c.customer_city),'') city, nullif(trim(c.customer_state),'') state,
 nullif(trim(o.order_status),'') status,
 nullif(trim(o.order_purchase_timestamp),'')::timestamp purchased,
 nullif(trim(o.order_approved_at),'')::timestamp approved,
 nullif(trim(o.order_delivered_carrier_date),'')::timestamp carrier,
 nullif(trim(o.order_delivered_customer_date),'')::timestamp delivered,
 nullif(trim(o.order_estimated_delivery_date),'')::timestamp estimated
 FROM raw.orders o LEFT JOIN raw.customers c ON nullif(trim(o.customer_id),'')=nullif(trim(c.customer_id),'')
)
INSERT INTO core.fct_orders (order_id,source_customer_id,customer_unique_id,customer_zip_code_prefix,customer_city_source,customer_state_source,
 order_status,purchase_at,purchase_date,approved_at,delivered_carrier_at,delivered_customer_at,estimated_delivery_at,
 delivery_days,estimate_days,delay_days,is_late,has_chronology_anomaly)
SELECT order_id,source_customer_id,customer_unique_id,zip,city,state,status,purchased,purchased::date,approved,carrier,delivered,estimated,
 extract(epoch FROM delivered-purchased)/86400.0, estimated::date-purchased::date, delivered::date-estimated::date,
 CASE WHEN delivered IS NOT NULL AND estimated IS NOT NULL THEN delivered::date>estimated::date END,
 coalesce(approved<purchased,false) OR coalesce(carrier<purchased,false) OR coalesce(delivered<purchased,false)
 OR coalesce(delivered<carrier,false) OR coalesce(carrier<approved,false)
FROM typed;
