-- Таблица: core.dim_customer
-- Гранулярность: один человек
-- PK: customer_unique_id
-- FK: нет
-- Ожидаемые строки: 96096
-- Назначение: Устойчивая идентичность покупателя; адрес принадлежит заказу
-- Пропуски: customer_id не хранится в измерении; пустой ключ запрещён
DROP TABLE IF EXISTS core.dim_customer CASCADE;
CREATE TABLE core.dim_customer (customer_unique_id text PRIMARY KEY);
INSERT INTO core.dim_customer SELECT DISTINCT nullif(trim(customer_unique_id),'') FROM raw.customers;
