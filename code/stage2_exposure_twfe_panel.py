"""
Stage 2: Exposure-Based TWFE Panel (Bartik-Style Policy Factor)
================================================================
From: "From Causal Evidence to Actionable Signals: A Dual-Track Framework
       for Policy-Aware Factor Investing in the Sustainable Fuel Sector"

This script constructs a Bartik-style policy factor by interacting firm
pre-policy exposure with daily policy intensity in a two-way fixed-effects
panel. It estimates AR-TWFE policy betas, CAR cross-sections, and
event-time lead-lag dynamics.

Requirements: pandas, numpy, statsmodels, linearmodels (optional)
Data: Policy_Influenced_Stock_Price_With_FF_5_Factors.csv,
      Financial_Ratios_Ticker.csv, All_Daily_Policy_Data.csv
"""

import os, warnings, re, glob
import numpy as np
import pandas as pd
import statsmodels.api as sm
warnings.filterwarnings("ignore")

# ============================================================
# Paths
# ============================================================
PRICE_PATH  = "Policy Influenced_Stock Price_With FF 5 Factors.csv"
RATIOS_PATH = "Financial Ratios_Ticker.csv"
POLICY_PATH = "All_Daily_Policy_Data.csv"
OUTDIR = "stage2_outputs"; os.makedirs(OUTDIR, exist_ok=True)

# ============================================================
# Column candidates (robust to different naming conventions)
# ============================================================
FIRM_KEYS  = ["tic","TICKER","Ticker","permno","PERMNO"]
DATE_KEYS  = ["Date","date","DATE"]
RET_KEYS   = ["daily_return","ret","RET","Ret"]
RF_KEYS    = ["RF","rf","RiskFree","RF*100","R_f"]
FF5_LIST   = ["Mkt_RF","SMB","HML","RMW","CMA"]
PX_KEYS    = ["adj_close","Adj Close","close","Close","PRC","prc","PX_LAST","Price"]
SHR_KEYS   = ["shares_outstanding","SHROUT","shrout","shares","csho","CSHO"]
CAP_KEYS   = ["market_cap","MarketCap","MktCap","mktcap","ME","me"]
ASSET_KEYS = ["AT","ATQ","at","total_assets","assets","TotalAssets"]
REV_KEYS   = ["SALE","SALEQ","sales","revenue","REVT","revt","Revenue"]
INDU_KEYS  = ["naics","gsubind","industry","segment"]

# ============================================================
# Policy configurations
# ============================================================
POLICIES = {
    "IRA":  {"event_dates": ["2022-08-16"], "core_naics": {325120},
             "edge_naics": {324110,325199,325193}},
    "LCFS": {"event_dates": ["2023-01-03"], "core_naics": {325193},
             "edge_naics": {324110,325199}},
    "RFS2": {"event_dates": ["2021-01-04"], "core_naics": {325193},
             "edge_naics": {324110,325199}},
}

PRE_EXPOSURE_DAYS = 120
POST_DAYS_AR      = 10
CAR_WINDOWS       = [5, 10]
RUN_DAILY_AR_FE   = False   # Set to True to run daily AR panel

# ============================================================
# Helpers
# ============================================================
def pick_col(cols, cands):
    for c in cands:
        if c in cols: return c
    return None

def as_dt(df, col):
    df[col] = pd.to_datetime(df[col], errors="coerce"); return df

def to_num(s):
    return pd.to_numeric(s, errors="coerce")

def z01(x):
    """Normalize to [0,1] after z-scoring and winsorizing."""
    x = to_num(x).replace([np.inf,-np.inf], np.nan)
    if x.dropna().empty or np.isclose(x.std(skipna=True), 0.0):
        return x * 0
    z = (x - x.mean()) / x.std()
    z = z.clip(z.quantile(0.01), z.quantile(0.99))
    return (z - z.min()) / (z.max() - z.min())

# ============================================================
# Daily policy intensity builder
# ============================================================
def build_dpi(price_df, date_col):
    """Build normalized daily policy intensity from available sources."""
    # Option 1: price file has daily_policy_index
    if "daily_policy_index" in price_df.columns:
        dpi = price_df[[date_col,"daily_policy_index"]].drop_duplicates().sort_values(date_col)
        dpi["dpi01"] = z01(dpi["daily_policy_index"])
        print("[DPI] Source: PRICE.daily_policy_index")
        return dpi.rename(columns={date_col:"Date"})[["Date","dpi01"]]

    # Option 2: separate policy file
    if os.path.exists(POLICY_PATH):
        po = pd.read_csv(POLICY_PATH, low_memory=False)
        if {"year","month","day"}.issubset(set(po.columns)):
            po["Date"] = pd.to_datetime(po[["year","month","day"]], errors="coerce")
        else:
            dcol = pick_col(po.columns, DATE_KEYS)
            po["Date"] = pd.to_datetime(po[dcol], errors="coerce") if dcol else pd.NaT
        cand = None
        for c in ["daily_policy_index","policy_index","dpi","DPI","DailyPolicyIndex"]:
            if c in po.columns: cand = c; break
        if cand is not None and po["Date"].notna().any():
            dpi = po[["Date",cand]].dropna().drop_duplicates("Date").sort_values("Date")
            dpi["dpi01"] = z01(dpi[cand])
            print(f"[DPI] Source: POLICY.{cand}")
            return dpi[["Date","dpi01"]]

    # Option 3: fallback to constant (reduces to Post × Exposure)
    dd  = pd.to_datetime(price_df[date_col].dropna().unique())
    dpi = pd.DataFrame({"Date": np.sort(dd), "dpi01": 1.0})
    print("[DPI] No daily policy index found; using fallback dpi01=1")
    return dpi

# ============================================================
# Data loading
# ============================================================
def load_data():
    price  = pd.read_csv(PRICE_PATH,  low_memory=False)
    ratios = pd.read_csv(RATIOS_PATH, low_memory=False)

    firm = pick_col(price.columns, FIRM_KEYS)
    date = pick_col(price.columns, DATE_KEYS)
    if firm is None or date is None:
        raise ValueError("Price file missing firm or date column.")
    as_dt(price, date)

    ret = pick_col(price.columns, RET_KEYS)
    if ret is None:
        raise ValueError("Cannot find return column.")
    price[ret] = to_num(price[ret])
    if price[ret].abs().quantile(0.9) > 1.5:
        price[ret] /= 100.0

    rf = pick_col(price.columns, RF_KEYS)
    if rf:
        price[rf] = to_num(price[rf])
        if price[rf].abs().quantile(0.9) > 1.5:
            price[rf] /= 100.0

    factors = [c for c in FF5_LIST if c in price.columns]
    for c in factors:
        price[c] = to_num(price[c])

    # Industry labels (prefer ratios file)
    r_firm = pick_col(ratios.columns, FIRM_KEYS) or \
             ("TICKER" if "TICKER" in ratios.columns else None)
    indu = pick_col(ratios.columns, INDU_KEYS)
    if r_firm and indu:
        lab = ratios[[r_firm,indu]].drop_duplicates().rename(columns={r_firm: firm})
        price = price.merge(lab, on=firm, how="left")
    else:
        indu = pick_col(price.columns, INDU_KEYS) or "industry"
        if indu not in price.columns:
            price[indu] = "ALL"

    dpi = build_dpi(price, date)
    return price, ratios, firm, date, ret, rf, factors, indu, dpi

# ============================================================
# Robust size → industry share
# ============================================================
def build_size(price, ratios, firm):
    """Build firm size using a robust fallback ladder."""
    cap_p = pick_col(price.columns, CAP_KEYS)
    if cap_p:
        size = to_num(price[cap_p]); size.loc[(~np.isfinite(size))|(size<=0)] = np.nan
        price["_size"] = size; print("[Size] Using price market cap:", cap_p)
        return price, "market_cap(price)"

    px  = pick_col(price.columns, PX_KEYS)
    shr = pick_col(price.columns, SHR_KEYS)
    if px and shr:
        _px  = np.abs(to_num(price[px])); _shr = to_num(price[shr])
        if shr.lower() == "shrout": _shr = _shr * 1000.0
        size = _px * _shr; size.loc[(~np.isfinite(size))|(size<=0)] = np.nan
        price["_size"] = size; print("[Size] Using price*shares:", px, "x", shr)
        return price, "price*shares"

    # Additional fallbacks: assets, revenue, equal-weight
    for key_list, label in [(ASSET_KEYS,"assets"), (REV_KEYS,"revenue")]:
        col = pick_col(ratios.columns, key_list)
        if col:
            rfirm = pick_col(ratios.columns, FIRM_KEYS) or "tic"
            tmp = ratios[[rfirm, col]].copy().rename(columns={rfirm: firm, col: "_size"})
            tmp["_size"] = to_num(tmp["_size"])
            price = price.merge(tmp[[firm,"_size"]].drop_duplicates(firm), on=firm, how="left")
            print(f"[Size] Using ratios {label} column: {col}")
            return price, f"{label}(ratios)"

    price["_size"] = 1.0; print("[Size] Equal weight")
    return price, "equal_weight"

def compute_industry_share(price, indu, date):
    """Compute time-varying industry share based on firm size."""
    price["_size"] = to_num(price["_size"])
    price.loc[(~np.isfinite(price["_size"]))|(price["_size"]<=0), "_size"] = np.nan
    price = price.sort_values([indu, date])
    price["_size"] = price.groupby([indu])["_size"].transform(lambda s: s.fillna(s.median()))
    pool = price.groupby([indu, date], dropna=False)["_size"].sum().rename("_pool").reset_index()
    out = price.merge(pool, on=[indu, date], how="left")
    out["_pool"].replace(0, np.nan, inplace=True)
    out["industry_share"] = out["_size"] / out["_pool"]
    return out

# ============================================================
# Abnormal returns
# ============================================================
def add_abnormal_returns(df, firm, date, ret, rf, factors):
    """Compute abnormal returns from firm-level FF5 models."""
    df = df.sort_values([firm, date])
    if factors:
        for g, d in df.groupby(firm):
            y = d[ret] - (d[rf] if rf else 0.0)
            X = sm.add_constant(d[factors], has_constant="add")
            try:
                m = sm.OLS(y, X, missing="drop").fit()
                yhat = m.predict(X)
                df.loc[d.index, "AR"] = d[ret] - (yhat + (d[rf] if rf else 0.0))
            except Exception:
                df.loc[d.index, "AR"] = d[ret] - \
                    (d["Mkt_RF"] + (d[rf] if rf else 0.0) if "Mkt_RF" in d.columns else 0.0)
    else:
        df["AR"] = df[ret] - \
            (df["Mkt_RF"] + (df[rf] if rf else 0.0) if "Mkt_RF" in df.columns else 0.0)
    return df

# ============================================================
# Exposure construction
# ============================================================
def s_weight(naics, core_set, edge_set):
    """NAICS-based policy exposure weight: core=1, edge=0.5, other=0."""
    try: code = int(naics)
    except: return 0.0
    if core_set and code in core_set: return 1.0
    if edge_set and code in edge_set: return 0.5
    return 0.0

def build_exposure_pre(df, indu, date, firm, policy_key, event_date):
    """
    Compute pre-event exposure: mean industry share over [-120, 0) × s_j.
    Returns per-firm Exposure_pre.
    """
    t0 = pd.Timestamp(event_date)
    sub = df[df[date] < t0].sort_values([firm, date])
    def last_k_mean(s, k=PRE_EXPOSURE_DAYS):
        return s.tail(min(k, len(s))).mean()
    avg_share = (sub.groupby(firm)["industry_share"]
                    .apply(last_k_mean)
                    .rename("avg_share")
                    .reset_index())

    core = POLICIES[policy_key]["core_naics"]
    edge = POLICIES[policy_key]["edge_naics"]
    w = (df[[firm, indu]].drop_duplicates().rename(columns={firm: "tic"}))
    w["s_j"] = w[indu].apply(lambda x: s_weight(x, core, edge))

    expo = (avg_share.rename(columns={firm: "tic"})
                     .merge(w[["tic", "s_j"]], on="tic", how="left"))
    expo["Exposure_pre"] = expo["avg_share"] * expo["s_j"]
    expo["policy"]      = policy_key
    expo["event_date"]  = pd.Timestamp(event_date).date().isoformat()
    return expo[["tic", "policy", "event_date", "avg_share", "s_j", "Exposure_pre"]]

# ============================================================
# Panel builders
# ============================================================
def build_event_panel(df, firm, date, t0, post_max):
    rel = (df[date] - t0).dt.days
    sub = df[(rel >= -PRE_EXPOSURE_DAYS) & (rel <= post_max)].copy()
    sub["rel"] = (sub[date] - t0).dt.days
    return sub

def fe_regression(yname, panel, tag, extra_X=None):
    """Two-way FE regression with clustered SE."""
    reg = panel.dropna(subset=[yname,"ExpoQuick_it","logM"]).copy()
    try:
        from linearmodels.panel import PanelOLS
        reg = reg.set_index(["tic","Date"]).sort_index()
        Xcols = ["ExpoQuick_it","logM"]
        if extra_X: Xcols += extra_X
        X = sm.add_constant(reg[Xcols], has_constant="add")
        mod = PanelOLS(reg[yname], X, entity_effects=True, time_effects=True)
        res = mod.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
        summ_txt = str(res.summary)
    except Exception:
        # Fallback: manual demeaning with clustered OLS
        tmp = reg.copy()
        for col in [yname,"ExpoQuick_it","logM"] + (extra_X or []):
            tmp[col+"_dm"] = tmp[col] - tmp.groupby("tic")[col].transform("mean")
        dm_y = yname + "_dm"
        Xcols = ["ExpoQuick_it_dm","logM_dm"] + [c+"_dm" for c in (extra_X or [])]
        for col in Xcols:
            tmp[col] = tmp[col] - tmp.groupby("Date")[col].transform("mean") + tmp[col].mean()
        y = tmp[dm_y]; X = sm.add_constant(tmp[Xcols], has_constant="add")
        ols = sm.OLS(y, X, missing="drop").fit(
            cov_type="cluster", cov_kwds={"groups": tmp["tic"]})
        summ_txt = str(ols.summary())

    reg.reset_index().to_csv(os.path.join(OUTDIR, f"panel_data_{tag}.csv"), index=False)
    with open(os.path.join(OUTDIR, f"panel_results_{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(summ_txt)
    print(f"[Saved] stage2_outputs/panel_results_{tag}.txt")

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    price, ratios, firm, date, ret, rf, factors, indu, dpi = load_data()
    price, size_used = build_size(price, ratios, firm)
    print(f"[Info] Industry share based on: {size_used}")
    price = compute_industry_share(price, indu, date)
    price = add_abnormal_returns(price, firm, date, ret, rf, factors)
    dpi = dpi.rename(columns={"Date":"Date"})[["Date","dpi01"]]

    for pol, cfg in POLICIES.items():
        for ed in cfg["event_dates"]:
            t0 = pd.Timestamp(ed)

            # 1) Pre-event exposure
            expo_pre = build_exposure_pre(price, indu, date, firm, pol, ed)

            # 2) Event panel
            post_max = max(POST_DAYS_AR, *CAR_WINDOWS)
            panel = build_event_panel(
                price.rename(columns={date:"Date"}), firm, "Date", t0, post_max)
            panel = panel.rename(columns={firm:"tic"})
            panel = panel.merge(dpi, on="Date", how="left")
            panel["Post"] = (panel["rel"] >= 0).astype(int)
            panel["dpi01"] = panel["dpi01"].fillna(0.0)
            panel["QuickFactor_t"] = panel["Post"] * panel["dpi01"]
            panel = panel.merge(expo_pre[["tic","Exposure_pre"]], on="tic", how="left")
            panel["ExpoQuick_it"] = panel["Exposure_pre"].fillna(0.0) * panel["QuickFactor_t"]
            panel["logM"] = np.log(to_num(panel["_size"]).replace([np.inf,-np.inf], np.nan))

            # 3A) Optional: daily AR panel
            if RUN_DAILY_AR_FE:
                tag = f"{pol}_{ed.replace('-','')}_AR"
                fe_regression("AR", panel.dropna(subset=["AR"]), tag)

            # 3B) CAR path panels
            for L in CAR_WINDOWS:
                sub = panel[(panel["rel"] >= -PRE_EXPOSURE_DAYS) & (panel["rel"] <= L)].copy()
                sub = sub.sort_values(["tic","Date"])
                sub["CAR"] = np.nan
                for g, d in sub.groupby("tic"):
                    r = d["rel"].values
                    v = to_num(d["AR"]).values
                    v = np.where(np.isfinite(v), v, 0.0)
                    car = np.cumsum(np.where(r >= 0, v, 0.0))
                    sub.loc[d.index, "CAR"] = np.where(r >= 0, car, np.nan)
                sub = sub[sub["rel"].between(0, L)]
                tag = f"{pol}_{ed.replace('-','')}_CAR0_{L}"
                fe_regression("CAR", sub, tag)

    # ============================================================
    # Parse and summarize all Stage 2 results
    # ============================================================
    def parse_one(txt):
        pat = re.compile(
            r"^(ExpoQuick_it(?:_dm)?)\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+"
            r"([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+"
            r"([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+([0-9]*\.?[0-9]+)", re.M)
        m = pat.search(txt)
        if not m: return None
        n = None
        for patN in [r"Observations:\s+(\d+)", r"No\.\s*Observations:\s+(\d+)"]:
            mm = re.search(patN, txt)
            if mm: n = int(mm.group(1)); break
        return {"var": m.group(1), "coef": float(m.group(2)), "se": float(m.group(3)),
                "t": float(m.group(4)), "p": float(m.group(5)), "N": n}

    rows = []
    for fp in sorted(glob.glob(os.path.join(OUTDIR, "panel_results_*.txt"))):
        base = os.path.basename(fp)
        policy = base.split("_")[2]
        date_str = base.split("_")[3]
        win = base.rsplit(".",1)[0].split("_", 4)[-1]
        with open(fp, "r", encoding="utf-8") as f:
            txt = f.read()
        res = parse_one(txt)
        if res:
            res.update({"file": base, "policy": policy, "event": date_str, "window": win})
            rows.append(res)

    df = pd.DataFrame(rows).sort_values(["policy","event","window"])
    print("\n===== Summary of ExpoQuick effects =====")
    print(df[["policy","event","window","coef","t","p","N","file"]].to_string(index=False))

    out_csv = os.path.join(OUTDIR, "panel_results_summary.csv")
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"\nSummary exported to: {out_csv}")
