-- Таблица: core.dim_seller
-- Гранулярность: один продавец
-- PK: seller_id
-- FK: zip_code_prefix -> dim_geography
-- Ожидаемые строки: 3095
-- Назначение: Продавцы без денежных агрегатов; сохранён исходный город и штат
-- Пропуски: Пустые строки -> NULL
DROP TABLE IF EXISTS core.dim_seller CASCADE;
CREATE TABLE core.dim_seller (
 seller_id text PRIMARY KEY, zip_code_prefix text REFERENCES core.dim_geography,
 city text, state text
);
INSERT INTO core.dim_seller
SELECT nullif(trim(seller_id),''),nullif(trim(seller_zip_code_prefix),''),nullif(trim(seller_city),''),nullif(trim(seller_state),'') FROM raw.sellers;
