"""
Generates synthetic fintech user activity dataset (~3,000 transaction rows).

Realistic patterns baked in:
  - First-time UPI failure rate: ~32%  (drops to ~7% on repeat)
  - Post-failed-first-tx churn: ~62% of affected users never return
  - Bill Split adopted by only ~9% of users (complex UX, low discoverability)
  - Age 11-14: top-up heavy, parental controls, lower amounts (avg ₹160)
  - Age 15-19: UPI/peer-transfer heavy, higher amounts (avg ₹370)
  - Younger users have shorter active windows, older teens transact more
"""

import os, random, csv
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
random.seed(42)

ROOT     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ─── Parameters ───────────────────────────────────────────────────────────────
N_USERS       = 580
SIGNUP_START  = datetime(2024, 1, 1)
SIGNUP_END    = datetime(2025, 2, 28)

# (prob_11_14, prob_15_19, base_fail_rate, avg_amt_young, avg_amt_old)
TX_CONFIG = {
    "UPI Payment":    (0.18, 0.38, None,  170, 390),   # first-time fail handled separately
    "Card Top-up":    (0.40, 0.22, 0.05,  140, 230),
    "Peer Transfer":  (0.14, 0.26, 0.11,   90, 280),
    "Bill Split":     (0.06, 0.08, 0.17,  110, 190),   # low adoption
}

# Features associated with each transaction type
FEATURE_MAP = {
    "UPI Payment":   ["send money", "scan & pay", "rewards"],
    "Card Top-up":   ["top-up", "spending limit set by parent", "cashback tracker"],
    "Peer Transfer": ["send money", "split with friends"],
    "Bill Split":    ["split with friends", "send money"],
}

# Feature weights by age group (11-14 vs 15-19)
FEATURE_AGE_WEIGHTS = {
    "send money":                  (0.6,  1.0),
    "scan & pay":                  (0.5,  1.0),
    "top-up":                      (1.0,  0.5),
    "spending limit set by parent": (1.0,  0.05),  # almost exclusively young
    "cashback tracker":            (0.4,  1.0),
    "rewards":                     (0.7,  1.0),
    "split with friends":          (0.3,  1.0),
}


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = (end - start).days
    return start + timedelta(days=int(RNG.integers(0, delta)))


def pick_tx_type(age: int) -> str:
    is_young = age <= 14
    types = list(TX_CONFIG.keys())
    weights = [TX_CONFIG[t][0] if is_young else TX_CONFIG[t][1] for t in types]
    total = sum(weights)
    weights = [w / total for w in weights]
    return RNG.choice(types, p=weights)


def pick_feature(tx_type: str, age: int) -> str:
    candidates = FEATURE_MAP[tx_type]
    is_young   = age <= 14
    weights    = [FEATURE_AGE_WEIGHTS[f][0 if is_young else 1] for f in candidates]
    total      = sum(weights)
    if total == 0:
        return candidates[0]
    weights = [w / total for w in weights]
    return RNG.choice(candidates, p=weights)


def tx_status(tx_type: str, is_first_upi: bool, age: int) -> str:
    if tx_type == "UPI Payment" and is_first_upi:
        fail_p = 0.32
    else:
        base_fail = TX_CONFIG[tx_type][2]
        fail_p = base_fail if base_fail else 0.07

    r = float(RNG.uniform())
    if r < fail_p * 0.55:
        return "failed"
    elif r < fail_p:
        return "declined"
    return "success"


def tx_amount(tx_type: str, age: int) -> float:
    idx = 3 if age <= 14 else 4
    mean_amt = TX_CONFIG[tx_type][idx]
    amount = float(RNG.normal(mean_amt, mean_amt * 0.38))
    return round(max(10.0, amount), 2)


def session_length(is_first: bool, status: str) -> float:
    if is_first:
        base = float(RNG.uniform(8.0, 18.0))
    else:
        base = float(RNG.uniform(2.5, 9.0))
    if status != "success":
        base *= float(RNG.uniform(1.2, 1.6))  # frustrated users stay longer trying to fix
    return round(base, 1)


def num_transactions(age: int, first_tx_failed: bool) -> int:
    if first_tx_failed:
        # 62% churn: 1 transaction only; rest continue but fewer
        if RNG.uniform() < 0.62:
            return 1
        return int(RNG.integers(2, 6))
    if age <= 14:
        return int(RNG.choice([1,2,3,4,5,6,8,10,12], p=[0.10,0.15,0.18,0.18,0.15,0.10,0.07,0.04,0.03]))
    else:
        return int(RNG.choice([1,2,3,4,5,6,8,10,12,15,20], p=[0.07,0.10,0.14,0.16,0.14,0.12,0.10,0.07,0.05,0.03,0.02]))


def generate() -> pd.DataFrame:
    # Age distribution: skewed toward 14-17
    age_pool    = list(range(11, 20))
    age_weights = [0.05, 0.09, 0.14, 0.18, 0.20, 0.16, 0.10, 0.06, 0.02]

    all_rows = []

    for uid in range(1, N_USERS + 1):
        age       = int(RNG.choice(age_pool, p=age_weights))
        signup_dt = rand_date(SIGNUP_START, SIGNUP_END)
        upi_count = 0  # tracks UPI attempts for this user

        # First transaction: within 3-12 days of signup (some users are slow to transact)
        days_to_first = int(RNG.integers(1, 12))
        first_tx_dt   = signup_dt + timedelta(days=days_to_first)

        # Determine first transaction
        first_type   = pick_tx_type(age)
        is_first_upi = first_type == "UPI Payment"
        if is_first_upi:
            upi_count += 1
        first_status = tx_status(first_type, is_first_upi, age)
        first_failed = first_status != "success"

        n_tx = num_transactions(age, first_failed)

        for t_idx in range(n_tx):
            if t_idx == 0:
                tx_dt   = first_tx_dt
                tx_type = first_type
                status  = first_status
                is_first = True
            else:
                # Subsequent transactions: spread over next 30-180 days
                gap    = int(RNG.integers(1, 25)) * (2 if first_failed else 1)
                tx_dt  = first_tx_dt + timedelta(days=int(RNG.integers(t_idx * 3, t_idx * 25 + 10)))
                tx_type = pick_tx_type(age)
                is_first_upi_now = (tx_type == "UPI Payment" and upi_count == 0)
                if tx_type == "UPI Payment":
                    upi_count += 1
                status  = tx_status(tx_type, is_first_upi_now, age)
                is_first = False

            feature = pick_feature(tx_type, age)
            amount  = tx_amount(tx_type, age)
            slen    = session_length(is_first, status)

            # Cap transaction date at today-ish
            if tx_dt > datetime(2025, 6, 1):
                tx_dt = datetime(2025, 6, 1) - timedelta(days=int(RNG.integers(1, 15)))

            all_rows.append({
                "user_id":             f"USR_{uid:04d}",
                "age":                 age,
                "signup_date":         signup_dt.strftime("%Y-%m-%d"),
                "transaction_date":    tx_dt.strftime("%Y-%m-%d"),
                "transaction_type":    tx_type,
                "amount_inr":          amount,
                "status":              status,
                "feature_used":        feature,
                "app_session_length":  slen,
            })

    df = pd.DataFrame(all_rows)
    out = os.path.join(DATA_DIR, "user_activity.csv")
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} rows ({df['user_id'].nunique()} users) -> {out}")
    return df


if __name__ == "__main__":
    generate()
