"""
sumo_csv_export.py — Export database totals to SUMO-compatible CSV traffic state file.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence


def export_sumo_csv_from_db_totals(
    per_roi_totals: Sequence[dict[str, Any]],
    output_path: str = "sumo_output/traffic_state.csv",
) -> str:
    """
    Exports ROI occupancy and crossing totals into a structured CSV file.
    Creates parent directories if necessary and returns the output path.
    """
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        project_root = Path(__file__).resolve().parent
        path = project_root / path

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "roi_id",
        "name",
        "total_occupancy",
        "total_crossings",
        "exported_at",
    ]

    now_iso = datetime.now().isoformat(timespec="seconds")
    rows = []
    for item in per_roi_totals:
        rows.append({
            "roi_id": item.get("roi_id", ""),
            "name": item.get("name", ""),
            "total_occupancy": item.get("total_occupancy", 0),
            "total_crossings": item.get("total_crossings", 0),
            "exported_at": now_iso,
        })

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)

    return str(path)
