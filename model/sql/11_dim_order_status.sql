-- Таблица: core.dim_order_status
-- Гранулярность: один наблюдаемый статус
-- PK: order_status
-- FK: нет
-- Ожидаемые строки: 8
-- Назначение: Единственное место определения статусных флагов
-- Пропуски: неизвестный статус отклоняется FK
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
