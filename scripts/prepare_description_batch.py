#!/usr/bin/env python3
"""Prepare an OpenAI Batch API JSONL file for restaurant descriptions."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "public" / "data" / "restaurants.csv"
REVIEWS_DIR = ROOT / ".tmp" / "reviews"
OUTFILE = ROOT / ".tmp" / "openai" / "description_batch.jsonl"
DEFAULT_MODEL = "gpt-5.4-mini"

SYSTEM_PROMPT = """You write concise, original restaurant descriptions for a Michelin restaurant guide app.
Use only the provided source material. Do not quote or closely paraphrase reviews.
Do not mention source names. Avoid unsupported claims. If sources are sparse, stay conservative.
Return strict JSON with keys: description, confidence, notes.
""".strip()


def load_restaurants(path: Path = CSV_PATH) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}


def load_review_payload(restaurant_id: str, reviews_dir: Path) -> dict[str, Any]:
    path = reviews_dir / f"{restaurant_id}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compact_sources(payload: dict[str, Any], max_sources: int = 10, max_excerpt_chars: int = 900) -> list[dict[str, str]]:
    sources = []
    for source in payload.get("sources", [])[:max_sources]:
        if not isinstance(source, dict):
            continue
        excerpt = str(source.get("excerpt") or "").strip()
        if not excerpt:
            continue
        sources.append(
            {
                "source_name": str(source.get("source_name") or ""),
                "source_url": str(source.get("source_url") or ""),
                "title": str(source.get("title") or "")[:180],
                "rating": str(source.get("rating") or "")[:80],
                "date": str(source.get("date") or "")[:80],
                "excerpt": excerpt[:max_excerpt_chars],
            }
        )
    return sources


def user_prompt(row: dict[str, str], sources: list[dict[str, str]]) -> str:
    metadata = {
        "id": row["id"],
        "name": row["name"],
        "michelin_stars": row.get("stars") or "",
        "cuisine": row.get("cuisine") or "",
        "address": row.get("address") or "",
        "area": row.get("arrondissement") or "",
        "current_description": row.get("description") or "",
    }
    return (
        "Write one original 70-120 word synthetic description for this restaurant. "
        "Focus on cuisine/style, atmosphere, notable strengths, and who might enjoy it, but only when supported. "
        "Do not include markdown. Return JSON only.\n\n"
        f"Restaurant metadata:\n{json.dumps(metadata, ensure_ascii=False, indent=2)}\n\n"
        f"Source material:\n{json.dumps(sources, ensure_ascii=False, indent=2)}"
    )


def request_for(row: dict[str, str], sources: list[dict[str, str]], model: str) -> dict[str, Any]:
    return {
        "custom_id": f"description:{row['id']}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "temperature": 0.2,
            "max_completion_tokens": 260,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(row, sources)},
            ],
        },
    }


def select_ids(restaurants: dict[str, dict[str, str]], restaurant_id: str | None, all_rows: bool) -> list[str]:
    if restaurant_id:
        if restaurant_id not in restaurants:
            raise SystemExit(f"Restaurant not found: {restaurant_id}")
        return [restaurant_id]
    if all_rows:
        return sorted(restaurants)
    raise SystemExit("Pass --restaurant-id <id> or --all")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restaurant-id")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--reviews-dir", type=Path, default=REVIEWS_DIR)
    parser.add_argument("--out", type=Path, default=OUTFILE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--allow-empty", action="store_true", help="Include restaurants with no collected sources")
    args = parser.parse_args()

    restaurants = load_restaurants(args.csv)
    restaurant_ids = select_ids(restaurants, args.restaurant_id, args.all)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    with args.out.open("w", encoding="utf-8") as handle:
        for restaurant_id in restaurant_ids:
            row = restaurants[restaurant_id]
            payload = load_review_payload(restaurant_id, args.reviews_dir)
            sources = compact_sources(payload)
            if not sources and not args.allow_empty:
                skipped += 1
                continue
            handle.write(json.dumps(request_for(row, sources, args.model), ensure_ascii=False) + "\n")
            written += 1
    print(f"Wrote {written} batch requests to {args.out}")
    if skipped:
        print(f"Skipped {skipped} restaurants with no source material")


if __name__ == "__main__":
    main()
