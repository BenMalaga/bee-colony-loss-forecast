# Related work (the prior art this project extends)

The claim of this work is not "first to model NASS bee data" but "first pre-registered,
out-of-sample forecasting benchmark with naive baselines and a leading-vs-coincident test."

## Closest / must-differentiate-from
- **Insolia et al. 2022**, *Honey bee colony loss linked to parasites, pesticides and extreme
  weather across the United States*, Sci. Reports.
  <https://www.nature.com/articles/s41598-022-24946-4> · code+data:
  <https://github.com/LucaIns/honey_bee_loss_US_scirep>
  — Same NASS state×quarter stressor data (2015–2021) + PRISM + CDL. **In-sample robust
  regression, R²≈0.60, concurrent predictors, no train/test split, no forecasting.** Their
  Supp. Tables **S10–S11** briefly test lagged predictors ("do not appear to point to a
  significant contribution") — cite this; we extend it into a rigorous OOS benchmark, not claim
  lags are untouched.
- **Calovi et al. 2021**, *Summer weather conditions influence winter survival of honey bees*,
  Sci. Reports. <https://pmc.ncbi.nlm.nih.gov/articles/PMC7811010/>
  — Random Forest, PA only, 10×10-fold CV; authors **explicitly declined temporal validation**
  ("weather was very different across the 3 years"). We do exactly what they declined.
- **Gray, Goslee, Kammerer & Grozinger 2024**, *Effective pest management approaches can
  mitigate honey bee (Apis mellifera) colony winter loss across a range of weather conditions
  in small-scale, stationary apiaries*, **Journal of Insect Science** 24(3):15, doi:10.1093/jisesa/ieae043.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC11132132/>
  — Successor; PA survey + PRISM + CDL/NLCD, RF, 10-fold CV with year stratification, again
  noting that "a single year does not act as a good testing dataset" — the temporal,
  train-past/test-future test this project runs.

## Different problem (cite as related, not competing)
- **MDPI Sensors 2021** (TCN) — next-DAY single-hive loss-rate forecasting from in-hive sensors.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC8201321/> (genuine chronological holdout, but sensor
  data, not survey).
- **arXiv 2304.01215** — tree-based forecasting of next-day hive WEIGHT (production proxy),
  Italian sensor hives. <https://arxiv.org/html/2304.01215v2>
- **Calovi et al. 2022**, *Winter weather predicts honey bee colony loss at the national scale*,
  Ecological Indicators. <https://www.sciencedirect.com/science/article/pii/S1470160X22011827>
  — National BIP + PRISM, but spatial **explanatory** (period-averaged) regression, no temporal
  forward validation.

## Establishes interest, occupies nothing (informal attempts)
- **Saymanning/Honey_Bee_Colony_Loss_US** (GitHub) — course-project ETL + incomplete
  ARIMA/Prophet on USDA data; explicitly reports no usable correlation; no temporal split.
  <https://github.com/Saymanning/Honey_Bee_Colony_Loss_US>
- Kaggle "NASS Honey Bee 2015–2021" / "Buzzz Bee Stressors" — descriptive EDA only.

## Data sources
- **USDA NASS Quick Stats 2.0 API** — <https://quickstats.nass.usda.gov/api> ·
  survey guide: <https://www.nass.usda.gov/Surveys/Guide_to_NASS_Surveys/Bee_and_Honey/>
- **Bee Informed Partnership** Loss & Management survey (context) —
  <https://research.beeinformed.org/loss-map/>
- **FAO/FAOSTAT** (global managed-colony context) — <https://www.fao.org/faostat>
