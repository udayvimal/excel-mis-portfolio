-- ============================================================
-- Indian Salary Gap Analysis — SQL Queries (PostgreSQL)
-- ============================================================

-- QUERY 1: Gender pay gap by role — find the exact % difference
SELECT
    job_role,
    gender,
    COUNT(*)                              AS employees,
    ROUND(AVG(total_ctc_lpa), 2)          AS avg_ctc_lpa,
    ROUND(MEDIAN(total_ctc_lpa)::numeric, 2) AS median_ctc_lpa,
    ROUND(MIN(total_ctc_lpa), 2)          AS min_ctc,
    ROUND(MAX(total_ctc_lpa), 2)          AS max_ctc
FROM india_salaries
WHERE gender IN ('Male', 'Female')
GROUP BY job_role, gender

UNION ALL

SELECT
    job_role,
    'GAP_%' AS gender,
    NULL,
    ROUND(
        (MAX(CASE WHEN gender = 'Male' THEN avg_ctc END) -
         MAX(CASE WHEN gender = 'Female' THEN avg_ctc END)) /
        NULLIF(MAX(CASE WHEN gender = 'Male' THEN avg_ctc END), 0) * 100, 2
    ) AS pay_gap_pct,
    NULL, NULL, NULL
FROM (
    SELECT job_role, gender, AVG(total_ctc_lpa) AS avg_ctc
    FROM india_salaries
    WHERE gender IN ('Male', 'Female')
    GROUP BY job_role, gender
) sub
GROUP BY job_role
ORDER BY job_role, gender;

-- Simplified version (easier to read):
SELECT
    job_role,
    ROUND(AVG(CASE WHEN gender = 'Male'   THEN total_ctc_lpa END), 2) AS male_avg_ctc,
    ROUND(AVG(CASE WHEN gender = 'Female' THEN total_ctc_lpa END), 2) AS female_avg_ctc,
    ROUND(
        (AVG(CASE WHEN gender = 'Male' THEN total_ctc_lpa END) -
         AVG(CASE WHEN gender = 'Female' THEN total_ctc_lpa END)) /
        NULLIF(AVG(CASE WHEN gender = 'Male' THEN total_ctc_lpa END), 0) * 100, 2
    ) AS gender_pay_gap_pct
FROM india_salaries
WHERE gender IN ('Male', 'Female')
GROUP BY job_role
ORDER BY gender_pay_gap_pct DESC;


-- ============================================================
-- QUERY 2: City-wise median salary heatmap data
SELECT
    city,
    job_role,
    COUNT(*)                                              AS employees,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)          AS median_ctc_lpa,
    ROUND(AVG(total_ctc_lpa), 2)                         AS avg_ctc_lpa,
    ROUND(STDDEV(total_ctc_lpa), 2)                      AS stddev_ctc
FROM india_salaries
GROUP BY city, job_role
ORDER BY city, median_ctc_lpa DESC;


-- ============================================================
-- QUERY 3: Experience vs salary curve — bucket experience into bands
SELECT
    CASE
        WHEN experience_years = 0          THEN '0 yrs (Fresher)'
        WHEN experience_years BETWEEN 1 AND 2 THEN '1-2 yrs'
        WHEN experience_years BETWEEN 3 AND 5 THEN '3-5 yrs'
        WHEN experience_years BETWEEN 6 AND 10 THEN '6-10 yrs'
        WHEN experience_years BETWEEN 11 AND 15 THEN '11-15 yrs'
        ELSE '15+ yrs (Senior)'
    END                                              AS experience_band,
    job_role,
    COUNT(*)                                         AS employees,
    ROUND(AVG(base_salary_lpa), 2)                   AS avg_base_lpa,
    ROUND(AVG(total_ctc_lpa), 2)                     AS avg_ctc_lpa,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)      AS median_ctc_lpa,
    ROUND(AVG(bonus_lpa), 2)                         AS avg_bonus_lpa
FROM india_salaries
GROUP BY experience_band, job_role
ORDER BY MIN(experience_years), job_role;


-- ============================================================
-- QUERY 4: Company type salary comparison with RANK() window function
SELECT
    company_type,
    job_role,
    COUNT(*)                                          AS employees,
    ROUND(AVG(total_ctc_lpa), 2)                      AS avg_ctc_lpa,
    RANK() OVER (
        PARTITION BY job_role
        ORDER BY AVG(total_ctc_lpa) DESC
    )                                                 AS rank_within_role,
    ROUND(
        AVG(total_ctc_lpa) / SUM(AVG(total_ctc_lpa)) OVER (PARTITION BY job_role) * 100, 2
    )                                                 AS share_of_role_salary_pct
FROM india_salaries
GROUP BY company_type, job_role
ORDER BY job_role, rank_within_role;


-- ============================================================
-- QUERY 5: Education premium — does MBA/MTech actually pay more?
SELECT
    education,
    COUNT(*)                                                       AS employees,
    ROUND(AVG(total_ctc_lpa), 2)                                   AS avg_ctc_lpa,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)                    AS median_ctc_lpa,
    ROUND(AVG(total_ctc_lpa) - AVG(AVG(total_ctc_lpa)) OVER (), 2) AS vs_overall_avg,
    ROUND(
        (AVG(total_ctc_lpa) - AVG(AVG(total_ctc_lpa)) OVER ()) /
        NULLIF(AVG(AVG(total_ctc_lpa)) OVER (), 0) * 100, 2
    )                                                              AS premium_pct,
    DENSE_RANK() OVER (ORDER BY AVG(total_ctc_lpa) DESC)          AS salary_rank
FROM india_salaries
GROUP BY education
ORDER BY avg_ctc_lpa DESC;


-- ============================================================
-- QUERY 6: Remote work salary premium analysis
SELECT
    remote_work,
    COUNT(*)                                   AS employees,
    ROUND(AVG(total_ctc_lpa), 2)               AS avg_ctc_lpa,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2) AS median_ctc_lpa,
    ROUND(AVG(total_ctc_lpa) -
          MIN(AVG(total_ctc_lpa)) OVER (), 2)   AS premium_vs_no_remote,
    ROUND(
        (AVG(total_ctc_lpa) - MIN(AVG(total_ctc_lpa)) OVER ()) /
        NULLIF(MIN(AVG(total_ctc_lpa)) OVER (), 0) * 100, 2
    )                                           AS remote_premium_pct
FROM india_salaries
GROUP BY remote_work
ORDER BY avg_ctc_lpa DESC;


-- ============================================================
-- QUERY 7: Industry growth — top industries by average salary
SELECT
    industry,
    company_type,
    COUNT(*)                                      AS employees,
    ROUND(AVG(total_ctc_lpa), 2)                  AS avg_ctc_lpa,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)   AS p25_ctc,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)   AS p75_ctc,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)   AS p90_ctc,
    RANK() OVER (ORDER BY AVG(total_ctc_lpa) DESC) AS industry_rank
FROM india_salaries
GROUP BY industry, company_type
ORDER BY avg_ctc_lpa DESC;


-- ============================================================
-- QUERY 8: Top paying roles for freshers (0-2 years experience)
SELECT
    job_role,
    industry,
    company_type,
    COUNT(*)                                          AS fresher_count,
    ROUND(AVG(total_ctc_lpa), 2)                      AS avg_ctc_lpa,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
          (ORDER BY total_ctc_lpa)::numeric, 2)       AS median_ctc_lpa,
    ROUND(MAX(total_ctc_lpa), 2)                      AS max_ctc_lpa,
    DENSE_RANK() OVER (
        ORDER BY AVG(total_ctc_lpa) DESC
    )                                                 AS rank
FROM india_salaries
WHERE experience_years <= 2
GROUP BY job_role, industry, company_type
HAVING COUNT(*) >= 10
ORDER BY avg_ctc_lpa DESC
LIMIT 20;
