-- Таблица: core.fct_payments
-- Гранулярность: одна исходная запись оплаты
-- PK: (order_id, payment_sequential)
-- FK: order_id -> fct_orders
-- Ожидаемые строки: 103886
-- Назначение: Платежи отдельно от стоимости товаров; installments не множитель payment_value
-- Пропуски: Нулевые платежи и installments сохраняются
DROP TABLE IF EXISTS core.fct_payments CASCADE;
CREATE TABLE core.fct_payments (
 order_id text NOT NULL REFERENCES core.fct_orders, payment_sequential integer NOT NULL CHECK(payment_sequential>0),
 payment_type text, payment_installments integer CHECK(payment_installments>=0),
 payment_value numeric(12,2) NOT NULL CHECK(payment_value>=0),
 PRIMARY KEY(order_id,payment_sequential)
);
INSERT INTO core.fct_payments
SELECT nullif(trim(order_id),''),nullif(trim(payment_sequential),'')::int,nullif(trim(payment_type),''),
 nullif(trim(payment_installments),'')::int,nullif(trim(payment_value),'')::numeric(12,2)
FROM raw.order_payments;
