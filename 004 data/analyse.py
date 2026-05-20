"""
LOG650 - Etterspørselsprognoseanalyse
Student: Morten Eidsvåg
Modeller: Naiv, Holt-Winters, ARIMA (SARIMA), XGBoost
Evalueringsmål: RMSE, MAE, MAPE (median over 105 SKU-er)
"""

import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from itertools import product as iterproduct
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller, acf
from statsmodels.tsa.seasonal import STL
import xgboost as xgb

warnings.filterwarnings("ignore")

# ── Konfigurasjon ──────────────────────────────────────────────────────────────
DATA_FILE      = "salgsdata_anonymized.csv"
TRAIN_END      = 36        # Jan 2022 – Des 2024
TEST_PERIODS   = 12        # Jan 2025 – Des 2025
SEASON_PERIOD  = 12
RANDOM_SEED    = 42
OUTPUT_DIR     = "."
FS_THRESHOLD   = 0.64      # Sesongstyrke-terskel (M4-konkurransen)
CV_THRESHOLD   = 0.5       # Variationskoeffisient-terskel for Holt-Winters
XGB_LAGS       = list(range(1, 13))  # Lagg 1–12, alle med meningsfull ACF


# ── 1. Last inn og klargjør data ───────────────────────────────────────────────
def load_data(filepath):
    df = pd.read_csv(filepath, sep=";", index_col=0)
    df = df.iloc[:, :-1]
    months = pd.date_range(start="2022-01", periods=len(df.columns), freq="MS")
    df.columns = months
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.fillna(0)
    return df


# ── 2. Evalueringsmål ─────────────────────────────────────────────────────────
def rmse(actual, pred):
    return np.sqrt(mean_squared_error(actual, pred))

def mae_metric(actual, pred):
    return mean_absolute_error(actual, pred)

def mape_metric(actual, pred):
    actual, pred = np.array(actual), np.array(pred)
    mask = actual != 0
    if mask.sum() == 0:
        return np.nan
    return np.mean(np.abs((actual[mask] - pred[mask]) / actual[mask])) * 100


# ── 3. Utforskende dataanalyse (EDA) ──────────────────────────────────────────
def compute_fs(series_train):
    """Beregn sesongstyrke Fs fra STL-dekomponering (Cleveland et al., 1990)."""
    try:
        stl = STL(series_train, period=SEASON_PERIOD, robust=True)
        res = stl.fit()
        var_resid = np.var(res.resid)
        var_seasonal_plus_resid = np.var(res.seasonal + res.resid)
        if var_seasonal_plus_resid == 0:
            return 0.0
        return max(0.0, 1 - var_resid / var_seasonal_plus_resid)
    except Exception:
        return np.nan

def compute_cv(series_train):
    """Beregn variationskoeffisient (CV = std / mean) for treningssettet."""
    mean_val = np.mean(series_train)
    if mean_val == 0:
        return np.nan
    return np.std(series_train) / mean_val

def run_adf_test(series_train):
    """
    Kjør ADF-test (Said & Dickey, 1984).
    Returnerer (statistikk, p-verdi, stasjonær_bool).
    """
    try:
        result = adfuller(series_train, autolag="AIC")
        return result[0], result[1], bool(result[1] < 0.05)
    except Exception:
        return np.nan, np.nan, None

def run_eda(df):
    """
    Gjennomfør utforskende dataanalyse på treningssettet:
      - ADF-test for stasjonaritet per SKU
      - STL sesongstyrke (Fs) per SKU
      - Variationskoeffisient (CV) per SKU
      - Holt-Winters sesongform basert på CV
    Lagrer eda_resultater.csv og returnerer DataFrame.
    """
    print("\nKjører utforskende dataanalyse (EDA)...")
    records = []
    for sku in df.index:
        series = df.loc[sku].values.astype(float)
        train = series[:TRAIN_END]

        adf_stat, adf_p, is_stationary = run_adf_test(train)
        fs  = compute_fs(train)
        cv  = compute_cv(train)
        mean_vol = np.mean(train)

        # Multiplikativ HW kun hvis CV > terskel OG ingen nullverdier i treningssett
        has_zeros = np.any(train == 0)
        hw_form = (
            "multiplikativ"
            if (not np.isnan(cv) and cv > CV_THRESHOLD and not has_zeros)
            else "additiv"
        )

        records.append({
            "SKU":                  sku,
            "Mean_monthly_volume":  round(mean_vol, 1),
            "CV":                   round(cv, 3) if not np.isnan(cv) else np.nan,
            "Has_zeros":            has_zeros,
            "ADF_stat":             round(adf_stat, 4) if not np.isnan(adf_stat) else np.nan,
            "ADF_p":                round(adf_p, 4)    if not np.isnan(adf_p)    else np.nan,
            "Stationary_ADF":       is_stationary,
            "Fs_sesongstyrke":      round(fs, 4) if not np.isnan(fs) else np.nan,
            "Sterk_sesong":         (fs >= FS_THRESHOLD) if not np.isnan(fs) else None,
            "HW_form":              hw_form,
        })

    eda_df = pd.DataFrame(records).set_index("SKU")
    eda_df.to_csv(f"{OUTPUT_DIR}/eda_resultater.csv")

    # Oppsummering
    n = len(eda_df)
    n_stationary    = eda_df["Stationary_ADF"].sum()
    n_strong_season = eda_df["Sterk_sesong"].sum()
    n_mult          = (eda_df["HW_form"] == "multiplikativ").sum()

    print(f"  Stasjonaere serier (ADF p<0.05) : {n_stationary}/{n} ({100*n_stationary/n:.1f}%)")
    print(f"  Sterk sesong (Fs >= {FS_THRESHOLD})       : {n_strong_season}/{n} ({100*n_strong_season/n:.1f}%)")
    print(f"  Multiplikativ HW (CV>{CV_THRESHOLD}, ingen nuller): {n_mult}/{n} ({100*n_mult/n:.1f}%)")
    print(f"  Lagret: eda_resultater.csv")

    return eda_df

def analyse_acf_lag_selection(df):
    """
    ACF-analyse for å dokumentere og begrunne lagg-valg til XGBoost.
    Beregner gjennomsnittlig |ACF| per lagg på tvers av alle SKU-er.
    Lagrer eda_acf_lag_analyse.csv.
    """
    print("\nKjører ACF-analyse for lagg-valg...")
    max_lag = 13
    acf_matrix = []
    for sku in df.index:
        series = df.loc[sku].values.astype(float)
        train = series[:TRAIN_END]
        try:
            acf_vals = acf(train, nlags=max_lag, fft=True)[1:]  # hopp over lag 0
            acf_matrix.append(acf_vals)
        except Exception:
            pass

    acf_array = np.array(acf_matrix)
    mean_acf  = np.nanmean(np.abs(acf_array), axis=0)

    acf_df = pd.DataFrame({
        "Lagg":                       range(1, max_lag + 1),
        "Gjennomsnittlig_abs_ACF":    np.round(mean_acf, 4),
        "Valgt_i_XGBoost":            [lag in XGB_LAGS for lag in range(1, max_lag + 1)],
    }).set_index("Lagg")
    acf_df.to_csv(f"{OUTPUT_DIR}/eda_acf_lag_analyse.csv")

    print("  Gjennomsnittlig |ACF| per lagg:")
    for lag, val in zip(range(1, max_lag + 1), mean_acf):
        marker = " ← valgt" if lag in XGB_LAGS else ""
        print(f"    Lag {lag:2d}: {val:.4f}{marker}")
    print(f"  Lagret: eda_acf_lag_analyse.csv")

    return acf_df


# ── 4. Hyperparameteroptimalisering for XGBoost ────────────────────────────────
def build_xgboost_features(series, lags=None):
    """
    Bygg feature-matrise med valgte lagg, månedsnummer og trendindeks.
    Lagg-valg er begrunnet i ACF-analyse (se eda_acf_lag_analyse.csv).
    """
    if lags is None:
        lags = XGB_LAGS
    max_lag = max(lags)
    rows = []
    for t in range(max_lag, len(series)):
        lag_vals = [series[t - i] for i in lags]
        month = (t % 12) + 1
        trend = t
        rows.append(lag_vals + [month, trend, series[t]])
    cols = [f"lag_{i}" for i in lags] + ["month", "trend", "target"]
    return pd.DataFrame(rows, columns=cols)

def tune_xgboost_hyperparams(df, n_splits=3):
    """
    Tidsserie-krysskalibrering (TimeSeriesSplit, n_splits folder) for
    XGBoost hyperparametre. Søkegitter: n_estimators, learning_rate, max_depth.
    Lagrer xgboost_hyperparameter_cv.csv og returnerer beste parametre.
    """
    print(f"\nOptimaliserer XGBoost hyperparametre ({n_splits}-fold tidsserie-CV)...")

    all_data = []
    for sku in df.index:
        series = df.loc[sku].values.astype(float)
        feat_df = build_xgboost_features(series[:TRAIN_END])
        all_data.append(feat_df)
    combined = pd.concat(all_data, ignore_index=True)
    X = combined.drop("target", axis=1).values
    y = combined["target"].values

    param_grid = {
        "n_estimators":  [100, 200, 300],
        "learning_rate": [0.05, 0.10],
        "max_depth":     [3, 4, 5],
    }

    tscv = TimeSeriesSplit(n_splits=n_splits)
    best_rmse  = np.inf
    best_params = {}
    cv_records  = []

    keys = list(param_grid.keys())
    for values in iterproduct(*param_grid.values()):
        params = dict(zip(keys, values))
        fold_rmses = []
        for tr_idx, val_idx in tscv.split(X):
            X_tr, X_val = X[tr_idx], X[val_idx]
            y_tr, y_val = y[tr_idx], y[val_idx]
            model = xgb.XGBRegressor(
                **params,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=RANDOM_SEED,
                verbosity=0
            )
            model.fit(X_tr, y_tr)
            preds = model.predict(X_val)
            fold_rmses.append(np.sqrt(mean_squared_error(y_val, preds)))
        mean_cv_rmse = np.mean(fold_rmses)
        cv_records.append({**params, "CV_RMSE": round(mean_cv_rmse, 2)})
        if mean_cv_rmse < best_rmse:
            best_rmse   = mean_cv_rmse
            best_params = params

    cv_df = pd.DataFrame(cv_records).sort_values("CV_RMSE")
    cv_df.to_csv(f"{OUTPUT_DIR}/xgboost_hyperparameter_cv.csv", index=False)

    print(f"  Beste hyperparametre: {best_params}")
    print(f"  Beste CV-RMSE       : {best_rmse:.2f}")
    print(f"  Lagret: xgboost_hyperparameter_cv.csv")

    return best_params


# ── 5. Modeller ────────────────────────────────────────────────────────────────
def naive_forecast(train):
    """Sesongnaiv: siste årets verdier som prognose."""
    return np.array(train[-SEASON_PERIOD:])

def holtwinters_forecast(train, hw_form="additiv"):
    """
    Holt-Winters eksponentiell glatting.
    Sesongform velges basert på CV og forekomst av nullverdier (jf. eda_df):
      - multiplikativ hvis CV > 0.5 og ingen nullverdier i treningssett
      - additiv ellers
    """
    seasonal_mode = "mul" if hw_form == "multiplikativ" else "add"
    try:
        model = ExponentialSmoothing(
            train,
            trend="add",
            seasonal=seasonal_mode,
            seasonal_periods=SEASON_PERIOD,
            initialization_method="estimated"
        )
        fit = model.fit(optimized=True, remove_bias=True)
        return fit.forecast(TEST_PERIODS)
    except Exception:
        # Fallback 1: additiv
        try:
            model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=SEASON_PERIOD,
                initialization_method="estimated"
            )
            fit = model.fit(optimized=True)
            return fit.forecast(TEST_PERIODS)
        except Exception:
            # Fallback 2: ingen sesongkomponent
            try:
                model = ExponentialSmoothing(
                    train,
                    trend="add",
                    seasonal=None,
                    initialization_method="estimated"
                )
                fit = model.fit(optimized=True)
                return fit.forecast(TEST_PERIODS)
            except Exception:
                return np.full(TEST_PERIODS, np.mean(train))

def arima_forecast(train):
    """Auto ARIMA / SARIMA via pmdarima (AIC-minimering)."""
    try:
        from pmdarima import auto_arima
        model = auto_arima(
            train,
            seasonal=True,
            m=SEASON_PERIOD,
            stepwise=True,
            suppress_warnings=True,
            error_action="ignore",
            max_p=3, max_q=3, max_P=2, max_Q=2
        )
        return model.predict(n_periods=TEST_PERIODS)
    except Exception:
        return np.full(TEST_PERIODS, np.mean(train))

def train_xgboost_global(df, best_params=None):
    """Tren global XGBoost-modell på alle SKU-er med optimerte hyperparametre."""
    if best_params is None:
        best_params = {"n_estimators": 200, "learning_rate": 0.05, "max_depth": 4}

    all_data = []
    for sku in df.index:
        series = df.loc[sku].values.astype(float)
        feat_df = build_xgboost_features(series[:TRAIN_END])
        all_data.append(feat_df)
    combined = pd.concat(all_data, ignore_index=True)
    X = combined.drop("target", axis=1)
    y = combined["target"]

    model = xgb.XGBRegressor(
        **best_params,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        verbosity=0
    )
    model.fit(X, y)
    return model

def predict_xgboost_sku(model, train_series):
    """Rullende out-of-sample prognose for én SKU med den globale modellen."""
    history = list(train_series.astype(float))
    preds = []
    for _ in range(TEST_PERIODS):
        t = len(history)
        lag_vals = [history[-i] for i in XGB_LAGS]
        month = (t % 12) + 1
        trend = t
        X = pd.DataFrame(
            [lag_vals + [month, trend]],
            columns=[f"lag_{i}" for i in XGB_LAGS] + ["month", "trend"]
        )
        pred = max(0.0, float(model.predict(X)[0]))
        preds.append(pred)
        history.append(pred)
    return np.array(preds)


# ── 5b. XGBoost individuell per SKU ───────────────────────────────────────────
def run_xgboost_individual(df, best_params=None):
    """
    Trener én XGBoost-modell per SKU (105 modeller) med samme 36 treningsobservasjoner
    som HW og ARIMA. Kontrolleksperiment for å isolere pooling-effekten fra
    global XGBoost (jf. avsnitt 8.3 og 8.4 i rapporten).
    """
    if best_params is None:
        best_params = {"n_estimators": 300, "learning_rate": 0.05, "max_depth": 4}

    print("\nKjører XGBoost individuell per SKU...")
    max_lag = max(XGB_LAGS)
    n_train_feats = TRAIN_END - max_lag  # typisk 36 - 12 = 24 treningsrader per SKU

    rmse_list, mae_list, mape_list = [], [], []
    sku_records = []

    for i, sku in enumerate(df.index):
        if (i + 1) % 20 == 0:
            print(f"  SKU {i+1}/{len(df.index)}...")

        series = df.loc[sku].values.astype(float)

        feat_df = build_xgboost_features(series, lags=XGB_LAGS)
        X_train = feat_df.iloc[:n_train_feats].drop("target", axis=1).values
        y_train = feat_df.iloc[:n_train_feats]["target"].values
        X_test  = feat_df.iloc[n_train_feats:n_train_feats + TEST_PERIODS].drop("target", axis=1).values
        y_test  = feat_df.iloc[n_train_feats:n_train_feats + TEST_PERIODS]["target"].values

        if len(X_train) < 5 or len(X_test) == 0:
            rmse_list.append(np.nan)
            mae_list.append(np.nan)
            mape_list.append(np.nan)
            sku_records.append({"SKU": sku, "RMSE": None, "MAE": None, "MAPE": None})
            continue

        model = xgb.XGBRegressor(
            **best_params,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_SEED,
            verbosity=0,
        )
        model.fit(X_train, y_train)
        preds = np.maximum(0.0, model.predict(X_test))

        r = rmse(y_test, preds)
        m = mae_metric(y_test, preds)
        p = mape_metric(y_test, preds)

        rmse_list.append(r)
        mae_list.append(m)
        mape_list.append(p)
        sku_records.append({"SKU": sku, "RMSE": round(r, 4), "MAE": round(m, 4), "MAPE": round(p, 4) if p is not None else None})

    ind_df = pd.DataFrame(sku_records)
    ind_df.to_csv(f"{OUTPUT_DIR}/resultater_xgboost_individuell.csv", index=False)

    mape_vals = [v for v in mape_list if not np.isnan(v)]
    print(f"  Median RMSE : {np.median([v for v in rmse_list if not np.isnan(v)]):.2f}")
    print(f"  Median MAE  : {np.median([v for v in mae_list  if not np.isnan(v)]):.2f}")
    print(f"  Median MAPE : {np.median(mape_vals):.2f}%  (n={len(mape_vals)} SKU-er)")
    print(f"  Lagret: resultater_xgboost_individuell.csv")

    return {"RMSE": rmse_list, "MAE": mae_list, "MAPE": mape_list, "preds": [], "actuals": []}


# ── 6. Kjør alle modeller ──────────────────────────────────────────────────────
def run_analysis(df, xgb_model, eda_df):
    print("\nKjører modeller (dette tar noen minutter for ARIMA)...")
    results = {
        "Naiv":         {"RMSE": [], "MAE": [], "MAPE": [], "preds": [], "actuals": []},
        "Holt-Winters": {"RMSE": [], "MAE": [], "MAPE": [], "preds": [], "actuals": []},
        "ARIMA":        {"RMSE": [], "MAE": [], "MAPE": [], "preds": [], "actuals": []},
        "XGBoost":      {"RMSE": [], "MAE": [], "MAPE": [], "preds": [], "actuals": []},
    }

    n_skus = len(df)
    for i, sku in enumerate(df.index):
        if (i + 1) % 10 == 0:
            print(f"  Behandler SKU {i+1}/{n_skus}...")

        series = df.loc[sku].values.astype(float)
        train  = series[:TRAIN_END]
        actual = series[TRAIN_END:TRAIN_END + TEST_PERIODS]

        hw_form = eda_df.loc[sku, "HW_form"] if sku in eda_df.index else "additiv"

        forecasts = {
            "Naiv":         naive_forecast(train),
            "Holt-Winters": holtwinters_forecast(train, hw_form=hw_form),
            "ARIMA":        arima_forecast(train),
            "XGBoost":      predict_xgboost_sku(xgb_model, train),
        }

        for model_name, pred in forecasts.items():
            pred = np.array(pred[:TEST_PERIODS])
            results[model_name]["RMSE"].append(rmse(actual, pred))
            results[model_name]["MAE"].append(mae_metric(actual, pred))
            results[model_name]["MAPE"].append(mape_metric(actual, pred))
            results[model_name]["preds"].extend(list(pred))
            results[model_name]["actuals"].extend(list(actual))

    return results


# ── 7. Aggreger resultater ─────────────────────────────────────────────────────
def summarize_results(results):
    rows = []
    for model_name, metrics in results.items():
        mape_vals = [v for v in metrics["MAPE"] if not np.isnan(v)]
        rows.append({
            "Modell":              model_name,
            "RMSE (median)":       round(np.median(metrics["RMSE"]), 2),
            "MAE (median)":        round(np.median(metrics["MAE"]), 2),
            "MAPE (median, %)":    round(np.median(mape_vals), 2) if mape_vals else np.nan,
            "MAPE (SKU-er brukt)": len(mape_vals),
        })
    return pd.DataFrame(rows).set_index("Modell")


# ── 8. Segmentanalyse ──────────────────────────────────────────────────────────
def run_segment_analysis(df, results, eda_df):
    """
    Beregn median MAPE per modell fordelt på:
      - Sesongstyrke: tydelig (Fs ≥ 0.64) vs. svak/ingen
      - Volumnivå: høy / middels / lav (tertiler)
    Lagrer resultater_segment_sesong.csv og resultater_segment_volum.csv.
    """
    print("\nKjører segmentanalyse...")
    sku_list = list(df.index)

    # MAPE per SKU per modell
    sku_mape = {}
    for model_name, metrics in results.items():
        sku_mape[model_name] = {
            sku: metrics["MAPE"][i]
            for i, sku in enumerate(sku_list)
        }

    # ── Sesong-segment ──
    sesong_rows = []
    for label, flag in [("Tydelig sesong", True), ("Svak/ingen sesong", False)]:
        seg_skus = eda_df[eda_df["Sterk_sesong"] == flag].index.tolist()
        for model_name in ["Naiv", "Holt-Winters", "ARIMA", "XGBoost"]:
            vals = [
                sku_mape[model_name][s]
                for s in seg_skus
                if s in sku_mape[model_name] and not np.isnan(sku_mape[model_name][s])
            ]
            sesong_rows.append({
                "Segment":    label,
                "Modell":     model_name,
                "Median_MAPE": round(np.median(vals), 2) if vals else np.nan,
                "N_SKU":      len(vals),
            })
    sesong_df = pd.DataFrame(sesong_rows)
    sesong_df.to_csv(f"{OUTPUT_DIR}/resultater_segment_sesong.csv", index=False)

    # ── Volum-segment (tertiler) ──
    mean_vol = {sku: np.mean(df.loc[sku].values[:TRAIN_END]) for sku in sku_list}
    vol_series  = pd.Series(mean_vol)
    low_thresh  = vol_series.quantile(1 / 3)
    high_thresh = vol_series.quantile(2 / 3)

    volum_rows = []
    for label, condition in [
        ("Høyt volum",    vol_series >= high_thresh),
        ("Middels volum", (vol_series >= low_thresh) & (vol_series < high_thresh)),
        ("Lavt volum",    vol_series < low_thresh),
    ]:
        seg_skus = vol_series[condition].index.tolist()
        for model_name in ["Naiv", "Holt-Winters", "ARIMA", "XGBoost"]:
            vals = [
                sku_mape[model_name][s]
                for s in seg_skus
                if s in sku_mape[model_name] and not np.isnan(sku_mape[model_name][s])
            ]
            volum_rows.append({
                "Segment":    label,
                "Modell":     model_name,
                "Median_MAPE": round(np.median(vals), 2) if vals else np.nan,
                "N_SKU":      len(vals),
            })
    volum_df = pd.DataFrame(volum_rows)
    volum_df.to_csv(f"{OUTPUT_DIR}/resultater_segment_volum.csv", index=False)

    print("\n  Median MAPE per sesong-segment:")
    print(sesong_df.pivot(index="Modell", columns="Segment", values="Median_MAPE").to_string())
    print("\n  Median MAPE per volum-segment:")
    print(volum_df.pivot(index="Modell", columns="Segment", values="Median_MAPE").to_string())

    return sesong_df, volum_df


# ── 9. Diebold-Mariano test ────────────────────────────────────────────────────
def run_dm_test(results):
    """DM-test: HW vs. ARIMA og XGBoost vs. ARIMA (Diebold & Mariano, 1995)."""
    try:
        from dieboldmariano import dm_test as dm
        actuals     = results["ARIMA"]["actuals"]
        hw_preds    = results["Holt-Winters"]["preds"]
        arima_preds = results["ARIMA"]["preds"]
        xgb_preds   = results["XGBoost"]["preds"]

        stat_hw,  p_hw  = dm(actuals, hw_preds,  arima_preds, h=1)
        stat_xgb, p_xgb = dm(actuals, xgb_preds, arima_preds, h=1)

        print(f"\nDiebold-Mariano (Holt-Winters vs. ARIMA):")
        print(f"  DM={stat_hw:.4f}, p={p_hw:.4f} — {'Signifikant' if p_hw < 0.05 else 'Ikke signifikant'} (α=0.05)")
        print(f"Diebold-Mariano (XGBoost vs. ARIMA):")
        print(f"  DM={stat_xgb:.4f}, p={p_xgb:.4f} — {'Signifikant' if p_xgb < 0.05 else 'Ikke signifikant'} (α=0.05)")

        return (stat_hw, p_hw), (stat_xgb, p_xgb)
    except Exception as e:
        print(f"\nDM-test feilet: {e}")
        return (None, None), (None, None)


# ── 10. Visualiseringer ────────────────────────────────────────────────────────
def plot_mape_sammenligning(results, output_dir):
    """Stolpediagram: median MAPE per modell — brukes som Figur 2 i rapporten."""
    models = ["Naiv", "Holt-Winters", "XGBoost (individuell)", "ARIMA", "XGBoost"]
    labels = ["Naiv", "Holt-Winters", "XGBoost\n(individuell)", "ARIMA", "XGBoost\n(global)"]
    colors = ["#aaaaaa", "#5b9bd5", "#9dc3e6", "#ed7d31", "#70ad47"]
    medians = []
    for m in models:
        vals = [v for v in results[m]["MAPE"] if not np.isnan(v)]
        medians.append(np.median(vals))

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(labels, medians, color=colors, edgecolor="white", linewidth=0.8)
    for bar, val in zip(bars, medians):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{val:.1f} %", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_title("Figur 2: Median MAPE per modell (alle 105 SKU-er, testperiode Jan\u2013Des 2025)",
                 fontsize=12)
    ax.set_ylabel("Median MAPE (%)")
    ax.set_ylim(0, max(medians) * 1.18)
    ax.axhline(medians[0], color="gray", linestyle="--", linewidth=0.8, alpha=0.6, label="Naiv referanse")
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figur2_mape_sammenligning.png", dpi=150)
    plt.close()
    print(f"  Lagret: figur2_mape_sammenligning.png")

def plot_mape_boxplot(results, output_dir):
    fig, ax = plt.subplots(figsize=(11, 6))
    model_keys   = ["Naiv", "Holt-Winters", "XGBoost (individuell)", "ARIMA", "XGBoost"]
    model_labels = ["Naiv", "Holt-Winters", "XGBoost\n(individuell)", "ARIMA", "XGBoost\n(global)"]
    data = [
        [v for v in results[m]["MAPE"] if not np.isnan(v)]
        for m in model_keys
    ]
    bp = ax.boxplot(
        data,
        labels=model_labels,
        patch_artist=True,
        medianprops=dict(color="darkblue", linewidth=2)
    )
    box_colors = ["#dddddd", "#5b9bd5", "#9dc3e6", "#ed7d31", "#70ad47"]
    for patch, color in zip(bp["boxes"], box_colors):
        patch.set_facecolor(color)
    ax.set_title("Figur 2: Fordeling av MAPE per modell (alle SKU-er)", fontsize=13)
    ax.set_ylabel("MAPE (%)")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figur2_mape_boxplot.png", dpi=150)
    plt.close()
    print(f"  Lagret: figur2_mape_boxplot.png")

def plot_example_forecasts(df, output_dir, xgb_model, eda_df):
    sku    = df.index[1]
    series = df.loc[sku].values.astype(float)
    train  = series[:TRAIN_END]
    actual = series[TRAIN_END:TRAIN_END + TEST_PERIODS]
    hw_form = eda_df.loc[sku, "HW_form"] if sku in eda_df.index else "additiv"

    naive_pred = naive_forecast(train)
    hw_pred    = holtwinters_forecast(train, hw_form=hw_form)
    arima_pred = arima_forecast(train)
    xgb_pred   = predict_xgboost_sku(xgb_model, train)

    months_train = pd.date_range("2022-01", periods=TRAIN_END,  freq="MS")
    months_test  = pd.date_range("2025-01", periods=TEST_PERIODS, freq="MS")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(months_train, train,                   label="Historisk (2022–2024)", color="black",      linewidth=1.5)
    ax.plot(months_test,  actual,                  label="Faktisk (2025)",        color="black",      linestyle="--", linewidth=1.5)
    ax.plot(months_test,  naive_pred,              label="Naiv",                  color="gray",       linestyle=":",  linewidth=1.5)
    ax.plot(months_test,  hw_pred[:TEST_PERIODS],  label="Holt-Winters",          color="steelblue",  linestyle="-",  linewidth=1.5)
    ax.plot(months_test,  arima_pred[:TEST_PERIODS], label="ARIMA",               color="darkorange", linestyle="-.", linewidth=1.5)
    ax.plot(months_test,  xgb_pred[:TEST_PERIODS], label="XGBoost",               color="green",      linestyle="--", linewidth=1.5)
    ax.axvline(pd.Timestamp("2025-01-01"), color="red", linestyle="--", alpha=0.5, linewidth=1.2, label="Train/test-grense")
    ax.set_title(f"Figur 1: Eksempel prognose — SKU {sku}", fontsize=13)
    ax.set_ylabel("Volum (pakninger)")
    ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/figur1_eksempel_prognose.png", dpi=150)
    plt.close()
    print(f"  Lagret: figur1_eksempel_prognose.png")


# ── Hovedprogram ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("LOG650 — Etterspørselsprognoseanalyse")
    print("=" * 60)

    print("\nLaster inn data...")
    df = load_data(DATA_FILE)
    print(f"  {len(df)} SKU-er, {len(df.columns)} måneder")

    # EDA: ADF, STL, CV
    eda_df = run_eda(df)

    # ACF-analyse for lagg-dokumentasjon
    acf_df = analyse_acf_lag_selection(df)

    # Hyperparameteroptimalisering for XGBoost
    best_params = tune_xgboost_hyperparams(df, n_splits=3)

    # Tren global XGBoost med optimerte hyperparametre
    print("\nTrener global XGBoost-modell med optimerte hyperparametre...")
    xgb_model = train_xgboost_global(df, best_params=best_params)

    # Kjør alle modeller
    results = run_analysis(df, xgb_model, eda_df)

    # XGBoost individuell per SKU (kontrolleksperiment for pooling-effekten)
    results["XGBoost (individuell)"] = run_xgboost_individual(df, best_params=best_params)

    # Oppsummering
    print("\n" + "=" * 60)
    print("RESULTATER — Median over alle SKU-er")
    print("=" * 60)
    summary = summarize_results(results)
    print(summary.to_string())
    summary.to_csv(f"{OUTPUT_DIR}/resultater_sammenligning.csv")
    print(f"  Lagret: resultater_sammenligning.csv")

    # Segmentanalyse
    sesong_df, volum_df = run_segment_analysis(df, results, eda_df)

    # DM-test
    print("\nKjører Diebold-Mariano test...")
    run_dm_test(results)

    # Visualiseringer
    print("\nLager visualiseringer...")
    plot_mape_sammenligning(results, OUTPUT_DIR)
    plot_mape_boxplot(results, OUTPUT_DIR)
    plot_example_forecasts(df, OUTPUT_DIR, xgb_model, eda_df)

    print("\n" + "=" * 60)
    print("Ferdig! Produserte filer:")
    print("  eda_resultater.csv              — ADF, Fs, CV, HW-form per SKU")
    print("  eda_acf_lag_analyse.csv         — ACF-begrunnelse for lagg-valg")
    print("  xgboost_hyperparameter_cv.csv   — Krysskalibrering av hyperparametre")
    print("  resultater_sammenligning.csv              — Hovedresultater (Tabell 2)")
    print("  resultater_xgboost_individuell.csv        — Per-SKU resultater for XGBoost individuell")
    print("  resultater_segment_sesong.csv             — Segmentresultater etter sesong (Tabell 3)")
    print("  resultater_segment_volum.csv    — Segmentresultater etter volum (Tabell 4)")
    print("  figur1_eksempel_prognose.png")
    print("  figur2_mape_boxplot.png")
    print("=" * 60)
