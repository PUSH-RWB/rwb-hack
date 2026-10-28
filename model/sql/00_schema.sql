-- Таблица: core, mart
-- Гранулярность: схемы
-- PK: не применимо
-- FK: не применимо
-- Ожидаемые строки: не применимо
-- Назначение: Атомарная пересборка только нашей модели
-- Пропуски: raw не изменяется
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET LOCAL client_min_messages = warning;
SELECT set_config('capibara.product_change_at', :'product_change_at', true) AS product_change_clock \gset
DROP SCHEMA IF EXISTS mart CASCADE;
DROP SCHEMA IF EXISTS core CASCADE;
CREATE SCHEMA core;
CREATE SCHEMA mart;
SET LOCAL search_path = core, public;
SET LOCAL TIME ZONE 'UTC';
