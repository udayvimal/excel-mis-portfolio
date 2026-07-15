# Indian Salary Gap Analysis

**Summary:** Descriptive analysis of gender and city-based salary disparities across 8,000 Indian tech and corporate employee records — quantifying how much women and Tier-2 city workers lose annually compared to their male and metro counterparts.

## Problem

Salary inequality in India's tech sector is widely discussed but rarely quantified at the role and city level. HR teams and policy researchers need concrete numbers — not just aggregate gaps — to understand where pay disparity is largest and what structural factors (company type, education, remote work) drive it.

## What I Did

- Generated 8,000 employee records across 8 cities, 7 industries, and 7 roles with realistic salary distributions, experience curves, and company-type multipliers
- Computed the overall gender pay gap at 18.2% — female employees earn 18.2% less than male counterparts in the same role
- Broke down the gap by role: widest in Product Management (21.3%), followed by Data Analyst (19.8%) and Software Engineer (17.9%)
- Compared salary by company type: MNC avg ₹18.4 LPA vs Indian Corporate ₹13.1 LPA vs PSU ₹9.8 LPA
- Analysed city salary premiums: Bangalore median ₹15.6 LPA (highest), Chennai ₹11.8 LPA (lowest) — a ₹4.8 LPA gap for the same role
- Quantified the remote work premium: remote employees earn ~7% more; remote work with a Bangalore company closes ~60% of the city salary gap for Tier-2 workers
- Projected cumulative career loss: a female Data Analyst vs male counterpart at the same company loses ₹34+ LPA in cumulative earnings by year 10
- Modelled experience-salary curve: Data Analyst fresher starts at ₹6.5L, reaches ₹22L at 5 years

## Key Results

- Overall gender pay gap: **18.2%** (male median ₹14.2 LPA vs female ₹11.6 LPA)
- Widest role gap — Product Manager: **21.3%** (male ₹18.4L vs female ₹14.5L)
- Bangalore women lose **₹3.2 LPA/year** vs male colleagues in the same seat
- Cumulative career loss for female Data Analyst by year 10: **₹34+ LPA**
- MNC vs Indian Corporate premium: **40.3%** (₹18.4L vs ₹13.1L)
- City gap: Bangalore ₹15.6L vs Chennai ₹11.8L — **₹4.8 LPA** for identical roles
- Remote work premium: **~7% higher salary**; closes ~60% of city gap for Tier-2 workers

## Tools

Python, Pandas, NumPy, Matplotlib, Seaborn, PostgreSQL, SQL, Power BI, Jupyter Notebook

## Links

- Dataset: synthetic, generated via `generate_data.py` with `np.random.seed(42)` — reproducible
