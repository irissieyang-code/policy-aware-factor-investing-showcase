"""
Stage 1: Weighted Event Study (Narrow vs Wide Treatment Definitions)
====================================================================
From: "From Causal Evidence to Actionable Signals: A Dual-Track Framework
       for Policy-Aware Factor Investing in the Sustainable Fuel Sector"

This script implements the weighted event study design described in the paper.
It estimates firm-level Fama-French 5-factor models in a pre-event window,
computes abnormal returns, and tests for policy effects using Patell Z,
Corrado rank test, and cluster bootstrap p-values.

Requirements: pandas, numpy, scipy, statsmodels
Data: Policy_Influenced_Stock_Price_With_FF_5_Factors.csv,
      All_Daily_Policy_Data.csv, Financial_Ratios_Ticker.csv
"""

import os, warnings
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
warnings.filterwarnings("ignore")

# ============================================================
# Configuration
# ============================================================
PRICE_PATH = "Policy Influenced_Stock Price_With FF 5 Factors.csv"
POLICY_PATH = "All_Daily_Policy_Data.csv"
RATIOS_PATH = "Financial Ratios_Ticker.csv"
OUTDIR = "event_outputs"; os.makedirs(OUTDIR, exist_ok=True)

FIRM_COL = "tic"
DATE_COL = "Date"
RET_CANDS = ["daily_return","ret","RET","Ret"]
RF_CANDS  = ["RF","rf","RiskFree","RF*100","R_f"]
FF5       = ["Mkt_RF","SMB","HML","RMW","CMA"]

POLICIES = {
    "IRA":  {"event_dates": ["2022-08-16","2022-09-30","2022-10-01"], "treat_col": "IRA"},
    "LCFS": {"event_dates": ["2023-01-03"], "treat_col": "LCFS"},
    "RFS2": {"event_dates": ["2021-01-04"], "treat_col": "RFS2_Inf"},
}

WINDOWS  = [(0,1), (-1,1), (0,5), (0,10)]
EST_WIN  = (-120, -20)      # estimation window relative to event
BOOT_B   = 2000             # bootstrap iterations
RNG      = np.random.default_rng(1234)

# ============================================================
# Load data
# ============================================================
price     = pd.read_csv(PRICE_PATH, low_memory=False)
policy_df = pd.read_csv(POLICY_PATH, low_memory=False)
ratios    = pd.read_csv(RATIOS_PATH, low_memory=False)

# Parse dates
price[DATE_COL] = pd.to_datetime(price[DATE_COL])
if {"year","month","day"}.issubset(set(policy_df.columns)):
    policy_df[DATE_COL] = pd.to_datetime(policy_df[["year","month","day"]])
elif "Date" in policy_df.columns:
    policy_df[DATE_COL] = pd.to_datetime(policy_df["Date"])

# Identify return and risk-free columns
ret_col = next((c for c in RET_CANDS if c in price.columns), None)
rf_col  = next((c for c in RF_CANDS  if c in price.columns), None)

# Scale returns if stored as percentages
price[ret_col] = pd.to_numeric(price[ret_col], errors="coerce")
if price[ret_col].abs().quantile(0.9) > 1:
    price[ret_col] /= 100.0
if rf_col:
    price[rf_col] = pd.to_numeric(price[rf_col], errors="coerce")
    if price[rf_col].abs().quantile(0.9) > 1:
        price[rf_col] /= 100.0

factor_cols = [c for c in FF5 if c in price.columns]
TRADING_DAYS = pd.to_datetime(price[DATE_COL].drop_duplicates().sort_values().values)

# ============================================================
# Treatment weights (wide definition)
# ============================================================
# Core and edge NAICS codes for each policy
core_lcfs_naics = {325193}
edge_lcfs_naics = {324110, 325199}
core_ira_naics  = {325120}
edge_ira_naics  = {324110, 325199, 325193}

def weight_by_naics(naics_code, core_set, edge_set):
    """Assign value-chain weights: core=1.0, edge=0.5, other=0.0"""
    try: code = int(naics_code)
    except: return 0.0
    if code in core_set: return 1.0
    if code in edge_set: return 0.5
    return 0.0

tic_naics = price[[FIRM_COL,"naics"]].drop_duplicates(FIRM_COL).copy()
tic_naics['LCFS_w'] = tic_naics['naics'].apply(lambda x: weight_by_naics(x, core_lcfs_naics, edge_lcfs_naics))
tic_naics['IRA_w']  = tic_naics['naics'].apply(lambda x: weight_by_naics(x, core_ira_naics,  edge_ira_naics))
price = price.merge(tic_naics[[FIRM_COL,"LCFS_w","IRA_w"]], on=FIRM_COL, how="left") \
             .fillna({'LCFS_w':0.0,'IRA_w':0.0})

# ============================================================
# Factor model estimation
# ============================================================
def fit_factor_model(df_firm, t0):
    """Estimate FF5 factor model in the pre-event estimation window."""
    rel = (df_firm[DATE_COL] - t0).dt.days
    est = df_firm[(rel >= EST_WIN[0]) & (rel <= EST_WIN[1])]
    if est.empty or len(est) < 30:
        return None
    y = est[ret_col] - (est[rf_col] if rf_col else 0.0)
    X = est[factor_cols].copy()
    X = sm.add_constant(X, has_constant="add")
    m = sm.OLS(y, X, missing="drop").fit()
    sigma = np.nanstd(m.resid.values, ddof=max(1, X.shape[1]))
    return {"model": m, "sigma": sigma}

def expected_return(df, fm):
    """Compute expected returns from factor model."""
    if fm is None:
        return pd.Series(0.0, index=df.index)
    X = sm.add_constant(df[factor_cols], has_constant="add")
    return pd.Series(fm["model"].predict(X), index=df.index) + \
           (df[rf_col] if rf_col else 0.0)

# ============================================================
# Test statistics
# ============================================================
def patell_z_from_AR(ar_mat, sigmas, w=None):
    """Weighted Patell Z-statistic (Patell, 1976)."""
    ok = np.isfinite(sigmas) & (sigmas > 0)
    if ok.sum() == 0: return np.nan
    sar = ar_mat[ok] / sigmas[ok][:, None]
    car = np.nansum(sar, axis=1)
    if w is None:
        return np.nanmean(car) / (np.nanstd(car, ddof=1) / np.sqrt(len(car)))
    w = w / np.nansum(w)
    m = np.nansum(w * car)
    v = np.nansum(w * (car - m)**2) / (1 - np.sum(w**2) + 1e-12)
    se = np.sqrt(v / len(car))
    return m / se

def corrado_rank_test(ret_win, ret_est, w=None):
    """Weighted Corrado rank test (Corrado, 1992)."""
    scores = []
    for r_est, r_win in zip(ret_est, ret_win):
        if r_est is None or r_win is None: continue
        pool = np.r_[r_est, r_win]
        if len(pool) < 10: continue
        ranks = stats.rankdata(pool)
        k = len(r_win); rank_evt = ranks[-k:]
        mu = (len(pool) + 1) / 2.0
        var = (len(pool)**2 - 1) / 12.0
        scores.append(((rank_evt - mu).sum()) / np.sqrt(k * var))
    if not scores: return np.nan
    scores = np.array(scores)
    if w is None:
        return np.nanmean(scores) / (np.nanstd(scores, ddof=1) / np.sqrt(len(scores)))
    w = w / np.nansum(w); m = np.nansum(w * scores)
    v = np.nansum(w * (scores - m)**2) / (1 - np.sum(w**2) + 1e-12)
    se = np.sqrt(v / len(scores))
    return m / se

def firm_bootstrap_p(x, w=None, B=BOOT_B):
    """Cluster bootstrap p-value (firm-level resampling)."""
    x = np.array(x); mask = np.isfinite(x); x = x[mask]
    if len(x) == 0: return np.nan
    if w is None:
        obs = np.nanmean(x)
    else:
        w = w[mask]; w = w / np.sum(w); obs = np.sum(w * x)
    boot = []
    for _ in range(B):
        idx = np.random.choice(len(x), size=len(x), replace=True)
        if w is None: boot.append(np.nanmean(x[idx]))
        else: boot.append(np.sum(w[idx] * x[idx]))
    boot = np.asarray(boot)
    return 2 * min((boot >= obs).mean(), (boot <= obs).mean())

# ============================================================
# Main event study loop
# ============================================================
def run_event_study(pol_key, cfg, use_weights=False):
    """Run event study for a given policy under narrow or wide treatment."""
    treat_col = cfg["treat_col"]
    treat_wcol = f"{pol_key}_w" if pol_key in ["IRA","LCFS"] else None
    md = price.copy()
    md[treat_col] = md[treat_col].fillna(0).astype(int)
    results = []
    for ed in cfg["event_dates"]:
        t0 = pd.to_datetime(ed)
        # Estimate factor models for all firms
        firm_models = {tic: fit_factor_model(df, t0)
                       for tic, df in md.groupby(FIRM_COL)}
        for (a, b) in WINDOWS:
            rel = (md[DATE_COL] - t0).dt.days
            sub = md[(rel >= a) & (rel <= b)].copy()
            if sub.empty: continue
            ARs, sigmas, info, corr_win, corr_est = [], [], [], [], []
            win_len = b - a + 1
            for tic, g in sub.groupby(FIRM_COL):
                fm = firm_models.get(tic)
                if fm is None: continue
                exp = expected_return(g, fm)
                ar = (g[ret_col] - exp).values
                if len(ar) != win_len: continue
                ARs.append(ar); sigmas.append(fm["sigma"])
                base_treat = g[treat_col].iloc[0]
                tw = g[treat_wcol].iloc[0] if (use_weights and treat_wcol in g.columns) \
                     else float(base_treat)
                info.append((tic, base_treat, tw))
                # Estimation-window returns for Corrado test
                df_all = md[md[FIRM_COL] == tic]
                rrel = (df_all[DATE_COL] - t0).dt.days
                est_ret = df_all[(rrel >= EST_WIN[0]) & (rrel <= EST_WIN[1])][ret_col].dropna().values
                corr_est.append(est_ret if len(est_ret) > 0 else None)
                corr_win.append(g[ret_col].values)
            if not ARs: continue
            ARs = np.asarray(ARs); sigmas = np.asarray(sigmas)
            info = pd.DataFrame(info, columns=["tic","treat","treat_w"])
            treated = info["treat"] == 1 if not use_weights else info["treat_w"] > 0
            if treated.any():
                AR_treat = ARs[treated.values]; sig_treat = sigmas[treated.values]
                w = info.loc[treated,"treat_w"].values if use_weights else None
                meanAR = np.sum(w * np.nanmean(AR_treat, axis=1)) / np.sum(w) \
                         if use_weights else np.nanmean(AR_treat)
                z_patell = patell_z_from_AR(AR_treat, sig_treat, w)
                z_corr = corrado_rank_test(
                    [corr_win[i] for i, m in enumerate(treated) if m],
                    [corr_est[i] for i, m in enumerate(treated) if m], w)
                p_boot = firm_bootstrap_p(np.nanmean(AR_treat, axis=1), w)
                results.append({
                    "policy": pol_key, "event": t0.date().isoformat(),
                    "window": f"[{a},{b}]", "n_treat": int(treated.sum()),
                    "meanAR_treat": meanAR, "patellZ": z_patell,
                    "corradoZ": z_corr, "p_boot": p_boot
                })
    return pd.DataFrame(results)

# ============================================================
# Run narrow and wide specifications
# ============================================================
ALL_narrow = []; ALL_wide = []
for pol, cfg in POLICIES.items():
    ALL_narrow.append(run_event_study(pol, cfg, use_weights=False))
    ALL_wide.append(run_event_study(pol, cfg, use_weights=True))

ALL_narrow = pd.concat([x for x in ALL_narrow if not x.empty], ignore_index=True)
ALL_wide   = pd.concat([x for x in ALL_wide   if not x.empty], ignore_index=True)

ALL_narrow.to_csv(os.path.join(OUTDIR, "EventStudy_ALL_narrow.csv"), index=False)
ALL_wide.to_csv(os.path.join(OUTDIR, "EventStudy_ALL_weighted.csv"), index=False)

print("Narrow results:\n", ALL_narrow.head())
print("Wide (weighted) results:\n", ALL_wide.head())
