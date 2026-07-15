"""
Core significance-testing pipeline.

For ANY experiment_id, computes:
  - Sample sizes per variant
  - Conversion rate, CTR, avg revenue per variant
  - Chi-square test: conversion (binary)
  - Chi-square test: click-through (binary)
  - Welch t-test: revenue (continuous)
  - Logistic regression: converted ~ variant + channel (effect size controlling for channel)
  - Verdict: "Significant lift" / "No significant difference" / "Significant negative effect"
  - Recommended action: scale / stop / inconclusive / monitor

Usage:
  from src.significance_pipeline import run_experiment
  result = run_experiment(df_pandas, experiment_id="EXP_001")
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import config

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")

ALPHA = config.ALPHA


def chi2_test(n_pos_a: int, n_total_a: int,
              n_pos_b: int, n_total_b: int) -> tuple:
    """Chi-square test of independence for a 2x2 contingency table."""
    contingency = np.array([
        [n_pos_a,   n_total_a - n_pos_a],
        [n_pos_b,   n_total_b - n_pos_b],
    ])
    if contingency.min() < 5:
        return (np.nan, np.nan, "insufficient_sample")
    stat, p, dof, _ = chi2_contingency(contingency, correction=False)
    return (round(stat, 4), round(p, 6), "ok")


def t_test_revenue(ctrl_rev: np.ndarray, treat_rev: np.ndarray) -> tuple:
    """Welch t-test on revenue distributions."""
    if len(ctrl_rev) < 30 or len(treat_rev) < 30:
        return (np.nan, np.nan)
    stat, p = ttest_ind(treat_rev, ctrl_rev, equal_var=False)
    return (round(float(stat), 4), round(float(p), 6))


def logistic_regression_effect(df: pd.DataFrame) -> dict:
    """
    Logistic regression: converted ~ is_treatment + channel_encoded.
    Returns treatment coefficient (log-odds), odds ratio, and p-approx via Wald test.
    """
    sub = df[["variant", "channel", "converted"]].copy()
    sub["is_treatment"] = (sub["variant"] == "treatment").astype(int)

    le = LabelEncoder()
    sub["channel_enc"] = le.fit_transform(sub["channel"])

    X = sub[["is_treatment", "channel_enc"]].values
    y = sub["converted"].values

    if y.sum() < 10 or (1 - y).sum() < 10:
        return {"coef_treatment": np.nan, "odds_ratio": np.nan, "wald_p": np.nan}

    try:
        model = LogisticRegression(max_iter=300, solver="lbfgs")
        model.fit(X, y)
        coef = float(model.coef_[0][0])          # treatment coefficient (log-odds)
        odds_ratio = round(np.exp(coef), 4)

        # Wald approximation for p-value
        n = len(y)
        se = np.sqrt(1 / n)                       # rough SE approximation
        z  = coef / (se + 1e-10)
        from scipy.stats import norm
        wald_p = round(float(2 * norm.sf(abs(z))), 6)

        return {"coef_treatment": round(coef, 5), "odds_ratio": odds_ratio, "wald_p": wald_p}
    except Exception:
        return {"coef_treatment": np.nan, "odds_ratio": np.nan, "wald_p": np.nan}


def verdict(conv_lift_pp: float, p_conv: float,
            rev_lift_pp: float, p_rev: float) -> tuple:
    """
    Returns (verdict_str, recommended_action) based on test results.
    """
    sig_conv = (not np.isnan(p_conv)) and (p_conv < ALPHA)
    sig_rev  = (not np.isnan(p_rev))  and (p_rev  < ALPHA)
    any_sig  = sig_conv or sig_rev

    if any_sig and conv_lift_pp > 0:
        v = "Significant lift"
        a = "Scale campaign"
    elif any_sig and conv_lift_pp < 0:
        v = "Significant negative effect"
        a = "Stop campaign immediately"
    elif any_sig and abs(conv_lift_pp) < 0.1:
        v = "Significant revenue lift only"
        a = "Monitor and extend"
    else:
        if abs(conv_lift_pp) < 0.05:
            v = "No significant difference"
            a = "Stop (no effect)"
        else:
            v = "Inconclusive (underpowered)"
            a = "Extend experiment"

    return v, a


def run_experiment(df: pd.DataFrame, experiment_id: str) -> dict:
    """
    Run full significance pipeline for a single experiment.

    Parameters
    ----------
    df            : full experiment dataset (all experiments or filtered)
    experiment_id : e.g. "EXP_001"

    Returns
    -------
    dict with all metrics, test statistics, and verdict
    """
    exp_df   = df[df.experiment_id == experiment_id].copy()
    ctrl_df  = exp_df[exp_df.variant == "control"]
    treat_df = exp_df[exp_df.variant == "treatment"]

    exp_name = exp_df["experiment_name"].iloc[0] if len(exp_df) > 0 else experiment_id

    n_ctrl   = len(ctrl_df)
    n_treat  = len(treat_df)

    # --- Rates ---
    ctrl_conv  = ctrl_df["converted"].sum()
    treat_conv = treat_df["converted"].sum()
    ctrl_click = ctrl_df["clicked"].sum()
    treat_click= treat_df["clicked"].sum()

    ctrl_conv_rate  = ctrl_conv  / n_ctrl  if n_ctrl  else np.nan
    treat_conv_rate = treat_conv / n_treat if n_treat else np.nan
    ctrl_ctr        = ctrl_click / n_ctrl  if n_ctrl  else np.nan
    treat_ctr       = treat_click/ n_treat if n_treat else np.nan
    ctrl_rev        = ctrl_df["revenue"].mean()
    treat_rev       = treat_df["revenue"].mean()

    conv_lift_pp   = (treat_conv_rate - ctrl_conv_rate) * 100
    ctr_lift_pp    = (treat_ctr       - ctrl_ctr)       * 100
    rev_lift_pp    = (treat_rev       - ctrl_rev)
    conv_rel_lift  = (conv_lift_pp / (ctrl_conv_rate * 100) * 100) if ctrl_conv_rate else np.nan

    # --- Statistical tests ---
    chi2_conv, p_conv, _ = chi2_test(treat_conv, n_treat, ctrl_conv, n_ctrl)
    chi2_ctr,  p_ctr,  _ = chi2_test(treat_click, n_treat, ctrl_click, n_ctrl)
    t_stat_rev, p_rev    = t_test_revenue(ctrl_df["revenue"].values,
                                           treat_df["revenue"].values)

    # --- Logistic regression ---
    lr_result = logistic_regression_effect(exp_df)

    # --- Confidence level ---
    min_p = min(v for v in [p_conv, p_ctr, p_rev] if not np.isnan(v)) if any(
        not np.isnan(v) for v in [p_conv, p_ctr, p_rev]) else 1.0
    confidence = round((1 - min_p) * 100, 2)

    # --- Verdict ---
    v_str, action = verdict(conv_lift_pp, p_conv, rev_lift_pp, p_rev)

    return {
        "experiment_id":        experiment_id,
        "experiment_name":      exp_name,
        "n_control":            n_ctrl,
        "n_treatment":          n_treat,
        "ctrl_conv_rate_pct":   round(ctrl_conv_rate * 100, 4),
        "treat_conv_rate_pct":  round(treat_conv_rate * 100, 4),
        "conv_lift_pp":         round(conv_lift_pp, 4),
        "conv_relative_lift_pct": round(conv_rel_lift, 2) if not np.isnan(conv_rel_lift) else np.nan,
        "ctrl_ctr_pct":         round(ctrl_ctr * 100, 4),
        "treat_ctr_pct":        round(treat_ctr * 100, 4),
        "ctr_lift_pp":          round(ctr_lift_pp, 4),
        "ctrl_avg_revenue":     round(ctrl_rev, 4),
        "treat_avg_revenue":    round(treat_rev, 4),
        "rev_lift_usd":         round(rev_lift_pp, 4),
        "chi2_stat_conv":       chi2_conv,
        "p_conv":               p_conv,
        "chi2_stat_ctr":        chi2_ctr,
        "p_ctr":                p_ctr,
        "t_stat_revenue":       t_stat_rev,
        "p_revenue":            p_rev,
        "lr_treatment_coef":    lr_result["coef_treatment"],
        "lr_odds_ratio":        lr_result["odds_ratio"],
        "lr_wald_p":            lr_result["wald_p"],
        "min_p_value":          round(min_p, 6),
        "confidence_pct":       confidence,
        "verdict":              v_str,
        "recommended_action":   action,
        "significant":          min_p < ALPHA,
    }


if __name__ == "__main__":
    print("Significance pipeline module — import run_experiment() to use.")
    print("Run 04_batch_runner.py to process all experiments.")
