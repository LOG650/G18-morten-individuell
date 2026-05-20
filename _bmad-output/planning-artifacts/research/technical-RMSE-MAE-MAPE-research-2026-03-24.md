---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Evaluering av prognosemodeller — RMSE, MAE, MAPE i praksis'
research_goals: 'Forstå teori, praktisk bruk og svakheter ved RMSE, MAE og MAPE for bruk i teori- og metodedelen av LOG650-rapporten'
user_name: 'Mort1'
date: '2026-03-24'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-03-24
**Author:** Mort1
**Research Type:** technical

---

## Research Overview

Teknisk forskningsrapport om evalueringsmål for prognosemodeller: RMSE, MAE og MAPE.
Basert på websøk med kildeverifisering, 2026-03-24.

---

## Teknisk forskningsomfang

**Forskningstema:** Evaluering av prognosemodeller — RMSE, MAE, MAPE i praksis
**Forskningsmål:** Forstå teori, praktisk bruk og svakheter ved RMSE, MAE og MAPE
**Dato:** 2026-03-24

---

## 1. Matematisk teori og formler

### MAE — Mean Absolute Error

MAE er gjennomsnittet av de absolutte avvikene mellom faktisk og predikert verdi:

**MAE = (1/n) · Σ|yₜ − ŷₜ|**

- Uttrykkes i samme enheter som dataene (pakninger, kroner, etc.)
- Enkel å kommunisere og tolke
- Robust mot ekstremverdier (outliers)
- En modell som minimerer MAE gir prognoser for **medianen** av fordelingen

### RMSE — Root Mean Squared Error

RMSE er kvadratroten av gjennomsnittlig kvadrert avvik:

**RMSE = √((1/n) · Σ(yₜ − ŷₜ)²)**

- Uttrykkes i samme enheter som dataene
- Straffer store avvik hardere enn MAE (pga. kvadrering)
- Sensitiv for outliers
- En modell som minimerer RMSE gir prognoser for **gjennomsnittet** av fordelingen

### MAPE — Mean Absolute Percentage Error

MAPE uttrykker feil som prosentandel av faktisk verdi:

**MAPE = (1/n) · Σ|(yₜ − ŷₜ)/yₜ| · 100**

- Skala-uavhengig — kan sammenligne presisjon på tvers av varelinjer med ulike volumer
- Intuitiv for beslutningstakere («gjennomsnittlig X % feil»)
- **Kritisk svakhet:** udefinert når yₜ = 0

---

## 2. Praktisk valg av feilmål

### Beslutningsguide

| Situasjon | Anbefalt mål |
|-----------|-------------|
| Standardsituasjon, robust oppsummering | MAE |
| Store feil er særlig kostbare | RMSE |
| Sammenligning på tvers av ulike volumnivåer | MAPE (hvis ingen nullverdier) |
| Datasett med nullverdier/sporadisk etterspørsel | WMAPE eller MASE |

### Kombinert bruk

Forskere anbefaler å rapportere **flere mål simultant** for et mer fullstendig bilde:
- Dersom MAE og RMSE er nær hverandre: feilene er jevnt fordelt
- Dersom RMSE >> MAE: det finnes store enkeltavvik som dominerer

**Kilde:** Hyndman & Athanasopoulos (2021), Hyndman (2014)

---

## 3. Svakheter og fallgruver

### MAPE

1. **Nullverdier:** Dersom yₜ = 0 oppstår divisjon med null. Selv verdier nær null gir ekstreme MAPE-verdier.
2. **Asymmetri:** Undervurdering kan aldri gi feil > 100 %, mens overvurdering ikke har øvre grense. Dette gir systematisk favorisering av modeller som underestimerer.
3. **Ikke egnet for sporadisk etterspørsel (intermittent demand):** Vanlig problem i farmasøytisk logistikk.

### RMSE

1. **Sensitiv for outliers:** Én stor feil kan dominere hele metrikken
2. **Vanskelig å sammenligne på tvers av serier** med ulike volumnivåer

### MAE

1. **Skala-avhengig:** Kan ikke brukes til å sammenligne serier med svært ulike volumnivåer uten normalisering

---

## 4. Alternativer

| Mål | Beskrivelse | Fordel |
|-----|-------------|--------|
| **WMAPE** | Vektet MAPE (vektet etter faktisk volum) | Løser nullverdi-problemet |
| **MASE** | Mean Absolute Scaled Error (Hyndman & Koehler, 2006) | Skala-uavhengig, robust |
| **MAAPE** | Mean Arctangent APE | Håndterer nullverdier matematisk |
| **sMAPE** | Symmetric MAPE | Reduserer asymmetri-problemet |

**MASE** er i dag ansett som det mest robuste enkeltmålet for tidsseriesammenligning (Hyndman & Athanasopoulos, 2021).

---

## 5. Python-implementasjon

```python
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

def rmse(actual, predicted):
    return np.sqrt(mean_squared_error(actual, predicted))

def mae(actual, predicted):
    return mean_absolute_error(actual, predicted)

def mape(actual, predicted):
    actual, predicted = np.array(actual), np.array(predicted)
    # Unngå divisjon med null
    mask = actual != 0
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100

def wmape(actual, predicted):
    actual, predicted = np.array(actual), np.array(predicted)
    return np.sum(np.abs(actual - predicted)) / np.sum(np.abs(actual)) * 100
```

---

## 6. Relevans for LOG650-prosjektet

**Anbefaling for ditt datasett (105 SKU-er, farmasøytisk distribusjon):**

- Bruk **alle tre** (RMSE, MAE, MAPE) for sammenlignbarhet med litteraturen
- Vær oppmerksom på varelinjer med **nullverdier** — ekskluder disse fra MAPE-beregningen eller bytt til WMAPE
- Rapporter **median** fremfor gjennomsnitt på tvers av SKU-er for å redusere påvirkning fra outlier-serier
- MAPE er særlig nyttig for å kommunisere resultater til bedriften (ikke-teknisk publikum)

---

## Kilder

- [5.8 Evaluating point forecast accuracy — Forecasting: Principles and Practice (3rd ed)](https://otexts.com/fpp3/accuracy.html)
- [Measuring forecast accuracy — Hyndman (2014)](https://www.robjhyndman.com/papers/forecast-accuracy.pdf)
- [MAPE weaknesses and alternatives — StatWorx](https://www.statworx.com/en/content-hub/blog/what-the-mape-is-falsely-blamed-for-its-true-weaknesses-and-better-alternatives)
- [Choosing the correct error metric: MAPE vs. sMAPE — Towards Data Science](https://towardsdatascience.com/choosing-the-correct-error-metric-mape-vs-smape-5328dec53fac/)
- [Time Series Forecasting Performance Measures With Python — MachineLearningMastery](https://machinelearningmastery.com/time-series-forecasting-performance-measures-with-python/)
- [Forecast KPI: RMSE, MAE, MAPE & Bias — LinkedIn/Vandeput](https://www.linkedin.com/pulse/forecast-kpi-rmse-mae-mape-bias-nicolas-vandeput)
- [Mean absolute percentage error — Wikipedia](https://en.wikipedia.org/wiki/Mean_absolute_percentage_error)

---

## 7. Evalueringspipeline og beste praksis

### Krysskalibrering for tidsserier (Walk-Forward Validation)

Standard k-fold krysskalibrering er **ikke egnet** for tidsserier da den bryter den temporale rekkefølgen og gir datalekkasje. Walk-forward validering er riktig tilnærming:

```
Treningsvindu 1: [1..36]  → Test: [37..48]   ← Hold-out (brukt i dette prosjektet)
Treningsvindu 2: [1..24]  → Test: [25..36]   ← Utvidet validering (valgfritt)
Treningsvindu 3: [1..12]  → Test: [13..24]   ← Ytterligere robusthet
```

Hold-out-strategien (ett fast treningssett + ett testsett) er akseptabel ved begrenset historikk (48 måneder), og anbefales av Hyndman & Athanasopoulos (2021) for korte tidsserier.

**Kritisk regel:** Testsettet må alltid ligge *etter* treningssettet i tid — aldri bland fremtidig data inn i trening.

### Aggregering over 105 SKU-er

**Anbefalt tilnærming:**
- Beregn RMSE, MAE og MAPE **per SKU** individuelt
- Aggreger med **median** (ikke gjennomsnitt) på tvers av alle 105 SKU-er
- Rapporter også **interkvartilbredde (IQR)** for å vise spredning i modellpresisjon

**Hvorfor median fremfor gjennomsnitt?**
Fordelingen av feilmål på tvers av SKU-er vil typisk inneholde ekstreme verdier (lavvolum-produkter med høy MAPE). Median er robust mot slike outliers og gir et mer representativt bilde.

### Diebold-Mariano-test i Python

DM-testen er standardverktøyet for å teste om to prognosemodeller har statistisk signifikant ulik presisjon (Diebold & Mariano, 1995):

```python
# Installasjon
pip install dieboldmariano

# Bruk
from dieboldmariano import dm_test

# actual: faktiske verdier
# pred1: prognoser fra Holt-Winters
# pred2: prognoser fra ARIMA
dm_stat, p_value = dm_test(actual, pred1, pred2, h=12, crit="MSE")

print(f"DM-statistikk: {dm_stat:.4f}")
print(f"p-verdi: {p_value:.4f}")
# p < 0.05 → signifikant forskjell mellom modellene
```

**Nullhypotese:** De to modellene har lik prognosepresisjon
**Alternativ hypotese:** Den ene modellen er signifikant bedre

### Komplett evalueringspipeline (Python-skjelett)

```python
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

def evaluate_all_models(results_dict, actuals_dict):
    """
    results_dict: {'HoltWinters': {sku: predictions}, 'ARIMA': {...}, ...}
    actuals_dict: {sku: actual_values}
    """
    summary = {}
    for model_name, predictions in results_dict.items():
        rmse_list, mae_list, mape_list = [], [], []
        for sku in predictions:
            actual = np.array(actuals_dict[sku])
            pred   = np.array(predictions[sku])
            rmse_list.append(np.sqrt(mean_squared_error(actual, pred)))
            mae_list.append(mean_absolute_error(actual, pred))
            # MAPE: ekskluder nullverdier
            mask = actual != 0
            if mask.sum() > 0:
                mape_list.append(np.mean(np.abs((actual[mask]-pred[mask])/actual[mask]))*100)
        summary[model_name] = {
            'RMSE_median': np.median(rmse_list),
            'MAE_median':  np.median(mae_list),
            'MAPE_median': np.median(mape_list)
        }
    return pd.DataFrame(summary).T
```

---

## 8. Oppsummering — Relevante akademiske referanser

| Kilde | Relevans |
|-------|----------|
| Hyndman & Athanasopoulos (2021), kap. 5.8 | Definisjon og anbefaling av MAE, RMSE, MAPE |
| Hyndman (2014) — *Measuring forecast accuracy* | Kritikk av MAPE, anbefaling av MASE |
| Diebold & Mariano (1995) | Statistisk test for modellsammenligning |
| Hyndman & Koehler (2006) | Introduksjon av MASE som alternativ |

### Tilleggskilder

- [5.10 Time series cross-validation — Forecasting: Principles and Practice (3rd ed)](https://otexts.com/fpp3/tscv.html)
- [Diebold-Mariano Test Python — Medium](https://medium.com/@philippetousignant/comparing-forecast-accuracy-in-python-diebold-mariano-test-ad109026f6ab)
- [dieboldmariano — PyPI](https://pypi.org/project/dieboldmariano/)
- [Walk-Forward Validation — Medium](https://medium.com/@ahmedfahad04/understanding-walk-forward-validation-in-time-series-analysis-a-practical-guide-ea3814015abf)
- [Measuring forecast accuracy — RELEX Solutions](https://www.relexsolutions.com/resources/measuring-forecast-accuracy/)

---

## 9. Modellvalg og etterspørselsklassifisering

### SKU-klassifisering etter etterspørselsmønster

Forskning viser at valg av prognosemodell og evalueringsmål bør tilpasses etterspørselstypen (Syntetos et al., 2005). SKU-er kan klassifiseres langs to dimensjoner:

| Etterspørselstype | CV² | ADI | Anbefalt modell | Anbefalt mål |
|-------------------|-----|-----|----------------|--------------|
| Jevn (smooth) | Lav | Lav | Holt-Winters | MAPE/RMSE |
| Intermittent | Lav | Høy | Croston / SBA | MASE |
| Erratisk | Høy | Lav | ARIMA / XGBoost | MAE/RMSE |
| Klumpet (lumpy) | Høy | Høy | Neg. binomial | MASE |

**For ditt prosjekt:** Farmasøytiske SKU-er vil sannsynligvis fordele seg over disse kategoriene. Varelinjer med intermittent etterspørsel (nullverdier) bør ikke evalueres med MAPE.

### MASE — anbefalingen fra Hyndman & Koehler (2006)

Hyndman & Koehler (2006) anbefaler MASE som standardmål for sammenligning av prognosemodeller på tvers av tidsserier:

**MASE = MAE_modell / MAE_naiv**

- MASE < 1 → modellen er bedre enn naiv prognose
- MASE = 1 → modellen er like god som naiv prognose
- MASE > 1 → modellen er dårligere enn naiv prognose

**Fordeler:**
- Fungerer ved nullverdier (ingen divisjon med null)
- Skala-uavhengig — direkte sammenlignbar på tvers av alle 105 SKU-er
- Tolkes intuitivt relativt til referansemodellen

**Praktisk anbefaling for LOG650-rapporten:**
Rapporter RMSE, MAE og MAPE (standardkrav i litteraturen) + vurder å inkludere MASE som supplementært mål, særlig for SKU-er med nullverdier.

### Litteraturreferanser for farmasøytisk prognose

- Fourkiotis & Tsadiras (2024): XGBoost og gradient boosting gir ofte lavere RMSE enn Holt-Winters på farmasøytiske data
- Burinskiene (2022): Datakvalitet og aggregeringsnivå er like viktig som modellvalg
- Neural network-studier viser mean RMSE ≈ 6.27 for farmasøytiske data med nevrale nett (Springer, 2022)

---

## 10. Komplett anbefaling for LOG650-prosjektet

### Feilmål å rapportere
1. **RMSE** — sensitiv for store feil, standard i ML-litteraturen
2. **MAE** — robust, enkel å tolke for bedriften
3. **MAPE** — kun for SKU-er uten nullverdier; ekskluder eller erstat med WMAPE ellers
4. **(Valgfritt) MASE** — robust alternativ for intermittent etterspørsel

### Aggregering
- Beregn per SKU → rapporter **median** på tvers av 105 SKU-er
- Segmenter resultater etter sesongstyrke og volumnivå

### Statistisk test
- Kjør **Diebold-Mariano-test** mellom Holt-Winters og ARIMA
- Bruk `pip install dieboldmariano` i Python

### Akademiske referanser å bruke i rapporten
- Hyndman & Athanasopoulos (2021) — definisjon og anbefaling av MAE/RMSE/MAPE
- Hyndman & Koehler (2006) — MASE og kritikk av MAPE
- Diebold & Mariano (1995) — statistisk modellsammenligning

---

### Tilleggskilder (steg 4)

- [Another look at measures of forecast accuracy — Hyndman & Koehler (2006)](https://robjhyndman.com/papers/mase.pdf)
- [Forecast accuracy metrics for intermittent demand — Hyndman](https://robjhyndman.com/papers/foresight.pdf)
- [Applying ML and Statistical Methods for Pharmaceutical Sales — Fourkiotis & Tsadiras (2024)](https://www.mdpi.com/2571-9394/6/1/10)
- [Forecasting Model: The Case of Pharmaceutical Retail — Burinskiene (2022)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9381873/)
