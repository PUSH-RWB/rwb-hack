-- Второй разрез Q9: весь период и все статусы, без ограничения по штату.
-- Среднее по записям платежей. Два исходных нулевых installments сохранены.
SELECT payment_type, count(*) AS payment_count,
 round(avg(payment_installments), 2) AS average_installments
FROM core.fct_payments
GROUP BY payment_type
ORDER BY payment_count DESC, payment_type NULLS LAST;
