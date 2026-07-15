-- ============================================================
-- UPI Fraud Analysis — SQL Queries (PostgreSQL)
-- ============================================================

-- QUERY 1: Fraud rate by time of day — prove night is dangerous
SELECT
    time_of_day,
    COUNT(*)                                                  AS total_transactions,
    SUM(is_fraud)                                             AS fraud_count,
    ROUND(SUM(is_fraud)::numeric / COUNT(*) * 100, 3)         AS fraud_rate_pct,
    ROUND(AVG(amount), 2)                                     AS avg_transaction_amount,
    ROUND(AVG(CASE WHEN is_fraud = 1 THEN amount END), 2)     AS avg_fraud_amount,
    RANK() OVER (ORDER BY SUM(is_fraud)::numeric / COUNT(*) DESC) AS risk_rank
FROM upi_transactions
GROUP BY time_of_day
ORDER BY fraud_rate_pct DESC;

-- Expected: Late Night ~19-20%, Morning ~0.8%, Afternoon ~1.2%


-- ============================================================
-- QUERY 2: New receiver fraud risk — calculate odds ratio
WITH receiver_stats AS (
    SELECT
        is_new_receiver,
        COUNT(*)                                               AS total,
        SUM(is_fraud)                                         AS fraud_count,
        ROUND(SUM(is_fraud)::numeric / COUNT(*) * 100, 3)     AS fraud_rate_pct
    FROM upi_transactions
    GROUP BY is_new_receiver
)
SELECT
    CASE WHEN is_new_receiver = 1 THEN 'New Receiver' ELSE 'Known Receiver' END AS receiver_type,
    total,
    fraud_count,
    fraud_rate_pct,
    ROUND(
        fraud_rate_pct / NULLIF(MIN(fraud_rate_pct) OVER (), 0), 2
    ) AS odds_vs_known_receiver,
    ROUND(
        (fraud_rate_pct / NULLIF(100 - fraud_rate_pct, 0)) /
        NULLIF(MIN(fraud_rate_pct) OVER () / NULLIF(100 - MIN(fraud_rate_pct) OVER (), 0), 0)
    , 2) AS odds_ratio
FROM receiver_stats
ORDER BY is_new_receiver DESC;


-- ============================================================
-- QUERY 3: Amount clustering — find suspicious amount bands using CASE WHEN
SELECT
    CASE
        WHEN amount = 4999                        THEN 'Exactly ₹4,999 (limit dodge)'
        WHEN amount = 9999                        THEN 'Exactly ₹9,999 (limit dodge)'
        WHEN amount BETWEEN 4900 AND 4998         THEN '₹4,900-4,998 (near limit)'
        WHEN amount BETWEEN 5001 AND 5100         THEN '₹5,001-5,100 (just over)'
        WHEN amount BETWEEN 9900 AND 9998         THEN '₹9,900-9,998 (near limit)'
        WHEN amount BETWEEN 10001 AND 10100       THEN '₹10,001-10,100 (just over)'
        WHEN amount < 500                         THEN 'Under ₹500 (micro)'
        WHEN amount BETWEEN 500 AND 2000          THEN '₹500-2,000 (low)'
        WHEN amount BETWEEN 2001 AND 10000        THEN '₹2,001-10,000 (medium)'
        WHEN amount BETWEEN 10001 AND 25000       THEN '₹10,001-25,000 (high)'
        ELSE 'Over ₹25,000 (very high)'
    END                                          AS amount_band,
    COUNT(*)                                     AS total_transactions,
    SUM(is_fraud)                                AS fraud_count,
    ROUND(SUM(is_fraud)::numeric / COUNT(*) * 100, 3) AS fraud_rate_pct,
    ROUND(AVG(amount), 2)                        AS avg_amount
FROM upi_transactions
GROUP BY amount_band
ORDER BY fraud_rate_pct DESC;


-- ============================================================
-- QUERY 4: Month-wise fraud trend — find seasonal spikes
SELECT
    TO_CHAR(timestamp::timestamp, 'YYYY-MM')        AS year_month,
    EXTRACT(MONTH FROM timestamp::timestamp)        AS month_num,
    EXTRACT(YEAR FROM timestamp::timestamp)         AS year,
    COUNT(*)                                        AS total_transactions,
    SUM(is_fraud)                                   AS fraud_count,
    ROUND(SUM(is_fraud)::numeric / COUNT(*) * 100, 3) AS fraud_rate_pct,
    LAG(SUM(is_fraud)::numeric / COUNT(*)) OVER
        (ORDER BY TO_CHAR(timestamp::timestamp, 'YYYY-MM')) AS prev_month_rate,
    ROUND(
        (SUM(is_fraud)::numeric / COUNT(*) -
         LAG(SUM(is_fraud)::numeric / COUNT(*)) OVER
             (ORDER BY TO_CHAR(timestamp::timestamp, 'YYYY-MM'))) /
        NULLIF(LAG(SUM(is_fraud)::numeric / COUNT(*)) OVER
               (ORDER BY TO_CHAR(timestamp::timestamp, 'YYYY-MM')), 0) * 100, 2
    )                                               AS mom_change_pct
FROM upi_transactions
GROUP BY year_month, month_num, year
ORDER BY year_month;


-- ============================================================
-- QUERY 5: UPI app fraud comparison — which app has most fraud?
SELECT
    upi_app,
    COUNT(*)                                                   AS total_transactions,
    SUM(is_fraud)                                              AS fraud_count,
    ROUND(SUM(is_fraud)::numeric / COUNT(*) * 100, 3)          AS fraud_rate_pct,
    ROUND(AVG(CASE WHEN is_fraud = 1 THEN amount END), 2)      AS avg_fraud_amount,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END), 2) AS total_fraud_amount,
    RANK() OVER (ORDER BY SUM(is_fraud)::numeric / COUNT(*) DESC) AS fraud_risk_rank
FROM upi_transactions
GROUP BY upi_app
ORDER BY fraud_rate_pct DESC;


-- ============================================================
-- QUERY 6: City pair analysis — which sender→receiver city combos are risky?
SELECT
    sender_city,
    receiver_city,
    COUNT(*)                                                   AS transactions,
    SUM(is_fraud)                                              AS fraud_count,
    ROUND(SUM(is_fraud)::numeric / COUNT(*) * 100, 3)          AS fraud_rate_pct,
    ROUND(AVG(CASE WHEN is_fraud = 1 THEN amount END), 2)      AS avg_fraud_amount
FROM upi_transactions
WHERE sender_city != receiver_city    -- cross-city transactions are riskier
GROUP BY sender_city, receiver_city
HAVING COUNT(*) >= 20
ORDER BY fraud_rate_pct DESC
LIMIT 20;


-- ============================================================
-- QUERY 7: Fraud type distribution with ROLLUP
SELECT
    COALESCE(fraud_type, 'NOT FRAUD')  AS fraud_category,
    transaction_type,
    COUNT(*)                           AS count,
    ROUND(AVG(amount), 2)              AS avg_amount,
    ROUND(SUM(amount), 2)              AS total_amount
FROM upi_transactions
WHERE is_fraud = 1 OR fraud_type IS NULL
GROUP BY ROLLUP(fraud_type, transaction_type)
ORDER BY fraud_type NULLS LAST, transaction_type;


-- ============================================================
-- QUERY 8: Transaction failure rate before fraud — find retry pattern
WITH failed_transactions AS (
    SELECT
        sender_id,
        timestamp::timestamp AS txn_time,
        transaction_status,
        is_fraud,
        amount,
        LEAD(transaction_status) OVER (PARTITION BY sender_id ORDER BY timestamp) AS next_status,
        LEAD(is_fraud)          OVER (PARTITION BY sender_id ORDER BY timestamp) AS next_is_fraud,
        LEAD(timestamp)         OVER (PARTITION BY sender_id ORDER BY timestamp) AS next_time
    FROM upi_transactions
)
SELECT
    CASE
        WHEN transaction_status = 'Failed'
             AND next_status = 'Success'
             AND EXTRACT(EPOCH FROM (next_time::timestamp - txn_time)) < 300
        THEN 'Failed→Success (within 5min)'
        WHEN transaction_status = 'Failed' AND next_is_fraud = 1 THEN 'Failed→Fraud'
        WHEN transaction_status = 'Success' AND is_fraud = 1     THEN 'Direct Fraud Success'
        ELSE 'Normal'
    END                                              AS pattern,
    COUNT(*)                                         AS occurrences,
    SUM(CASE WHEN is_fraud = 1 OR next_is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_in_pattern,
    ROUND(
        SUM(CASE WHEN next_is_fraud = 1 THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 3
    )                                                AS leads_to_fraud_pct
FROM failed_transactions
GROUP BY pattern
ORDER BY leads_to_fraud_pct DESC;


-- ============================================================
-- QUERY 9: Rolling 7-day fraud rate using window functions
WITH daily_stats AS (
    SELECT
        DATE(timestamp::timestamp)            AS txn_date,
        COUNT(*)                              AS daily_transactions,
        SUM(is_fraud)                         AS daily_frauds
    FROM upi_transactions
    GROUP BY txn_date
)
SELECT
    txn_date,
    daily_transactions,
    daily_frauds,
    ROUND(daily_frauds::numeric / NULLIF(daily_transactions, 0) * 100, 3) AS daily_fraud_rate,
    SUM(daily_transactions) OVER (
        ORDER BY txn_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                         AS rolling_7d_transactions,
    SUM(daily_frauds) OVER (
        ORDER BY txn_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                         AS rolling_7d_frauds,
    ROUND(
        SUM(daily_frauds) OVER (
            ORDER BY txn_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric /
        NULLIF(SUM(daily_transactions) OVER (
            ORDER BY txn_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 0) * 100, 3
    )                                         AS rolling_7d_fraud_rate_pct
FROM daily_stats
ORDER BY txn_date;
