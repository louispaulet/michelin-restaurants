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
from html import unescape
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - exercised only when tqdm is not installed.
    tqdm = None

OUTFILE = Path(__file__).resolve().parents[1] / "public" / "data" / "restaurants.csv"
USER_AGENT = "michelin-restaurants/0.1 (https://github.com/louispaulet/michelin-restaurants)"
MICHELIN_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_PARIS_TITLE = "List of Michelin-starred restaurants in Paris"
PARIS_MICHELIN_PREFIX = "ile-de-france/paris/restaurant/"
MICHELIN_BASE_URL = "https://guide.michelin.com"
ALGOLIA_APP_ID = "8NVHRD7ONV"
ALGOLIA_SEARCH_KEY = "3222e669cf890dc73fa5f38241117ba5"
ALGOLIA_RESTAURANT_INDEX = "prod-restaurants-en"
ALGOLIA_QUERY_ENDPOINT = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{ALGOLIA_RESTAURANT_INDEX}/query"
ALGOLIA_CACHE: dict[str, dict[str, object]] = {}
NOMINATIM_ENDPOINT = "https://nominatim.openstreetmap.org/search"
NOMINATIM_CACHE: dict[str, dict[str, object]] = {}

MICHELIN_ID_OVERRIDES = {
    "Chakaiseki Akiyoshi": "ile-de-france/paris/restaurant/chakaiseiki-akiyoshi",
    "L'Abysse au Pavillon Ledoyen": "ile-de-france/paris/restaurant/l-abysse-au-pavillon-ledoyen",
    "L'Abysse Paris": "ile-de-france/paris/restaurant/l-abysse-paris",
    "La Tour d'Argent": "ile-de-france/paris/restaurant/tour-d-argent",
    "Sushi B": "ile-de-france/paris/restaurant/sushi-b514232",
}

MICHELIN_SEARCH_NAME_OVERRIDES = {
    "L'Abysse au Pavillon Ledoyen": "L'Abysse Paris",
}

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
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, timeout: int = 20) -> str:
    headers = {"User-Agent": MICHELIN_USER_AGENT, "Accept-Language": "en,fr;q=0.9"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="ignore")
        if text:
            return text
    except (urllib.error.URLError, TimeoutError):
        pass

    result = subprocess.run(
        ["curl", "-Ls", "--compressed", "-A", USER_AGENT, url],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.stdout:
        return result.stdout

    result = subprocess.run(
        ["curl", "-Ls", "--compressed", "-A", MICHELIN_USER_AGENT, url],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout


def fetch_wikipedia_wikitext(title: str) -> str:
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2",
    }
    url = f"{WIKIPEDIA_API_ENDPOINT}?{urllib.parse.urlencode(params)}"
    data = fetch_json(url)
    return data["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]


def fetch_algolia_hits(query: str, hits_per_page: int = 5) -> list[dict[str, object]]:
    params = urllib.parse.urlencode({"query": query, "hitsPerPage": hits_per_page})
    body = json.dumps({"params": params}).encode("utf-8")
    req = urllib.request.Request(
        ALGOLIA_QUERY_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Origin": MICHELIN_BASE_URL,
            "Referer": f"{MICHELIN_BASE_URL}/",
            "User-Agent": MICHELIN_USER_AGENT,
            "X-Algolia-Application-Id": ALGOLIA_APP_ID,
            "X-Algolia-API-Key": ALGOLIA_SEARCH_KEY,
        },
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("hits", [])


def fetch_nominatim_hit(query: str) -> dict[str, object]:
    cache_key = normalized_name(query)
    if cache_key in NOMINATIM_CACHE:
        return NOMINATIM_CACHE[cache_key]

    params = urllib.parse.urlencode(
        {"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1, "countrycodes": "fr"}
    )
    req = urllib.request.Request(
        f"{NOMINATIM_ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en,fr;q=0.9"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        data = []
    time.sleep(1.1)

    NOMINATIM_CACHE[cache_key] = data[0] if data else {}
    return NOMINATIM_CACHE[cache_key]


def wikidata_query() -> list[dict[str, str]]:
    query = """
SELECT ?restaurant ?restaurantLabel ?restaurantDescription ?michelinId ?coord
       ?address ?website ?cuisineLabel ?locationLabel ?countryLabel WHERE {
  ?restaurant wdt:P166 wd:Q20824563;
              wdt:P4160 ?michelinId;
              wdt:P17 wd:Q142.
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


def progress(iterable, **kwargs):
    if tqdm:
        return tqdm(iterable, **kwargs)
    return iterable


def clean_wikitext(value: str) -> str:
    value = re.sub(r"<ref[^>]*>.*?</ref>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<ref[^/]*/>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\{\{[^{}]*\}\}", "", value)
    value = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    value = value.replace("&nbsp;", " ")
    value = value.replace("'''", "").replace("''", "")
    value = unescape(value)
    value = value.strip(" |")
    return re.sub(r"\s+", " ", value).strip()


def star_count_from_wikitext(value: str) -> str:
    match = re.search(r"stars\s*=\s*([^|}]+)", value)
    if not match:
        return ""
    stars = match.group(1).strip().lower()
    if stars in {"none", "closed"}:
        return ""
    return stars if stars in {"1", "2", "3"} else ""


def michelin_id_for_paris_row(name: str) -> str:
    if name in MICHELIN_ID_OVERRIDES:
        return MICHELIN_ID_OVERRIDES[name]
    return f"ile-de-france/paris/restaurant/{restaurant_slug(name, '')}"


def michelin_url(michelin_id: str, language: str = "en") -> str:
    return f"{MICHELIN_BASE_URL}/{language}/{michelin_id.strip('/')}"


def normalized_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", normalized.lower()).strip()


def normalized_name_variants(value: str) -> set[str]:
    name = normalized_name(value)
    variants = {name} if name else set()
    for prefix in ("restaurant ", "le restaurant "):
        if name.startswith(prefix):
            variants.add(name.removeprefix(prefix).strip())
    return {variant for variant in variants if variant}


def has_matching_name(expected: str, actual: str) -> bool:
    expected_variants = normalized_name_variants(expected)
    actual_variants = normalized_name_variants(actual)
    if not expected_variants or not actual_variants:
        return True
    if expected_variants & actual_variants:
        return True
    return any(
        (len(expected_normalized.split()) > 1 and expected_normalized in actual_normalized)
        or actual_normalized.startswith(f"{expected_normalized} ")
        for expected_normalized in expected_variants
        for actual_normalized in actual_variants
    )


def json_ld_values(value: object) -> list[dict]:
    if isinstance(value, dict):
        values = [value]
        graph = value.get("@graph")
        if isinstance(graph, list):
            values.extend(item for item in graph if isinstance(item, dict))
        return values
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def extract_michelin_json_ld(html: str) -> dict[str, object]:
    for block in re.findall(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        try:
            data = json.loads(unescape(block.strip()))
        except json.JSONDecodeError:
            continue
        for item in json_ld_values(data):
            item_type = item.get("@type")
            if item_type == "Restaurant" or (isinstance(item_type, list) and "Restaurant" in item_type):
                return item
    return {}


def country_name(value: str) -> str:
    if value.upper() in {"FR", "FRA"}:
        return "France"
    return value


def format_michelin_address(address: object) -> str:
    if not isinstance(address, dict):
        return ""
    street = str(address.get("streetAddress") or "").strip()
    locality = str(address.get("addressLocality") or "").strip()
    postal_code = str(address.get("postalCode") or "").strip()
    country = country_name(str(address.get("addressCountry") or "").strip())
    city = " ".join(part for part in [postal_code, locality] if part)
    return ", ".join(part for part in [street, city, country] if part)


def michelin_id_from_url(url: str) -> str:
    match = re.search(r"/en/(.+?/restaurant/[^/?#]+)", url)
    return match.group(1).strip("/") if match else ""


def michelin_id_from_algolia_hit(hit: dict[str, object]) -> str:
    url = str(hit.get("url") or "")
    if url.startswith("/en/"):
        return url.removeprefix("/en/").strip("/")
    slug = str(hit.get("slug") or "").strip("/")
    return f"{PARIS_MICHELIN_PREFIX}{slug}" if slug else ""


def stars_from_algolia_hit(hit: dict[str, object]) -> str:
    star = str(hit.get("michelin_star") or "").upper()
    return {"ONE": "1", "TWO": "2", "THREE": "3"}.get(star, "")


def cuisine_from_algolia_hit(hit: dict[str, object]) -> str:
    cuisines = hit.get("cuisines")
    if isinstance(cuisines, list) and cuisines:
        first = cuisines[0]
        if isinstance(first, dict):
            return str(first.get("label") or "").replace(" Cuisine", "")
    return ""


def format_algolia_address(hit: dict[str, object]) -> str:
    city = hit.get("city")
    country = hit.get("country")
    city_name = str(city.get("name") or "") if isinstance(city, dict) else ""
    country_name_value = str(country.get("name") or "") if isinstance(country, dict) else ""
    street = str(hit.get("street") or "").strip()
    postcode = str(hit.get("postcode") or "").strip()
    city_line = " ".join(part for part in [postcode, city_name] if part)
    return ", ".join(part for part in [street, city_line, country_name_value] if part)


def format_nominatim_address(hit: dict[str, object]) -> str:
    address = hit.get("address")
    if not isinstance(address, dict):
        return ""
    road = str(address.get("road") or address.get("pedestrian") or address.get("square") or "").strip()
    house_number = str(address.get("house_number") or "").strip()
    street = " ".join(part for part in [house_number, road] if part)
    postcode = str(address.get("postcode") or "").strip()
    city = str(address.get("city") or address.get("town") or "Paris").strip()
    country = str(address.get("country") or "France").strip()
    city_line = " ".join(part for part in [postcode, city] if part)
    return ", ".join(part for part in [street, city_line, country] if part)


def is_nominatim_paris_hit(hit: dict[str, object]) -> bool:
    address = hit.get("address")
    if not isinstance(address, dict):
        return False
    location = " ".join(
        str(address.get(key) or "") for key in ("city", "city_district", "suburb", "postcode", "county")
    )
    return bool(re.search(r"\bParis\b|\b75\d{3}\b", location, re.IGNORECASE))


def select_algolia_hit(name: str) -> dict[str, object]:
    cache_key = normalized_name(name)
    if cache_key in ALGOLIA_CACHE:
        return ALGOLIA_CACHE[cache_key]

    hits = []
    query_names = [MICHELIN_SEARCH_NAME_OVERRIDES.get(name, name)]
    query_names.extend(variant for variant in normalized_name_variants(name) if variant != cache_key)
    for query_name in query_names:
        try:
            hits.extend(fetch_algolia_hits(f"{query_name} Paris"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            continue

    paris_hits = []
    for hit in hits:
        city = hit.get("city")
        country = hit.get("country")
        city_name = str(city.get("name") or "") if isinstance(city, dict) else ""
        country_code = str(country.get("code") or "") if isinstance(country, dict) else ""
        if city_name.lower() == "paris" and country_code.upper() == "FR":
            paris_hits.append(hit)

    for hit in paris_hits:
        hit_name = str(hit.get("name") or "")
        if has_matching_name(name, hit_name) or any(has_matching_name(query_name, hit_name) for query_name in query_names):
            ALGOLIA_CACHE[cache_key] = hit
            return hit

    ALGOLIA_CACHE[cache_key] = {}
    return ALGOLIA_CACHE[cache_key]


def enrich_row_from_nominatim(row: dict[str, str]) -> dict[str, str]:
    hit = fetch_nominatim_hit(f"{row.get('name', '')} Paris France")
    if not hit or not is_nominatim_paris_hit(hit):
        return row
    address = format_nominatim_address(hit)
    if address and not row.get("address"):
        row["address"] = address
        row["arrondissement"] = infer_area(address, "Paris", row.get("country") or "France")
    if hit.get("lat") and not row.get("latitude"):
        row["latitude"] = str(hit["lat"])
    if hit.get("lon") and not row.get("longitude"):
        row["longitude"] = str(hit["lon"])
    return row


def find_michelin_id_by_search(name: str) -> str:
    query = urllib.parse.urlencode({"q": f"{name} Paris"})
    html = fetch_text(f"{MICHELIN_BASE_URL}/en/restaurants?{query}")
    candidates = []
    for match in re.finditer(r'href="(/en/ile-de-france/paris/restaurant/[^"]+)"', html):
        href = match.group(1)
        context = html[max(0, match.start() - 3000) : match.end() + 500]
        name_match = re.search(r'data-restaurant-name="([^"]+)"', context)
        candidate_name = unescape(name_match.group(1)).strip() if name_match else ""
        michelin_id = michelin_id_from_url(href)
        if michelin_id and has_matching_name(name, candidate_name):
            return michelin_id
        if michelin_id:
            candidates.append(michelin_id)
    return candidates[0] if candidates else ""


def fetch_michelin_data(michelin_id: str, name: str = "") -> tuple[str, dict[str, object]]:
    html = fetch_text(michelin_url(michelin_id))
    data = extract_michelin_json_ld(html)
    data_name = str(data.get("name") or "") if data else ""
    data_address = data.get("address") if data else None
    locality = str(data_address.get("addressLocality") or "") if isinstance(data_address, dict) else ""
    if name and data and has_matching_name(name, data_name) and locality.lower() == "paris":
        return michelin_id.strip("/"), data
    if name:
        resolved_id = find_michelin_id_by_search(name)
        if resolved_id and resolved_id != michelin_id.strip("/"):
            html = fetch_text(michelin_url(resolved_id))
            resolved_data = extract_michelin_json_ld(html)
            if resolved_data:
                return resolved_id, resolved_data
    return michelin_id.strip("/"), data


def enrich_row_from_michelin(row: dict[str, str]) -> dict[str, str]:
    if not row.get("michelin_id"):
        return row

    hit = select_algolia_hit(row.get("name", ""))
    if hit:
        michelin_id = michelin_id_from_algolia_hit(hit)
        if michelin_id:
            row["michelin_id"] = michelin_id
            row["michelin_url"] = michelin_url(michelin_id)

        address = format_algolia_address(hit)
        if address and not row.get("address"):
            row["address"] = address
            row["arrondissement"] = infer_area(address, "Paris", row.get("country") or "France")

        geoloc = hit.get("_geoloc")
        if isinstance(geoloc, dict):
            if geoloc.get("lat") and not row.get("latitude"):
                row["latitude"] = str(geoloc["lat"])
            if geoloc.get("lng") and not row.get("longitude"):
                row["longitude"] = str(geoloc["lng"])
        if hit.get("website") and not row.get("website"):
            row["website"] = str(hit["website"])
        if not row.get("stars"):
            row["stars"] = stars_from_algolia_hit(hit)
        if not row.get("cuisine"):
            row["cuisine"] = cuisine_from_algolia_hit(hit)
        return row

    if not row.get("address") or not row.get("latitude") or not row.get("longitude"):
        row = enrich_row_from_nominatim(row)
        if row.get("address") and row.get("latitude") and row.get("longitude"):
            return row

    michelin_id, data = fetch_michelin_data(row["michelin_id"], row.get("name", ""))
    if not data:
        return row

    row["michelin_id"] = michelin_id
    row["michelin_url"] = michelin_url(michelin_id)

    address = format_michelin_address(data.get("address"))
    if address and not row.get("address"):
        row["address"] = address
        data_address = data.get("address")
        locality = str(data_address.get("addressLocality") or "") if isinstance(data_address, dict) else ""
        row["arrondissement"] = infer_area(address, locality, row.get("country") or "France")
    if data.get("latitude") and not row.get("latitude"):
        row["latitude"] = str(data["latitude"])
    if data.get("longitude") and not row.get("longitude"):
        row["longitude"] = str(data["longitude"])
    if data.get("url") and not row.get("website"):
        row["website"] = str(data["url"])
    if data.get("servesCuisine") and not row.get("cuisine"):
        row["cuisine"] = str(data["servesCuisine"]).replace(" Cuisine", "")
    return row


def is_paris_france_row(row: dict[str, str]) -> bool:
    if row.get("country") != "France":
        return False
    michelin_id = row.get("michelin_id", "").strip("/")
    location_text = " ".join([row.get("address", ""), row.get("arrondissement", ""), row.get("michelin_url", "")])
    return michelin_id.startswith(PARIS_MICHELIN_PREFIX) or re.search(r"\bparis\b", location_text, re.IGNORECASE)


def parse_wikipedia_table_row(block: str) -> dict[str, str] | None:
    match = re.search(r'!\s*scope="row"\s*\|([^\n]+)\n(.+)', block, flags=re.DOTALL)
    if not match:
        return None

    name = clean_wikitext(match.group(1))
    cells = []
    for line in match.group(2).split("\n|"):
        line = line.strip()
        if not line:
            continue
        cells.extend(part.strip() for part in line.split("||"))

    if len(cells) < 6:
        return None

    stars = star_count_from_wikitext(cells[-1])
    if not stars:
        return None

    cuisine = clean_wikitext(cells[0])
    location = clean_wikitext(cells[1])
    michelin_id = michelin_id_for_paris_row(name)
    return {
        "id": restaurant_slug(name, michelin_id),
        "name": name,
        "stars": stars,
        "cuisine": cuisine,
        "address": "",
        "arrondissement": f"{location}, France" if location else "Paris, France",
        "country": "France",
        "latitude": "",
        "longitude": "",
        "website": "",
        "wikidata_url": "",
        "michelin_id": michelin_id,
        "michelin_url": f"https://guide.michelin.com/en/{michelin_id}",
        "description": "Michelin-starred restaurant in Paris from Wikipedia's current Michelin list.",
    }


def rows_from_wikipedia_paris_list() -> list[dict[str, str]]:
    wikitext = fetch_wikipedia_wikitext(WIKIPEDIA_PARIS_TITLE)
    rows = []
    for block in wikitext.split("|-"):
        row = parse_wikipedia_table_row(block)
        if row:
            rows.append(row)
    print(f"Found {len(rows)} current Paris restaurants from Wikipedia.")
    return rows


def extract_stars_from_michelin(michelin_id: str) -> str:
    if not michelin_id:
        return ""

    urls = [
        michelin_url(michelin_id, "en"),
        michelin_url(michelin_id, "fr"),
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
    items = wikidata_query()
    print(f"Found {len(items)} Wikidata candidates.")
    for item in progress(items, desc="Enriching Michelin pages", unit="restaurant"):
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
        restaurant_michelin_url = michelin_url(michelin_id)
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
                "michelin_url": restaurant_michelin_url,
                "description": value(item, "restaurantDescription"),
            }
        )
        time.sleep(0.15)
    return rows


def merge_rows(base_rows: list[dict[str, str]], extra_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = list(base_rows)
    rows_by_id = {row["michelin_id"].strip("/"): row for row in rows if row["michelin_id"]}
    rows_by_name = {row["name"].casefold(): row for row in rows if row["name"]}

    added = 0
    updated = 0
    for row in extra_rows:
        michelin_id = row["michelin_id"].strip("/")
        existing = rows_by_id.get(michelin_id) or rows_by_name.get(row["name"].casefold())
        if existing:
            for key in ("stars", "cuisine"):
                if row[key] and not existing[key]:
                    existing[key] = row[key]
                    updated += 1
            continue
        rows.append(row)
        rows_by_id[michelin_id] = row
        rows_by_name[row["name"].casefold()] = row
        added += 1

    print(f"Added {added} Paris restaurants from Wikipedia that were missing from Wikidata.")
    print(f"Filled {updated} blank fields on existing Wikidata rows from Wikipedia.")
    return rows


def main() -> None:
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    merged_rows = merge_rows(rows_from_wikidata(), rows_from_wikipedia_paris_list())
    rows = [enrich_row_from_michelin(row) for row in progress(merged_rows, desc="Filling Michelin addresses", unit="restaurant")]
    rows = [row for row in rows if is_paris_france_row(row)]
    rows.sort(key=lambda row: (row["name"].lower(), row["michelin_id"]))
    with OUTFILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} restaurants to {OUTFILE}")


if __name__ == "__main__":
    main()
