"""
PySpark data generator: 5-10M rows of multi-experiment A/B test events.

Schema:
  user_id       string   unique user identifier
  experiment_id string   EXP_001 ... EXP_010
  experiment_name string
  variant        string  control | treatment
  channel        string  email | display | social | search | app
  exposure_month string  2025-10 | 2025-11 | 2025-12
  clicked        int     1 if clicked
  converted      int     1 if converted (primary KPI)
  revenue        float   revenue amount (0 for non-converters)

Realistic design:
  - 10 concurrent experiments with different effect sizes
  - Some experiments show real lift, some null, one negative
  - Channels are randomised within experiment to allow regression control
  - Total rows: ~9.1M (sum of n_per_arm*2 across experiments)
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import config

import numpy as np
import pandas as pd

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField,
                                StringType, IntegerType, FloatType)

RNG_SEED = 42


def get_spark():
    return (SparkSession.builder
            .appName("ABTest_DataGenerator")
            .master("local[*]")
            .config("spark.sql.warehouse.dir", config.WAREHOUSE)
            .config("spark.driver.memory", "6g")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.sql.catalogImplementation", "in-memory")
            .getOrCreate())


def generate_experiment_pandas(exp: tuple, rng: np.random.Generator) -> pd.DataFrame:
    """Generate one experiment's data as a pandas DataFrame."""
    exp_id, exp_name, primary_channel, conv_ctrl, conv_treat, rev_ctrl, rev_treat, n = exp

    n_ctrl  = n // 2
    n_treat = n - n_ctrl

    # User IDs unique within experiment
    ctrl_ids  = [f"{exp_id}_C_{i:07d}" for i in range(n_ctrl)]
    treat_ids = [f"{exp_id}_T_{i:07d}" for i in range(n_treat)]

    # Channels: primary channel gets 60%, others split equally
    other_channels = [c for c in config.CHANNELS if c != primary_channel]
    channel_probs  = [0.60] + [0.10] * len(other_channels)

    def rand_channels(n_users):
        channels_pool = [primary_channel] + other_channels
        return rng.choice(channels_pool, size=n_users, p=channel_probs)

    # Exposure month (roughly equal split)
    def rand_months(n_users):
        return rng.choice(config.MONTHS, size=n_users)

    # Click rates: ~3x conversion rate
    click_ctrl_r  = min(conv_ctrl * 3.2, 0.35)
    click_treat_r = min(conv_treat * 3.0, 0.40)

    # Control arm
    ctrl_conv = rng.binomial(1, conv_ctrl, n_ctrl)
    ctrl_click = np.maximum(ctrl_conv, rng.binomial(1, click_ctrl_r, n_ctrl))
    ctrl_rev  = np.where(ctrl_conv == 1,
                         rng.normal(rev_ctrl, rev_ctrl * 0.3, n_ctrl).clip(0),
                         0.0)

    # Treatment arm
    treat_conv  = rng.binomial(1, conv_treat, n_treat)
    treat_click = np.maximum(treat_conv, rng.binomial(1, click_treat_r, n_treat))
    treat_rev   = np.where(treat_conv == 1,
                           rng.normal(rev_treat, rev_treat * 0.3, n_treat).clip(0),
                           0.0)

    ctrl_df = pd.DataFrame({
        "user_id":         ctrl_ids,
        "experiment_id":   exp_id,
        "experiment_name": exp_name,
        "variant":         "control",
        "channel":         rand_channels(n_ctrl),
        "exposure_month":  rand_months(n_ctrl),
        "clicked":         ctrl_click.astype(int),
        "converted":       ctrl_conv.astype(int),
        "revenue":         ctrl_rev.round(2).astype(float),
    })

    treat_df = pd.DataFrame({
        "user_id":         treat_ids,
        "experiment_id":   exp_id,
        "experiment_name": exp_name,
        "variant":         "treatment",
        "channel":         rand_channels(n_treat),
        "exposure_month":  rand_months(n_treat),
        "clicked":         treat_click.astype(int),
        "converted":       treat_conv.astype(int),
        "revenue":         treat_rev.round(2).astype(float),
    })

    return pd.concat([ctrl_df, treat_df], ignore_index=True)


def run():
    print("=== Data Generation ===\n")
    spark = get_spark()
    spark.sparkContext.setLogLevel("WARN")

    rng = np.random.default_rng(RNG_SEED)
    all_frames = []

    total_rows = 0
    for exp in config.EXPERIMENTS:
        exp_id = exp[0]
        print(f"  Generating {exp_id}: {exp[1]} ({exp[7]*2:,} rows) ...", end=" ")
        df_pd = generate_experiment_pandas(exp, rng)
        all_frames.append(df_pd)
        total_rows += len(df_pd)
        ctrl_cr  = df_pd[df_pd.variant=="control"]["converted"].mean()*100
        treat_cr = df_pd[df_pd.variant=="treatment"]["converted"].mean()*100
        print(f"ctrl={ctrl_cr:.2f}%  treat={treat_cr:.2f}%  lift={treat_cr-ctrl_cr:+.2f}pp")

    full_pd = pd.concat(all_frames, ignore_index=True)
    print(f"\nTotal rows generated: {total_rows:,}")

    # Convert to Spark DataFrame
    SCHEMA = StructType([
        StructField("user_id",         StringType(),  False),
        StructField("experiment_id",   StringType(),  False),
        StructField("experiment_name", StringType(),  False),
        StructField("variant",         StringType(),  False),
        StructField("channel",         StringType(),  False),
        StructField("exposure_month",  StringType(),  False),
        StructField("clicked",         IntegerType(), False),
        StructField("converted",       IntegerType(), False),
        StructField("revenue",         FloatType(),   False),
    ])

    spark_df = spark.createDataFrame(full_pd, schema=SCHEMA)
    print(f"\nSpark DataFrame created: {spark_df.count():,} rows")
    spark_df.printSchema()

    # Sample check
    print("\nSample by experiment:")
    spark_df.groupBy("experiment_id", "variant").agg(
        F.count("*").alias("n"),
        F.round(F.avg("converted")*100, 3).alias("conv_pct")
    ).orderBy("experiment_id", "variant").show(25)

    spark.stop()
    print("Data generation complete. Spark DF validated.")
    return full_pd


if __name__ == "__main__":
    run()
