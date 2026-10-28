-- Таблица: mart.order_metrics
-- Гранулярность: один заказ
-- PK: логический order_id из core.fct_orders
-- FK: только core
-- Ожидаемые строки: 99441
-- Назначение: Удобное представление поверх детали, не таблица под вопрос
-- Пропуски: Все NULL сохраняются
DROP VIEW IF EXISTS mart.order_metrics CASCADE;
CREATE VIEW mart.order_metrics AS
SELECT o.*,s.is_revenue,s.is_terminal,s.is_canceled,s.is_shipped_out,d.month_key
FROM core.fct_orders o
LEFT JOIN core.dim_order_status s USING(order_status)
LEFT JOIN core.dim_date d ON d.date_key=o.purchase_date;
