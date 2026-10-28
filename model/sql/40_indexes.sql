-- Таблица: core (индексы и статистика)
-- Гранулярность: не применимо
-- PK: уже созданы PK
-- FK: поддерживаются индексы FK
-- Ожидаемые строки: не применимо
-- Назначение: Фильтрация по дате, статусу, покупателю, продавцу и товару
-- Пропуски: не применимо
CREATE INDEX orders_purchase_idx ON core.fct_orders(purchase_date);
CREATE INDEX orders_customer_idx ON core.fct_orders(customer_unique_id);
CREATE INDEX orders_status_idx ON core.fct_orders(order_status);
CREATE INDEX orders_geography_idx ON core.fct_orders(customer_zip_code_prefix);
CREATE INDEX items_seller_date_idx ON core.fct_order_items(seller_id,purchase_date);
CREATE INDEX items_product_version_idx ON core.fct_order_items(product_key);
CREATE INDEX items_product_idx ON core.fct_order_items(product_id);
CREATE INDEX items_customer_idx ON core.fct_order_items(customer_unique_id);
CREATE INDEX items_date_idx ON core.fct_order_items(purchase_date);
CREATE INDEX seller_geography_idx ON core.dim_seller(zip_code_prefix);
CREATE INDEX product_category_idx ON core.dim_product(category_name_pt);
ANALYZE core.dim_date; ANALYZE core.dim_order_status; ANALYZE core.dim_geography;
ANALYZE core.dim_customer; ANALYZE core.dim_seller; ANALYZE core.dim_product;
ANALYZE core.fct_orders; ANALYZE core.fct_order_items; ANALYZE core.fct_payments; ANALYZE core.fct_reviews;
