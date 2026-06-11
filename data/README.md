# Data — how to fetch every dataset (raw data is NOT committed)

> ⚠️ Integrity gate: the NASS pull fetches **outcome** data (colony loss). Per
> `../PRE_REGISTRATION.md`, do not fetch until the pre-registration is committed. `fetch_nass.py`
> refuses to run without `--confirm-prereg-locked`.

## 1. USDA NASS — Honey Bee Colonies (PRIMARY)

- Source: USDA NASS Quick Stats 2.0 API — <https://quickstats.nass.usda.gov/api>
- Get a **free API key** at that page (instant). Then:
  ```bash
  export QUICKSTATS_API_KEY=your_key_here
  python -m src.fetch_nass --discover-only              # tiny: writes data/raw/bee_colony_short_descs.txt
  python -m src.fetch_nass --confirm-prereg-locked      # writes data/raw/nass_honey_<year>.json
  python -m src.build_panel                             # writes data/processed/panel.csv (+ panel_long.csv)
  ```
- The ingest is **standard-library only** (urllib) — no third-party deps — so it runs before the
  analysis venv is installed.
- What it pulls: `commodity_desc=HONEY`, `agg_level_desc=STATE`, `source_desc=SURVEY`, all years
  2015–2025, filtered to `short_desc` containing "BEE COLONIES" (inventory, lost, added,
  renovated, and "colonies affected by" each stressor: Varroa, other pests/parasites incl.
  *Nosema*, disease, pesticides, other, unknown).
- Discovery: the fetch first writes `data/raw/bee_colony_short_descs.txt` listing the exact
  `short_desc` strings, so the panel mapping (`src/build_panel.py`) can be locked to real fields.
- Manual sanity check (single series, browser/curl):
  ```bash
  curl "https://quickstats.nass.usda.gov/api/api_GET/?key=$QUICKSTATS_API_KEY&commodity_desc=HONEY&agg_level_desc=STATE&year=2024&format=JSON"
  ```
- License: U.S. Government work — public domain. Safe to redistribute the derived panel.
- Quirks to handle (see `../PRE_REGISTRATION.md`): suppressed cells `(D)/(Z)`, small-state noise,
  the same-survey co-measurement of stressor% and loss%, COVID-era 2020–21 quarters.

## 2. Insolia et al. 2022 — released combined dataset (reproducibility anchor + H3 covariates)

- Code + `bee_data.csv` (NASS + PRISM weather + USDA Cropland Data Layer, 44 states, quarterly
  2015–2021): <https://github.com/LucaIns/honey_bee_loss_US_scirep>
  ```bash
  git clone https://github.com/LucaIns/honey_bee_loss_US_scirep data/raw/insolia_2022
  ```
- Use to (a) cross-check our NASS panel, (b) supply weather/land covariates for H3.
- Respect their repo license; cite the paper (`docs/related_work.md`).

## 3. Context only (NOT modeled)

- FAO global colony series (global "managed bees are rising" context): <https://www.fao.org/faostat>
- Bee Informed Partnership Loss & Management survey (different instrument; descriptive only):
  <https://research.beeinformed.org/loss-map/>

Do not conflate BIP loss rates or FAO stock with the NASS state×quarter target.
