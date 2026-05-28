#!/usr/bin/env python3
"""Generate a CSV of Michelin-starred restaurants from Wikidata.

The discovery query uses award received (P166) = Michelin star (Q20824563)
and requires a Michelin Restaurants ID (P4160). Michelin pages are then
best-effort enriched for current star tiers.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUTFILE = Path(__file__).resolve().parents[1] / "public" / "data" / "restaurants.csv"
USER_AGENT = "michelin-restaurants/0.1 (https://github.com/louispaulet/michelin-restaurants)"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

FIELDS = [
    "id",
    "name",
    "stars",
    "cuisine",
    "address",
    "arrondissement",
    "country",
    "latitude",
    "longitude",
    "website",
    "wikidata_url",
    "michelin_id",
    "michelin_url",
    "description",
]


def fetch_json(url: str, timeout: int = 45) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, timeout: int = 12) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en,fr;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        text = response.read().decode("utf-8", errors="ignore")
    if text:
        return text

    result = subprocess.run(
        ["curl", "-Ls", "--compressed", "-A", USER_AGENT, url],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout


def wikidata_query() -> list[dict[str, str]]:
    query = """
SELECT ?restaurant ?restaurantLabel ?restaurantDescription ?michelinId ?coord
       ?address ?website ?cuisineLabel ?locationLabel ?countryLabel WHERE {
  ?restaurant wdt:P166 wd:Q20824563;
              wdt:P4160 ?michelinId.
  OPTIONAL { ?restaurant wdt:P625 ?coord. }
  OPTIONAL { ?restaurant wdt:P6375 ?address. }
  OPTIONAL { ?restaurant wdt:P856 ?website. }
  OPTIONAL { ?restaurant wdt:P2012 ?cuisine. }
  OPTIONAL { ?restaurant wdt:P131 ?location. }
  OPTIONAL { ?restaurant wdt:P17 ?country. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
}
ORDER BY ?restaurantLabel
"""
    url = f"{SPARQL_ENDPOINT}?{urllib.parse.urlencode({'query': query, 'format': 'json'})}"
    data = fetch_json(url)
    return data["results"]["bindings"]


def value(row: dict, key: str) -> str:
    return row.get(key, {}).get("value", "").strip()


def parse_point(point: str) -> tuple[str, str]:
    match = re.search(r"Point\(([-0-9.]+) ([-0-9.]+)\)", point)
    if not match:
        return "", ""
    longitude, latitude = match.groups()
    return latitude, longitude


def infer_paris_arrondissement(address: str, label: str) -> str:
    combined = f"{address} {label}"
    match = re.search(r"\b750(\d{2})\b", combined)
    if match:
        number = int(match.group(1))
        if 1 <= number <= 20:
            return f"{number}e"
    if "paris" not in combined.lower():
        return ""
    match = re.search(r"(\d{1,2})(?:st|nd|rd|th|er|e)\s+arr", combined, re.IGNORECASE)
    if match:
        number = int(match.group(1))
        if 1 <= number <= 20:
            return f"{number}e"
    arrondissement = label.replace(" arrondissement of Paris", "e").replace("Paris ", "")
    return arrondissement if arrondissement != label else ""


def infer_area(address: str, location: str, country: str) -> str:
    paris_arrondissement = infer_paris_arrondissement(address, location)
    if paris_arrondissement:
        return ", ".join(part for part in [f"Paris {paris_arrondissement}", country] if part)
    return ", ".join(part for part in [location, country] if part)


def restaurant_slug(name: str, michelin_id: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or re.sub(r"[^a-z0-9]+", "-", michelin_id.lower()).strip("-")


def name_from_michelin_id(michelin_id: str) -> str:
    slug = michelin_id.rstrip("/").split("/")[-1]
    slug = re.sub(r"\d+$", "", slug).strip("-")
    words = [word for word in slug.split("-") if word]
    return " ".join(word.capitalize() for word in words)


def extract_stars_from_michelin(michelin_id: str) -> str:
    if not michelin_id:
        return ""

    urls = [
        f"https://guide.michelin.com/en/en/{michelin_id}",
        f"https://guide.michelin.com/fr/fr/{michelin_id}",
    ]
    for url in urls:
        try:
            html = fetch_text(url)
        except (urllib.error.URLError, TimeoutError):
            continue

        star_patterns = [
            r"(\d)\s+MICHELIN\s+Stars?",
            r"(\d)\s+étoiles?\s+MICHELIN",
            r"Trois\s+étoiles?",
            r"Deux\s+étoiles?",
            r"Une\s+étoile",
            r"data-award=['\"](\d)['\"]",
            r"michelin-star(?:red)?[^0-9]{0,40}(\d)",
        ]
        for pattern in star_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                if match.groups() and match.group(1) in {"1", "2", "3"}:
                    return match.group(1)
                words = match.group(0).lower()
                if "trois" in words:
                    return "3"
                if "deux" in words:
                    return "2"
                if "une" in words:
                    return "1"

        icon_count = len(re.findall(r"icon-star|star-icon|michelin-star", html, re.IGNORECASE))
        if 1 <= icon_count <= 3:
            return str(icon_count)
    return ""


def rows_from_wikidata() -> list[dict[str, str]]:
    rows = []
    seen = set()
    for item in wikidata_query():
        michelin_id = value(item, "michelinId").strip("/")
        name = value(item, "restaurantLabel")
        if re.fullmatch(r"Q\d+", name):
            name = name_from_michelin_id(michelin_id)
        if not name or michelin_id in seen:
            continue
        seen.add(michelin_id)
        latitude, longitude = parse_point(value(item, "coord"))
        address = value(item, "address")
        country = value(item, "countryLabel")
        area = infer_area(address, value(item, "locationLabel"), country)
        michelin_url = f"https://guide.michelin.com/en/en/{michelin_id}"
        stars = extract_stars_from_michelin(michelin_id)
        rows.append(
            {
                "id": restaurant_slug(name, michelin_id),
                "name": name,
                "stars": stars,
                "cuisine": value(item, "cuisineLabel"),
                "address": address,
                "arrondissement": area,
                "country": country,
                "latitude": latitude,
                "longitude": longitude,
                "website": value(item, "website"),
                "wikidata_url": value(item, "restaurant"),
                "michelin_id": michelin_id,
                "michelin_url": michelin_url,
                "description": value(item, "restaurantDescription"),
            }
        )
        time.sleep(0.15)
    return rows


def main() -> None:
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    rows = rows_from_wikidata()
    rows.sort(key=lambda row: (row["name"].lower(), row["michelin_id"]))
    with OUTFILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} restaurants to {OUTFILE}")


if __name__ == "__main__":
    main()
