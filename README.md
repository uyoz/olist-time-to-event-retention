# Time-to-Repurchase in Marketplace E-Commerce Data
## Kaplan–Meier and Cox PH Baselines (Reproducibility Pack)

This repository contains a **leakage-aware, time-to-event baseline** for marketplace repurchase using the **Olist Brazilian E-Commerce Public Dataset**, plus the **aggregated output artifacts** referenced in the accompanying manuscript.

---

## What's in this repo

- `scripts/01_build_cohort_survival.py` — builds the customer-level survival cohort (index order anchored at first delivered order; snapshot-based censoring).
- `outputs/` — aggregated model artifacts (Kaplan–Meier summaries, Cox PH tables/diagnostics, C-index report, segment summaries/effects).
- `data/processed/` — sanitized row-level cohort extracts (customer identifiers removed) and cohort metadata JSON files for the pre-filter and analytic cohorts.
- `data/README.md` — instructions to obtain the raw Olist data (not redistributed here).

---

## Cohorts (as reported)

- **Pre-filter cohort:** 93,350 customers with delivered index orders.
- **Analytic cohort (≥180d potential follow-up):** 63,760 customers; 1,563 repurchase events (2.45%).
- **Administrative snapshot:** `2018-10-17 17:30:18`.

---

## Data

The raw Olist dataset is **not included**. Download it from Kaggle and place CSVs as described in `data/README.md`.

Dataset page: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

---

## Running the cohort build

From the repository root:

```bash
python scripts/01_build_cohort_survival.py
```

**Note:** The contents of `outputs/` are provided as **reported artifacts** to support transparency and verification of the accompanying manuscript. Reproducing the full modeling pipeline requires additional survival modeling dependencies (e.g., `scikit-survival` or `lifelines`) and modeling scripts beyond the cohort build.

---

## Citation

If you use this repository, cite:

Yousaf, U. (2025). *Time-to-Repurchase in Marketplace E-Commerce Data: Kaplan–Meier and Cox PH Baselines (Reproducibility Pack).* GitHub repository.

---

## Contact

**Usman Yousaf, PhD**  
University of Tasmania

- Email: [research.usman@gmail.com](mailto:research.usman@gmail.com)
- GitHub: [https://github.com/uyoz](https://github.com/uyoz)
- LinkedIn: [https://www.linkedin.com/in/usman-yousaf/](https://www.linkedin.com/in/usman-yousaf/)
- Google Scholar: [https://scholar.google.com.au/citations?hl=en&user=f8lx2WwAAAAJ](https://scholar.google.com.au/citations?hl=en&user=f8lx2WwAAAAJ)

---

## License

MIT (see `LICENSE`).

---

## Dataset Attribution

Olist. (2018). *Brazilian E-Commerce Public Dataset by Olist.* Kaggle.  
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
