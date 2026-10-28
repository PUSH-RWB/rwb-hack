-- Одна строка: день оформления + фактическая цена продажи выбранного товара.
-- Продажи: is_revenue, как в Q1/Q2/Q5. Одна позиция источника = одна единица.
-- При равенстве числа цен выбирается минимальный product_id, чтобы ответ был воспроизводим.
WITH winner AS (
 SELECT product_id
 FROM core.fct_order_items
 WHERE is_revenue
 GROUP BY product_id
 ORDER BY count(DISTINCT price) DESC, product_id
 LIMIT 1
)
SELECT i.purchase_date AS sale_date, i.price, count(*) AS units
FROM core.fct_order_items i JOIN winner USING (product_id)
WHERE i.is_revenue
GROUP BY i.purchase_date, i.price
ORDER BY i.purchase_date, i.price;
