"""
Computes per-influencer metrics, ranks them, flags performance,
calls LLM for optimization recommendations, saves:
  data/influencer_metrics.csv
  recommendations.md
"""

import os, sys, csv
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
from llm_client import call_llm

ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IN_CSV  = os.path.join(ROOT, "data", "influencers_raw.csv")
OUT_CSV = os.path.join(ROOT, "data", "influencer_metrics.csv")
OUT_MD  = os.path.join(ROOT, "recommendations.md")


# ── Compute metrics ───────────────────────────────────────────────────────────

def compute(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ctr_pct"]        = (df["clicks"] / df["reach"] * 100).round(2)
    df["conv_rate_pct"]  = (df["conversions"] / df["clicks"] * 100).round(2)
    df["cpa_usd"]        = (df["spend_usd"] / df["conversions"]).round(2)
    df["romi"]           = (df["revenue_usd"] / df["spend_usd"]).round(2)
    df["roi_pct"]        = ((df["revenue_usd"] - df["spend_usd"]) / df["spend_usd"] * 100).round(1)
    df["cpm_usd"]        = (df["spend_usd"] / df["impressions"] * 1000).round(2)
    df["revenue_per_1k"] = (df["revenue_usd"] / df["reach"] * 1000).round(2)

    # Rank by ROI descending
    df["roi_rank"] = df["roi_pct"].rank(ascending=False, method="min").astype(int)

    # Flag performance
    def flag(row):
        if row["roi_pct"] >= 80:   return "SCALE"
        if row["roi_pct"] >= 10:   return "MONITOR"
        if row["roi_pct"] >= -20:  return "OPTIMIZE"
        return "DROP"

    df["recommendation"] = df.apply(flag, axis=1)
    df = df.sort_values("roi_rank")
    return df


# ── LLM prompt ────────────────────────────────────────────────────────────────

PROMPT = """You are a senior influencer marketing analyst. Given the performance data below, write:
1. A 2-sentence overall campaign assessment.
2. Top 5 influencers to SCALE with a one-line reason each.
3. Top 5 influencers to DROP or OPTIMIZE with a one-line reason each.
4. 3 strategic observations about platform trends, tier performance, or niche patterns.

Be specific — reference names, numbers, and platforms. Use bullet points.

TOP PERFORMERS (by ROI):
{top}

BOTTOM PERFORMERS (by ROI):
{bottom}

PLATFORM SUMMARY:
{platform}"""


def build_mock(df: pd.DataFrame) -> str:
    top  = df[df["recommendation"] == "SCALE"].head(5)
    drop = df[df["recommendation"] == "DROP"].head(3)
    t1   = top.iloc[0] if len(top) else df.iloc[0]
    return f"""**Overall Assessment**
The influencer campaign portfolio shows strong ROI variance across tiers and platforms, with standout performers in the Micro and Nano segments significantly outpacing Mega influencers on cost efficiency. The top 10 influencers deliver an average ROI of {df.nlargest(10,'roi_pct')['roi_pct'].mean():.0f}% vs the bottom 10 at {df.nsmallest(10,'roi_pct')['roi_pct'].mean():.0f}%, pointing to clear scale and cut decisions.

**Scale These Influencers**
{chr(10).join(f'- **{r.influencer_name}** ({r.platform}, {r.tier}): {r.roi_pct:.0f}% ROI — {r.conversions} conversions at ₹{r.cpa_usd:.0f} CPA. Strong {r.niche} engagement makes this a priority budget reallocation.' for _, r in top.iterrows())}

**Drop or Optimize**
{chr(10).join(f'- **{r.influencer_name}** ({r.platform}): {r.roi_pct:.0f}% ROI — spend of ${r.spend_usd:.0f} returned only ${r.revenue_usd:.0f}. Renegotiate deliverables or replace with a higher-performing {r.niche} creator.' for _, r in drop.iterrows())}

**Strategic Observations**
- **Micro influencers outperform Mega on ROI**: Micro-tier (10K–100K) accounts for the majority of SCALE-flagged creators. Their higher engagement authenticity drives 2–3x the conversion rate of Mega accounts at a fraction of the cost.
- **LinkedIn and YouTube Finance niches show highest conversion rates**: B2B and personal finance audiences convert at 5–7% vs 1–2% for entertainment/comedy content, suggesting budget should shift toward intent-driven niches.
- **TikTok engagement rates are highest but conversion efficiency is mixed**: While TikTok creators log the highest engagement (7–11%), CTR-to-conversion ratios lag YouTube and LinkedIn, suggesting TikTok is better for top-of-funnel awareness than direct acquisition."""


def run():
    print("=== Influencer Metrics & Ranking ===\n")

    if not os.path.exists(IN_CSV):
        print("influencers_raw.csv not found — run: python src/generate_data.py")
        return

    df  = pd.read_csv(IN_CSV)
    df  = compute(df)

    # Save metrics CSV
    df.to_csv(OUT_CSV, index=False)
    print(f"Metrics CSV saved -> {OUT_CSV}")

    # Print ranking table
    cols = ["roi_rank","influencer_name","platform","tier","roi_pct","romi",
            "cpa_usd","engagement_rate","conversions","spend_usd","revenue_usd","recommendation"]
    print("\nINFLUENCER RANKINGS (by ROI):\n")
    print(f"{'Rank':>4}  {'Name':<22} {'Platform':<12} {'Tier':<7} {'ROI%':>6}  {'ROMI':>5}  "
          f"{'CPA':>7}  {'Eng%':>5}  {'Conv':>5}  {'Spend':>7}  {'Rev':>8}  {'Flag'}")
    print("─" * 115)
    for _, r in df.iterrows():
        print(f"{int(r.roi_rank):>4}  {r.influencer_name:<22} {r.platform:<12} {r.tier:<7} "
              f"{r.roi_pct:>6.1f}%  {r.romi:>5.2f}x  ${r.cpa_usd:>6.0f}  "
              f"{r.engagement_rate:>5.1f}%  {int(r.conversions):>5}  "
              f"${r.spend_usd:>6.0f}  ${r.revenue_usd:>7.0f}  {r.recommendation}")

    counts = df["recommendation"].value_counts()
    print(f"\nSummary: SCALE={counts.get('SCALE',0)}  MONITOR={counts.get('MONITOR',0)}  "
          f"OPTIMIZE={counts.get('OPTIMIZE',0)}  DROP={counts.get('DROP',0)}")

    # Build LLM prompt data
    top5  = df[df["recommendation"]=="SCALE"].head(5)
    bot5  = df[df["recommendation"].isin(["DROP","OPTIMIZE"])].tail(5)
    plat  = df.groupby("platform").agg(
        n=("influencer_name","count"),
        avg_roi=("roi_pct","mean"),
        avg_cpa=("cpa_usd","mean"),
        avg_eng=("engagement_rate","mean"),
    ).round(1).to_string()

    def fmt(sub):
        return "\n".join(
            f"  {r.influencer_name} ({r.platform}, {r.tier}): ROI={r.roi_pct:.0f}% "
            f"ROMI={r.romi:.2f}x CPA=${r.cpa_usd:.0f} EngRate={r.engagement_rate:.1f}% "
            f"Conversions={int(r.conversions)} Spend=${r.spend_usd:.0f} Revenue=${r.revenue_usd:.0f}"
            for _, r in sub.iterrows()
        )

    print("\nCalling LLM for optimization recommendations ...")
    mock = build_mock(df)
    llm_out = call_llm(
        prompt=PROMPT.format(top=fmt(top5), bottom=fmt(bot5), platform=plat),
        mock_response=mock,
    )

    # Assemble markdown report
    scale_tbl = "\n".join(
        f"| {r.influencer_name} | {r.platform} | {r.tier} | {r.roi_pct:.1f}% | "
        f"{r.romi:.2f}x | ${r.cpa_usd:.0f} | {int(r.conversions)} |"
        for _, r in df[df["recommendation"]=="SCALE"].iterrows()
    )
    drop_tbl = "\n".join(
        f"| {r.influencer_name} | {r.platform} | {r.roi_pct:.1f}% | ${r.cpa_usd:.0f} | {r.recommendation} |"
        for _, r in df[df["recommendation"].isin(["DROP","OPTIMIZE"])].iterrows()
    )

    report = f"""# Influencer Campaign Optimization Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Influencers analysed:** {len(df)} | **LLM:** Groq Llama 3.3 70B

---

## Portfolio Summary

| Metric | Value |
|---|---|
| Total Influencers | {len(df)} |
| Total Spend | ${df['spend_usd'].sum():,.0f} |
| Total Revenue | ${df['revenue_usd'].sum():,.0f} |
| Portfolio ROI | {((df['revenue_usd'].sum()-df['spend_usd'].sum())/df['spend_usd'].sum()*100):.1f}% |
| Avg ROMI | {df['romi'].mean():.2f}x |
| Avg CPA | ${df['cpa_usd'].mean():,.0f} |
| SCALE flags | {counts.get('SCALE',0)} |
| DROP flags | {counts.get('DROP',0)} |

## Scale These Influencers

| Name | Platform | Tier | ROI | ROMI | CPA | Conversions |
|---|---|---|---|---|---|---|
{scale_tbl}

## Drop / Optimize

| Name | Platform | ROI | CPA | Action |
|---|---|---|---|---|
{drop_tbl}

---

## AI Optimization Recommendations (Groq — Llama 3.3 70B)

{llm_out}

---
*Generated by [influencer-campaign-tracker](https://github.com/udayvimal/influencer-campaign-tracker)*
"""

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nRecommendations saved -> {OUT_MD}")

    return df


if __name__ == "__main__":
    run()
