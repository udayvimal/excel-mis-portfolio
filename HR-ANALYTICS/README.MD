# HR Analytics Dashboard

**Summary:** Employee segmentation and attrition analysis on 8,950 records across departments, roles, education levels, and geographies — surfacing which workforce segments drive the 10.8% termination rate — with an interactive Tableau dashboard.

## Problem

HR teams struggle to answer "who is leaving and why" from raw headcount data. Without a clear view of attrition by department, tenure, performance, and demographics, retention spend goes to the wrong places. This project builds the analytical foundation for a data-driven workforce retention strategy.

## What I Did

- Generated 8,950 employee records with realistic distributions across departments (Operations 30%, Sales 21%, Customer Service 19%, IT 15%), performance ratings, hire/termination years, and US state geography (New York 70%)
- Calculated overall attrition: 966 terminated employees out of 8,950 — **10.8% termination rate** (7,984 currently active)
- Segmented attrition by department: Operations, Sales, and Customer Service are the top three attrition-contributing departments
- Analysed salary by education level: High School avg $62,774 → Bachelor's $65,653 → Master's $86,335 → PhD $92,655
- Identified gender distribution: Female 47.94%, Male 41.26% across the active workforce
- Mapped termination year weights: 2021 saw the highest relative termination activity (weight 20) — consistent with post-COVID attrition spike
- Built Tableau dashboard with views covering headcount over time, attrition by department and role, salary bands, performance distribution, and geographic spread across US states

## Key Results

- Total employees: **8,950** | Active: **7,984** | Terminated: **966**
- Overall attrition rate: **10.8%**
- Highest termination activity year: **2021** (weighted 2× any other year)
- PhD holders earn **47.6% more** than High School graduates ($92,655 vs $62,774)
- Master's degree premium over Bachelor's: **31.5%** ($86,335 vs $65,653)
- Top departments by headcount: Operations (30%), Sales (21%), Customer Service (19%)
- Overtime workers: **30%** of workforce; non-overtime: 70%

## Tools

Python (data generation), Tableau (interactive dashboard), Figma, Draw.io, CSV

## Links

- Dashboard summary: see `HR _ SUMMARY.pdf` in repo
