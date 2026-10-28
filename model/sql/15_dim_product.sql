-- Таблица: core.dim_product; постоянный источник версий: history.product_versions.
-- Гранулярность: версия карточки товара; PK product_key, естественный product_id не уникален.
-- FK факта: (product_key, product_id); интервалы [valid_from, valid_to).
-- Исходный снимок: 32951 версия. Пропуски/переводы сохранены по прежним правилам.
-- Mapping: product_name_lenght/product_description_lenght -> *_length только в модели.
-- Первая версия с -infinity — допущение исходного снимка, не восстановленная история.
CREATE SCHEMA IF NOT EXISTS history;
CREATE TABLE IF NOT EXISTS history.product_versions (
 product_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 product_id text NOT NULL, category_name_pt text NOT NULL, category_name_en text,
 category_name_display text NOT NULL, has_category boolean NOT NULL,
 product_name_length integer, product_description_length integer, product_photos_qty integer,
 product_weight_g integer, product_length_cm integer, product_height_cm integer, product_width_cm integer,
 product_volume_cm3 bigint,
 valid_from timestamp NOT NULL, valid_to timestamp,
 source_payload jsonb NOT NULL,
 UNIQUE(product_id, valid_from), UNIQUE(product_key, product_id),
 CHECK(valid_to IS NULL OR valid_to > valid_from)
);
CREATE UNIQUE INDEX IF NOT EXISTS product_versions_one_current
 ON history.product_versions(product_id) WHERE valid_to IS NULL;
CREATE TABLE IF NOT EXISTS history.product_publication (
 product_id text PRIMARY KEY, last_purchase_at timestamp NOT NULL
);
LOCK TABLE history.product_versions IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE product_snapshot ON COMMIT DROP AS
SELECT nullif(trim(p.product_id),'') AS product_id,
 coalesce(nullif(trim(p.product_category_name),''),'__unknown__') AS category_name_pt,
 nullif(trim(t.product_category_name_english),'') AS category_name_en,
 coalesce(nullif(trim(t.product_category_name_english),''),nullif(trim(p.product_category_name),''),'__unknown__') AS category_name_display,
 nullif(trim(p.product_category_name),'') IS NOT NULL AS has_category,
 nullif(trim(p.product_name_lenght),'')::int AS product_name_length,
 nullif(trim(p.product_description_lenght),'')::int AS product_description_length,
 nullif(trim(p.product_photos_qty),'')::int AS product_photos_qty,
 nullif(trim(p.product_weight_g),'')::int AS product_weight_g,
 nullif(trim(p.product_length_cm),'')::int AS product_length_cm,
 nullif(trim(p.product_height_cm),'')::int AS product_height_cm,
 nullif(trim(p.product_width_cm),'')::int AS product_width_cm,
 nullif(trim(p.product_length_cm),'')::bigint * nullif(trim(p.product_height_cm),'')::bigint * nullif(trim(p.product_width_cm),'')::bigint AS product_volume_cm3
FROM raw.products p LEFT JOIN raw.product_category_translation t
 ON nullif(trim(t.product_category_name),'')=nullif(trim(p.product_category_name),'');
CREATE TEMP TABLE product_change_clock ON COMMIT DROP AS
SELECT coalesce(nullif(current_setting('capibara.product_change_at',true),'')::timestamp,
 transaction_timestamp() AT TIME ZONE 'UTC') AS effective_at;
CREATE TEMP TABLE changed_products ON COMMIT DROP AS
SELECT s.*, h.product_key AS previous_key, h.valid_from AS previous_from
FROM product_snapshot s JOIN history.product_versions h USING(product_id)
WHERE h.valid_to IS NULL AND h.source_payload IS DISTINCT FROM to_jsonb(s);
DO $guard$
BEGIN
 IF EXISTS(SELECT 1 FROM changed_products c CROSS JOIN product_change_clock t
           WHERE t.effective_at <= c.previous_from) THEN
  RAISE EXCEPTION 'Product change must be later than the current version start';
 END IF;
 IF EXISTS(SELECT 1 FROM changed_products c JOIN history.product_publication p USING(product_id)
           CROSS JOIN product_change_clock t WHERE t.effective_at <= p.last_purchase_at) THEN
  RAISE EXCEPTION 'Backdated product change would reclassify published sales; use a later effective timestamp';
 END IF;
END $guard$;
UPDATE history.product_versions h SET valid_to=t.effective_at
FROM changed_products c CROSS JOIN product_change_clock t WHERE h.product_key=c.previous_key;
INSERT INTO history.product_versions (product_id, category_name_pt, category_name_en, category_name_display, has_category, product_name_length, product_description_length, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm, product_volume_cm3,valid_from,source_payload)
SELECT s.product_id, s.category_name_pt, s.category_name_en, s.category_name_display, s.has_category, s.product_name_length, s.product_description_length, s.product_photos_qty, s.product_weight_g, s.product_length_cm, s.product_height_cm, s.product_width_cm, s.product_volume_cm3, t.effective_at, to_jsonb(s)-'previous_key'-'previous_from'
FROM changed_products s CROSS JOIN product_change_clock t ORDER BY s.product_id;
INSERT INTO history.product_versions (product_id, category_name_pt, category_name_en, category_name_display, has_category, product_name_length, product_description_length, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm, product_volume_cm3,valid_from,source_payload)
SELECT s.product_id, s.category_name_pt, s.category_name_en, s.category_name_display, s.has_category, s.product_name_length, s.product_description_length, s.product_photos_qty, s.product_weight_g, s.product_length_cm, s.product_height_cm, s.product_width_cm, s.product_volume_cm3, '-infinity'::timestamp, to_jsonb(s)
FROM product_snapshot s
WHERE NOT EXISTS(SELECT 1 FROM history.product_versions h WHERE h.product_id=s.product_id)
ORDER BY s.product_id;
CREATE TABLE core.dim_product (
 product_key bigint PRIMARY KEY,
 product_id text NOT NULL, category_name_pt text NOT NULL, category_name_en text,
 category_name_display text NOT NULL, has_category boolean NOT NULL,
 product_name_length integer, product_description_length integer, product_photos_qty integer,
 product_weight_g integer, product_length_cm integer, product_height_cm integer, product_width_cm integer,
 product_volume_cm3 bigint,
 valid_from timestamp NOT NULL, valid_to timestamp, is_current boolean NOT NULL,
 UNIQUE(product_key,product_id), UNIQUE(product_id,valid_from),
 CHECK(valid_to IS NULL OR valid_to>valid_from), CHECK(is_current=(valid_to IS NULL))
);
INSERT INTO core.dim_product
SELECT product_key,product_id, category_name_pt, category_name_en, category_name_display, has_category, product_name_length, product_description_length, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm, product_volume_cm3,valid_from,valid_to,valid_to IS NULL
FROM history.product_versions ORDER BY product_key;
CREATE UNIQUE INDEX dim_product_one_current ON core.dim_product(product_id) WHERE is_current;
