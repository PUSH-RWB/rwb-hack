-- Таблица: core.dim_date
-- Гранулярность: один календарный день
-- PK: date_key
-- FK: нет
-- Диапазон: полные годы min/max оформления плюс год с каждой стороны; исходный снимок 1826 дней
-- Назначение: Полный календарь, включая дни без заказов
-- Пропуски: ключи не пустые
DROP TABLE IF EXISTS core.dim_date CASCADE;
CREATE TABLE core.dim_date (
 date_key date PRIMARY KEY, year smallint NOT NULL, quarter smallint NOT NULL,
 month smallint NOT NULL, month_key text NOT NULL, day_of_month smallint NOT NULL,
 day_of_week smallint NOT NULL, is_weekend boolean NOT NULL
);
INSERT INTO core.dim_date
SELECT d::date, extract(year FROM d), extract(quarter FROM d), extract(month FROM d),
 to_char(d,'YYYY-MM'), extract(day FROM d), extract(isodow FROM d), extract(isodow FROM d) IN (6,7)
FROM (SELECT date_trunc('year',min(nullif(trim(order_purchase_timestamp),'')::timestamp))-interval '1 year' AS first_day,
 date_trunc('year',max(nullif(trim(order_purchase_timestamp),'')::timestamp))+interval '2 years'-interval '1 day' AS last_day
 FROM raw.orders) bounds
CROSS JOIN LATERAL generate_series(bounds.first_day,bounds.last_day,interval '1 day') d;
