-- Таблица: core.dim_product
-- Гранулярность: одна карточка товара
-- PK: product_id
-- FK: нет
-- Ожидаемые строки: 32951
-- Назначение: Каталог, исходная категория и необязательный перевод
-- Пропуски: Пустая категория -> __unknown__; отсутствующий перевод не объединяет категории
-- Mapping: product_name_lenght -> product_name_length;
-- product_description_lenght -> product_description_length. Raw не меняется.
DROP TABLE IF EXISTS core.dim_product CASCADE;
CREATE TABLE core.dim_product (
 product_id text PRIMARY KEY, category_name_pt text NOT NULL, category_name_en text,
 category_name_display text NOT NULL, has_category boolean NOT NULL,
 product_name_length integer, product_description_length integer, product_photos_qty integer,
 product_weight_g integer, product_length_cm integer, product_height_cm integer, product_width_cm integer,
 product_volume_cm3 bigint
);
INSERT INTO core.dim_product
SELECT nullif(trim(p.product_id),''),coalesce(nullif(trim(p.product_category_name),''),'__unknown__'),
 nullif(trim(t.product_category_name_english),''),
 coalesce(nullif(trim(t.product_category_name_english),''),nullif(trim(p.product_category_name),''),'__unknown__'),
 nullif(trim(p.product_category_name),'') IS NOT NULL,
 nullif(trim(p.product_name_lenght),'')::int,nullif(trim(p.product_description_lenght),'')::int,
 nullif(trim(p.product_photos_qty),'')::int,nullif(trim(p.product_weight_g),'')::int,
 nullif(trim(p.product_length_cm),'')::int,nullif(trim(p.product_height_cm),'')::int,nullif(trim(p.product_width_cm),'')::int,
 nullif(trim(p.product_length_cm),'')::bigint * nullif(trim(p.product_height_cm),'')::bigint * nullif(trim(p.product_width_cm),'')::bigint
FROM raw.products p LEFT JOIN raw.product_category_translation t
 ON nullif(trim(t.product_category_name),'')=nullif(trim(p.product_category_name),'');
