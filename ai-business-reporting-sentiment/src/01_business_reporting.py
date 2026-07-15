"""
Branch A — AI Business Reporting
=================================
Loads sales_data.csv, computes key metrics, prompts an LLM for an executive
summary + 3 actionable insights, and saves the result as business_report.md.

Run: python src/01_business_reporting.py
"""

import os, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from llm_client import call_llm

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "sales_data.csv")
OUTPUT_PATH  = os.path.join(PROJECT_ROOT, "business_report.md")


# ── 1. Load & compute metrics ─────────────────────────────────────────────────

def compute_metrics(df: pd.DataFrame) -> dict:
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    total_revenue = df["revenue"].sum()
    total_units   = df["units_sold"].sum()
    avg_discount  = df["discount_pct"].mean()

    # Top 5 products by revenue
    top_products = (df.groupby("product")["revenue"]
                    .sum().sort_values(ascending=False).head(5))

    # Revenue by category
    cat_revenue = (df.groupby("category")["revenue"]
                   .sum().sort_values(ascending=False))

    # Units by category
    cat_units = df.groupby("category")["units_sold"].sum()

    # Top discounted products (avg discount > 20%)
    top_discounts = (df.groupby("product")["discount_pct"]
                     .mean().sort_values(ascending=False).head(5))

    # Monthly revenue trend
    monthly = (df.groupby("month")["revenue"]
               .sum().sort_index())

    # Best and worst months
    best_month  = monthly.idxmax()
    worst_month = monthly.idxmin()

    return {
        "total_revenue":  round(total_revenue, 2),
        "total_units":    int(total_units),
        "avg_discount":   round(avg_discount, 1),
        "top_products":   top_products,
        "cat_revenue":    cat_revenue,
        "cat_units":      cat_units,
        "top_discounts":  top_discounts,
        "monthly":        monthly,
        "best_month":     best_month,
        "worst_month":    worst_month,
        "top_category":   cat_revenue.index[0],
        "top_cat_rev":    round(cat_revenue.iloc[0], 2),
        "top_product":    top_products.index[0],
        "top_prod_rev":   round(top_products.iloc[0], 2),
    }


def format_metrics_for_prompt(m: dict) -> str:
    top_p = "\n".join(
        f"  - {p}: ₹{v:,.0f}" for p, v in m["top_products"].items()
    )
    cat_r = "\n".join(
        f"  - {c}: ₹{v:,.0f} ({m['cat_units'][c]:,} units)"
        for c, v in m["cat_revenue"].items()
    )
    monthly = "\n".join(
        f"  - {mo}: ₹{v:,.0f}" for mo, v in m["monthly"].items()
    )
    top_disc = "\n".join(
        f"  - {p}: {v:.1f}% avg discount"
        for p, v in m["top_discounts"].items()
    )

    return f"""
D2C Business Sales Metrics (last 90 days)
==========================================
Total Revenue:       ₹{m['total_revenue']:,.2f}
Total Units Sold:    {m['total_units']:,}
Average Discount:    {m['avg_discount']}%
Best Month:          {m['best_month']}
Worst Month:         {m['worst_month']}

Top 5 Products by Revenue:
{top_p}

Revenue & Units by Category:
{cat_r}

Monthly Revenue Trend:
{monthly}

Most Discounted Products:
{top_disc}
""".strip()


# ── 2. Mock response (used when no API key) ───────────────────────────────────

def build_mock_report(m: dict) -> str:
    top5 = list(m["top_products"].items())
    return f"""## Executive Summary

The D2C portfolio recorded **₹{m['total_revenue']:,.0f} in total revenue** across {m['total_units']:,} units sold over the last 90 days, with an average promotional discount of {m['avg_discount']}%. **{m['top_category']}** emerged as the strongest category, contributing ₹{m['top_cat_rev']:,.0f} — the highest of all segments. The standout performer was **{m['top_product']}**, which generated ₹{m['top_prod_rev']:,.0f} in revenue, validating strong consumer demand in this sub-segment. Revenue peaked in {m['best_month']}, while {m['worst_month']} underperformed — suggesting seasonal or campaign-driven demand patterns that merit deeper investigation.

## 3 Actionable Business Insights

**1. Double down on {m['top_category']} — it is your revenue engine.**
{m['top_category']} leads all categories in both revenue and unit volume. Prioritise inventory depth and new SKU launches here. A limited-edition or bundle offering within this category could capture incremental spend from existing loyal buyers.

**2. Reassess high-discount products — margin erosion is a risk.**
Products averaging above 20% discount ({top5[-1][0]} included) may be training customers to wait for promotions before purchasing. Run a 30-day price-normalisation test on the top two discounted SKUs to identify which discounts are demand-drivers vs which are margin leaks.

**3. Investigate the {m['worst_month']} revenue dip and build a counter-campaign.**
The gap between best month ({m['best_month']}) and worst ({m['worst_month']}) suggests demand is uneven across the quarter. A targeted reactivation email campaign or flash sale in the historically weaker period could smooth out revenue and improve monthly predictability for planning."""


# ── 3. Build the full markdown report ────────────────────────────────────────

PROMPT_TEMPLATE = """You are a senior D2C business analyst writing a monthly leadership report.

Given the following sales metrics, write:
1. A concise executive summary (150–200 words) highlighting total revenue, top category, and key trend.
2. Exactly 3 actionable business insights as numbered bullet points (bold headline + 2-sentence explanation each).

Be specific — reference the actual numbers. Write in professional business English.

METRICS:
{metrics}

Format your response starting with:
## Executive Summary
[summary]

## 3 Actionable Business Insights
[numbered insights]"""


def run():
    print("=== Branch A: AI Business Reporting ===\n")

    if not os.path.exists(DATA_PATH):
        print("sales_data.csv not found — run: python src/generate_data.py")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows from sales_data.csv")

    m = compute_metrics(df)
    metrics_text = format_metrics_for_prompt(m)

    print(f"\nMetrics computed:")
    print(f"  Total revenue:  ₹{m['total_revenue']:,.2f}")
    print(f"  Total units:    {m['total_units']:,}")
    print(f"  Top category:   {m['top_category']} (₹{m['top_cat_rev']:,.0f})")
    print(f"  Top product:    {m['top_product']}")

    print("\nCalling LLM for executive summary ...")
    mock = build_mock_report(m)
    llm_output = call_llm(
        prompt=PROMPT_TEMPLATE.format(metrics=metrics_text),
        mock_response=mock,
    )

    # Build final markdown report
    report = f"""# AI Business Report — D2C Sales Analysis
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Data:** Last 90 days | **Rows:** {len(df)}

---

## Key Metrics at a Glance

| Metric | Value |
|---|---|
| Total Revenue | ₹{m['total_revenue']:,.2f} |
| Total Units Sold | {m['total_units']:,} |
| Avg Discount Applied | {m['avg_discount']}% |
| Best Month | {m['best_month']} |
| Top Category | {m['top_category']} |
| Top Product | {m['top_product']} |

### Revenue by Category
{chr(10).join(f"- **{c}**: ₹{v:,.0f}" for c, v in m['cat_revenue'].items())}

### Top 5 Products by Revenue
{chr(10).join(f"{i+1}. {p} — ₹{v:,.0f}" for i, (p, v) in enumerate(m['top_products'].items()))}

---

{llm_output}

---
*Report auto-generated by [ai-business-reporting-sentiment](https://github.com/udayvimal/ai-business-reporting-sentiment)*
"""

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved -> {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
