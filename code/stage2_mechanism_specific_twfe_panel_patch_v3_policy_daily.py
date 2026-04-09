"""
Stage 2 Patch v3: Mechanism-Specific TWFE Panel with Policy-Specific Daily Intensities
======================================================================================
This version upgrades the earlier patch by reading policy-specific mechanism
intensity columns from:

    All_Daily_Policy_Data_with_policy_mechanisms_v1.csv

instead of assigning all mechanisms the same fallback `dpi01`.

For each policy, the script expects daily columns:

    IRA_subsidy_intensity_t
    IRA_compliance_intensity_t
    IRA_credit_market_intensity_t
    IRA_demand_pull_intensity_t

(and likewise for LCFS and RFS2).

If a policy-specific mechanism column is unavailable, the script falls back to
the shared normalized daily index `dpi01`.
"""

import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")

PRICE_PATH = "Policy Influenced_Stock Price_With FF 5 Factors.csv"
RATIOS_PATH = "Financial Ratios_Ticker.csv"
POLICY_PATH = "All_Daily_Policy_Data_with_policy_mechanisms_v1.csv"
INTEGRATION_MAP_PATH = "p2_stage2_integration_map_v2_with_alt_bridge.csv"
OUTDIR = "stage2_mechanism_outputs_v2"
os.makedirs(OUTDIR, exist_ok=True)

POLICIES = {
    "IRA":  {"event_dates": ["2022-08-16"], "core_naics": {325120},
             "edge_naics": {324110, 325199, 325193}},
    "LCFS": {"event_dates": ["2023-01-03"], "core_naics": {325193},
             "edge_naics": {324110, 325199}},
    "RFS2": {"event_dates": ["2021-01-04"], "core_naics": {325193},
             "edge_naics": {324110, 325199}},
}

PRE_EXPOSURE_DAYS = 120
POST_DAYS_AR = 10
RUN_BASELINE_MODEL = True
RUN_MECHANISM_MODEL = True
RUN_MAIN_SAMPLE_ONLY = False
ALLOW_ALT_PROVISIONAL = True

FIRM_KEYS = ["tic", "TICKER", "Ticker", "permno", "PERMNO"]
DATE_KEYS = ["Date", "date", "DATE"]
RET_KEYS = ["daily_return", "ret", "RET", "Ret"]
RF_KEYS = ["RF", "rf", "RiskFree", "RF*100", "R_f"]
FF5_LIST = ["Mkt_RF", "SMB", "HML", "RMW", "CMA"]
PX_KEYS = ["adj_close", "Adj Close", "close", "Close", "PRC", "prc", "PX_LAST", "Price"]
SHR_KEYS = ["shares_outstanding", "SHROUT", "shrout", "shares", "csho", "CSHO"]
CAP_KEYS = ["market_cap", "MarketCap", "MktCap", "mktcap", "ME", "me"]
ASSET_KEYS = ["AT", "ATQ", "at", "total_assets", "assets", "TotalAssets"]
REV_KEYS = ["SALE", "SALEQ", "sales", "revenue", "REVT", "revt", "Revenue"]
INDU_KEYS = ["naics", "gsubind", "industry", "segment"]

MECHANISM_WEIGHT_COLS = {
    "subsidy": "subsidy_exposure_stage2_input_weight",
    "compliance": "compliance_exposure_stage2_input_weight",
    "credit_market": "credit_market_exposure_stage2_input_weight",
    "demand_pull": "demand_pull_exposure_stage2_input_weight",
}

def pick_col(cols, cands):
    for c in cands:
        if c in cols:
            return c
    return None

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def normalize_key(x):
    if pd.isna(x):
        return np.nan
    return str(x).strip().upper()

def as_dt(df, col):
    df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def load_data():
    price = pd.read_csv(PRICE_PATH, low_memory=False)
    ratios = pd.read_csv(RATIOS_PATH, low_memory=False) if os.path.exists(RATIOS_PATH) else pd.DataFrame()
    policy = pd.read_csv(POLICY_PATH, low_memory=False)

    firm = pick_col(price.columns, FIRM_KEYS)
    date = pick_col(price.columns, DATE_KEYS)
    ret = pick_col(price.columns, RET_KEYS)
    rf = pick_col(price.columns, RF_KEYS)
    indu = pick_col(price.columns, INDU_KEYS)
    if firm is None or date is None or ret is None:
        raise ValueError("Could not identify firm/date/return columns.")
    factors = [f for f in FF5_LIST if f in price.columns]
    price = as_dt(price, date)
    price[firm] = price[firm].map(normalize_key)

    if "Date" not in policy.columns:
        if {"year","month","day"}.issubset(policy.columns):
            policy["Date"] = pd.to_datetime(policy[["year","month","day"]], errors="coerce")
        else:
            dcol = pick_col(policy.columns, DATE_KEYS)
            policy["Date"] = pd.to_datetime(policy[dcol], errors="coerce")
    else:
        policy["Date"] = pd.to_datetime(policy["Date"], errors="coerce")

    return price, ratios, policy, firm, date, ret, rf, factors, indu

def build_size(price, ratios, firm):
    px = pick_col(price.columns, PX_KEYS)
    shr = pick_col(price.columns, SHR_KEYS)
    cap = pick_col(price.columns, CAP_KEYS)
    out = price.copy()
    if cap and cap in out.columns:
        out["_size"] = to_num(out[cap])
        return out, cap
    if px and shr and px in out.columns and shr in out.columns:
        out["_size"] = to_num(out[px]) * to_num(out[shr])
        return out, f"{px}*{shr}"
    out["_size"] = 1.0
    return out, "constant_1"

def compute_industry_share(df, indu, date):
    out = df.copy()
    out["_size"] = to_num(out["_size"]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if indu is None or indu not in out.columns:
        out["industry_share"] = 0.0
        return out
    grp = out.groupby([date, indu])["_size"].transform("sum")
    out["industry_share"] = np.where(grp > 0, out["_size"] / grp, 0.0)
    return out

def add_abnormal_returns(df, firm, date, ret, rf, factors):
    out = df.sort_values([firm, date]).copy()
    out["ret_excess"] = to_num(out[ret]) - to_num(out[rf]).fillna(0.0)
    for c in [ret, rf] + factors:
        if c in out.columns:
            out[c] = to_num(out[c])
    parts = []
    for tic, g in out.groupby(firm, sort=False):
        g = g.sort_values(date).copy()
        if g[factors].dropna().shape[0] < 30 or g["ret_excess"].dropna().shape[0] < 30:
            g["AR"] = np.nan
            parts.append(g)
            continue
        X = sm.add_constant(g[factors], has_constant="add")
        y = g["ret_excess"]
        try:
            fit = sm.OLS(y, X, missing="drop").fit()
            yhat = fit.predict(X)
            g["AR"] = y - yhat
        except Exception:
            g["AR"] = np.nan
        parts.append(g)
    return pd.concat(parts, ignore_index=True)

def s_weight(naics_val, core_set, edge_set):
    try:
        x = int(str(naics_val).split(".")[0])
    except Exception:
        return 0.0
    if x in core_set:
        return 1.0
    if x in edge_set:
        return 0.5
    return 0.0

def build_exposure_pre(df, indu, date, firm, policy_key, event_date):
    t0 = pd.Timestamp(event_date)
    sub = df[df[date] < t0].sort_values([firm, date]).copy()
    avg_share = (sub.groupby(firm)["industry_share"].apply(lambda s: s.tail(min(PRE_EXPOSURE_DAYS, len(s))).mean())
                   .rename("avg_share").reset_index())
    core = POLICIES[policy_key]["core_naics"]
    edge = POLICIES[policy_key]["edge_naics"]
    w = df[[firm, indu]].drop_duplicates().copy()
    w["s_j"] = w[indu].apply(lambda x: s_weight(x, core, edge))
    expo = avg_share.merge(w[[firm, "s_j"]], on=firm, how="left")
    expo["Exposure_pre"] = expo["avg_share"] * expo["s_j"]
    return expo[[firm, "Exposure_pre"]]

def load_integration_map():
    im = pd.read_csv(INTEGRATION_MAP_PATH, low_memory=False)
    im["ticker"] = im["ticker"].map(normalize_key)
    if not ALLOW_ALT_PROVISIONAL:
        im = im[im["integration_status"] != "included_provisional_alt"].copy()
    if RUN_MAIN_SAMPLE_ONLY:
        im = im[im["sample_decision"] == "keep"].copy()
    else:
        im = im[im["sample_decision"].isin(["keep", "edge"])].copy()
    keep_cols = ["ticker", "source_universe", "integration_status", "sample_decision"] + \
                list(MECHANISM_WEIGHT_COLS.values()) + ["manual_confidence_score", "sample_inclusion_weight"]
    keep_cols = [c for c in keep_cols if c in im.columns]
    return im[keep_cols].drop_duplicates("ticker").copy()

def build_event_panel(df, date_col, t0, post_max):
    rel = (df[date_col] - t0).dt.days
    sub = df[(rel >= -PRE_EXPOSURE_DAYS) & (rel <= post_max)].copy()
    sub["rel"] = (sub[date_col] - t0).dt.days
    return sub

def add_policy_specific_intensities(panel, policy_df, policy_key):
    cols = ["Date", "dpi01"]
    for mech in MECHANISM_WEIGHT_COLS:
        cname = f"{policy_key}_{mech}_intensity_t"
        if cname in policy_df.columns:
            cols.append(cname)
    tmp = policy_df[cols].drop_duplicates("Date").copy()
    panel = panel.merge(tmp, on="Date", how="left")
    for mech in MECHANISM_WEIGHT_COLS:
        src = f"{policy_key}_{mech}_intensity_t"
        dst = f"{mech}_intensity_t"
        if src in panel.columns:
            panel[dst] = to_num(panel[src]).fillna(to_num(panel["dpi01"]).fillna(0.0))
        else:
            panel[dst] = to_num(panel["dpi01"]).fillna(0.0)
    return panel

def add_mechanism_exposures(panel):
    for mech, weight_col in MECHANISM_WEIGHT_COLS.items():
        panel[weight_col] = to_num(panel[weight_col]).fillna(0.0)
        panel[f"{mech}_intensity_t"] = to_num(panel[f"{mech}_intensity_t"]).fillna(0.0)
        panel[f"{mech}_expo_it"] = to_num(panel["Exposure_pre"]).fillna(0.0) * panel[weight_col] * panel[f"{mech}_intensity_t"]
    return panel

def fe_regression(yname, panel, xcols, tag):
    req = [yname] + xcols + ["logM"]
    reg = panel.dropna(subset=req).copy()
    if reg.empty:
        return None
    try:
        from linearmodels.panel import PanelOLS
        reg = reg.set_index(["tic","Date"]).sort_index()
        X = sm.add_constant(reg[xcols + ["logM"]], has_constant="add")
        mod = PanelOLS(reg[yname], X, entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
        txt = str(res.summary)
    except Exception:
        tmp = reg.copy()
        for col in [yname] + xcols + ["logM"]:
            tmp[col + "_dm"] = tmp[col] - tmp.groupby("tic")[col].transform("mean")
            tmp[col + "_dm"] = tmp[col + "_dm"] - tmp.groupby("Date")[col + "_dm"].transform("mean") + tmp[col + "_dm"].mean()
        y = tmp[yname + "_dm"]
        X = sm.add_constant(tmp[[c + "_dm" for c in xcols + ["logM"]]], has_constant="add")
        ols = sm.OLS(y, X, missing="drop").fit(cov_type="cluster", cov_kwds={"groups": tmp["tic"]})
        txt = str(ols.summary())
    with open(os.path.join(OUTDIR, f"panel_results_{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    return txt

def parse_line(txt, vars_to_try):
    import re
    rows=[]
    for var in vars_to_try:
        pat = re.compile(rf"^({re.escape(var)}(?:_dm)?)\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+([0-9]*\.?[0-9]+)", re.M)
        m = pat.search(txt)
        if m:
            rows.append({"var":var,"coef":float(m.group(2)),"se":float(m.group(3)),"t":float(m.group(4)),"p":float(m.group(5))})
    return rows

if __name__ == "__main__":
    price, ratios, policy, firm, date, ret, rf, factors, indu = load_data()
    price, size_used = build_size(price, ratios, firm)
    price = compute_industry_share(price, indu, date)
    price = add_abnormal_returns(price, firm, date, ret, rf, factors)
    integration = load_integration_map()

    summary_rows = []

    for pol, cfg in POLICIES.items():
        for ed in cfg["event_dates"]:
            t0 = pd.Timestamp(ed)
            expo_pre = build_exposure_pre(price, indu, date, firm, pol, ed)
            expo_pre = expo_pre.rename(columns={firm:"tic"})
            expo_pre["tic"] = expo_pre["tic"].map(normalize_key)

            panel = build_event_panel(price.rename(columns={date:"Date", firm:"tic"}), "Date", t0, POST_DAYS_AR)
            panel["tic"] = panel["tic"].map(normalize_key)
            panel = add_policy_specific_intensities(panel, policy, pol)
            panel["Post"] = (panel["rel"] >= 0).astype(int)
            panel["dpi01"] = to_num(panel["dpi01"]).fillna(0.0)
            panel["QuickFactor_t"] = panel["Post"] * panel["dpi01"]
            for mech in MECHANISM_WEIGHT_COLS:
                panel[f"{mech}_intensity_t"] = panel["Post"] * to_num(panel[f"{mech}_intensity_t"]).fillna(0.0)

            panel = panel.merge(expo_pre[["tic","Exposure_pre"]], on="tic", how="left")
            panel = panel.merge(integration, left_on="tic", right_on="ticker", how="inner")
            panel["ExpoQuick_it"] = to_num(panel["Exposure_pre"]).fillna(0.0) * panel["QuickFactor_t"]
            panel["logM"] = np.log(to_num(panel["_size"]).replace([np.inf,-np.inf], np.nan))
            panel = add_mechanism_exposures(panel)
            panel.to_csv(os.path.join(OUTDIR, f"panel_mechanism_ready_{pol}_{ed}.csv"), index=False)

            if RUN_BASELINE_MODEL:
                txt=fe_regression("AR", panel, ["ExpoQuick_it"], f"baseline_{pol}_{ed}")
                if txt:
                    for row in parse_line(txt, ["ExpoQuick_it"]):
                        row.update({"policy":pol,"event":ed,"model":"baseline"})
                        summary_rows.append(row)
            if RUN_MECHANISM_MODEL:
                mech_vars=[f"{m}_expo_it" for m in MECHANISM_WEIGHT_COLS]
                txt=fe_regression("AR", panel, mech_vars, f"mechanism_{pol}_{ed}")
                if txt:
                    for row in parse_line(txt, mech_vars):
                        row.update({"policy":pol,"event":ed,"model":"mechanism"})
                        summary_rows.append(row)
    out = pd.DataFrame(summary_rows)
    out.to_csv(os.path.join(OUTDIR, "panel_results_summary.csv"), index=False)
    print(out.to_string(index=False))
