"""
build_congestion_dataset.py — Builds training dataset from traffic.db.

Uses only the 8 main lane ROIs (no junction connectors) as features.
Target: congestion level (LOW / MEDIUM / HIGH) 60 seconds ahead.
Features: per-lane occupancy counts + time-of-day features.
Crossings are intentionally excluded — occupancy is the clean signal.
"""
from pathlib import Path
import argparse
import json
import sqlite3

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "api" / "data" / "traffic.db"
OUT_DIR    = ROOT / "training" / "out"

# Only the 8 main lane ROIs — junctions excluded
ROI_ALIASES = {
    "1": "lane_1", "Lane 1": "lane_1",
    "2": "lane_2", "Lane 2": "lane_2",
    "3": "lane_3", "Lane 3": "lane_3",
    "4": "lane_4", "Lane 4": "lane_4",
    "5": "lane_5", "Lane 5": "lane_5",
    "6": "lane_6", "Lane 6": "lane_6",
    "7": "lane_7", "Lane 7": "lane_7",
    "8": "lane_8", "Lane 8": "lane_8",
}

COUNT_FEATURES = [
    "lane_1", "lane_2", "lane_3", "lane_4",
    "lane_5", "lane_6", "lane_7", "lane_8",
]


def canonical_roi(raw_value: str, roi_id_to_name: dict) -> str | None:
    if raw_value in ROI_ALIASES:
        return ROI_ALIASES[raw_value]
    mapped = roi_id_to_name.get(raw_value)
    if mapped in ROI_ALIASES:
        return ROI_ALIASES[mapped]
    return None


def label_from_total(total: float, low_max: int, medium_max: int) -> str:
    if total <= low_max:   return "LOW"
    if total <= medium_max: return "MEDIUM"
    return "HIGH"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db",           default=str(DEFAULT_DB))
    parser.add_argument("--out-dir",      default=str(OUT_DIR))
    parser.add_argument("--horizon-sec",  type=int, default=60)
    parser.add_argument("--low-max",      type=int, default=5)
    parser.add_argument("--medium-max",   type=int, default=10)
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    rois = pd.read_sql_query("SELECT roi_id, name FROM rois", conn)
    roi_id_to_name = dict(zip(rois["roi_id"], rois["name"]))

    counts = pd.read_sql_query(
        "SELECT ts_second, roi_id, car_count FROM counts ORDER BY ts_second", conn
    )
    conn.close()

    if counts.empty:
        raise SystemExit("counts table is empty — let the detector run longer, then retry.")

    counts["ts"] = pd.to_datetime(counts["ts_second"]).dt.floor("s")
    counts["roi_feature"] = counts["roi_id"].apply(lambda x: canonical_roi(x, roi_id_to_name))
    counts = counts.dropna(subset=["roi_feature"]).copy()

    count_wide = counts.pivot_table(
        index="ts", columns="roi_feature",
        values="car_count", aggfunc="max", fill_value=0,
    )

    for col in COUNT_FEATURES:
        if col not in count_wide.columns:
            count_wide[col] = 0
    count_wide = count_wide[COUNT_FEATURES].sort_index()

    full_index = pd.date_range(
        start=count_wide.index.min(),
        end=count_wide.index.max(),
        freq="1s",
    )
    count_wide = count_wide.reindex(full_index, fill_value=0)
    count_wide.columns = [f"{c}_count" for c in count_wide.columns]

    df = count_wide.copy()

    count_cols = [f"{c}_count" for c in COUNT_FEATURES]
    df["total_cars"] = df[count_cols].sum(axis=1)
    df["hour"]       = df.index.hour
    df["minute"]     = df.index.minute
    df["weekday"]    = df.index.weekday

    df["future_total_cars"] = df["total_cars"].shift(-args.horizon_sec)
    df = df.dropna(subset=["future_total_cars"]).copy()
    df["future_total_cars"] = df["future_total_cars"].astype(int)

    df["target"] = df["future_total_cars"].apply(
        lambda x: label_from_total(x, args.low_max, args.medium_max)
    )

    df = df.reset_index().rename(columns={"index": "ts"})
    df["ts"] = df["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    feature_columns = count_cols + ["total_cars", "hour", "minute", "weekday"]

    csv_path  = out_dir / "congestion_dataset.csv"
    meta_path = out_dir / "congestion_dataset_meta.json"

    df.to_csv(csv_path, index=False)

    meta = {
        "db_path":         str(db_path),
        "rows":            int(len(df)),
        "feature_columns": feature_columns,
        "target_column":   "target",
        "horizon_sec":     args.horizon_sec,
        "low_max":         args.low_max,
        "medium_max":      args.medium_max,
        "class_names":     ["LOW", "MEDIUM", "HIGH"],
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"[OK] Dataset: {csv_path}")
    print(f"[OK] Rows:    {len(df)}")
    print(f"[OK] Features: {feature_columns}")
    print("[OK] Class distribution:")
    print(df["target"].value_counts().to_string())


if __name__ == "__main__":
    main()
