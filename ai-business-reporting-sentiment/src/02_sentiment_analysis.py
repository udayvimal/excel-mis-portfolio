"""
Branch B — AI Review Sentiment Analysis
========================================
Loads reviews.csv, uses an LLM to classify sentiment per review + extract
themes, then generates a Voice of Customer (VoC) summary as sentiment_report.md.

Run: python src/02_sentiment_analysis.py
"""

import os, sys, csv
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from llm_client import call_llm

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH    = os.path.join(PROJECT_ROOT, "data", "reviews.csv")
OUTPUT_PATH  = os.path.join(PROJECT_ROOT, "sentiment_report.md")


# ── 1. Batch classify reviews ─────────────────────────────────────────────────

CLASSIFY_PROMPT = """You are a customer insights analyst. Classify each review below.

For each review, output a single line:
  <id>|<sentiment>|<theme>

Where:
  sentiment = positive | negative | neutral
  theme     = one of: product_quality | delivery | packaging | pricing | customer_support | effectiveness | other

Reviews:
{reviews}

Output only the lines, no explanation."""


def classify_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Classify all reviews via LLM (or use the label column in mock mode)."""

    # Build prompt with all reviews
    review_lines = "\n".join(
        f"{row['review_id']}. [{row['product']}] {row['review_text']}"
        for _, row in df.iterrows()
    )

    # Mock: derive from the sentiment_label column already in the CSV
    mock_lines = []
    theme_map = {
        "Protein": "effectiveness",
        "Serum": "product_quality",
        "Yoga": "product_quality",
        "Sleep": "effectiveness",
        "Resistance": "product_quality",
        "Dumbbell": "product_quality",
        "Lotion": "packaging",
        "Collagen": "product_quality",
        "Diffuser": "product_quality",
        "Kadha": "delivery",
        "Lip": "pricing",
        "Vitamin": "product_quality",
        "Omega": "effectiveness",
        "Foam": "product_quality",
        "Rose": "effectiveness",
        "Bamboo": "customer_support",
    }
    for _, row in df.iterrows():
        # infer theme from product name keyword
        theme = "other"
        for kw, t in theme_map.items():
            if kw.lower() in row["product"].lower():
                theme = t
                break
        mock_lines.append(f"{row['review_id']}|{row['sentiment_label']}|{theme}")
    mock_output = "\n".join(mock_lines)

    raw = call_llm(
        prompt=CLASSIFY_PROMPT.format(reviews=review_lines),
        mock_response=mock_output,
    )

    # Parse output
    results = {}
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            try:
                rid       = int(parts[0].strip().lstrip("0123456789. ").strip() or parts[0].strip())
            except ValueError:
                # handle "1." or "1:" prefix
                try:
                    rid = int(''.join(c for c in parts[0] if c.isdigit()))
                except ValueError:
                    continue
            sentiment = parts[1].strip().lower()
            theme     = parts[2].strip().lower()
            results[rid] = {"llm_sentiment": sentiment, "theme": theme}

    df = df.copy()
    df["llm_sentiment"] = df["review_id"].map(
        lambda x: results.get(x, {}).get("llm_sentiment", "neutral")
    )
    df["theme"] = df["review_id"].map(
        lambda x: results.get(x, {}).get("theme", "other")
    )
    return df


# ── 2. Aggregate stats ────────────────────────────────────────────────────────

def aggregate(df: pd.DataFrame) -> dict:
    total = len(df)
    counts = df["llm_sentiment"].value_counts().to_dict()
    pos   = counts.get("positive", 0)
    neg   = counts.get("negative", 0)
    neu   = counts.get("neutral",  0)

    top_themes = df[df["llm_sentiment"] == "negative"]["theme"].value_counts().head(4)
    product_sentiment = (df.groupby("product")["llm_sentiment"]
                         .apply(lambda x: (x == "negative").mean())
                         .sort_values(ascending=False).head(5))

    return {
        "total": total, "pos": pos, "neg": neg, "neu": neu,
        "pos_pct": round(pos / total * 100, 1),
        "neg_pct": round(neg / total * 100, 1),
        "neu_pct": round(neu / total * 100, 1),
        "top_themes": top_themes,
        "product_risk": product_sentiment,
    }


# ── 3. VoC summary via LLM ───────────────────────────────────────────────────

VOC_PROMPT = """You are a customer experience analyst writing a Voice of Customer report for a D2C brand.

Given this sentiment analysis of {total} customer reviews:
- Positive: {pos} ({pos_pct}%)
- Negative: {neg} ({neg_pct}%)
- Neutral:  {neu} ({neu_pct}%)

Top complaint themes: {themes}
Highest-risk products (negative review rate): {risk_products}

Sample negative reviews:
{neg_samples}

Write:
1. A 2-sentence VoC overview.
2. Top 3 recurring customer complaints (bold heading + 1-sentence detail each).
3. Recommended actions for product and marketing teams (3 bullets).

Be direct, specific, and action-oriented."""


def build_mock_voc(stats: dict, df: pd.DataFrame) -> str:
    themes_str = ", ".join(
        f"{t} ({c} reviews)" for t, c in stats["top_themes"].items()
    )
    risk_str = ", ".join(
        f"{p.split()[0]} ({v:.0%} negative)"
        for p, v in stats["product_risk"].items()
    )
    return f"""## Voice of Customer Overview

Customer sentiment is **{stats['pos_pct']}% positive** with {stats['neg'] } negative reviews flagging real product and operational gaps. The clearest signal: negative reviews cluster around {list(stats['top_themes'].index[:2])[0].replace('_',' ')} and {list(stats['top_themes'].index[:2])[-1].replace('_',' ')}, suggesting these are systemic issues, not one-off complaints.

## Top 3 Recurring Customer Complaints

**1. Product quality inconsistency.** Multiple reviews report items not performing as advertised — particularly around effectiveness claims for supplements and durability of fitness accessories.

**2. Packaging and delivery failures.** Leaked bottles, broken pump dispensers, and damaged items on arrival appear across multiple SKUs, pointing to a fulfilment or secondary-packaging gap.

**3. Customer support responsiveness.** Customers reporting unresolved issues after 4–5 days are escalating to public reviews — indicating a support SLA problem that is costing brand reputation.

## Recommended Actions

- **Product team:** Audit QC for the top-risk SKUs ({risk_str.split(',')[0]}); add a "real results timeline" section to product pages to manage effectiveness expectations.
- **Operations team:** Introduce mandatory bubble-wrap secondary packaging for liquid and glass products; implement a 48-hour SLA for support tickets flagged as "item damaged / arrived broken."
- **Marketing team:** Build a post-purchase review sequence with a 14-day check-in email to intercept unhappy customers before they post publicly; use positive verbatim quotes ({stats['pos_pct']}% of reviews) in retargeting ads."""


def run():
    print("=== Branch B: AI Sentiment Analysis ===\n")

    if not os.path.exists(DATA_PATH):
        print("reviews.csv not found — run: python src/generate_data.py")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} reviews from reviews.csv")

    print("Classifying reviews via LLM ...")
    df = classify_reviews(df)

    stats = aggregate(df)
    print(f"\nSentiment breakdown:")
    print(f"  Positive: {stats['pos']} ({stats['pos_pct']}%)")
    print(f"  Negative: {stats['neg']} ({stats['neg_pct']}%)")
    print(f"  Neutral:  {stats['neu']} ({stats['neu_pct']}%)")

    # Sample negatives for VoC prompt
    neg_samples = df[df["llm_sentiment"] == "negative"]["review_text"].head(4)
    neg_text    = "\n".join(f'- "{t}"' for t in neg_samples)
    themes_str  = ", ".join(
        f"{t} ({c})" for t, c in stats["top_themes"].items()
    )
    risk_str    = "\n".join(
        f"  {p}: {v:.0%} of reviews negative"
        for p, v in stats["product_risk"].items()
    )

    print("\nGenerating Voice of Customer summary ...")
    mock_voc = build_mock_voc(stats, df)
    voc = call_llm(
        prompt=VOC_PROMPT.format(
            total=stats["total"], pos=stats["pos"], neg=stats["neg"],
            neu=stats["neu"], pos_pct=stats["pos_pct"],
            neg_pct=stats["neg_pct"], neu_pct=stats["neu_pct"],
            themes=themes_str, risk_products=risk_str,
            neg_samples=neg_text,
        ),
        mock_response=mock_voc,
    )

    # Sentiment breakdown table
    theme_rows = "\n".join(
        f"| {t.replace('_',' ').title()} | {c} |"
        for t, c in stats["top_themes"].items()
    )
    risk_rows = "\n".join(
        f"| {p} | {v:.0%} |"
        for p, v in stats["product_risk"].items()
    )
    sample_table = "\n".join(
        f'| {row["product"][:30]} | {row["llm_sentiment"].title()} | {row["theme"].replace("_"," ")} | "{row["review_text"][:70]}..." |'
        for _, row in df.sample(8, random_state=1).iterrows()
    )

    report = f"""# Sentiment & Voice of Customer Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Reviews analysed:** {stats['total']}

---

## Sentiment Breakdown

| Sentiment | Count | Share |
|---|---|---|
| Positive | {stats['pos']} | {stats['pos_pct']}% |
| Negative | {stats['neg']} | {stats['neg_pct']}% |
| Neutral  | {stats['neu']} | {stats['neu_pct']}% |

### Top Complaint Themes (Negative Reviews)
| Theme | Count |
|---|---|
{theme_rows}

### Highest-Risk Products (Negative Review Rate)
| Product | Negative Rate |
|---|---|
{risk_rows}

### Review Sample
| Product | Sentiment | Theme | Review (excerpt) |
|---|---|---|---|
{sample_table}

---

{voc}

---
*Report auto-generated by [ai-business-reporting-sentiment](https://github.com/udayvimal/ai-business-reporting-sentiment)*
"""

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved -> {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
