"""
Batch runner: runs the significance pipeline across ALL experiments.

Outputs:
  dashboard/master_results.csv   -- one row per experiment, all metrics + verdict
  dashboard/monthly_readout.csv  -- wins/losses grouped by month
"""

import os, sys, csv
sys.path.insert(0, os.path.dirname(__file__))
import config

import numpy as np
import pandas as pd
from importlib import import_module


def load_or_generate() -> pd.DataFrame:
    """Load data from Parquet warehouse if it exists, else generate."""
    events_path = config.TABLE_PATH.replace("/", os.sep)
    if os.path.isdir(events_path):
        print("Loading from Parquet warehouse ...")
        from pyspark.sql import SparkSession
        spark = (SparkSession.builder
                 .appName("ABTest_BatchRunner")
                 .master("local[*]")
                 .config("spark.sql.warehouse.dir", config.WAREHOUSE)
                 .config("spark.driver.memory", "6g")
                 .config("spark.sql.shuffle.partitions", "8")
                 .config("spark.sql.catalogImplementation", "in-memory")
                 .getOrCreate())
        spark.sparkContext.setLogLevel("WARN")
        spark_df = spark.read.parquet(events_path)
        spark_df.createOrReplaceGlobalTempView("ab_events")

        # Collect per-experiment to pandas (one partition at a time to save memory)
        rows = spark_df.collect()
        full_pd = pd.DataFrame([r.asDict() for r in rows])
        spark.stop()
        print(f"  Loaded {len(full_pd):,} rows from Parquet.")
        return full_pd
    else:
        print("Parquet warehouse not found — running data generation ...")
        hive = import_module("02_hive_setup")
        hive.run()
        # After hive setup, recursively call with Parquet now present
        return load_or_generate()


def save_csv(records: list, path: str, cols: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)


def run():
    print("=== Batch Significance Runner ===\n")

    pipeline = import_module("03_significance_pipeline")
    full_pd  = load_or_generate()

    experiment_ids = sorted(full_pd["experiment_id"].unique())
    print(f"\nRunning pipeline for {len(experiment_ids)} experiments ...\n")

    results = []
    for exp_id in experiment_ids:
        print(f"  {exp_id} ...", end=" ", flush=True)
        res = pipeline.run_experiment(full_pd, exp_id)
        results.append(res)
        sig_flag = "[SIG]" if res["significant"] else "     "
        print(f"{sig_flag}  {res['verdict']:35s}  lift={res['conv_lift_pp']:+.3f}pp  "
              f"p_conv={str(res['p_conv'])[:8]:8s}  action={res['recommended_action']}")

    master_df = pd.DataFrame(results)

    # Save master results
    master_path = os.path.join(config.DATA_DIR, "master_results.csv")
    COLS = [
        "experiment_id", "experiment_name",
        "n_control", "n_treatment",
        "ctrl_conv_rate_pct", "treat_conv_rate_pct", "conv_lift_pp", "conv_relative_lift_pct",
        "ctrl_ctr_pct", "treat_ctr_pct", "ctr_lift_pp",
        "ctrl_avg_revenue", "treat_avg_revenue", "rev_lift_usd",
        "chi2_stat_conv", "p_conv",
        "chi2_stat_ctr",  "p_ctr",
        "t_stat_revenue",  "p_revenue",
        "lr_treatment_coef", "lr_odds_ratio", "lr_wald_p",
        "min_p_value", "confidence_pct",
        "verdict", "recommended_action", "significant",
    ]
    save_csv(results, master_path, COLS)
    print(f"\nMaster results saved -> {master_path}")

    # --- Monthly readout ---
    monthly_rows = []
    for month in config.MONTHS:
        month_pd = full_pd[full_pd.exposure_month == month]
        n_sig = 0
        n_pos = 0
        n_neg = 0
        n_null = 0
        for exp_id in experiment_ids:
            sub = month_pd[month_pd.experiment_id == exp_id]
            if len(sub) < 500:
                continue
            res_m = pipeline.run_experiment(month_pd, exp_id)
            if res_m["significant"]:
                n_sig += 1
                if res_m["conv_lift_pp"] > 0:
                    n_pos += 1
                else:
                    n_neg += 1
            else:
                n_null += 1

        n_total = n_pos + n_neg + n_null
        monthly_rows.append({
            "month": month,
            "n_experiments": n_total,
            "n_significant": n_sig,
            "n_positive_lift": n_pos,
            "n_negative_effect": n_neg,
            "n_no_effect": n_null,
            "win_rate_pct": round(n_pos / n_total * 100, 1) if n_total else 0,
        })
        print(f"  {month}: {n_total} exps tested | {n_pos} wins | {n_neg} stops | "
              f"{n_null} inconclusive  (win rate: {monthly_rows[-1]['win_rate_rate_pct'] if False else monthly_rows[-1]['win_rate_pct']}%)")

    monthly_path = os.path.join(config.DATA_DIR, "monthly_readout.csv")
    MONTHLY_COLS = ["month", "n_experiments", "n_significant", "n_positive_lift",
                    "n_negative_effect", "n_no_effect", "win_rate_pct"]
    save_csv(monthly_rows, monthly_path, MONTHLY_COLS)
    print(f"Monthly readout saved -> {monthly_path}")

    # --- Print master table ---
    print("\n" + "="*100)
    print("MASTER RESULTS TABLE")
    print("="*100)
    print(f"{'Exp':10s} {'Name':32s} {'Ctrl%':6s} {'Treat%':6s} {'Lift pp':8s} "
          f"{'Rel%':7s} {'p_conv':10s} {'Verdict':38s} {'Action':25s}")
    print("-"*100)
    for r in results:
        sig_mark = "*" if r["significant"] else " "
        print(f"{r['experiment_id']:10s} {r['experiment_name'][:31]:32s} "
              f"{r['ctrl_conv_rate_pct']:6.3f} {r['treat_conv_rate_pct']:6.3f} "
              f"{r['conv_lift_pp']:+8.3f} {r['conv_relative_lift_pct']:+7.1f}% "
              f"{str(r['p_conv'])[:10]:10s}{sig_mark} "
              f"{r['verdict'][:37]:38s} {r['recommended_action']:25s}")
    print("="*100)
    print(f"\n{sum(1 for r in results if r['significant'])} / {len(results)} experiments statistically significant (alpha=0.05)")

    return master_df, pd.DataFrame(monthly_rows)


if __name__ == "__main__":
    run()
