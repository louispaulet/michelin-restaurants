#!/usr/bin/env python3
"""Collect temporary source material for restaurant description generation.

Outputs one JSON file per restaurant under .tmp/reviews/. These files are not
tracked and should not be published; they are inputs for synthetic summaries.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "public" / "data" / "restaurants.csv"
DEFAULT_OUT_DIR = ROOT / ".tmp" / "reviews"
USER_AGENT = "michelin-restaurants/0.1 (+https://michelin.thefrenchartist.dev/)"
ALGOLIA_APP_ID = "8NVHRD7ONV"
ALGOLIA_SEARCH_KEY = "3222e669cf890dc73fa5f38241117ba5"
ALGOLIA_RESTAURANT_INDEX = "prod-restaurants-en"
ALGOLIA_QUERY_ENDPOINT = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{ALGOLIA_RESTAURANT_INDEX}/query"
MICHELIN_BASE_URL = "https://guide.michelin.com"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clean_text(value: str, limit: int = 1200) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit].rstrip()


def fetch_text(url: str, timeout: int = 12) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,fr;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="ignore")


def load_restaurants(path: Path = CSV_PATH) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def select_restaurants(rows: list[dict[str, str]], restaurant_id: str | None, all_rows: bool) -> list[dict[str, str]]:
    if all_rows:
        return rows
    if not restaurant_id:
        raise SystemExit("Pass --restaurant-id <id> or --all")
    matches = [row for row in rows if row["id"] == restaurant_id]
    if not matches:
        raise SystemExit(f"Restaurant not found: {restaurant_id}")
    return matches


def meta_content(document: str, names: tuple[str, ...]) -> str:
    for name in names:
        patterns = [
            rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(name)}["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(name)}["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, document, flags=re.I | re.S)
            if match:
                return clean_text(match.group(1))
    return ""


def title_text(document: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", document, flags=re.I | re.S)
    return clean_text(match.group(1), 250) if match else ""


def json_ld_items(document: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for block in re.findall(r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", document, flags=re.I | re.S):
        try:
            data = json.loads(html.unescape(block.strip()))
        except json.JSONDecodeError:
            continue
        stack = data if isinstance(data, list) else [data]
        for item in stack:
            if isinstance(item, dict):
                items.append(item)
                graph = item.get("@graph")
                if isinstance(graph, list):
                    items.extend(node for node in graph if isinstance(node, dict))
    return items


def restaurant_json_ld(document: str) -> dict[str, Any]:
    for item in json_ld_items(document):
        item_type = item.get("@type")
        types = item_type if isinstance(item_type, list) else [item_type]
        if "Restaurant" in types or "FoodEstablishment" in types or "LocalBusiness" in types:
            return item
    return {}


def source_record(source_name: str, source_url: str, title: str = "", excerpt: str = "", rating: str = "", date: str = "") -> dict[str, str]:
    return {
        "source_name": source_name,
        "source_url": source_url,
        "title": title,
        "excerpt": excerpt,
        "rating": rating,
        "date": date,
        "retrieved_at": now_iso(),
    }


def collect_page_source(source_name: str, url: str) -> list[dict[str, str]]:
    if not url:
        return []
    try:
        document = fetch_text(url)
    except (urllib.error.URLError, TimeoutError, ValueError, socket.timeout):
        return []

    records: list[dict[str, str]] = []
    title = title_text(document)
    description = meta_content(document, ("description", "og:description", "twitter:description"))
    data = restaurant_json_ld(document)
    json_description = clean_text(str(data.get("description") or "")) if data else ""

    aggregate = data.get("aggregateRating") if isinstance(data, dict) else None
    rating = ""
    if isinstance(aggregate, dict):
        rating_value = aggregate.get("ratingValue")
        review_count = aggregate.get("reviewCount") or aggregate.get("ratingCount")
        rating = f"{rating_value} ({review_count} ratings)" if rating_value and review_count else str(rating_value or "")

    excerpt = json_description or description
    if excerpt:
        records.append(source_record(source_name, url, title=title, excerpt=excerpt, rating=rating))

    reviews = data.get("review") if isinstance(data, dict) else None
    if isinstance(reviews, dict):
        reviews = [reviews]
    if isinstance(reviews, list):
        for review in reviews[:5]:
            if not isinstance(review, dict):
                continue
            review_body = clean_text(str(review.get("reviewBody") or review.get("description") or ""))
            if not review_body:
                continue
            review_rating = review.get("reviewRating")
            rating_text = ""
            if isinstance(review_rating, dict) and review_rating.get("ratingValue"):
                rating_text = str(review_rating["ratingValue"])
            records.append(
                source_record(
                    source_name,
                    url,
                    title=clean_text(str(review.get("name") or title), 250),
                    excerpt=review_body,
                    rating=rating_text,
                    date=str(review.get("datePublished") or ""),
                )
            )

    return records


def collect_michelin_algolia(row: dict[str, str]) -> list[dict[str, str]]:
    query = f'{row["name"]} Paris'
    params = urllib.parse.urlencode({"query": query, "hitsPerPage": 5})
    body = json.dumps({"params": params}).encode("utf-8")
    request = urllib.request.Request(
        ALGOLIA_QUERY_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Origin": MICHELIN_BASE_URL,
            "Referer": f"{MICHELIN_BASE_URL}/",
            "User-Agent": USER_AGENT,
            "X-Algolia-Application-Id": ALGOLIA_APP_ID,
            "X-Algolia-API-Key": ALGOLIA_SEARCH_KEY,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []

    expected_slug = (row.get("michelin_id") or "").strip("/").split("/")[-1]
    records = []
    for hit in data.get("hits", []):
        slug = str(hit.get("slug") or "")
        hit_name = str(hit.get("name") or "")
        if expected_slug and slug != expected_slug and hit_name.casefold() != row["name"].casefold():
            continue
        excerpt = clean_text(str(hit.get("main_desc") or ""), 1400)
        if not excerpt:
            continue
        url = hit.get("url") or row.get("michelin_url") or ""
        if str(url).startswith("/"):
            url = f"{MICHELIN_BASE_URL}{url}"
        rating = str(hit.get("michelin_star") or "").replace("ONE", "1 star").replace("TWO", "2 stars").replace("THREE", "3 stars")
        records.append(source_record("Michelin Guide", str(url), title=hit_name, excerpt=excerpt, rating=rating))
        break
    return records


def collect_brave_search(row: dict[str, str]) -> list[dict[str, str]]:
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return []
    query = f'"{row["name"]}" Paris restaurant review'
    params = urllib.parse.urlencode({"q": query, "count": 8, "search_lang": "en", "country": "FR"})
    request = urllib.request.Request(
        f"https://api.search.brave.com/res/v1/web/search?{params}",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key, "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return []
    records = []
    for result in data.get("web", {}).get("results", [])[:8]:
        url = str(result.get("url") or "")
        description = clean_text(str(result.get("description") or ""))
        if not url or not description:
            continue
        records.append(source_record("Brave Search", url, title=clean_text(str(result.get("title") or ""), 250), excerpt=description))
    return records


def google_place_details(row: dict[str, str]) -> list[dict[str, str]]:
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return []

    query = f'{row["name"]} {row.get("address") or "Paris France"}'
    find_params = urllib.parse.urlencode({"input": query, "inputtype": "textquery", "fields": "place_id", "key": api_key})
    try:
        find_data = json.loads(fetch_text(f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?{find_params}"))
        candidates = find_data.get("candidates") or []
        if not candidates:
            return []
        place_id = candidates[0].get("place_id")
        details_params = urllib.parse.urlencode(
            {"place_id": place_id, "fields": "name,rating,user_ratings_total,editorial_summary,reviews,url", "key": api_key}
        )
        details = json.loads(fetch_text(f"https://maps.googleapis.com/maps/api/place/details/json?{details_params}"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return []

    result = details.get("result") or {}
    source_url = str(result.get("url") or "")
    rating = ""
    if result.get("rating"):
        rating = f'{result.get("rating")} ({result.get("user_ratings_total", "")} ratings)'.strip()
    records = []
    summary = result.get("editorial_summary")
    if isinstance(summary, dict) and summary.get("overview"):
        records.append(source_record("Google Places", source_url, title=str(result.get("name") or ""), excerpt=clean_text(summary["overview"]), rating=rating))
    for review in (result.get("reviews") or [])[:5]:
        text = clean_text(str(review.get("text") or ""))
        if text:
            records.append(
                source_record(
                    "Google Places",
                    source_url,
                    title=str(review.get("author_name") or "Google review"),
                    excerpt=text,
                    rating=str(review.get("rating") or ""),
                    date=str(review.get("relative_time_description") or ""),
                )
            )
    return records


def dedupe_sources(records: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    unique = []
    for record in records:
        key = (record.get("source_name", ""), record.get("source_url", ""), record.get("excerpt", "")[:160])
        if key in seen or not record.get("excerpt"):
            continue
        seen.add(key)
        unique.append(record)
    return unique


def collect_for_restaurant(row: dict[str, str]) -> dict[str, Any]:
    sources: list[dict[str, str]] = []
    sources.extend(collect_michelin_algolia(row))
    sources.extend(collect_page_source("Michelin Guide", row.get("michelin_url", "")))
    time.sleep(0.3)
    sources.extend(collect_page_source("Official website", row.get("website", "")))
    sources.extend(collect_brave_search(row))
    sources.extend(google_place_details(row))
    return {
        "restaurant": {key: row.get(key, "") for key in ("id", "name", "stars", "cuisine", "address", "arrondissement", "website", "michelin_url")},
        "source_policy": "Temporary source material from public crawlable pages and optional official APIs; do not publish raw excerpts.",
        "collected_at": now_iso(),
        "sources": dedupe_sources(sources),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restaurant-id")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between restaurants in seconds")
    parser.add_argument("--skip-existing", action="store_true", help="Do not recollect restaurants that already have JSON output")
    args = parser.parse_args()

    rows = select_restaurants(load_restaurants(args.csv), args.restaurant_id, args.all)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for index, row in enumerate(rows, start=1):
        out_path = args.out_dir / f'{row["id"]}.json'
        if args.skip_existing and out_path.exists():
            print(f'[{index}/{len(rows)}] {row["id"]}: exists -> {out_path}')
        else:
            payload = collect_for_restaurant(row)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f'[{index}/{len(rows)}] {row["id"]}: {len(payload["sources"])} sources -> {out_path}')
        if index < len(rows):
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
