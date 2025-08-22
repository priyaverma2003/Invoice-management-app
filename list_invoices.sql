SELECT c.name,
    i.amount,
    COALESCE(SUM(p.amount), 0) AS total_paid,
    i.amount - COALESCE(SUM(p.amount), 0) AS outstanding,
    CASE
        WHEN i.due_date < DATEADD(DAY, -90, CURRENT_DATE)
        AND i.amount - COALESCE(SUM(p.amount), 0) > 0 THEN '90+ days overdue'
        WHEN i.due_date < DATEADD(DAY, -60, CURRENT_DATE)
        AND i.due_date >= DATEADD(DAY, -90, CURRENT_DATE)
        AND i.amount - COALESCE(SUM(p.amount), 0) > 0 THEN '61-90 days overdue'
        WHEN i.due_date < DATEADD(DAY, -30, CURRENT_DATE)
        AND i.due_date >= DATEADD(DAY, -60, CURRENT_DATE)
        AND i.amount - COALESCE(SUM(p.amount), 0) > 0 THEN '31-60 days overdue'
        WHEN i.due_date < CURRENT_DATE
        AND i.due_date >= DATEADD(DAY, -30, CURRENT_DATE)
        AND i.amount - COALESCE(SUM(p.amount), 0) > 0 THEN '0-30 days overdue'
        ELSE 'On Time'
    END AS aging_bucket
FROM invoices AS i
    LEFT JOIN payments AS p ON i.invoice_id = p.invoice_id
    JOIN customers AS c ON i.customer_id = c.customer_id
GROUP BY i.invoice_id
ORDER BY i.due_date DESC;