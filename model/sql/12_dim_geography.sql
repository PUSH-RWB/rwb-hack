-- Таблица: core.dim_geography
-- Гранулярность: один исходный почтовый префикс
-- PK: zip_code_prefix
-- FK: нет
-- Ожидаемые строки: 15080
-- Назначение: Модальный город и модальный штат этого города, детерминированные ничьи
-- Пропуски: Пустые строки -> NULL; исходные адреса сохраняются отдельно в заказах и продавцах
DROP TABLE IF EXISTS core.dim_geography CASCADE;
CREATE TABLE core.dim_geography (
 zip_code_prefix text PRIMARY KEY, city text, state text, city_variant_count integer NOT NULL,
 state_variant_count integer NOT NULL, source_row_count integer NOT NULL
);
WITH addresses AS (
 SELECT nullif(trim(customer_zip_code_prefix),'') zip, nullif(trim(customer_city),'') city, nullif(trim(customer_state),'') state FROM raw.customers
 UNION ALL
 SELECT nullif(trim(seller_zip_code_prefix),''), nullif(trim(seller_city),''), nullif(trim(seller_state),'') FROM raw.sellers
), variants AS (
 SELECT zip, count(DISTINCT city)::int cities, count(DISTINCT state)::int states, count(*)::int rows FROM addresses GROUP BY zip
) , city_modes AS (
 SELECT zip,city,row_number() OVER (PARTITION BY zip ORDER BY count(*) DESC,city COLLATE "C" NULLS LAST) city_rank
 FROM addresses GROUP BY zip,city
), modes AS (
 SELECT a.zip,a.city,a.state,row_number() OVER (PARTITION BY a.zip ORDER BY count(*) DESC,a.state COLLATE "C" NULLS LAST) rank
 FROM addresses a JOIN city_modes c ON a.zip=c.zip AND a.city IS NOT DISTINCT FROM c.city AND c.city_rank=1
 GROUP BY a.zip,a.city,a.state
)
INSERT INTO core.dim_geography
SELECT m.zip,m.city,m.state,v.cities,v.states,v.rows FROM modes m JOIN variants v USING(zip) WHERE m.rank=1;
