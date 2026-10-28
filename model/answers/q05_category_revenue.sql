-- Исходный код категории является идентификатором; отсутствие перевода не объединяет категории.
WITH categories AS (
 SELECT p.category_name_pt,p.category_name_en,p.category_name_display,sum(i.price)::numeric(12,2) revenue
 FROM core.fct_order_items i JOIN core.dim_product p USING(product_key)
 WHERE i.is_revenue
 GROUP BY p.category_name_pt,p.category_name_en,p.category_name_display
)
SELECT *,round(100.0*revenue/nullif(sum(revenue) OVER (),0),2) revenue_share_percentage
FROM categories ORDER BY revenue DESC,category_name_pt;
