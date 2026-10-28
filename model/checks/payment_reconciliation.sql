-- Разные базы сверки не смешиваются; неизвестный платёж остаётся NULL.
SELECT count(*) delivered_orders,sum(o.order_amount) order_amount,sum(o.payment_amount) payment_amount,
 sum(o.order_amount)-sum(o.payment_amount) total_amount_gap,
 sum(o.order_amount-o.payment_amount) comparable_order_gap,
 count(*) FILTER(WHERE NOT o.has_payments) missing_payment_orders,
 sum(o.order_amount) FILTER(WHERE NOT o.has_payments) missing_payment_order_amount
FROM core.fct_orders o JOIN core.dim_order_status s USING(order_status) WHERE s.is_revenue;
