-- Таблица: core.fct_order_items
-- Гранулярность: одна единица товара продавца в заказе
-- PK: (order_id, order_item_id)
-- FK: order_id, product_id, seller_id, purchase_date, order_status, customer_unique_id -> core
-- Ожидаемые строки: 112650
-- Назначение: Канонический источник стоимости товаров и доставки; атрибуты заказа денормализованы
-- Пропуски: Пустые строки -> NULL; цены не заменяются нулями
DROP TABLE IF EXISTS core.fct_order_items CASCADE;
CREATE TABLE core.fct_order_items (
 order_id text NOT NULL REFERENCES core.fct_orders,
 order_item_id integer NOT NULL CHECK(order_item_id>0),
 product_id text NOT NULL REFERENCES core.dim_product, seller_id text NOT NULL REFERENCES core.dim_seller,
 shipping_limit_at timestamp, price numeric(12,2) NOT NULL CHECK(price>=0), freight_value numeric(12,2) NOT NULL CHECK(freight_value>=0),
 purchase_date date NOT NULL REFERENCES core.dim_date, order_status text NOT NULL REFERENCES core.dim_order_status,
 is_revenue boolean NOT NULL, customer_unique_id text NOT NULL REFERENCES core.dim_customer,
 PRIMARY KEY(order_id,order_item_id)
);
INSERT INTO core.fct_order_items
SELECT nullif(trim(i.order_id),''),nullif(trim(i.order_item_id),'')::int,
 nullif(trim(i.product_id),''),nullif(trim(i.seller_id),''),nullif(trim(i.shipping_limit_date),'')::timestamp,
 nullif(trim(i.price),'')::numeric(12,2),nullif(trim(i.freight_value),'')::numeric(12,2),
 o.purchase_date,o.order_status,s.is_revenue,o.customer_unique_id
FROM raw.order_items i LEFT JOIN core.fct_orders o ON o.order_id=nullif(trim(i.order_id),'')
LEFT JOIN core.dim_order_status s ON s.order_status=o.order_status;
