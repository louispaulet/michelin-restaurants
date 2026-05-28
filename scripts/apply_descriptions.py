#!/usr/bin/env python3
"""Overlay generated restaurant descriptions onto public/data/restaurants.csv."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "public" / "data" / "restaurants.csv"
DEFAULT_DESCRIPTIONS = ROOT / "data" / "restaurant_descriptions.json"


def load_descriptions(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    descriptions: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            text = str(value.get("description") or "").strip()
        else:
            text = str(value or "").strip()
        if text:
            descriptions[key] = text
    return descriptions


def apply_descriptions(csv_path: Path, descriptions_path: Path) -> int:
    descriptions = load_descriptions(descriptions_path)
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if "description" not in fieldnames:
        fieldnames.append("description")

    updated = 0
    for row in rows:
        description = descriptions.get(row.get("id", ""))
        if description and row.get("description") != description:
            row["description"] = description
            updated += 1

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptions", nargs="?", type=Path, default=DEFAULT_DESCRIPTIONS)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    args = parser.parse_args()

    updated = apply_descriptions(args.csv, args.descriptions)
    print(f"Updated {updated} descriptions in {args.csv}")


if __name__ == "__main__":
    main()
