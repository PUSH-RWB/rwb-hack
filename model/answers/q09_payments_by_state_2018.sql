-- Одна строка на исходный штат покупателя; одна запись оплаты = один платёж.
-- Даты платежа нет: 2018 определяется по дате оформления заказа. Все статусы.
-- installment — число частей, payment_value не умножается на installment.
SELECT o.customer_state_source AS state, count(*) AS payment_count,
 sum(p.payment_value)::numeric(14,2) AS payment_amount,
 round(avg(p.payment_installments), 2) AS average_installments
FROM core.fct_payments p JOIN core.fct_orders o USING (order_id)
WHERE o.purchase_date >= DATE '2018-01-01' AND o.purchase_date < DATE '2019-01-01'
GROUP BY o.customer_state_source
ORDER BY payment_count DESC, state;
