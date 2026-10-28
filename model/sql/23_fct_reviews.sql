-- Таблица: core.fct_reviews
-- Гранулярность: одна исходная запись отзыва о заказе
-- PK: (order_id, review_id)
-- FK: order_id -> fct_orders
-- Ожидаемые строки: 99224
-- Назначение: Сохраняет все отзывы; review_id глобально не уникален
-- Пропуски: Текст может быть NULL; даты не исправляются
DROP TABLE IF EXISTS core.fct_reviews CASCADE;
CREATE TABLE core.fct_reviews (
 order_id text NOT NULL REFERENCES core.fct_orders, review_id text NOT NULL,
 review_score smallint NOT NULL CHECK(review_score BETWEEN 1 AND 5),
 review_comment_title text, review_comment_message text,
 review_creation_at timestamp, review_answer_at timestamp,
 PRIMARY KEY(order_id,review_id)
);
INSERT INTO core.fct_reviews
SELECT nullif(trim(order_id),''),nullif(trim(review_id),''),nullif(trim(review_score),'')::smallint,
 nullif(trim(review_comment_title),''),nullif(trim(review_comment_message),''),
 nullif(trim(review_creation_date),'')::timestamp,nullif(trim(review_answer_timestamp),'')::timestamp
FROM raw.order_reviews;
