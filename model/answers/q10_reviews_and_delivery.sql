-- Одна строка на оценку 1..5; заказ один раз внутри каждой оценки.
-- Заказ с разными оценками может входить в несколько групп; их числа не складываются.
-- Все статусы с фактической датой вручения, как в Q7. Это связь, не доказательство причины.
WITH ratings AS (
 SELECT DISTINCT order_id, review_score FROM core.fct_reviews
), rated_orders AS (
 SELECT r.order_id, r.review_score, o.delivery_days, o.is_late
 FROM ratings r JOIN core.fct_orders o USING (order_id)
 WHERE o.delivered_customer_at IS NOT NULL
)
SELECT scores.review_score, count(r.order_id) AS order_count,
 round(avg(r.delivery_days), 2) AS average_delivery_days,
 round(100.0 * count(r.order_id) FILTER (WHERE r.is_late) / nullif(count(r.is_late), 0), 2) AS late_percentage
FROM generate_series(1, 5) scores(review_score)
LEFT JOIN rated_orders r USING (review_score)
GROUP BY scores.review_score
ORDER BY scores.review_score;
