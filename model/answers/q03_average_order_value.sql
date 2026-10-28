-- Среднее от заказов, не от позиций; одна позиция равна единице товара в этой выгрузке.
SELECT round(avg(o.order_amount),2) average_order_value,
 round(avg(o.item_count),4) average_lines_per_order,
 round(avg(o.item_count),4) average_units_per_order,count(*) order_count
FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status)
WHERE s.is_revenue;
