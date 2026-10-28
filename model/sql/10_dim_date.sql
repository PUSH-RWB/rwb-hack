-- Таблица: core.dim_date
-- Гранулярность: один календарный день
-- PK: date_key
-- FK: нет
-- Ожидаемые строки: 1096
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
FROM generate_series(timestamp '2016-01-01',timestamp '2018-12-31',interval '1 day') d;
