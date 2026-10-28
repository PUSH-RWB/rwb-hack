-- Таблица: core, mart
-- Гранулярность: схемы
-- PK: не применимо
-- FK: не применимо
-- Ожидаемые строки: не применимо
-- Назначение: Атомарная пересборка только нашей модели
-- Пропуски: raw не изменяется
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
SET LOCAL client_min_messages = warning;
DROP SCHEMA IF EXISTS mart CASCADE;
DROP SCHEMA IF EXISTS core CASCADE;
CREATE SCHEMA core;
CREATE SCHEMA mart;
SET LOCAL search_path = core, public;
SET LOCAL TIME ZONE 'UTC';
