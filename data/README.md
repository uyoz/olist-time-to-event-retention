# Data

This repository does **not** redistribute the raw Olist dataset.

## To reproduce the pipeline end-to-end:

1. Download the **Olist Brazilian E-Commerce Public Dataset** from Kaggle:  
   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

2. Place the raw CSV files under `data/raw/`

3. Run the cohort construction script:
```bash
   python scripts/01_build_cohort_survival.py
```

## Included processed artifacts

For transparency and lightweight verification, this repo includes **sanitized** cohort extracts under `data/processed/`:

- No customer/order identifiers
- Timestamps reduced to date-only
- Contains only time-to-event fields and censoring metadata

These files correspond to the cohorts reported in the manuscript:
- `cohort_survival_prefilter_sanitized.csv` (93,350 customers)
- `cohort_survival_filtered_180d_sanitized.csv` (63,760 customers, ≥180-day follow-up)
