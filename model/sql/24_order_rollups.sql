-- Таблица: core.fct_orders (обновление свёрток)
-- Гранулярность: один заказ
-- PK: order_id
-- FK: сохраняются ограничения fct_orders
-- Ожидаемые строки: 99441
-- Назначение: Независимые GROUP BY каждого факта; денежные свёртки берутся из core, не raw
-- Пропуски: Отсутствующая свёртка остаётся NULL; счётчики остаются 0
-- Каждое UPDATE использует строго одну строку на order_id. Независимые 1:N не соединяются.
WITH item_rollup AS (
 SELECT order_id,count(*)::int item_count,count(DISTINCT seller_id)::int seller_count,
 sum(price)::numeric(12,2) item_amount,sum(freight_value)::numeric(12,2) freight_amount,
 sum(price+freight_value)::numeric(12,2) order_amount
 FROM core.fct_order_items GROUP BY order_id
)
UPDATE core.fct_orders o SET item_count=a.item_count,seller_count=a.seller_count,
 item_amount=a.item_amount,freight_amount=a.freight_amount,order_amount=a.order_amount,has_items=true
FROM item_rollup a WHERE a.order_id=o.order_id;
WITH payment_rollup AS (
 SELECT order_id,count(*)::int payment_count,sum(payment_value)::numeric(12,2) payment_amount
 FROM core.fct_payments GROUP BY order_id
)
UPDATE core.fct_orders o SET payment_count=a.payment_count,payment_amount=a.payment_amount,has_payments=true
FROM payment_rollup a WHERE a.order_id=o.order_id;
WITH review_rollup AS (
 SELECT order_id,count(*)::int review_count,avg(review_score)::numeric(8,4) review_score_avg
 FROM core.fct_reviews GROUP BY order_id
)
UPDATE core.fct_orders o SET review_count=a.review_count,review_score_avg=a.review_score_avg,has_reviews=true
FROM review_rollup a WHERE a.order_id=o.order_id;
UPDATE core.fct_orders SET payment_delta=payment_amount-order_amount;
