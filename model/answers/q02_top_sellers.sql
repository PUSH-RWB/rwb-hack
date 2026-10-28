-- Одна строка на продавца. Заказы не аддитивны между продавцами.
SELECT i.seller_id,s.city,s.state,count(DISTINCT i.order_id) order_count,count(*) units,
 sum(i.price)::numeric(12,2) revenue
FROM core.fct_order_items i JOIN core.dim_seller s USING(seller_id)
WHERE i.is_revenue
GROUP BY i.seller_id,s.city,s.state
ORDER BY revenue DESC,i.seller_id LIMIT 10;
