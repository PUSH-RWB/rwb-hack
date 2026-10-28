-- Одна строка на штат покупателя, не менее 500 заказов с датой вручения.
-- Все текущие статусы: анализ фактической доставки, а не признания выручки.
-- Срок: прошедшие сутки от оформления до вручения. Просрочка: календарные дни.
-- NULL is_late не попадает в знаменатель доли; отсутствующая дата не заменяется нулём.
SELECT customer_state_source AS state, count(*) AS order_count,
 round(avg(delivery_days), 2) AS average_delivery_days,
 round(100.0 * count(*) FILTER (WHERE is_late) / nullif(count(is_late), 0), 2) AS late_percentage
FROM core.fct_orders
WHERE delivered_customer_at IS NOT NULL
GROUP BY customer_state_source
HAVING count(*) >= 500
ORDER BY average_delivery_days DESC, state NULLS LAST;
