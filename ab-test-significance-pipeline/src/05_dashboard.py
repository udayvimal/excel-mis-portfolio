"""
Dashboard generator: 6 charts styled as a leadership report.

Charts:
  01_experiment_ranking.png     -- All experiments ranked by conversion lift (coloured by verdict)
  02_significance_matrix.png    -- p-value heatmap for all 3 tests per experiment
  03_monthly_readout.png        -- Win/loss/inconclusive breakdown by month
  04_revenue_lift.png           -- Revenue lift vs conversion lift scatter
  05_ctr_vs_conversion.png      -- CTR lift vs conversion lift per experiment
  06_executive_summary.png      -- KPI scorecard: top winners, stops, and summary stats
"""

import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
import config

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

DASHBOARD_DIR = config.DATA_DIR
os.makedirs(DASHBOARD_DIR, exist_ok=True)

PALETTE = {
    "Significant lift":             "#2ecc71",
    "Significant negative effect":  "#e74c3c",
    "No significant difference":    "#95a5a6",
    "Significant revenue lift only": "#f39c12",
    "Inconclusive (underpowered)":  "#3498db",
}

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.0)


def load_results() -> tuple:
    master_path  = os.path.join(DASHBOARD_DIR, "master_results.csv")
    monthly_path = os.path.join(DASHBOARD_DIR, "monthly_readout.csv")

    if not os.path.exists(master_path):
        raise FileNotFoundError("Run 04_batch_runner.py first to generate master_results.csv")

    master  = pd.read_csv(master_path)
    monthly = pd.read_csv(monthly_path) if os.path.exists(monthly_path) else pd.DataFrame()
    return master, monthly


def save_fig(fig, name: str):
    path = os.path.join(DASHBOARD_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


def chart_experiment_ranking(master: pd.DataFrame):
    df = master.sort_values("conv_lift_pp", ascending=True).copy()
    colors = [PALETTE.get(v, "#95a5a6") for v in df["verdict"]]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(df["experiment_id"], df["conv_lift_pp"], color=colors, edgecolor="white", linewidth=0.5)

    ax.axvline(0, color="black", linewidth=1.2, linestyle="--", alpha=0.6)
    ax.set_xlabel("Conversion Lift (percentage points)", fontsize=11)
    ax.set_title("Experiments Ranked by Conversion Lift\nGreen = Significant | Red = Negative | Grey = No effect",
                 fontsize=13, fontweight="bold", pad=12)

    for bar, (_, row) in zip(bars, df.iterrows()):
        x = bar.get_width()
        label = f"{row['conv_lift_pp']:+.3f}pp"
        ax.text(x + (0.002 if x >= 0 else -0.002), bar.get_y() + bar.get_height()/2,
                label, va="center", ha="left" if x >= 0 else "right", fontsize=9)

    patches = [mpatches.Patch(color=c, label=l) for l, c in PALETTE.items() if l in df["verdict"].values]
    ax.legend(handles=patches, loc="lower right", fontsize=8)
    ax.set_xlim(df["conv_lift_pp"].min() - 0.15, df["conv_lift_pp"].max() + 0.25)
    fig.tight_layout()
    save_fig(fig, "01_experiment_ranking.png")


def chart_significance_matrix(master: pd.DataFrame):
    cols = ["p_conv", "p_ctr", "p_revenue"]
    labels = ["Conv p-value", "CTR p-value", "Revenue p-value"]
    matrix = master.set_index("experiment_id")[cols].astype(float)
    log_matrix = -np.log10(matrix.clip(lower=1e-300))
    log_matrix.columns = labels

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(log_matrix, annot=True, fmt=".1f", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={"label": "-log10(p)"})
    ax.set_title("Statistical Significance Matrix\n(-log10 p-value; higher = more significant; red line at -log10(0.05)=1.30)",
                 fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    save_fig(fig, "02_significance_matrix.png")


def chart_monthly_readout(monthly: pd.DataFrame):
    if monthly.empty:
        print("  Skipping monthly readout chart (no data)")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Stacked bar
    ax = axes[0]
    months = monthly["month"]
    x = np.arange(len(months))
    w = 0.55
    ax.bar(x, monthly["n_positive_lift"],   w, label="Wins (positive lift)", color="#2ecc71")
    ax.bar(x, monthly["n_no_effect"],       w, bottom=monthly["n_positive_lift"],
           label="No effect", color="#95a5a6")
    ax.bar(x, monthly["n_negative_effect"], w,
           bottom=monthly["n_positive_lift"] + monthly["n_no_effect"],
           label="Stops (negative)", color="#e74c3c")
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.set_ylabel("Number of Experiments")
    ax.set_title("Monthly Experiment Outcomes", fontweight="bold")
    ax.legend(fontsize=9)

    # Win rate line
    ax2 = axes[1]
    ax2.plot(months, monthly["win_rate_pct"], marker="o", color="#2ecc71", linewidth=2.5)
    ax2.axhline(50, color="gray", linestyle="--", alpha=0.5)
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("Win Rate (%)")
    ax2.set_title("Monthly Win Rate", fontweight="bold")
    for i, (m, wr) in enumerate(zip(months, monthly["win_rate_pct"])):
        ax2.annotate(f"{wr:.0f}%", (m, wr), textcoords="offset points",
                     xytext=(0, 10), ha="center", fontsize=11, fontweight="bold")
    fig.suptitle("Monthly Experiment Readout — Leadership Summary", fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, "03_monthly_readout.png")


def chart_revenue_vs_conversion(master: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = [PALETTE.get(v, "#95a5a6") for v in master["verdict"]]
    scatter = ax.scatter(master["conv_lift_pp"], master["rev_lift_usd"],
                         c=colors, s=120, edgecolors="white", linewidths=0.7, zorder=3)
    for _, row in master.iterrows():
        ax.annotate(row["experiment_id"],
                    (row["conv_lift_pp"], row["rev_lift_usd"]),
                    textcoords="offset points", xytext=(6, 3), fontsize=8)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("Conversion Lift (pp)", fontsize=11)
    ax.set_ylabel("Revenue Lift ($/user)", fontsize=11)
    ax.set_title("Revenue Lift vs Conversion Lift\nQuadrant I = double win", fontsize=12, fontweight="bold")
    patches = [mpatches.Patch(color=c, label=l) for l, c in PALETTE.items() if l in master["verdict"].values]
    ax.legend(handles=patches, fontsize=8, loc="upper left")
    fig.tight_layout()
    save_fig(fig, "04_revenue_vs_conversion.png")


def chart_ctr_vs_conversion(master: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = [PALETTE.get(v, "#95a5a6") for v in master["verdict"]]
    ax.scatter(master["ctr_lift_pp"], master["conv_lift_pp"],
               c=colors, s=120, edgecolors="white", linewidths=0.7, zorder=3)
    for _, row in master.iterrows():
        ax.annotate(row["experiment_id"],
                    (row["ctr_lift_pp"], row["conv_lift_pp"]),
                    textcoords="offset points", xytext=(6, 3), fontsize=8)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel("CTR Lift (pp)", fontsize=11)
    ax.set_ylabel("Conversion Lift (pp)", fontsize=11)
    ax.set_title("Click-Through Rate Lift vs Conversion Lift\nStrong experiments appear in Quadrant I",
                 fontsize=12, fontweight="bold")
    patches = [mpatches.Patch(color=c, label=l) for l, c in PALETTE.items() if l in master["verdict"].values]
    ax.legend(handles=patches, fontsize=8, loc="upper left")
    fig.tight_layout()
    save_fig(fig, "05_ctr_vs_conversion.png")


def chart_executive_summary(master: pd.DataFrame, monthly: pd.DataFrame):
    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor("#1a1a2e")

    wins = master[master["verdict"] == "Significant lift"].sort_values("conv_lift_pp", ascending=False)
    stops = master[master["verdict"] == "Significant negative effect"]
    no_eff = master[master["verdict"] == "No significant difference"]
    inconcl = master[~master["experiment_id"].isin(
        pd.concat([wins, stops, no_eff])["experiment_id"] if len(wins) + len(stops) + len(no_eff) > 0
        else pd.DataFrame(columns=["experiment_id"])
    )]

    n_total = len(master)
    n_wins  = len(wins)
    n_stops = len(stops)

    # Title
    ax_title = fig.add_axes([0.0, 0.88, 1.0, 0.12])
    ax_title.set_facecolor("#1a1a2e")
    ax_title.axis("off")
    ax_title.text(0.5, 0.5, "A/B Test Significance Pipeline — Executive Readout",
                  ha="center", va="center", fontsize=16, fontweight="bold",
                  color="white", transform=ax_title.transAxes)

    def kpi_box(ax, val, label, color):
        ax.set_facecolor("#16213e")
        ax.axis("off")
        ax.text(0.5, 0.60, str(val), ha="center", va="center",
                fontsize=30, fontweight="bold", color=color, transform=ax.transAxes)
        ax.text(0.5, 0.20, label, ha="center", va="center",
                fontsize=10, color="#aaaaaa", transform=ax.transAxes)

    ax1 = fig.add_axes([0.02, 0.62, 0.18, 0.24])
    ax2 = fig.add_axes([0.22, 0.62, 0.18, 0.24])
    ax3 = fig.add_axes([0.42, 0.62, 0.18, 0.24])
    ax4 = fig.add_axes([0.62, 0.62, 0.18, 0.24])
    ax5 = fig.add_axes([0.82, 0.62, 0.18, 0.24])

    kpi_box(ax1, n_total,            "Experiments Tested",        "#ffffff")
    kpi_box(ax2, n_wins,             "Significant Wins",          "#2ecc71")
    kpi_box(ax3, n_stops,            "Stopped (Negative)",        "#e74c3c")
    win_rate = round(n_wins / n_total * 100) if n_total else 0
    kpi_box(ax4, f"{win_rate}%",     "Win Rate",                  "#f39c12")
    avg_lift = round(wins["conv_lift_pp"].mean(), 3) if len(wins) else 0
    kpi_box(ax5, f"+{avg_lift}pp",   "Avg Lift (Winners)",        "#3498db")

    # Top winners table
    ax_wins = fig.add_axes([0.02, 0.06, 0.55, 0.50])
    ax_wins.set_facecolor("#16213e")
    ax_wins.axis("off")
    ax_wins.text(0.02, 0.96, "Top Experiments to Scale", fontsize=11, fontweight="bold",
                 color="white", transform=ax_wins.transAxes, va="top")

    top_n = wins.head(5) if len(wins) > 0 else master.sort_values("conv_lift_pp", ascending=False).head(5)
    headers = ["Exp", "Name", "Lift", "p-value", "Action"]
    col_xs = [0.02, 0.18, 0.62, 0.76, 0.88]
    y0 = 0.82
    for j, h in enumerate(headers):
        ax_wins.text(col_xs[j], y0, h, fontsize=9, fontweight="bold",
                     color="#aaaaaa", transform=ax_wins.transAxes)
    for i, (_, row) in enumerate(top_n.iterrows()):
        y = y0 - 0.15 * (i + 1)
        vals = [row["experiment_id"], row["experiment_name"][:20],
                f"{row['conv_lift_pp']:+.3f}pp",
                f"{row['p_conv']:.2e}" if not pd.isna(row["p_conv"]) else "n/a",
                "SCALE"]
        colors_row = ["white", "#eeeeee", "#2ecc71", "#aaaaaa", "#2ecc71"]
        for j, (val, clr) in enumerate(zip(vals, colors_row)):
            ax_wins.text(col_xs[j], y, str(val), fontsize=8.5, color=clr,
                         transform=ax_wins.transAxes)

    # Donut chart
    ax_donut = fig.add_axes([0.62, 0.06, 0.36, 0.50])
    ax_donut.set_facecolor("#16213e")
    sizes  = [n_wins, n_stops, len(no_eff), len(inconcl)]
    clrs   = ["#2ecc71", "#e74c3c", "#95a5a6", "#3498db"]
    lbls   = ["Scale", "Stop", "No effect", "Monitor"]
    valid  = [(s, c, l) for s, c, l in zip(sizes, clrs, lbls) if s > 0]
    if valid:
        wedge, texts, auto = ax_donut.pie(
            [v[0] for v in valid],
            colors=[v[1] for v in valid],
            labels=[v[2] for v in valid],
            autopct="%1.0f%%",
            pctdistance=0.75,
            startangle=90,
            wedgeprops={"linewidth": 2, "edgecolor": "#1a1a2e"},
            textprops={"color": "white", "fontsize": 9},
        )
        circle = plt.Circle((0, 0), 0.50, color="#16213e")
        ax_donut.add_artist(circle)
    ax_donut.set_title("Experiment Outcomes", color="white", fontsize=10, fontweight="bold")

    save_fig(fig, "06_executive_summary.png")


def run():
    print("=== Dashboard Generation ===\n")
    master, monthly = load_results()

    chart_experiment_ranking(master)
    chart_significance_matrix(master)
    chart_monthly_readout(monthly)
    chart_revenue_vs_conversion(master)
    chart_ctr_vs_conversion(master)
    chart_executive_summary(master, monthly)

    print("\nAll 6 dashboard charts generated.")


if __name__ == "__main__":
    run()
