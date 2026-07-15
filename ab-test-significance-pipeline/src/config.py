"""
Central config: experiment definitions, paths, and Spark settings.
"""
import os

import sys
os.environ["JAVA_HOME"]            = r"C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot"
os.environ["HADOOP_HOME"]          = r"D:\hadoop"
os.environ["PATH"]                 = os.environ["PATH"] + r";D:\hadoop\bin"
os.environ["PYSPARK_PYTHON"]       = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"]= sys.executable

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WAREHOUSE    = os.path.join(PROJECT_ROOT, "warehouse").replace("\\", "/")
DATA_DIR     = os.path.join(PROJECT_ROOT, "dashboard")
TABLE_PATH   = os.path.join(WAREHOUSE, "ab_events").replace("\\", "/")

ALPHA = 0.05   # significance threshold

# 10 experiments with carefully chosen effect sizes so the pipeline's
# detection is meaningful — some win, some null, one negative.
EXPERIMENTS = [
    # (exp_id, name,                          channel,  conv_ctrl, conv_treat, rev_ctrl, rev_treat, n_per_arm)
    ("EXP_001", "Email Welcome Series",        "email",   0.032,   0.042,   18.5,  22.0,  500_000),
    ("EXP_002", "Display Retargeting",         "display", 0.018,   0.026,   12.0,  14.5,  600_000),
    ("EXP_003", "Social Prospecting Null",     "social",  0.015,   0.0155,  10.0,  10.2,  450_000),
    ("EXP_004", "Search Bid Optimisation",     "search",  0.045,   0.055,   35.0,  40.5,  350_000),
    ("EXP_005", "Push Notification Negative",  "app",     0.022,   0.018,   14.0,  12.5,  400_000),
    ("EXP_006", "Loyalty Rewards Offer",       "email",   0.028,   0.040,   22.0,  28.5,  550_000),
    ("EXP_007", "Cross-sell Email Marginal",   "email",   0.035,   0.037,   20.0,  21.0,  300_000),
    ("EXP_008", "Landing Page Optimisation",   "display", 0.040,   0.048,   25.0,  27.5,  480_000),
    ("EXP_009", "Coupon Code Acquisition",     "social",  0.020,   0.030,   15.0,  18.0,  520_000),
    ("EXP_010", "Card Upgrade Offer",          "email",   0.060,   0.060,   45.0,  45.0,  400_000),
]

CHANNELS = ["email", "display", "social", "search", "app"]

# months for exposure_date (2025-10 through 2025-12)
MONTHS = ["2025-10", "2025-11", "2025-12"]
