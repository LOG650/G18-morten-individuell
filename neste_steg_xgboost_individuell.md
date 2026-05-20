# Neste steg: XGBoost individuell per SKU

## Bakgrunn

Rapporten sammenligner fire modeller på 105 farmasøytiske SKU-er (48 måneder,
treningssett 36 mnd, testperiode 12 mnd):

- Naiv sesongprognose
- Holt-Winters (individuell per SKU)
- ARIMA/SARIMA (individuell per SKU)
- XGBoost **global** (én modell trent på alle 105 SKU-er samlet, lagg 1–12)

XGBoost global gir lavest MAPE (52,19 %), men rapporten har en åpen metodisk svakhet:
sammenligningen er asymmetrisk. HW og ARIMA trenes individuelt (36 obs per modell),
XGBoost trenes globalt (3 780 obs totalt). Vi kan ikke skille om XGBoosts fordel
skyldes modellarkitekturen eller den økte datautnyttelsen fra global pooling.

## Målet

Legge til en femte modell: **XGBoost individuell** — 105 separate XGBoost-modeller,
én per SKU, trent på de samme 36 treningsobservasjonene som HW og ARIMA.

Dette er det kontrolleksperimentet rapporten etterlyser i avsnitt 8.3 og 8.4.

## Forventet utfall

Individuell XGBoost vil sannsynligvis prestere **dårligere** enn global XGBoost,
fordi 36 observasjoner minus 12 lagg gir kun ~24 brukbare treningsrader per modell —
svært lite for en trebasert modell. Det er det interessante: hvis individuell XGBoost
er dårligere enn global XGBoost, bekrefter det at pooling-effekten er en reell del
av forklaringen, ikke bare modellarkitekturen.

Tre mulige utfall og hva de betyr:
1. Individuell XGBoost er dårligere enn global → pooling er årsaken til fordelen
2. Individuell XGBoost er omtrent lik global → arkitekturen er årsaken
3. Individuell XGBoost er bedre enn global → global modell overfittes på støyrike SKU-er

## Kodeendringer i analyse.py

Filen ligger i: `004 data/analyse.py`

### 1. Legg til ny funksjon etter `run_forecasts()`

```python
def run_xgboost_individual(df, results_global):
    """
    Trener én XGBoost-modell per SKU (individuell, ikke global).
    Sammenligner med global XGBoost fra results_global.
    """
    from xgboost import XGBRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error

    individual_results = []
    skus = df["SKU"].unique()

    for sku in skus:
        series = df[df["SKU"] == sku]["Salg"].values
        train = series[:TRAIN_END]
        test  = series[TRAIN_END:TRAIN_END + TEST_PERIODS]

        # Bygg feature-matrise med lagg 1-12
        X_all, y_all = build_xgboost_features(series[:TRAIN_END + TEST_PERIODS], lags=XGB_LAGS)
        X_train = X_all[:len(train) - max(XGB_LAGS)]
        y_train = y_all[:len(train) - max(XGB_LAGS)]
        X_test  = X_all[len(train) - max(XGB_LAGS):]
        y_test  = test[max(XGB_LAGS) - (TEST_PERIODS - len(X_test)):]  # justering

        if len(X_train) < 5 or len(X_test) == 0:
            # For lite data — hopp over og sett NaN
            individual_results.append({
                "SKU": sku, "RMSE": None, "MAE": None, "MAPE": None
            })
            continue

        # Bruk samme hyperparametere som global modell
        model = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=4,
            random_state=RANDOM_SEED,
            verbosity=0
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mae  = mean_absolute_error(y_test, preds)
        # MAPE — unngå divisjon på null
        mask = y_test != 0
        mape = np.mean(np.abs((y_test[mask] - preds[mask]) / y_test[mask])) * 100 if mask.any() else None

        individual_results.append({
            "SKU": sku, "RMSE": rmse, "MAE": mae, "MAPE": mape
        })

    ind_df = pd.DataFrame(individual_results)
    ind_df.to_csv(os.path.join(OUTPUT_DIR, "resultater_xgboost_individuell.csv"), index=False)

    # Summer opp median-tall
    median_rmse = ind_df["RMSE"].median()
    median_mae  = ind_df["MAE"].median()
    median_mape = ind_df["MAPE"].median()

    print(f"\nXGBoost individuell — median RMSE: {median_rmse:.2f}, MAE: {median_mae:.2f}, MAPE: {median_mape:.2f}%")
    print(f"XGBoost global     — median RMSE fra tabell: se resultater_sammenligning.csv")

    return ind_df
```

### 2. Kall funksjonen i `main()`

Legg til etter at `results` er beregnet og `run_forecasts()` er ferdig:

```python
xgb_ind_df = run_xgboost_individual(df, results)
```

### 3. Legg til i sammenligningstabellen

Etter at `resultater_sammenligning.csv` er generert, legg til en rad for
"XGBoost (individuell)" med median RMSE/MAE/MAPE fra `xgb_ind_df`.

## Rapportendringer etter kjøring

Når koden er kjørt og tallene er klare, legg til:

1. **Tabell 2** i rapport: ny rad "XGBoost (individuell)" med resultatene
2. **Avsnitt 8.3**: erstatt den åpne setningen om at individuell XGBoost
   "ligger utenfor studiens rammer" med faktiske resultater og tolkning
3. **Avsnitt 8.4** (begrensninger): fjern eller oppdater den tredje
   begrensningen om asymmetri, siden den nå er adressert
4. **Konklusjon 9.0**: oppdater med hva sammenligningen viste

## Viktig å merke seg ved oppstart

- Kjør alltid med: `python -X utf8 analyse.py` (Windows encoding-problem)
- Arbeidskatalog må være: `004 data/`
- Datafilen heter: `salgsdata_anonymized.csv`
- Globale XGBoost-hyperparametere (fra CV): n_estimators=300, learning_rate=0.05, max_depth=4
- XGB_LAGS = list(range(1, 13)) — alle lagg 1–12

## Kontekstfil for ny Claude-økt

For å starte en ny økt med full kontekst, si til Claude:
> "Les filen neste_steg_xgboost_individuell.md og implementer XGBoost individuell
> per SKU i analyse.py som beskrevet der."
