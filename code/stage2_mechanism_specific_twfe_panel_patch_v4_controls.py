
import pandas as pd, numpy as np, statsmodels.api as sm, os, warnings
warnings.filterwarnings("ignore")

BASE_DIR = "."
PRICE_PATH = "Policy Influenced_Stock Price_With FF 5 Factors.csv"
POLICY_PATH = "All_Daily_Policy_Data_with_policy_mechanisms_v1.csv"
RATIOS_PATH = "Financial Ratios_Ticker.csv"
INTEGRATION_MAP_PATH = "p2_stage2_integration_map_v2_with_alt_bridge.csv"
OUTDIR = "stage2_mechanism_outputs_v4_controls"

POLICIES = {
    "IRA":  {"event_dates": ["2022-08-16"], "core_naics": {325120}, "edge_naics": {324110, 325199, 325193}},
    "LCFS": {"event_dates": ["2023-01-03"], "core_naics": {325193}, "edge_naics": {324110, 325199}},
    "RFS2": {"event_dates": ["2021-01-04"], "core_naics": {325193}, "edge_naics": {324110, 325199}},
}

def s_weight(naics_val, core_set, edge_set):
    try:
        x = int(str(naics_val).split(".")[0])
    except:
        return 0.0
    if x in core_set:
        return 1.0
    if x in edge_set:
        return 0.5
    return 0.0

def twfe_cluster(dfreg, y, xs):
    tmp = dfreg[["tic","Date",y] + xs].dropna().copy()
    for col in [y] + xs:
        ent_mean = tmp.groupby("tic")[col].transform("mean")
        time_mean = tmp.groupby("Date")[col].transform("mean")
        grand = tmp[col].mean()
        tmp[col+"_twfe"] = tmp[col] - ent_mean - time_mean + grand
    Y = tmp[y+"_twfe"]
    X = sm.add_constant(tmp[[c+"_twfe" for c in xs]], has_constant="add")
    res = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": tmp["tic"]})
    return res

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)

    price = pd.read_csv(PRICE_PATH, parse_dates=["Date"], low_memory=False)
    policy = pd.read_csv(POLICY_PATH, parse_dates=["Date"], low_memory=False)
    ratios = pd.read_csv(RATIOS_PATH, low_memory=False)
    integration = pd.read_csv(INTEGRATION_MAP_PATH)

    for c in ["public_date","adate","qdate"]:
        ratios[c] = pd.to_datetime(ratios[c], errors="coerce")

    price["tic"] = price["tic"].astype(str).str.upper().str.strip()
    ratios["TICKER"] = ratios["TICKER"].astype(str).str.upper().str.strip()
    integration["ticker"] = integration["ticker"].astype(str).str.upper().str.strip()

    price = price.sort_values(["Date","tic"]).copy()
    ratios = ratios.sort_values(["public_date","TICKER"]).copy()

    df = pd.merge_asof(
        price, ratios,
        left_on="Date", right_on="public_date",
        left_by="tic", right_by="TICKER",
        direction="backward"
    )

    df["_size_proxy"] = pd.to_numeric(df["prccd"], errors="coerce").clip(lower=1e-6)
    grp = df.groupby(["Date","naics"])["_size_proxy"].transform("sum")
    df["industry_share"] = np.where(grp > 0, df["_size_proxy"] / grp, 0.0)
    df["AR"] = pd.to_numeric(df["daily_abnormal_return"], errors="coerce")
    df["logP"] = np.log(df["_size_proxy"])

    for c in ["bm","debt_assets","curr_ratio","roa"]:
        s = pd.to_numeric(df[c], errors="coerce")
        std = s.std()
        z = (s - s.mean()) / std if pd.notna(std) and std != 0 else s * 0
        df[c+"_z"] = z.fillna(0)
        df[c+"_missing"] = s.isna().astype(int)

    integration = integration[integration["sample_decision"].isin(["keep","edge"])].copy()
    df = df[df["tic"].isin(set(integration["ticker"]))].copy()
    df = df.merge(integration, left_on="tic", right_on="ticker", how="inner")

    ctrl = ["logP","bm_z","debt_assets_z","curr_ratio_z","roa_z","bm_missing","debt_assets_missing","curr_ratio_missing","roa_missing"]
    mech_map = {
        "subsidy":"subsidy_exposure_stage2_input_weight",
        "compliance":"compliance_exposure_stage2_input_weight",
        "credit_market":"credit_market_exposure_stage2_input_weight",
        "demand_pull":"demand_pull_exposure_stage2_input_weight"
    }

    for pol, cfg in POLICIES.items():
        for ed in cfg["event_dates"]:
            t0 = pd.Timestamp(ed)
            subpre = df[df["Date"] < t0].copy()
            avg_share = subpre.groupby("tic")["industry_share"].apply(lambda s: s.tail(min(120, len(s))).mean()).rename("avg_share").reset_index()
            w = df[["tic","naics"]].drop_duplicates().copy()
            w["s_j"] = w["naics"].apply(lambda x: s_weight(x, cfg["core_naics"], cfg["edge_naics"]))
            expo = avg_share.merge(w, on="tic", how="left")
            expo["Exposure_pre"] = expo["avg_share"] * expo["s_j"]

            panel = df[(df["Date"] >= t0 - pd.Timedelta(days=120)) & (df["Date"] <= t0 + pd.Timedelta(days=10))].copy()
            panel["rel"] = (panel["Date"] - t0).dt.days
            panel["Post"] = (panel["rel"] >= 0).astype(int)

            pcols = ["Date","dpi01",
                     f"{pol}_subsidy_intensity_t",f"{pol}_compliance_intensity_t",
                     f"{pol}_credit_market_intensity_t",f"{pol}_demand_pull_intensity_t"]
            panel = panel.merge(policy[pcols], on="Date", how="left")
            panel = panel.merge(expo[["tic","Exposure_pre"]], on="tic", how="left")
            panel["ExpoQuick_it"] = panel["Exposure_pre"].fillna(0) * panel["Post"] * panel["dpi01"].fillna(0)

            for mech, wcol in mech_map.items():
                panel[f"{mech}_expo_it"] = panel["Exposure_pre"].fillna(0) * panel[wcol].fillna(0) * panel[f"{pol}_{mech}_intensity_t"].fillna(0) * panel["Post"]

            baseline = twfe_cluster(panel, "AR", ["ExpoQuick_it"] + ctrl)
            open(os.path.join(OUTDIR, f"panel_results_baseline_{pol}_{ed}.txt"), "w", encoding="utf-8").write(str(baseline.summary()))

            mechanism = twfe_cluster(panel, "AR", [f"{m}_expo_it" for m in mech_map] + ctrl)
            open(os.path.join(OUTDIR, f"panel_results_mechanism_{pol}_{ed}.txt"), "w", encoding="utf-8").write(str(mechanism.summary()))
