"""
Master runner: executes the full pipeline in order.
  1. Generate data (PySpark)
  2. Write Hive tables (Parquet + global temp views)
  3. Run batch significance pipeline across all experiments
  4. Generate dashboard charts
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from importlib import import_module


def run():
    print("\n" + "="*60)
    print("  AB-TEST SIGNIFICANCE PIPELINE  ")
    print("="*60 + "\n")

    print("STEP 2: Hive table setup ...")
    hive = import_module("02_hive_setup")
    hive.run()

    print("\nSTEP 3: Batch significance runner ...")
    batch = import_module("04_batch_runner")
    batch.run()

    print("\nSTEP 4: Dashboard generation ...")
    dash = import_module("05_dashboard")
    dash.run()

    print("\n" + "="*60)
    print("  PIPELINE COMPLETE")
    print("="*60)
    print("Outputs:")
    print("  dashboard/master_results.csv")
    print("  dashboard/monthly_readout.csv")
    print("  dashboard/01_experiment_ranking.png")
    print("  dashboard/02_significance_matrix.png")
    print("  dashboard/03_monthly_readout.png")
    print("  dashboard/04_revenue_vs_conversion.png")
    print("  dashboard/05_ctr_vs_conversion.png")
    print("  dashboard/06_executive_summary.png")


if __name__ == "__main__":
    run()
