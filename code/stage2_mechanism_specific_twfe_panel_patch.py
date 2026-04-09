"""
Stage 2 Patch: Mechanism-Specific TWFE Panel
============================================
This script extends the original Stage 2 panel by merging the issuer-level
manual calibration integration map and constructing mechanism-specific
exposure terms.

Key idea
--------
Instead of using a single shared Exposure_pre regressor, this patch builds:

    SubsidyExpo_it
    ComplianceExpo_it
    CreditMarketExpo_it
    DemandPullExpo_it

using:

    Exposure_pre_j
    × issuer-level manual mechanism weight
    × policy-side mechanism intensity at time t

If policy-side mechanism intensities are not yet available in the policy file,
the script falls back to the shared normalized daily policy index (dpi01),
so the mechanism-specific structure can still be tested mechanically.

Requirements
------------
pandas, numpy, statsmodels, linearmodels (optional)

Expected files
--------------
- Policy Influenced_Stock Price_With FF 5 Factors.csv
- Financial Ratios_Ticker.csv
- All_Daily_Policy_Data.csv
- p2_stage2_integration_map_v2_with_alt_bridge.csv
"""

import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore")

# ============================================================
# Paths
# ============================================================
PRICE_PATH = "Policy Influenced_Stock Price_With FF 5 Factors.csv"
RATIOS_PATH = "Financial Ratios_Ticker.csv"
POLICY_PATH = "All_Daily_Policy_Data.csv"
INTEGRATION_MAP_PATH = "p2_stage2_integration_map_v2_with_alt_bridge.csv"

OUTDIR = "stage2_mechanism_outputs"
os.makedirs(OUTDIR, exist_ok=True)

# ============================================================
# Configuration
# ============================================================
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
CAR_WINDOWS = [5, 10]
RUN_BASELINE_MODEL = True
RUN_MECHANISM_MODEL = True
RUN_MAIN_SAMPLE_ONLY = False
ALLOW_ALT_PROVISIONAL = True

# Fallback behavior when policy-side text mechanism intensities are missing
USE_DPI_FALLBACK = True

# ============================================================
# Column candidates
# ============================================================
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

# Columns the script will look for in the policy file. The first match wins.
MECHANISM_INTENSITY_CANDIDATES = {
    "subsidy": [
        "subsidy_intensity", "text_subsidy_intensity", "SubsidyIntensity", "subsidy_score"
    ],
    "compliance": [
        "compliance_intensity", "text_compliance_intensity", "ComplianceIntensity", "compliance_score"
    ],
    "credit_market": [
        "credit_market_intensity", "text_credit_market_intensity", "CreditMarketIntensity", "credit_market_score"
    ],
    "demand_pull": [
        "demand_pull_intensity", "text_demand_pull_intensity", "DemandPullIntensity", "demand_pull_score"
    ],
}

# ============================================================
# Helpers
# ============================================================
def pick_col(cols, cands):
    for c in cands:
        if c in cols:
            return c
    return None

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def z01(x):
    x = to_num(x).replace([np.inf, -np.inf], np.nan)
    if x.dropna().empty or np.isclose(x.std(skipna=True), 0.0):
        return x * 0
    z = (x - x.mean()) / x.std()
    q01 = z.quantile(0.01)
    q99 = z.quantile(0.99)
    z = z.clip(q01, q99)
    denom = z.max() - z.min()
    if pd.isna(denom) or np.isclose(denom, 0.0):
        return z * 0
    return (z - z.min()) / denom

def normalize_key(x):
    if pd.isna(x):
        return np.nan
    return str(x).strip().upper()

def as_dt(df, col):
    df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

# ============================================================
# Load data
# ============================================================
def load_data():
    price = pd.read_csv(PRICE_PATH, low_memory=False)
    ratios = pd.read_csv(RATIOS_PATH, low_memory=False) if os.path.exists(RATIOS_PATH) else pd.DataFrame()
    policy = pd.read_csv(POLICY_PATH, low_memory=False) if os.path.exists(POLICY_PATH) else pd.DataFrame()

    firm = pick_col(price.columns, FIRM_KEYS)
    date = pick_col(price.columns, DATE_KEYS)
    ret = pick_col(price.columns, RET_KEYS)
    rf = pick_col(price.columns, RF_KEYS)
    indu = pick_col(price.columns, INDU_KEYS)

    if firm is None or date is None or ret is None:
        raise ValueError("Could not identify required firm/date/return columns in price file.")

    factors = [f for f in FF5_LIST if f in price.columns]
    if len(factors) < 3:
        raise ValueError("Price file does not contain enough FF factor columns.")

    price = as_dt(price, date)
    price[firm] = price[firm].map(normalize_key)

    if not ratios.empty:
        r_firm = pick_col(ratios.columns, FIRM_KEYS)
        if r_firm:
            ratios[r_firm] = ratios[r_firm].map(normalize_key)

    return price, ratios, policy, firm, date, ret, rf, factors, indu

# ============================================================
# Build size and industry share
# ============================================================
def build_size(price, ratios, firm, date):
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

    if not ratios.empty:
        r_firm = pick_col(ratios.columns, FIRM_KEYS)
        r_cap = pick_col(ratios.columns, CAP_KEYS)
        r_asset = pick_col(ratios.columns, ASSET_KEYS)
        r_rev = pick_col(ratios.columns, REV_KEYS)

        if r_firm and r_cap:
            tmp = ratios[[r_firm, r_cap]].drop_duplicates(r_firm)
            tmp.columns = [firm, "_size"]
            out = out.merge(tmp, on=firm, how="left")
            return out, f"RATIOS.{r_cap}"

        if r_firm and r_asset:
            tmp = ratios[[r_firm, r_asset]].drop_duplicates(r_firm)
            tmp.columns = [firm, "_size"]
            out = out.merge(tmp, on=firm, how="left")
            return out, f"RATIOS.{r_asset}"

        if r_firm and r_rev:
            tmp = ratios[[r_firm, r_rev]].drop_duplicates(r_firm)
            tmp.columns = [firm, "_size"]
            out = out.merge(tmp, on=firm, how="left")
            return out, f"RATIOS.{r_rev}"

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

# ============================================================
# Abnormal returns
# ============================================================
def add_abnormal_returns(df, firm, date, ret, rf, factors):
    out = df.copy().sort_values([firm, date]).copy()
    out["ret_excess"] = to_num(out[ret]) - to_num(out[rf]).fillna(0.0)
    req = [ret, rf] + factors
    for c in req:
        out[c] = to_num(out[c])

    ar_list = []
    for tic, g in out.groupby(firm, sort=False):
        g = g.sort_values(date).copy()
        if g[factors].dropna().shape[0] < 30 or g["ret_excess"].dropna().shape[0] < 30:
            g["AR"] = np.nan
            ar_list.append(g)
            continue
        X = sm.add_constant(g[factors], has_constant="add")
        y = g["ret_excess"]
        try:
            fit = sm.OLS(y, X, missing="drop").fit()
            yhat = fit.predict(X)
            g["AR"] = y - yhat
        except Exception:
            g["AR"] = np.nan
        ar_list.append(g)
    return pd.concat(ar_list, ignore_index=True)

# ============================================================
# Policy intensity builders
# ============================================================
def build_dpi(policy, price, date_col):
    # Option 1: directly in price file
    if "daily_policy_index" in price.columns:
        dpi = price[[date_col, "daily_policy_index"]].drop_duplicates().sort_values(date_col)
        dpi["Date"] = pd.to_datetime(dpi[date_col], errors="coerce")
        dpi["dpi01"] = z01(dpi["daily_policy_index"])
        return dpi[["Date", "dpi01"]]

    # Option 2: separate policy file
    if not policy.empty:
        po = policy.copy()
        if {"year", "month", "day"}.issubset(po.columns):
            po["Date"] = pd.to_datetime(po[["year", "month", "day"]], errors="coerce")
        else:
            dcol = pick_col(po.columns, DATE_KEYS)
            if dcol:
                po["Date"] = pd.to_datetime(po[dcol], errors="coerce")
            else:
                po["Date"] = pd.NaT

        cand = None
        for c in ["daily_policy_index", "policy_index", "dpi", "DPI", "DailyPolicyIndex"]:
            if c in po.columns:
                cand = c
                break
        if cand and po["Date"].notna().any():
            dpi = po[["Date", cand]].dropna().drop_duplicates("Date").sort_values("Date")
            dpi["dpi01"] = z01(dpi[cand])
            return dpi[["Date", "dpi01"]]

    # fallback constant
    dpi = pd.DataFrame({"Date": pd.to_datetime(price[date_col].dropna().unique())})
    dpi = dpi.sort_values("Date")
    dpi["dpi01"] = 1.0
    return dpi

def build_policy_mechanism_intensity(policy, dpi):
    """
    Returns a daily mechanism intensity table with columns:
        Date,
        subsidy_intensity_t,
        compliance_intensity_t,
        credit_market_intensity_t,
        demand_pull_intensity_t

    If policy-side mechanism columns are not found, the function falls back
    to dpi01 for all mechanisms when USE_DPI_FALLBACK=True.
    """
    out = dpi.copy()
    if not policy.empty:
        po = policy.copy()
        if {"year", "month", "day"}.issubset(po.columns):
            po["Date"] = pd.to_datetime(po[["year", "month", "day"]], errors="coerce")
        else:
            dcol = pick_col(po.columns, DATE_KEYS)
            po["Date"] = pd.to_datetime(po[dcol], errors="coerce") if dcol else pd.NaT

        if po["Date"].notna().any():
            base = po[["Date"]].dropna().drop_duplicates().sort_values("Date")
            for mech, cands in MECHANISM_INTENSITY_CANDIDATES.items():
                chosen = pick_col(po.columns, cands)
                colname = f"{mech}_intensity_t"
                if chosen:
                    tmp = po[["Date", chosen]].dropna().drop_duplicates("Date").sort_values("Date")
                    tmp[colname] = z01(tmp[chosen])
                    base = base.merge(tmp[["Date", colname]], on="Date", how="left")
                elif USE_DPI_FALLBACK:
                    base[colname] = np.nan
                else:
                    base[colname] = 0.0

            out = out.merge(base, on="Date", how="left")

    for mech in MECHANISM_WEIGHT_COLS:
        colname = f"{mech}_intensity_t"
        if colname not in out.columns:
            out[colname] = np.nan
        if USE_DPI_FALLBACK:
            out[colname] = out[colname].fillna(out["dpi01"])
        else:
            out[colname] = out[colname].fillna(0.0)

    return out[["Date", "dpi01"] + [f"{m}_intensity_t" for m in MECHANISM_WEIGHT_COLS]]

# ============================================================
# Exposure builders
# ============================================================
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
    """
    Original exposure_pre:
        average pre-event industry share × NAICS weight
    """
    t0 = pd.Timestamp(event_date)
    sub = df[df[date] < t0].sort_values([firm, date]).copy()

    def last_k_mean(s, k=PRE_EXPOSURE_DAYS):
        return s.tail(min(k, len(s))).mean()

    avg_share = (
        sub.groupby(firm)["industry_share"]
           .apply(last_k_mean)
           .rename("avg_share")
           .reset_index()
    )

    core = POLICIES[policy_key]["core_naics"]
    edge = POLICIES[policy_key]["edge_naics"]

    w = df[[firm, indu]].drop_duplicates().copy()
    w["s_j"] = w[indu].apply(lambda x: s_weight(x, core, edge))

    expo = avg_share.merge(w[[firm, "s_j"]], on=firm, how="left")
    expo["Exposure_pre"] = expo["avg_share"] * expo["s_j"]
    return expo[[firm, "avg_share", "s_j", "Exposure_pre"]]

def load_integration_map():
    if not os.path.exists(INTEGRATION_MAP_PATH):
        raise FileNotFoundError(f"Missing integration map: {INTEGRATION_MAP_PATH}")

    im = pd.read_csv(INTEGRATION_MAP_PATH, low_memory=False)
    if "ticker" not in im.columns:
        raise ValueError("Integration map must contain a 'ticker' column.")

    im["ticker"] = im["ticker"].map(normalize_key)

    if not ALLOW_ALT_PROVISIONAL:
        im = im[im["integration_status"] != "included_provisional_alt"].copy()

    if RUN_MAIN_SAMPLE_ONLY:
        im = im[im["sample_decision"] == "keep"].copy()
    else:
        im = im[im["sample_decision"].isin(["keep", "edge"])].copy()

    keep_cols = ["ticker", "source_universe", "integration_status", "sample_decision"]
    keep_cols += list(MECHANISM_WEIGHT_COLS.values())
    keep_cols += ["manual_confidence_score", "sample_inclusion_weight"]
    keep_cols = [c for c in keep_cols if c in im.columns]
    return im[keep_cols].drop_duplicates("ticker").copy()

# ============================================================
# Panel builders
# ============================================================
def build_event_panel(df, date_col, t0, post_max):
    rel = (df[date_col] - t0).dt.days
    sub = df[(rel >= -PRE_EXPOSURE_DAYS) & (rel <= post_max)].copy()
    sub["rel"] = (sub[date_col] - t0).dt.days
    return sub

def add_mechanism_exposures(panel):
    for mech, weight_col in MECHANISM_WEIGHT_COLS.items():
        intensity_col = f"{mech}_intensity_t"
        exposure_col = f"{mech}_expo_it"
        panel[weight_col] = to_num(panel[weight_col]).fillna(0.0)
        panel[intensity_col] = to_num(panel[intensity_col]).fillna(0.0)
        panel[exposure_col] = (
            to_num(panel["Exposure_pre"]).fillna(0.0)
            * panel[weight_col]
            * panel[intensity_col]
        )
    return panel

# ============================================================
# FE regression wrappers
# ============================================================
def fe_regression(yname, panel, xcols, tag):
    """
    Two-way FE regression with clustered SE.
    """
    req = [yname] + xcols + ["logM"]
    reg = panel.dropna(subset=req).copy()

    if reg.empty:
        print(f"[Skip] {tag}: no usable rows after dropping missing values.")
        return

    try:
        from linearmodels.panel import PanelOLS
        reg = reg.set_index(["tic", "Date"]).sort_index()
        X = sm.add_constant(reg[xcols + ["logM"]], has_constant="add")
        mod = PanelOLS(reg[yname], X, entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
        summ_txt = str(res.summary)
    except Exception:
        tmp = reg.copy()
        dm_cols = [yname] + xcols + ["logM"]
        for col in dm_cols:
            tmp[col + "_dm"] = tmp[col] - tmp.groupby("tic")[col].transform("mean")
        dm_y = yname + "_dm"
        Xcols_dm = [c + "_dm" for c in xcols + ["logM"]]
        for col in Xcols_dm:
            tmp[col] = tmp[col] - tmp.groupby("Date")[col].transform("mean") + tmp[col].mean()
        y = tmp[dm_y]
        X = sm.add_constant(tmp[Xcols_dm], has_constant="add")
        ols = sm.OLS(y, X, missing="drop").fit(
            cov_type="cluster", cov_kwds={"groups": tmp["tic"]}
        )
        summ_txt = str(ols.summary())

    reg.reset_index().to_csv(os.path.join(OUTDIR, f"panel_data_{tag}.csv"), index=False)
    with open(os.path.join(OUTDIR, f"panel_results_{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(summ_txt)
    print(f"[Saved] {os.path.join(OUTDIR, f'panel_results_{tag}.txt')}")

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    price, ratios, policy, firm, date, ret, rf, factors, indu = load_data()
    price, size_used = build_size(price, ratios, firm, date)
    price = compute_industry_share(price, indu, date)
    price = add_abnormal_returns(price, firm, date, ret, rf, factors)

    dpi = build_dpi(policy, price, date)
    mech_daily = build_policy_mechanism_intensity(policy, dpi)
    integration = load_integration_map()

    print(f"[Info] Size proxy used: {size_used}")
    print(f"[Info] Integration map rows used: {len(integration)}")
    print(f"[Info] Main-only mode: {RUN_MAIN_SAMPLE_ONLY}")
    print(f"[Info] Allow provisional alt inclusion: {ALLOW_ALT_PROVISIONAL}")

    for pol, cfg in POLICIES.items():
        for ed in cfg["event_dates"]:
            t0 = pd.Timestamp(ed)

            # Original exposure_pre
            expo_pre = build_exposure_pre(price, indu, date, firm, pol, ed)
            expo_pre = expo_pre.rename(columns={firm: "tic"})
            expo_pre["tic"] = expo_pre["tic"].map(normalize_key)

            # Event panel
            post_max = max(POST_DAYS_AR, *CAR_WINDOWS)
            panel = build_event_panel(price.rename(columns={date: "Date", firm: "tic"}), "Date", t0, post_max)
            panel["tic"] = panel["tic"].map(normalize_key)

            # Merge policy intensity + manual integration map
            panel = panel.merge(mech_daily, on="Date", how="left")
            panel["Post"] = (panel["rel"] >= 0).astype(int)
            panel["dpi01"] = panel["dpi01"].fillna(0.0)
            panel["QuickFactor_t"] = panel["Post"] * panel["dpi01"]

            for mech in MECHANISM_WEIGHT_COLS:
                panel[f"{mech}_intensity_t"] = panel["Post"] * panel[f"{mech}_intensity_t"].fillna(0.0)

            panel = panel.merge(expo_pre[["tic", "Exposure_pre"]], on="tic", how="left")
            panel = panel.merge(integration, left_on="tic", right_on="ticker", how="inner")
            panel["ExpoQuick_it"] = to_num(panel["Exposure_pre"]).fillna(0.0) * panel["QuickFactor_t"]
            panel["logM"] = np.log(to_num(panel["_size"]).replace([np.inf, -np.inf], np.nan))
            panel = add_mechanism_exposures(panel)

            tag_stub = f"{pol}_{ed}"

            panel.to_csv(os.path.join(OUTDIR, f"panel_mechanism_ready_{tag_stub}.csv"), index=False)

            # Baseline model
            if RUN_BASELINE_MODEL:
                fe_regression(
                    yname="AR",
                    panel=panel,
                    xcols=["ExpoQuick_it"],
                    tag=f"baseline_{tag_stub}"
                )

            # Mechanism-specific model
            if RUN_MECHANISM_MODEL:
                mech_xcols = [f"{m}_expo_it" for m in MECHANISM_WEIGHT_COLS]
                fe_regression(
                    yname="AR",
                    panel=panel,
                    xcols=mech_xcols,
                    tag=f"mechanism_{tag_stub}"
                )

    print("[Done] Mechanism-specific Stage 2 patch completed.")
