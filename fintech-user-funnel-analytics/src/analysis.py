"""
Quantitative analysis + dashboard generation for fintech-user-funnel-analytics.
Outputs 6 PNGs to dashboard/ and prints all key metrics.
"""

import os, sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(ROOT, "data", "user_activity.csv")
DASH_DIR = os.path.join(ROOT, "dashboard")
os.makedirs(DASH_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
BRAND   = "#7C3AED"   # purple — youth fintech brand colour
SUCCESS = "#16A34A"
FAIL    = "#EF4444"
WARN    = "#F59E0B"


# ── Helpers ───────────────────────────────────────────────────────────────────

def save(fig, name):
    path = os.path.join(DASH_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {path}")


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["signup_date", "transaction_date"])
    df["age_group"] = df["age"].apply(lambda a: "11–14" if a <= 14 else "15–19")
    return df


# ── Analysis functions ────────────────────────────────────────────────────────

def funnel_metrics(df: pd.DataFrame) -> dict:
    """User journey funnel: Signup → First Txn → 2nd Txn → Active (3+ txns in 30d)."""
    total_users = df["user_id"].nunique()

    # All users have at least one transaction (they're in the dataset)
    first_tx_only = (
        df.groupby("user_id")["transaction_date"]
        .agg(["count", "min"])
        .rename(columns={"count": "tx_count", "min": "first_tx_date"})
        .reset_index()
    )
    signed_up        = total_users
    made_first_tx    = total_users          # everyone has ≥1 tx
    made_second_tx   = (first_tx_only["tx_count"] >= 2).sum()
    # Active = 3+ txns with at least two within 30 days of first
    def is_active(uid):
        user_txs = df[df["user_id"] == uid]["transaction_date"].sort_values().tolist()
        if len(user_txs) < 3:
            return False
        # Check if any 30-day window has 3+ transactions
        for i, t in enumerate(user_txs):
            window = [d for d in user_txs[i:] if (d - t).days <= 30]
            if len(window) >= 3:
                return True
        return False

    active_users = sum(1 for uid in df["user_id"].unique() if is_active(uid))

    # Users who never made a 2nd transaction
    one_tx_users = (first_tx_only["tx_count"] == 1).sum()
    # Of those, how many had a failed first tx?
    user_first_status = df.sort_values("transaction_date").groupby("user_id").first()["status"]
    one_tx_ids   = first_tx_only[first_tx_only["tx_count"] == 1]["user_id"]
    failed_first = user_first_status.loc[one_tx_ids][user_first_status.loc[one_tx_ids] != "success"].count()

    churn_after_fail = failed_first / one_tx_ids.shape[0] if one_tx_ids.shape[0] > 0 else 0

    return {
        "signed_up":       signed_up,
        "made_first_tx":   made_first_tx,
        "made_second_tx":  int(made_second_tx),
        "active_users":    int(active_users),
        "one_tx_users":    int(one_tx_users),
        "failed_first_n":  int(failed_first),
        "churn_after_fail_pct": round(churn_after_fail * 100, 1),
        "first_to_second_pct":  round(made_second_tx / made_first_tx * 100, 1),
        "second_to_active_pct": round(active_users / made_second_tx * 100, 1) if made_second_tx else 0,
        "overall_active_pct":   round(active_users / signed_up * 100, 1),
    }


def failure_by_type(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby("transaction_type")["status"]
        .apply(lambda s: (s != "success").mean() * 100)
        .rename("failure_rate_pct")
        .reset_index()
        .sort_values("failure_rate_pct", ascending=False)
    )
    return result


def failure_by_age_and_type(df: pd.DataFrame) -> pd.DataFrame:
    result = (
        df.groupby(["age_group", "transaction_type"])["status"]
        .apply(lambda s: (s != "success").mean() * 100)
        .rename("failure_rate_pct")
        .reset_index()
    )
    return result


def first_upi_vs_repeat(df: pd.DataFrame) -> dict:
    """Compare first-time UPI failure rate vs repeat UPI failure rate."""
    upi_txs = df[df["transaction_type"] == "UPI Payment"].sort_values("transaction_date")
    # First UPI per user
    first_upi = upi_txs.groupby("user_id").first().reset_index()
    repeat_upi = upi_txs[~upi_txs.index.isin(upi_txs.groupby("user_id").head(1).index)]

    first_fail  = (first_upi["status"] != "success").mean() * 100
    repeat_fail = (repeat_upi["status"] != "success").mean() * 100 if len(repeat_upi) else 0
    return {"first_upi_fail_pct": round(first_fail, 1), "repeat_upi_fail_pct": round(repeat_fail, 1)}


def feature_adoption(df: pd.DataFrame) -> pd.DataFrame:
    total_users = df["user_id"].nunique()
    feat_users  = df.groupby("feature_used")["user_id"].nunique().reset_index()
    feat_users["adoption_pct"] = (feat_users["user_id"] / total_users * 100).round(1)
    feat_users.columns         = ["feature", "unique_users", "adoption_pct"]
    return feat_users.sort_values("adoption_pct", ascending=False)


def cohort_comparison(df: pd.DataFrame) -> pd.DataFrame:
    cohort = df.groupby("age_group").agg(
        users=("user_id", "nunique"),
        avg_amount=("amount_inr", "mean"),
        avg_session=("app_session_length", "mean"),
        success_rate=("status", lambda s: (s == "success").mean() * 100),
        avg_tx_per_user=("user_id", "count"),
    ).reset_index()
    # avg_tx_per_user needs division by user count per group
    tx_per_user = df.groupby(["age_group", "user_id"]).size().groupby("age_group").mean().rename("avg_tx_per_user")
    cohort = cohort.drop(columns=["avg_tx_per_user"]).merge(tx_per_user.reset_index(), on="age_group")
    cohort["avg_amount"]   = cohort["avg_amount"].round(1)
    cohort["avg_session"]  = cohort["avg_session"].round(1)
    cohort["success_rate"] = cohort["success_rate"].round(1)
    cohort["avg_tx_per_user"] = cohort["avg_tx_per_user"].round(1)
    return cohort


def post_failure_churn(df: pd.DataFrame) -> dict:
    """Compare retention between users with successful vs failed first transactions."""
    user_first = (
        df.sort_values("transaction_date")
        .groupby("user_id")
        .agg(first_status=("status", "first"), tx_count=("user_id", "count"))
        .reset_index()
    )
    user_first["first_success"] = user_first["first_status"] == "success"
    success_repeat = (user_first[user_first["first_success"]]["tx_count"] > 1).mean() * 100
    failed_repeat  = (user_first[~user_first["first_success"]]["tx_count"] > 1).mean() * 100
    return {
        "pct_repeat_after_success": round(success_repeat, 1),
        "pct_repeat_after_fail":    round(failed_repeat, 1),
    }


# ── Charts ────────────────────────────────────────────────────────────────────

def chart_funnel(funnel: dict):
    stages  = ["Signed Up", "Made First\nTransaction", "Made Second\nTransaction", "Active User\n(3+ txns/30d)"]
    counts  = [funnel["signed_up"], funnel["made_first_tx"],
               funnel["made_second_tx"], funnel["active_users"]]
    pcts    = [100, 100,
               funnel["first_to_second_pct"],
               funnel["overall_active_pct"]]
    colors  = [BRAND, "#9333EA", "#A855F7", "#C084FC"]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(stages[::-1], counts[::-1], color=colors[::-1], edgecolor="white", height=0.55)

    for bar, count, pct in zip(bars, counts[::-1], pcts[::-1]):
        ax.text(bar.get_width() + funnel["signed_up"] * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{count:,}  ({pct:.0f}%)", va="center", fontsize=10.5, fontweight="bold")

    ax.set_xlim(0, funnel["signed_up"] * 1.28)
    ax.set_xlabel("Number of Users", fontsize=11)
    ax.set_title("User Journey Funnel — Youth Fintech App", fontsize=13, fontweight="bold", pad=12)
    ax.set_yticklabels(stages[::-1], fontsize=10.5)
    ax.tick_params(axis="x", labelsize=9)

    # Drop-off annotations
    drop1 = 100 - funnel["first_to_second_pct"]
    drop2 = funnel["first_to_second_pct"] - funnel["second_to_active_pct"] * funnel["first_to_second_pct"] / 100
    ax.annotate(f"▼ {drop1:.0f}% drop-off",
                xy=(funnel["made_second_tx"], 1), xytext=(funnel["signed_up"] * 0.55, 0.6),
                arrowprops=dict(arrowstyle="->", color=FAIL),
                color=FAIL, fontsize=9.5, fontweight="bold")

    fig.tight_layout()
    save(fig, "01_user_journey_funnel.png")


def chart_failure_by_type(fail_df: pd.DataFrame, upi_detail: dict):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(fail_df["transaction_type"], fail_df["failure_rate_pct"],
                  color=[FAIL if r > 15 else WARN if r > 8 else SUCCESS
                         for r in fail_df["failure_rate_pct"]],
                  edgecolor="white", width=0.6)
    for bar, val in zip(bars, fail_df["failure_rate_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                f"{val:.1f}%", ha="center", fontsize=10.5, fontweight="bold")
    ax.axhline(8, color="grey", linestyle="--", linewidth=1, alpha=0.6, label="Industry avg ~8%")
    ax.set_ylabel("Failure Rate (%)", fontsize=11)
    ax.set_title("Transaction Failure Rate by Type\n"
                 f"(First-time UPI: {upi_detail['first_upi_fail_pct']}%  →  Repeat UPI: {upi_detail['repeat_upi_fail_pct']}%)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, fail_df["failure_rate_pct"].max() * 1.25)
    fig.tight_layout()
    save(fig, "02_failure_rate_by_type.png")


def chart_failure_by_age(age_fail: pd.DataFrame):
    pivot = age_fail.pivot(index="transaction_type", columns="age_group", values="failure_rate_pct")
    pivot = pivot.fillna(0)

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(pivot))
    w = 0.35
    cols = list(pivot.columns)
    colors_grp = [BRAND, "#F59E0B"]
    for i, (col, color) in enumerate(zip(cols, colors_grp)):
        bars = ax.bar(x + (i - 0.5) * w, pivot[col], w, label=col, color=color, edgecolor="white")
        for bar, val in zip(bars, pivot[col]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    f"{val:.1f}%", ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, fontsize=10)
    ax.set_ylabel("Failure Rate (%)", fontsize=11)
    ax.set_title("Transaction Failure Rate: Age 11–14 vs 15–19", fontsize=12, fontweight="bold")
    ax.legend(title="Age Group", fontsize=10)
    ax.set_ylim(0, pivot.values.max() * 1.3)
    fig.tight_layout()
    save(fig, "03_failure_rate_by_age.png")


def chart_feature_adoption(feat: pd.DataFrame, total_users: int):
    feat_sorted = feat.sort_values("adoption_pct")
    bar_colors  = [FAIL if r < 15 else WARN if r < 35 else SUCCESS
                   for r in feat_sorted["adoption_pct"]]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(feat_sorted["feature"], feat_sorted["adoption_pct"],
                   color=bar_colors, edgecolor="white")
    for bar, val, n in zip(bars, feat_sorted["adoption_pct"], feat_sorted["unique_users"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%  ({n} users)", va="center", fontsize=9.5, fontweight="bold")

    ax.set_xlabel("% of Users Who Ever Used This Feature", fontsize=11)
    ax.set_title(f"Feature Adoption Rates  (n = {total_users} users)", fontsize=12, fontweight="bold")
    ax.set_xlim(0, feat_sorted["adoption_pct"].max() * 1.35)

    patches = [
        mpatches.Patch(color=SUCCESS, label="High adoption (≥35%)"),
        mpatches.Patch(color=WARN,    label="Medium (15–34%)"),
        mpatches.Patch(color=FAIL,    label="Low (<15%) — action needed"),
    ]
    ax.legend(handles=patches, fontsize=9, loc="lower right")
    fig.tight_layout()
    save(fig, "04_feature_adoption.png")


def chart_cohort(cohort: pd.DataFrame):
    metrics = [
        ("avg_amount",      "Avg Transaction\nAmount (₹)",      ["#7C3AED", "#F59E0B"]),
        ("avg_tx_per_user", "Avg Transactions\nper User",        ["#7C3AED", "#F59E0B"]),
        ("success_rate",    "Transaction\nSuccess Rate (%)",     ["#7C3AED", "#F59E0B"]),
        ("avg_session",     "Avg Session\nLength (min)",         ["#7C3AED", "#F59E0B"]),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.5))
    for ax, (col, label, colors) in zip(axes, metrics):
        bars = ax.bar(cohort["age_group"], cohort[col], color=colors, edgecolor="white", width=0.5)
        for bar, val in zip(bars, cohort[col]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                    f"{val:.1f}", ha="center", fontsize=11, fontweight="bold")
        ax.set_title(label, fontsize=10, fontweight="bold")
        ax.set_ylim(0, cohort[col].max() * 1.3)
        ax.tick_params(labelsize=9)
    fig.suptitle("Cohort Comparison: Age 11–14 vs 15–19", fontsize=13, fontweight="bold", y=1.04)
    fig.tight_layout()
    save(fig, "05_cohort_comparison.png")


def chart_post_failure_churn(churn: dict, funnel: dict):
    categories = ["After Successful\nFirst Transaction", "After Failed\nFirst Transaction"]
    retained   = [churn["pct_repeat_after_success"], churn["pct_repeat_after_fail"]]
    churned    = [100 - r for r in retained]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(categories))
    w = 0.42
    b1 = ax.bar(x - w/2, retained, w, label="Made 2nd Transaction", color=SUCCESS, edgecolor="white")
    b2 = ax.bar(x + w/2, churned,  w, label="Churned (1 transaction only)", color=FAIL, edgecolor="white")

    for bar, val in zip(list(b1) + list(b2), retained + churned):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{val:.0f}%", ha="center", fontsize=12, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylabel("% of Users", fontsize=11)
    ax.set_ylim(0, 115)
    ax.set_title("Retention After First Transaction\n(Failed vs Successful)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)

    diff = churn["pct_repeat_after_success"] - churn["pct_repeat_after_fail"]
    ax.annotate(f"{diff:.0f}pp\ngap", xy=(0.5, max(retained) * 0.6),
                fontsize=14, fontweight="bold", color=FAIL, ha="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEE2E2", edgecolor=FAIL))

    fig.tight_layout()
    save(fig, "06_post_failure_churn.png")


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=== Fintech User Funnel Analysis ===\n")

    if not os.path.exists(CSV_PATH):
        print("user_activity.csv not found — run: python src/generate_data.py")
        return {}

    df = load()
    print(f"Loaded {len(df):,} transactions  |  {df['user_id'].nunique()} unique users\n")

    funnel     = funnel_metrics(df)
    fail_type  = failure_by_type(df)
    age_fail   = failure_by_age_and_type(df)
    upi_detail = first_upi_vs_repeat(df)
    feat       = feature_adoption(df)
    cohort     = cohort_comparison(df)
    churn      = post_failure_churn(df)

    print("── FUNNEL ──────────────────────────────")
    print(f"  Signed up:               {funnel['signed_up']:,}")
    print(f"  Made first transaction:  {funnel['made_first_tx']:,} (100%)")
    print(f"  Made second transaction: {funnel['made_second_tx']:,} ({funnel['first_to_second_pct']}%)")
    print(f"  Active users (3+/30d):   {funnel['active_users']:,} ({funnel['overall_active_pct']}%)")
    print(f"  Single-tx users:         {funnel['one_tx_users']:,}")
    print()
    print("── FAILURE RATES ──────────────────────")
    print(f"  First-time UPI fail:     {upi_detail['first_upi_fail_pct']}%")
    print(f"  Repeat UPI fail:         {upi_detail['repeat_upi_fail_pct']}%")
    for _, r in fail_type.iterrows():
        print(f"  {r['transaction_type']:<22} {r['failure_rate_pct']:.1f}%")
    print()
    print("── FEATURE ADOPTION ───────────────────")
    for _, r in feat.iterrows():
        print(f"  {r['feature']:<32} {r['adoption_pct']:.1f}%  ({r['unique_users']} users)")
    print()
    print("── POST-FAILURE CHURN ─────────────────")
    print(f"  Retained after success:  {churn['pct_repeat_after_success']}%")
    print(f"  Retained after failure:  {churn['pct_repeat_after_fail']}%")
    print(f"  Gap:                     {churn['pct_repeat_after_success'] - churn['pct_repeat_after_fail']:.0f}pp")
    print()
    print("── COHORT ──────────────────────────────")
    print(cohort.to_string(index=False))
    print()

    print("Generating charts ...")
    chart_funnel(funnel)
    chart_failure_by_type(fail_type, upi_detail)
    chart_failure_by_age(age_fail)
    chart_feature_adoption(feat, df["user_id"].nunique())
    chart_cohort(cohort)
    chart_post_failure_churn(churn, funnel)
    print("\nAll 6 charts saved to dashboard/")

    return {
        "funnel": funnel, "fail_type": fail_type, "upi": upi_detail,
        "feat": feat, "cohort": cohort, "churn": churn
    }


if __name__ == "__main__":
    run()
