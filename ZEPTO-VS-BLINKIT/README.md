# Zepto vs Blinkit — Competitive Pricing & Category Analysis

**Summary:** Competitive benchmarking of Zepto and Blinkit across product categories, pricing, delivery speed, and order behaviour using scraped product data and synthetic order records, with a 6-dashboard Tableau readout.

## Problem

Quick-commerce platforms compete on speed, price, and category depth — but it is hard to tell from the outside where each actually wins. Brands and category managers need to know which platform leads on price, discount depth, and basket composition to make stocking and partnership decisions.

## What I Did

- Built scrapers for Blinkit (BeautifulSoup / requests) and Zepto (Selenium + headless Chrome) to collect product listings across 9 categories
- Generated a synthetic order dataset of 1,000 orders per platform (2,000 total) spanning the last 12 months, covering cities including Mumbai, Delhi, Bangalore, Pune, and Ahmedabad
- Compared average delivery times: Zepto 11.8 min vs Blinkit 16.5 min
- Compared average discount per order: Zepto ₹34.94 vs Blinkit ₹17.52
- Analysed average net order value after discount: Blinkit ₹431.83 vs Zepto ₹367.05
- Broke down category leadership: Blinkit leads in Snacks (132 vs 96 orders), Fruits, Household, Frozen Foods; Zepto leads in Personal Care, Dairy, Vegetables, Beverages
- Identified peak order window (6pm–10pm): Zepto 50.2% vs Blinkit 49.8% of daily orders
- Built Tableau dashboard with 6 views covering pricing, category share, delivery speed, city-level breakdown, and payment method split

## Key Results

- Zepto delivers **~28% faster** (11.8 min vs 16.5 min avg)
- Zepto offers **2× deeper average discounts** (₹34.94 vs ₹17.52 per order)
- Blinkit commands a **17.6% higher average net order value** (₹431.83 vs ₹367.05)
- UPI dominates payments on both platforms: **Blinkit 60.3% / Zepto 59.6%**
- Category verdict — Zepto: groceries & essentials (Dairy, Vegetables, Beverages); Blinkit: quick buys & treats (Snacks, Fruits, Frozen)
- Peak hour (6–10pm) accounts for ~**50% of all orders** on both platforms

## Tools

Python, BeautifulSoup, Selenium, Pandas, NumPy, Tableau Public

## Links

- Tableau Dashboard: [Zepto vs Blinkit — Uday Vimal](https://public.tableau.com/app/profile/uday.vimal/viz/ZEPTOVSBLINKIT-UDAYVIMAL/Dashboard1)
