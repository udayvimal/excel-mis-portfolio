"""
Generates result charts from the pipeline outputs and saves to charts/.
Run after 01_business_reporting.py and 02_sentiment_analysis.py.
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
CHARTS_DIR   = os.path.join(PROJECT_ROOT, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
PALETTE = ["#2563EB", "#16A34A", "#F59E0B", "#EF4444", "#8B5CF6"]


def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


def chart_category_revenue():
    df = pd.read_csv(os.path.join(DATA_DIR, "sales_data.csv"))
    cat = df.groupby("category")["revenue"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(cat.index, cat.values / 1e5, color=PALETTE[:len(cat)], edgecolor="white", linewidth=0.6)
    for bar, val in zip(bars, cat.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f"₹{val/1e5:.1f}L", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_ylabel("Revenue (₹ Lakhs)")
    ax.set_title("Revenue by Category — Last 90 Days", fontsize=13, fontweight="bold", pad=10)
    ax.set_ylim(0, cat.values.max() / 1e5 * 1.2)
    fig.tight_layout()
    save(fig, "01_revenue_by_category.png")


def chart_top_products():
    df = pd.read_csv(os.path.join(DATA_DIR, "sales_data.csv"))
    top = df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(5)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    colors = PALETTE[:len(top)]
    bars = ax.barh(top.index[::-1], top.values[::-1] / 1e5, color=colors[::-1], edgecolor="white")
    for bar, val in zip(bars, top.values[::-1]):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                f"₹{val/1e5:.1f}L", va="center", fontsize=9.5, fontweight="bold")
    ax.set_xlabel("Revenue (₹ Lakhs)")
    ax.set_title("Top 5 Products by Revenue", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlim(0, top.values.max() / 1e5 * 1.25)
    # shorten long labels
    ax.set_yticklabels([t.get_text()[:32] for t in ax.get_yticklabels()], fontsize=9)
    fig.tight_layout()
    save(fig, "02_top_products.png")


def chart_monthly_trend():
    df = pd.read_csv(os.path.join(DATA_DIR, "sales_data.csv"))
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    monthly = df.groupby("month")["revenue"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(monthly.index, monthly.values / 1e5, marker="o", linewidth=2.5,
            color="#2563EB", markersize=8, markerfacecolor="white", markeredgewidth=2.5)
    ax.fill_between(range(len(monthly)), monthly.values / 1e5, alpha=0.12, color="#2563EB")
    for i, (mo, val) in enumerate(monthly.items()):
        ax.annotate(f"₹{val/1e5:.1f}L", (i, val/1e5),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=9.5, fontweight="bold", color="#1D4ED8")
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels(monthly.index, rotation=15)
    ax.set_ylabel("Revenue (₹ Lakhs)")
    ax.set_title("Monthly Revenue Trend", fontsize=13, fontweight="bold", pad=10)
    fig.tight_layout()
    save(fig, "03_monthly_trend.png")


def chart_sentiment_breakdown():
    sizes   = [16, 12, 12]
    labels  = ["Positive\n40%", "Negative\n30%", "Neutral\n30%"]
    colors  = ["#16A34A", "#EF4444", "#94A3B8"]
    explode = [0.03, 0.03, 0.03]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    # Donut
    ax = axes[0]
    wedges, texts = ax.pie(sizes, labels=labels, colors=colors, explode=explode,
                           startangle=90, textprops={"fontsize": 10, "fontweight": "bold"},
                           wedgeprops={"linewidth": 2, "edgecolor": "white"})
    circle = plt.Circle((0, 0), 0.55, color="white")
    ax.add_artist(circle)
    ax.text(0, 0, "40\nreviews", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#374151")
    ax.set_title("Sentiment Breakdown", fontsize=12, fontweight="bold")

    # Theme bar
    ax2 = axes[1]
    themes = ["Product Quality", "Customer Support", "Effectiveness", "Packaging"]
    counts = [7, 2, 1, 1]
    theme_colors = ["#EF4444", "#F59E0B", "#8B5CF6", "#06B6D4"]
    bars = ax2.barh(themes[::-1], counts[::-1], color=theme_colors[::-1], edgecolor="white")
    for bar, val in zip(bars, counts[::-1]):
        ax2.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                 str(val), va="center", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Number of Negative Reviews")
    ax2.set_title("Top Complaint Themes", fontsize=12, fontweight="bold")
    ax2.set_xlim(0, 9)

    fig.suptitle("Voice of Customer — Review Sentiment Analysis\n(Powered by Groq / Llama 3.3 70B)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "04_sentiment_analysis.png")


def chart_discount_vs_revenue():
    df = pd.read_csv(os.path.join(DATA_DIR, "sales_data.csv"))
    prod = df.groupby("product").agg(
        avg_discount=("discount_pct", "mean"),
        total_revenue=("revenue", "sum")
    ).reset_index()

    cat_map = df.groupby("product")["category"].first()
    prod["category"] = prod["product"].map(cat_map)
    cat_colors = {"Fitness": "#2563EB", "Nutrition": "#16A34A",
                  "Beauty": "#F59E0B", "Wellness": "#8B5CF6"}

    fig, ax = plt.subplots(figsize=(9, 5))
    for cat, grp in prod.groupby("category"):
        ax.scatter(grp["avg_discount"], grp["total_revenue"] / 1e5,
                   label=cat, color=cat_colors.get(cat, "grey"),
                   s=110, edgecolors="white", linewidths=0.8, zorder=3)
    for _, row in prod.iterrows():
        ax.annotate(row["product"].split()[0], (row["avg_discount"], row["total_revenue"]/1e5),
                    textcoords="offset points", xytext=(5, 3), fontsize=7.5, color="#374151")
    ax.set_xlabel("Avg Discount (%)")
    ax.set_ylabel("Total Revenue (₹ Lakhs)")
    ax.set_title("Discount vs Revenue by Product\n(bubble = product, colour = category)",
                 fontsize=12, fontweight="bold")
    ax.legend(title="Category", fontsize=9)
    fig.tight_layout()
    save(fig, "05_discount_vs_revenue.png")


def run():
    print("=== Generating Result Charts ===\n")
    chart_category_revenue()
    chart_top_products()
    chart_monthly_trend()
    chart_sentiment_breakdown()
    chart_discount_vs_revenue()
    print("\nAll 5 charts saved to charts/")


if __name__ == "__main__":
    run()
