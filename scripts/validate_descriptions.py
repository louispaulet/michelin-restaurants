#!/usr/bin/env python3
"""Validate generated restaurant descriptions."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "public" / "data" / "restaurants.csv"
DEFAULT_DESCRIPTIONS = ROOT / "data" / "restaurant_descriptions.json"


def words(text: str) -> list[str]:
    return re.findall(r"[\w'’-]+", text, flags=re.UNICODE)


def load_descriptions(path: Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    descriptions: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            descriptions[key] = str(value.get("description") or "").strip()
        else:
            descriptions[key] = str(value or "").strip()
    return descriptions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptions", nargs="?", type=Path, default=DEFAULT_DESCRIPTIONS)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--min-words", type=int, default=45)
    parser.add_argument("--max-words", type=int, default=140)
    args = parser.parse_args()

    rows = list(csv.DictReader(args.csv.open(encoding="utf-8", newline="")))
    descriptions = load_descriptions(args.descriptions)
    ids = {row["id"] for row in rows}
    problems: list[str] = []

    missing = sorted(ids - set(descriptions))
    extra = sorted(set(descriptions) - ids)
    for restaurant_id in missing:
        problems.append(f"missing: {restaurant_id}")
    for restaurant_id in extra:
        problems.append(f"unknown id: {restaurant_id}")

    seen_normalized: dict[str, str] = {}
    for restaurant_id, description in descriptions.items():
        count = len(words(description))
        if not description:
            problems.append(f"empty: {restaurant_id}")
            continue
        if count < args.min_words:
            problems.append(f"too short ({count} words): {restaurant_id}")
        if count > args.max_words:
            problems.append(f"too long ({count} words): {restaurant_id}")
        if re.search(r"\b(Michelin Guide|Google|Tripadvisor|Yelp|Brave Search)\b", description, flags=re.I):
            problems.append(f"source name mentioned: {restaurant_id}")
        normalized = re.sub(r"\W+", " ", description.lower()).strip()
        if normalized in seen_normalized:
            problems.append(f"duplicate description: {restaurant_id} duplicates {seen_normalized[normalized]}")
        seen_normalized[normalized] = restaurant_id

    print(f"restaurants={len(rows)} descriptions={len(descriptions)} problems={len(problems)}")
    for problem in problems[:200]:
        print(problem)
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
