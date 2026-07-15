"""
Generates 6 dashboard charts saved to dashboard/.
Run after 01_metrics_and_ranking.py.
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DASH_DIR = os.path.join(ROOT, "dashboard")
os.makedirs(DASH_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.0)

FLAG_COLORS = {
    "SCALE":    "#16A34A",
    "MONITOR":  "#2563EB",
    "OPTIMIZE": "#F59E0B",
    "DROP":     "#EF4444",
}
PLATFORM_COLORS = {
    "Instagram": "#E1306C",
    "YouTube":   "#FF0000",
    "TikTok":    "#010101",
    "Twitter/X": "#1DA1F2",
    "LinkedIn":  "#0077B5",
}


def load():
    path = os.path.join(ROOT, "data", "influencer_metrics.csv")
    if not os.path.exists(path):
        print("Run 01_metrics_and_ranking.py first.")
        sys.exit(1)
    return pd.read_csv(path)


def save(fig, name):
    path = os.path.join(DASH_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


def chart_roi_ranking(df):
    top = df.nlargest(20, "roi_pct").sort_values("roi_pct")
    colors = [FLAG_COLORS[f] for f in top["recommendation"]]

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(top["influencer_name"], top["roi_pct"], color=colors, edgecolor="white", linewidth=0.5)
    for bar, val in zip(bars, top["roi_pct"]):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}%", va="center", fontsize=8.5, fontweight="bold")
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("ROI (%)")
    ax.set_title("Top 20 Influencers Ranked by ROI", fontsize=13, fontweight="bold", pad=10)
    patches = [mpatches.Patch(color=c, label=l) for l, c in FLAG_COLORS.items()]
    ax.legend(handles=patches, title="Recommendation", fontsize=9, loc="lower right")
    ax.set_xlim(-50, top["roi_pct"].max() * 1.15)
    fig.tight_layout()
    save(fig, "01_roi_ranking.png")


def chart_engagement_vs_conversion(df):
    fig, ax = plt.subplots(figsize=(9, 6))
    for platform, grp in df.groupby("platform"):
        ax.scatter(grp["engagement_rate"], grp["conv_rate_pct"],
                   label=platform, color=PLATFORM_COLORS.get(platform, "grey"),
                   s=80 + grp["spend_usd"] / 80,
                   edgecolors="white", linewidths=0.7, alpha=0.85, zorder=3)
    ax.set_xlabel("Engagement Rate (%)", fontsize=11)
    ax.set_ylabel("Conversion Rate (%)", fontsize=11)
    ax.set_title("Engagement Rate vs Conversion Rate\n(bubble size = spend)",
                 fontsize=12, fontweight="bold")
    ax.legend(title="Platform", fontsize=9)
    fig.tight_layout()
    save(fig, "02_engagement_vs_conversion.png")


def chart_spend_vs_revenue(df):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = [FLAG_COLORS[f] for f in df["recommendation"]]
    sizes  = np.sqrt(df["followers"]) / 12

    sc = ax.scatter(df["spend_usd"], df["revenue_usd"],
                    c=colors, s=sizes, edgecolors="white", linewidths=0.7, alpha=0.85, zorder=3)

    # Break-even line
    lim = max(df["spend_usd"].max(), df["revenue_usd"].max()) * 1.05
    ax.plot([0, lim], [0, lim], color="black", linestyle="--", linewidth=1, alpha=0.4, label="Break-even")

    ax.set_xlabel("Spend (USD)", fontsize=11)
    ax.set_ylabel("Revenue (USD)", fontsize=11)
    ax.set_title("Spend vs Revenue\n(bubble size = followers  |  colour = performance flag)",
                 fontsize=12, fontweight="bold")
    patches = [mpatches.Patch(color=c, label=l) for l, c in FLAG_COLORS.items()]
    patches.append(mpatches.Patch(color="black", label="Break-even"))
    ax.legend(handles=patches, fontsize=9)
    fig.tight_layout()
    save(fig, "03_spend_vs_revenue.png")


def chart_roi_by_platform(df):
    platform_order = df.groupby("platform")["roi_pct"].median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(9, 5))
    pal = [PLATFORM_COLORS.get(p, "grey") for p in platform_order]
    sns.boxplot(data=df, x="platform", y="roi_pct", order=platform_order,
                palette=pal, ax=ax, linewidth=1.2)
    ax.axhline(0, color="red", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("Platform", fontsize=11)
    ax.set_ylabel("ROI (%)", fontsize=11)
    ax.set_title("ROI Distribution by Platform", fontsize=12, fontweight="bold")
    fig.tight_layout()
    save(fig, "04_roi_by_platform.png")


def chart_tier_efficiency(df):
    tier_order = ["Nano", "Micro", "Macro", "Mega"]
    tier_stats = df.groupby("tier").agg(
        avg_roi=("roi_pct", "mean"),
        avg_cpa=("cpa_usd", "mean"),
        avg_romi=("romi", "mean"),
    ).reindex(tier_order).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    tier_colors = ["#8B5CF6", "#2563EB", "#F59E0B", "#EF4444"]

    # Avg ROI by tier
    axes[0].bar(tier_stats["tier"], tier_stats["avg_roi"], color=tier_colors, edgecolor="white")
    for i, (_, r) in enumerate(tier_stats.iterrows()):
        axes[0].text(i, r["avg_roi"] + 2, f"{r['avg_roi']:.0f}%",
                     ha="center", fontsize=10, fontweight="bold")
    axes[0].axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.4)
    axes[0].set_title("Avg ROI by Influencer Tier", fontweight="bold")
    axes[0].set_ylabel("ROI (%)")

    # Avg CPA by tier
    axes[1].bar(tier_stats["tier"], tier_stats["avg_cpa"], color=tier_colors, edgecolor="white")
    for i, (_, r) in enumerate(tier_stats.iterrows()):
        axes[1].text(i, r["avg_cpa"] + 1, f"${r['avg_cpa']:.0f}",
                     ha="center", fontsize=10, fontweight="bold")
    axes[1].set_title("Avg CPA by Influencer Tier", fontweight="bold")
    axes[1].set_ylabel("Cost Per Acquisition (USD)")

    fig.suptitle("Tier Efficiency Analysis", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "05_tier_efficiency.png")


def chart_cpa_vs_conversions(df):
    fig, ax = plt.subplots(figsize=(9, 6))
    for platform, grp in df.groupby("platform"):
        ax.scatter(grp["cpa_usd"], grp["conversions"],
                   label=platform, color=PLATFORM_COLORS.get(platform, "grey"),
                   s=90, edgecolors="white", linewidths=0.7, alpha=0.85, zorder=3)
    for _, r in df.nlargest(5, "conversions").iterrows():
        ax.annotate(r["influencer_name"].split()[0],
                    (r["cpa_usd"], r["conversions"]),
                    textcoords="offset points", xytext=(6, 3), fontsize=8)
    ax.set_xlabel("Cost Per Acquisition - CPA (USD)", fontsize=11)
    ax.set_ylabel("Total Conversions", fontsize=11)
    ax.set_title("CPA vs Conversions by Platform\n(ideal: low CPA + high conversions = bottom-right)",
                 fontsize=12, fontweight="bold")
    ax.legend(title="Platform", fontsize=9)
    fig.tight_layout()
    save(fig, "06_cpa_vs_conversions.png")


def run():
    print("=== Dashboard Generation ===\n")
    df = load()
    chart_roi_ranking(df)
    chart_engagement_vs_conversion(df)
    chart_spend_vs_revenue(df)
    chart_roi_by_platform(df)
    chart_tier_efficiency(df)
    chart_cpa_vs_conversions(df)
    print(f"\nAll 6 charts saved to dashboard/")


if __name__ == "__main__":
    run()
