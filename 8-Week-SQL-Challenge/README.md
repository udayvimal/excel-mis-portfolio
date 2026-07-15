# 8 Week SQL Challenge

**Summary:** Seven real-world SQL case studies — restaurant loyalty, pizza delivery, streaming subscriptions, digital banking, e-commerce impact analysis, web funnels, and retail clothing — each answered end-to-end with PostgreSQL to demonstrate production-grade analytical SQL.

## Problem

Business teams need analysts who can translate messy relational schemas into clear KPI answers without hand-holding. Each of Danny Ma's case studies presents a realistic schema and 10–14 business questions that require progressively advanced SQL — from basic aggregations up to window functions, cohort logic, and before/after impact measurement.

## What I Did

- **Case Study #1 — Danny's Diner:** Customer spending, visit frequency, and menu popularity to inform loyalty programme expansion. Used CTEs, DENSE_RANK(), CASE. Customer A: $76 spend, 4 visits. Ramen most ordered (8×).
- **Case Study #2 — Pizza Runner:** Cleaned NULL-ridden order data with TEMP TABLEs and REGEXP; analysed runner speed and kitchen efficiency. 14 pizzas ordered, 8 delivered. 2-pizza orders most efficient (8 min/pizza). Runner 2 flagged for 300% speed fluctuation.
- **Case Study #3 — Foodie-Fi:** Subscription churn and plan migration with LEAD/LAG and date series. 1,000 customers; 30.7% churn rate; 9.2% churned immediately after free trial; avg 105 days to upgrade to annual.
- **Case Study #4 — Data Bank:** Rolling closing balances with SUM() OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) and GENERATE_SERIES(). 2,671 deposits totalling $1,359,168. 44.8% of customers had a negative first-month balance.
- **Case Study #5 — Data Mart:** Before/after sales impact of a June 2020 sustainable packaging change. 4-week variance: −$26.9M (−1.15%). 12-week variance: −$152.3M (−2.14%) vs +$104.3M (+1.63%) in 2018.
- **Case Study #6 — Clique Bait:** E-commerce funnel — page views → cart adds → purchases — using STRING_AGG() and pivoted MAX(CASE WHEN). Cart-add rate: 60.95%; cart-to-purchase: 75.93%. Lobster had highest view-to-purchase rate at 48.74%.
- **Case Study #7 — Balanced Tree:** Retail financial reporting with PERCENTILE_CONT(), RANK() OVER (PARTITION BY), and multi-table JOINs. 2,500 transactions; Blue Polo Shirt top revenue product; members vs non-members differed by only $1.23 avg revenue per transaction.

## Key Results

- 80+ business questions answered across 7 case studies
- Foodie-Fi churn: **30.7%** overall; **9.2%** churned immediately after free trial
- Data Mart packaging impact: **−$152.3M (−2.14%)** over 12 weeks — a 3.77pp swing vs 2018
- Data Bank: customers reallocated to new nodes every **24 days** on average; 44.8% had negative first-month balance
- Pizza Runner: Runner 1 only runner at **100% delivery success rate**
- Balanced Tree: top product Blue Polo Shirt — **$276M** revenue before discount

## Tools

PostgreSQL, CTEs, Window Functions (RANK, DENSE_RANK, ROW_NUMBER, LEAD, LAG, SUM OVER), GENERATE_SERIES, PERCENTILE_CONT, STRING_AGG, REGEXP, Date/Time Logic, DB Fiddle

## Links

- Challenge source: [8weeksqlchallenge.com](https://8weeksqlchallenge.com)
