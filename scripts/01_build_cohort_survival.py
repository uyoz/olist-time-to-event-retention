"""
01_build_cohort_survival.py

Constructs survival analysis cohort from Olist Brazilian E-Commerce dataset.
Implements temporal-leakage-safe cohort construction with deterministic index
order selection and administrative censoring at dataset snapshot.

Part of: "Survival Analysis of Customer Repurchase in E-Commerce Marketplaces"
Author: Usman Yousaf
Repository: 
"""

import argparse
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd


def resolve_data_dir(explicit: str | None) -> Path:
    """
    Resolve data directory using precedence: CLI arg > env var > default.
    
    Args:
        explicit: Command-line specified directory (or None)
    
    Returns:
        Resolved Path to data directory
    """
    # Precedence: --data-dir > $OLIST_RAW_DIR > repo/raw_data/
    if explicit:
        return Path(explicit).expanduser().resolve()
    root = Path(__file__).resolve().parents[1]  # repo root
    env = os.getenv("OLIST_RAW_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return (root / "raw_data").resolve()


def main() -> None:
    """
    Build survival cohort with t0=index_order_delivery, event=first_repurchase.
    
    Outputs:
        - cohort_survival.csv: One row per customer with survival outcome
        - cohort_metadata.json: Snapshot timestamp and build parameters
        - cohort_build_summary.txt: Human-readable summary
    """
    parser = argparse.ArgumentParser(
        description="Build survival cohort from Olist dataset.",
        epilog="Example: python 01_build_cohort.py --data-dir ~/data/olist"
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Directory containing Olist raw CSVs (default: $OLIST_RAW_DIR or repo/raw_data/)",
    )
    args = parser.parse_args()

    data_dir = resolve_data_dir(args.data_dir)
    orders_f = data_dir / "olist_orders_dataset.csv"
    customers_f = data_dir / "olist_customers_dataset.csv"

    if not orders_f.exists() or not customers_f.exists():
        missing = [str(p) for p in (orders_f, customers_f) if not p.exists()]
        raise FileNotFoundError(
            "Required input file(s) not found:\n"
            + "\n".join(f"  - {p}" for p in missing)
            + "\n\nSolution: Provide --data-dir, set $OLIST_RAW_DIR, or place files under repo/raw_data/"
        )

    print("=== BUILD SURVIVAL COHORT ===\n")
    orders = pd.read_csv(orders_f)
    customers = pd.read_csv(customers_f)

    # Parse timestamps
    orders["purchase_dt"] = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
    orders["delivery_dt"] = pd.to_datetime(orders["order_delivered_customer_date"], errors="coerce")

    # CRITICAL: Snapshot computed from RAW orders before any filtering
    # This establishes administrative censoring boundary for entire cohort
    snapshot_ts = orders["purchase_dt"].max()
    print(f"Dataset snapshot (max purchase_dt from raw orders): {snapshot_ts}")

    # Join customer unique ID for longitudinal tracking
    orders = orders.merge(
        customers[["customer_id", "customer_unique_id"]], 
        on="customer_id", 
        how="inner"
    )

    # ─── INDEX ORDER CONSTRUCTION ───
    # t0 = delivery timestamp of first delivered order
    delivered = orders[
        (orders["order_status"] == "delivered")
        & orders["delivery_dt"].notna()
        & orders["purchase_dt"].notna()
    ].copy()

    # Deterministic tie-breaking ensures reproducibility
    delivered = delivered.sort_values(
        ["customer_unique_id", "delivery_dt", "purchase_dt"]
    )
    index_orders = delivered.groupby("customer_unique_id", as_index=False).first()
    index_orders = index_orders.rename(
        columns={
            "order_id": "index_order_id",
            "purchase_dt": "p0",
            "delivery_dt": "t0"
        }
    )[["customer_unique_id", "index_order_id", "p0", "t0"]]

    print(f"Customers with delivered index order: {len(index_orders):,}")

    # ─── REPURCHASE EVENT CONSTRUCTION ───
    # Event = first VALID order with purchase_dt > t0
    excluded_statuses = {"canceled", "unavailable"}
    valid_status_mask = (
        orders["order_status"].notna() 
        & ~orders["order_status"].isin(excluded_statuses)
    )

    candidates = orders.loc[valid_status_mask].merge(
        index_orders[["customer_unique_id", "t0"]],
        on="customer_unique_id",
        how="inner",
    )
    # Temporal leakage prevention: only orders AFTER t0
    candidates = candidates[
        candidates["purchase_dt"].notna() 
        & (candidates["purchase_dt"] > candidates["t0"])
    ].copy()

    candidates = candidates.sort_values(["customer_unique_id", "purchase_dt"])
    first_rep = candidates.groupby("customer_unique_id", as_index=False).first()
    first_rep = first_rep.rename(
        columns={
            "order_id": "repurchase_order_id",
            "purchase_dt": "p1",
            "order_status": "repurchase_order_status",
        }
    )[["customer_unique_id", "repurchase_order_id", "p1", "repurchase_order_status"]]

    # ─── SURVIVAL OUTCOME ASSEMBLY ───
    cohort = index_orders.merge(first_rep, on="customer_unique_id", how="left")
    cohort["event"] = cohort["p1"].notna().astype(int)

    # Duration: t0->p1 for events, t0->snapshot for administrative censoring
    cohort["duration_days"] = np.where(
        cohort["event"].eq(1),
        (cohort["p1"] - cohort["t0"]).dt.total_seconds() / 86400.0,
        (snapshot_ts - cohort["t0"]).dt.total_seconds() / 86400.0,
    )

    cohort = cohort[
        cohort["duration_days"].notna() & (cohort["duration_days"] >= 0)
    ].copy()

    # Diagnostic: monitor same-day repurchases (quality check)
    within_24h = cohort["event"].eq(1) & (cohort["duration_days"] <= 1.0)
    pct_within_24h = within_24h.mean() * 100

    print(f"Event rate (any repurchase observed): {cohort['event'].mean():.2%}")
    print(f"% of repurchases within 24h of t0 (diagnostic): {pct_within_24h:.2f}%")

    if cohort["event"].sum() > 0:
        dist = cohort.loc[
            cohort["event"].eq(1), "repurchase_order_status"
        ].value_counts(normalize=True)
        print("\nRepurchase order status distribution (event=1):")
        print(dist)

    # ─── OUTPUTS ───
    out_dir = Path(__file__).resolve().parent
    
    # 1. Cohort CSV
    cohort_path = out_dir / "cohort_survival.csv"
    cohort.to_csv(cohort_path, index=False)
    print(f"\n[OK] Saved: {cohort_path}")
    print(f"  Columns: {list(cohort.columns)}")

    # 2. Metadata JSON (for downstream scripts)
    meta = {
        "snapshot_ts": str(pd.Timestamp(snapshot_ts)),
        "customers_with_delivered_index_order": int(len(index_orders)),
        "cohort_rows": int(len(cohort)),
        "event_rate_any_repurchase": float(cohort["event"].mean()),
        "excluded_repurchase_statuses": sorted(excluded_statuses),
        "index_order_definition": "earliest delivered order by delivery_dt; tie-break by purchase_dt",
        "repurchase_definition": "earliest subsequent order with purchase_dt > t0 and valid status",
        "data_dir": str(data_dir),
        "inputs": {"orders": orders_f.name, "customers": customers_f.name},
    }
    meta_path = out_dir / "cohort_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[OK] Saved: {meta_path}")

    # 3. Human-readable summary
    summary_lines = [
        "SURVIVAL COHORT BUILD SUMMARY",
        "=" * 50,
        "",
        f"Dataset snapshot (max purchase_dt): {pd.Timestamp(snapshot_ts)}",
        f"Customers with delivered index order: {len(index_orders):,}",
        f"Cohort rows (1 row per customer): {len(cohort):,}",
        f"Event rate (any repurchase observed): {cohort['event'].mean():.2%}",
        f"Excluded repurchase statuses: {', '.join(sorted(excluded_statuses))}",
        "",
        "Index order definition:",
        "  Earliest delivered order by delivery_dt; tie-break by purchase_dt",
        "",
        "Repurchase definition:",
        "  Earliest subsequent order with purchase_dt > t0 and valid status",
        "",
    ]
    summary_path = out_dir / "cohort_build_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"[OK] Saved: {summary_path}")


if __name__ == "__main__":
    main()
