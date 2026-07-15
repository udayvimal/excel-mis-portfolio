"""
Hive table setup: write generated data into partitioned Parquet tables.

Tables:
  ab_events        -- raw events, partitioned by experiment_id
  ab_monthly_agg   -- pre-aggregated by experiment + month + variant

Both use Spark SQL catalog (in-memory) over Parquet storage, equivalent
to Hive external tables in a production cluster.
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import config

import numpy as np
import pandas as pd
import shutil

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField,
                                StringType, IntegerType, FloatType)

# Import generator from step 1
from importlib import import_module


def get_spark():
    return (SparkSession.builder
            .appName("ABTest_HiveSetup")
            .master("local[*]")
            .config("spark.sql.warehouse.dir", config.WAREHOUSE)
            .config("spark.driver.memory", "6g")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.sql.catalogImplementation", "in-memory")
            .getOrCreate())


def run():
    print("=== Hive Table Setup ===\n")

    # --- Generate data ---
    gen = import_module("01_generate_data")
    full_pd = gen.run()

    spark = get_spark()
    spark.sparkContext.setLogLevel("WARN")

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

    # --- Write ab_events partitioned by experiment_id ---
    events_path = config.TABLE_PATH
    if os.path.exists(events_path.replace("/", os.sep)):
        shutil.rmtree(events_path.replace("/", os.sep))

    print("Writing ab_events table (partitioned by experiment_id) ...")
    (spark_df.write
     .mode("overwrite")
     .partitionBy("experiment_id")
     .parquet(events_path))
    print(f"  Written -> {events_path}")

    # --- Write monthly aggregation table ---
    monthly_agg = spark_df.groupBy(
        "experiment_id", "experiment_name", "exposure_month", "variant", "channel"
    ).agg(
        F.count("*").alias("n_users"),
        F.sum("clicked").alias("n_clicked"),
        F.sum("converted").alias("n_converted"),
        F.sum("revenue").alias("total_revenue"),
        F.round(F.avg("clicked"), 5).alias("ctr"),
        F.round(F.avg("converted"), 5).alias("conv_rate"),
        F.round(F.avg("revenue"), 4).alias("avg_revenue"),
    )

    monthly_path = os.path.join(config.WAREHOUSE, "ab_monthly_agg").replace("\\", "/")
    if os.path.exists(monthly_path.replace("/", os.sep)):
        shutil.rmtree(monthly_path.replace("/", os.sep))

    (monthly_agg.write
     .mode("overwrite")
     .partitionBy("experiment_id")
     .parquet(monthly_path))
    print(f"  Written monthly agg -> {monthly_path}")

    # --- Register as global temp views for SQL access ---
    spark.read.parquet(events_path).createOrReplaceGlobalTempView("ab_events")
    spark.read.parquet(monthly_path).createOrReplaceGlobalTempView("ab_monthly_agg")

    print("\nRegistered: global_temp.ab_events, global_temp.ab_monthly_agg")

    # Verify with SQL
    print("\nPartition summary (HiveQL via spark.sql):")
    spark.sql("""
        SELECT experiment_id, variant,
               COUNT(*) AS n_users,
               ROUND(AVG(converted)*100, 3) AS conv_pct,
               ROUND(AVG(clicked)*100, 3) AS ctr_pct
        FROM global_temp.ab_events
        GROUP BY experiment_id, variant
        ORDER BY experiment_id, variant
    """).show(25)

    spark.stop()
    print("\nHive table setup complete.")


if __name__ == "__main__":
    run()
