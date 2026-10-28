-- Таблица: core.dim_order_status
-- Гранулярность: один наблюдаемый статус
-- PK: order_status
-- FK: нет
-- Исходный снимок: 8; новые статусы добавляются с консервативными флагами
-- Назначение: Единственное место определения статусных флагов
-- Пропуски: пустой статус недопустим; неизвестный непустой статус принимается и помечается проверкой
DROP TABLE IF EXISTS core.dim_order_status CASCADE;
CREATE TABLE core.dim_order_status (
 order_status text PRIMARY KEY, is_revenue boolean NOT NULL, is_terminal boolean NOT NULL,
 is_canceled boolean NOT NULL, is_shipped_out boolean NOT NULL
);
-- Флаги описывают статус, не заменяют фактические даты и историю событий.
INSERT INTO core.dim_order_status VALUES
 ('delivered',true,true,false,true), ('shipped',false,false,false,true),
 ('canceled',false,true,true,false), ('unavailable',false,true,false,false),
 ('invoiced',false,false,false,false), ('processing',false,false,false,false),
 ('created',false,false,false,false), ('approved',false,false,false,false);

-- Новые значения требуют бизнес-классификации; автоматически выручкой не становятся.
INSERT INTO core.dim_order_status
SELECT DISTINCT nullif(trim(o.order_status),''),false,false,false,false
FROM raw.orders o
WHERE nullif(trim(o.order_status),'') IS NOT NULL
 AND NOT EXISTS(SELECT 1 FROM core.dim_order_status s WHERE s.order_status=nullif(trim(o.order_status),''));
