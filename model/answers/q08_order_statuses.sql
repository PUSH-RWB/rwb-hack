-- Распределение текущих статусов, не история переходов между ними.
-- Одна строка на статус; сохраняются статусы без заказов и заказы без позиций.
SELECT s.order_status, count(o.order_id) AS order_count,
 round(100.0 * count(o.order_id) / nullif(sum(count(o.order_id)) OVER (), 0), 2) AS share_percentage,
 count(o.order_id) FILTER (WHERE NOT o.has_items) AS orders_without_items
FROM core.dim_order_status s
LEFT JOIN core.fct_orders o USING (order_status)
GROUP BY s.order_status
ORDER BY order_count DESC, s.order_status;
