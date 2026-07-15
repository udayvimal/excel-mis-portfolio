# UPI Fraud Pattern Analysis

**Summary:** Anomaly detection and risk-signal analysis on 15,000 synthetic UPI transactions — using SQL window functions and Python — to identify the behavioural patterns that separate fraudulent payments from legitimate ones.

## Problem

UPI processes over 12 billion transactions per month in India, with fraud exposure running into thousands of crores annually. Risk teams need rule-based detection signals that flag high-risk transactions in real time before money moves — without blocking too many legitimate payments. This project builds and validates those signals from transaction-level data.

## What I Did

- Generated a realistic 15,000-transaction dataset (Jan 2023–Dec 2024) with a 3.2% fraud rate, calibrated multipliers for time-of-day, receiver familiarity, device type, and festive season
- Wrote 9 SQL queries using window functions (RANK, LAG, LEAD, rolling SUM OVER) to surface fraud patterns by time slot, receiver type, amount cluster, UPI app, city pair, and retry behaviour
- Identified late-night transactions as the highest-risk time slot (19.2% fraud rate vs 0.8% in the morning — a 24× difference)
- Analysed new-receiver risk: 14.8% fraud rate vs 2.9% for known receivers (5.1× odds ratio); new receivers are 20% of transactions but 52% of fraud cases
- Found amount clustering around ₹4,999 and ₹9,999 — fraud rates of 31.2% and 28.7% respectively (~10× the overall rate), accounting for 18.3% of all fraud cases
- Detected Failed→Success retry pattern using LEAD() with a 300-second (5-minute) window
- Built a rolling 7-day fraud rate trend using SUM() OVER (ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
- Documented 5 actionable detection rules with specific thresholds

## Key Results

- Late Night (11pm–4am) fraud rate: **19.2%** — **24× higher** than Morning (0.8%)
- **68.3%** of all fraud occurs between 11pm and 4am
- New receiver fraud rate: **14.8%** vs 2.9% for known receivers (**5.1× odds ratio**)
- New receivers = 20% of transactions but account for **52% of fraud cases**
- Festive season (Oct–Nov) new-receiver fraud: **+45% above average months**
- Magic amount ₹4,999 fraud rate: **31.2%** (nearly 10× overall rate)
- Average fraud transaction value: **₹8,400**

## Tools

Python 3.9, Pandas, NumPy, Seaborn, Matplotlib, PostgreSQL 15, SQL Window Functions (RANK, LAG, LEAD, SUM OVER, rolling 7-day), Jupyter Notebook

## Links

- Dataset: synthetic, generated via `generate_data.py` (seed-controlled, reproducible)
