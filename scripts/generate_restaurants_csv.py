#!/usr/bin/env python3
"""Generate an atomic, Wikidata-only Michelin restaurant dataset."""

from __future__ import annotations

import csv
import json
import os
import re
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
QUERY_PATH = ROOT / "scripts" / "wikidata_restaurants.sparql"
OUTFILE = ROOT / "public" / "data" / "restaurants.csv"
METADATA_FILE = ROOT / "public" / "data" / "metadata.json"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API_ENDPOINT = "https://www.wikidata.org/w/api.php"
USER_AGENT = "michelin-restaurants/0.2 (https://github.com/louispaulet/michelin-restaurants)"
MICHELIN_BASE_URL = "https://guide.michelin.com/en"
CITY_ITEM = "Q515"
NEIGHBORHOOD_ITEM = "Q123705"
SUBCITY_CLASS_ROOTS = {
    "Q408804": "borough of New York City",
    "Q211690": "London borough",
    "Q5327704": "special ward of Japan",
    "Q4286337": "city district",
    "Q1195098": "ward",
}
EXACT_SUBCITY_CLASSES = {NEIGHBORHOOD_ITEM: "neighborhood"}
ENTITY_BATCH_SIZE = 50

FIELDS = [
    "id",
    "wikidata_id",
    "name",
    "description",
    "cuisine",
    "address",
    "locality",
    "locality_wikidata_id",
    "city",
    "city_slug",
    "city_wikidata_id",
    "country",
    "country_slug",
    "country_wikidata_id",
    "latitude",
    "longitude",
    "website",
    "michelin_id",
    "michelin_url",
]


def fetch_json(url: str, *, timeout: int = 90, attempts: int = 3) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"Wikidata request failed after {attempts} attempts: {last_error}") from last_error


def fetch_sparql(query: str) -> list[dict[str, dict[str, str]]]:
    url = f"{SPARQL_ENDPOINT}?{urllib.parse.urlencode({'query': query, 'format': 'json'})}"
    data = fetch_json(url, timeout=120)
    try:
        return data["results"]["bindings"]
    except (KeyError, TypeError) as error:
        raise RuntimeError("Wikidata returned an invalid SPARQL response") from error


def chunks(values: Iterable[str], size: int) -> Iterable[list[str]]:
    values = list(values)
    for index in range(0, len(values), size):
        yield values[index : index + size]


def fetch_entities(ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    clean_ids = sorted({entity_id for entity_id in ids if re.fullmatch(r"Q\d+", entity_id)})
    for batch in chunks(clean_ids, ENTITY_BATCH_SIZE):
        params = {
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "claims|labels",
            "languages": "en|fr",
            "format": "json",
            "formatversion": "2",
        }
        data = fetch_json(f"{WIKIDATA_API_ENDPOINT}?{urllib.parse.urlencode(params)}", timeout=60)
        returned = data.get("entities")
        if not isinstance(returned, dict):
            raise RuntimeError("Wikidata returned an invalid entity response")
        entities.update({str(key): value for key, value in returned.items() if isinstance(value, dict)})
    return entities


def expand_entity_graph(seed_ids: Iterable[str], follow_properties: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    frontier = {entity_id for entity_id in seed_ids if re.fullmatch(r"Q\d+", entity_id)}
    while frontier:
        fetched = fetch_entities(frontier)
        cache.update(fetched)
        next_ids: set[str] = set()
        for entity in fetched.values():
            for property_id in follow_properties:
                next_ids.update(statement_entity_ids(entity, property_id))
        frontier = next_ids - set(cache)
    return cache


def value(binding: dict[str, dict[str, str]], key: str) -> str:
    return binding.get(key, {}).get("value", "").strip()


def entity_id(uri_or_id: str) -> str:
    candidate = uri_or_id.rstrip("/").split("/")[-1]
    return candidate if re.fullmatch(r"Q\d+", candidate) else ""


def parse_point(point: str) -> tuple[str, str]:
    match = re.fullmatch(r"Point\(([-0-9.]+) ([-0-9.]+)\)", point.strip())
    if not match:
        return "", ""
    longitude, latitude = match.groups()
    return latitude, longitude


def slugify(value_to_slug: str) -> str:
    normalized = unicodedata.normalize("NFKD", value_to_slug).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def label_for_entity(entity_id_value: str, entities: dict[str, dict[str, Any]]) -> str:
    labels = entities.get(entity_id_value, {}).get("labels")
    if not isinstance(labels, dict):
        return ""
    for language in ("en", "fr"):
        label = labels.get(language)
        if isinstance(label, dict) and str(label.get("value") or "").strip():
            return str(label["value"]).strip()
    return ""


def statement_entity_ids(entity: dict[str, Any], property_id: str) -> set[str]:
    claims = entity.get("claims")
    if not isinstance(claims, dict):
        return set()
    statements = claims.get(property_id)
    if not isinstance(statements, list):
        return set()
    ids: set[str] = set()
    for statement in statements:
        try:
            candidate = statement["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            continue
        if isinstance(candidate, str) and re.fullmatch(r"Q\d+", candidate):
            ids.add(candidate)
    return ids


def type_descends_from(
    type_id: str,
    ancestor_id: str,
    types: dict[str, dict[str, Any]],
    memo: dict[tuple[str, str], bool],
) -> bool:
    if type_id == ancestor_id:
        return True
    memo_key = (type_id, ancestor_id)
    if memo_key in memo:
        return memo[memo_key]
    memo[memo_key] = False
    memo[memo_key] = any(
        type_descends_from(parent, ancestor_id, types, memo)
        for parent in statement_entity_ids(types.get(type_id, {}), "P279")
    )
    return memo[memo_key]


def entity_is_subcity(
    entity: dict[str, Any],
    types: dict[str, dict[str, Any]],
    memo: dict[tuple[str, str], bool],
) -> bool:
    instance_types = statement_entity_ids(entity, "P31")
    if instance_types & set(EXACT_SUBCITY_CLASSES):
        return True
    return any(
        type_descends_from(type_id, root_id, types, memo)
        for type_id in instance_types
        for root_id in SUBCITY_CLASS_ROOTS
    )


def city_entity_ids(entities: dict[str, dict[str, Any]], types: dict[str, dict[str, Any]]) -> set[str]:
    memo: dict[tuple[str, str], bool] = {}
    city_ids = set()
    for candidate_id, entity in entities.items():
        is_city = any(
            type_descends_from(type_id, CITY_ITEM, types, memo)
            for type_id in statement_entity_ids(entity, "P31")
        )
        if is_city and not entity_is_subcity(entity, types, memo):
            city_ids.add(candidate_id)
    return city_ids


def nearest_city(location_ids: Iterable[str], entities: dict[str, dict[str, Any]], cities: set[str]) -> str:
    queue = deque((location_id, 0) for location_id in sorted(set(location_ids)))
    seen: set[str] = set()
    current_depth = 0
    candidates: list[str] = []
    while queue:
        candidate_id, depth = queue.popleft()
        if candidate_id in seen:
            continue
        if candidates and depth > current_depth:
            break
        seen.add(candidate_id)
        if candidate_id in cities:
            current_depth = depth
            candidates.append(candidate_id)
            continue
        for parent_id in sorted(statement_entity_ids(entities.get(candidate_id, {}), "P131")):
            queue.append((parent_id, depth + 1))
    return sorted(candidates)[0] if candidates else ""


def nearest_country(location_ids: Iterable[str], entities: dict[str, dict[str, Any]]) -> str:
    queue = deque((location_id, 0) for location_id in sorted(set(location_ids)))
    seen: set[str] = set()
    current_depth = 0
    candidates: list[str] = []
    while queue:
        candidate_id, depth = queue.popleft()
        if candidate_id in seen:
            continue
        if candidates and depth > current_depth:
            break
        seen.add(candidate_id)
        countries = sorted(statement_entity_ids(entities.get(candidate_id, {}), "P17"))
        if countries:
            current_depth = depth
            candidates.extend(countries)
            continue
        for parent_id in sorted(statement_entity_ids(entities.get(candidate_id, {}), "P131")):
            queue.append((parent_id, depth + 1))
    return sorted(set(candidates))[0] if candidates else ""


def aggregate_bindings(bindings: list[dict[str, dict[str, str]]]) -> list[dict[str, Any]]:
    restaurants: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        wikidata_id = entity_id(value(binding, "restaurant"))
        if not wikidata_id:
            raise ValueError("SPARQL result contained a restaurant without a Wikidata entity ID")
        row = restaurants.setdefault(
            wikidata_id,
            {
                "wikidata_id": wikidata_id,
                "name": "",
                "description": "",
                "cuisines": set(),
                "addresses": set(),
                "localities": {},
                "countries": {},
                "coordinates": set(),
                "websites": set(),
                "michelin_ids": set(),
            },
        )
        label = value(binding, "restaurantLabel")
        if label and label != wikidata_id:
            row["name"] = label
        if value(binding, "restaurantDescription"):
            row["description"] = value(binding, "restaurantDescription")
        if value(binding, "cuisineLabel"):
            row["cuisines"].add(value(binding, "cuisineLabel"))
        if value(binding, "address"):
            row["addresses"].add(value(binding, "address"))
        location_id = entity_id(value(binding, "location"))
        if location_id:
            row["localities"][location_id] = value(binding, "locationLabel") or location_id
        country_id = entity_id(value(binding, "country"))
        if country_id:
            row["countries"][country_id] = value(binding, "countryLabel") or country_id
        if value(binding, "coord"):
            row["coordinates"].add(value(binding, "coord"))
        if value(binding, "website"):
            row["websites"].add(value(binding, "website"))
        if value(binding, "michelinId"):
            row["michelin_ids"].add(value(binding, "michelinId").strip("/"))
    return list(restaurants.values())


def unique_slugs(entries: dict[str, str]) -> dict[str, str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for entity_id_value, label in entries.items():
        grouped[slugify(label) or entity_id_value.lower()].append(entity_id_value)
    slugs: dict[str, str] = {}
    for base, ids in grouped.items():
        for entity_id_value in sorted(ids):
            slugs[entity_id_value] = base if len(ids) == 1 else f"{base}-{entity_id_value.lower()}"
    return slugs


def finalize_rows(
    aggregated: list[dict[str, Any]],
    location_entities: dict[str, dict[str, Any]],
    type_entities: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    cities = city_entity_ids(location_entities, type_entities)
    needed_country_ids: set[str] = set()
    resolved: list[dict[str, Any]] = []
    for item in aggregated:
        location_ids = set(item["localities"])
        city_id = nearest_city(location_ids, location_entities, cities)
        direct_country_ids = sorted(item["countries"])
        country_id = direct_country_ids[0] if direct_country_ids else nearest_country(location_ids, location_entities)
        if country_id:
            needed_country_ids.add(country_id)
        resolved.append({**item, "city_id": city_id, "country_id": country_id})

    missing_country_entities = needed_country_ids - set(location_entities)
    country_entities = fetch_entities(missing_country_entities) if missing_country_entities else {}
    all_entities = {**location_entities, **country_entities}

    country_labels: dict[str, str] = {}
    city_labels: dict[str, str] = {}
    for item in resolved:
        country_id = item["country_id"]
        city_id = item["city_id"]
        if country_id:
            country_labels[country_id] = (
                item["countries"].get(country_id) or label_for_entity(country_id, all_entities) or country_id
            )
        if city_id:
            city_labels[city_id] = label_for_entity(city_id, all_entities) or city_id

    country_slugs = unique_slugs(country_labels)
    city_slugs_by_country: dict[str, str] = {}
    city_groups: dict[str, dict[str, str]] = defaultdict(dict)
    for item in resolved:
        if item["city_id"]:
            city_groups[item["country_id"]][item["city_id"]] = city_labels[item["city_id"]]
    for country_id, entries in city_groups.items():
        for city_id, city_slug in unique_slugs(entries).items():
            city_slugs_by_country[f"{country_id}:{city_id}"] = city_slug

    id_groups: dict[str, list[str]] = defaultdict(list)
    for item in resolved:
        base_id = slugify(item["name"] or item["wikidata_id"]) or item["wikidata_id"].lower()
        item["base_id"] = base_id
        id_groups[base_id].append(item["wikidata_id"])

    rows: list[dict[str, str]] = []
    for item in resolved:
        wikidata_id = item["wikidata_id"]
        restaurant_id = item["base_id"]
        if len(id_groups[restaurant_id]) > 1:
            restaurant_id = f"{restaurant_id}-{wikidata_id.lower()}"
        coordinates = sorted(item["coordinates"])
        latitude, longitude = parse_point(coordinates[0]) if coordinates else ("", "")
        location_ids = sorted(item["localities"])
        country_id = item["country_id"]
        city_id = item["city_id"]
        michelin_ids = sorted(item["michelin_ids"])
        michelin_id = michelin_ids[0] if michelin_ids else ""
        rows.append(
            {
                "id": restaurant_id,
                "wikidata_id": wikidata_id,
                "name": item["name"] or wikidata_id,
                "description": item["description"],
                "cuisine": " / ".join(sorted(item["cuisines"])),
                "address": sorted(item["addresses"])[0] if item["addresses"] else "",
                "locality": " / ".join(item["localities"][key] for key in location_ids),
                "locality_wikidata_id": " / ".join(location_ids),
                "city": city_labels.get(city_id, ""),
                "city_slug": city_slugs_by_country.get(f"{country_id}:{city_id}", ""),
                "city_wikidata_id": city_id,
                "country": country_labels.get(country_id, ""),
                "country_slug": country_slugs.get(country_id, ""),
                "country_wikidata_id": country_id,
                "latitude": latitude,
                "longitude": longitude,
                "website": sorted(item["websites"])[0] if item["websites"] else "",
                "michelin_id": michelin_id,
                "michelin_url": f"{MICHELIN_BASE_URL}/{michelin_id}" if michelin_id else "",
            }
        )
    rows.sort(key=lambda row: (row["name"].casefold(), row["wikidata_id"]))
    return rows


def validate_rows(rows: list[dict[str, str]], source_ids: set[str]) -> None:
    problems: list[str] = []
    row_source_ids = {row["wikidata_id"] for row in rows}
    if len(rows) != len(source_ids):
        problems.append(f"expected {len(source_ids)} rows, produced {len(rows)}")
    if row_source_ids != source_ids:
        missing = sorted(source_ids - row_source_ids)
        extra = sorted(row_source_ids - source_ids)
        problems.append(f"source mismatch; missing={missing[:10]} extra={extra[:10]}")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        problems.append("restaurant IDs are not unique")
    for row in rows:
        if not row["name"]:
            problems.append(f"{row['wikidata_id']}: missing name")
        if row["latitude"] or row["longitude"]:
            try:
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])
            except ValueError:
                problems.append(f"{row['wikidata_id']}: invalid coordinates")
            else:
                if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                    problems.append(f"{row['wikidata_id']}: coordinates out of range")
        if row["city"] and not row["city_wikidata_id"]:
            problems.append(f"{row['wikidata_id']}: city label without Wikidata ID")
        if row["country"] and not row["country_wikidata_id"]:
            problems.append(f"{row['wikidata_id']}: country label without Wikidata ID")
    if problems:
        raise ValueError("Dataset validation failed:\n" + "\n".join(problems[:100]))


def build_metadata(rows: list[dict[str, str]]) -> dict[str, Any]:
    country_ids = {row["country_wikidata_id"] for row in rows if row["country_wikidata_id"]}
    city_ids = {row["city_wikidata_id"] for row in rows if row["city_wikidata_id"]}
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": {
            "name": "Wikidata",
            "query_file": "scripts/wikidata_restaurants.sparql",
            "award_property": "P166",
            "award_item": "Q20824563",
            "instance_of_item": "Q11707",
            "michelin_id_property": "P4160",
            "michelin_id_required": False,
            "canonical_city": {
                "hierarchy_property": "P131",
                "city_class": CITY_ITEM,
                "excluded_subcity_class_roots": [
                    {"id": item_id, "name": name}
                    for item_id, name in SUBCITY_CLASS_ROOTS.items()
                ],
                "excluded_exact_classes": [
                    {"id": item_id, "name": name}
                    for item_id, name in EXACT_SUBCITY_CLASSES.items()
                ],
                "fallbacks": [],
            },
            "fallback_sources": [],
        },
        "counts": {
            "restaurants": len(rows),
            "countries": len(country_ids),
            "cities": len(city_ids),
            "mapped_restaurants": sum(bool(row["latitude"] and row["longitude"]) for row in rows),
        },
        "missing": {
            "country": sum(not row["country"] for row in rows),
            "city": sum(not row["city"] for row in rows),
            "coordinates": sum(not (row["latitude"] and row["longitude"]) for row in rows),
            "address": sum(not row["address"] for row in rows),
            "michelin_id": sum(not row["michelin_id"] for row in rows),
        },
    }


def write_csv_temp(rows: list[dict[str, str]]) -> Path:
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=OUTFILE.parent, delete=False)
    try:
        with handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        return Path(handle.name)
    except Exception:
        Path(handle.name).unlink(missing_ok=True)
        raise


def write_json_temp(payload: dict[str, Any]) -> Path:
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=METADATA_FILE.parent, delete=False)
    try:
        with handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return Path(handle.name)
    except Exception:
        Path(handle.name).unlink(missing_ok=True)
        raise


def main() -> None:
    query = QUERY_PATH.read_text(encoding="utf-8")
    print("Fetching all Michelin-star award records from Wikidata...")
    bindings = fetch_sparql(query)
    aggregated = aggregate_bindings(bindings)
    source_ids = {row["wikidata_id"] for row in aggregated}
    print(f"Fetched {len(bindings)} bindings for {len(source_ids)} unique restaurants.")

    location_ids = {location_id for row in aggregated for location_id in row["localities"]}
    print(f"Resolving the Wikidata hierarchy for {len(location_ids)} immediate locations...")
    location_entities = expand_entity_graph(location_ids, ("P131",))
    type_ids = {
        type_id
        for entity in location_entities.values()
        for type_id in statement_entity_ids(entity, "P31")
    }
    type_entities = expand_entity_graph(type_ids, ("P279",))
    rows = finalize_rows(aggregated, location_entities, type_entities)
    validate_rows(rows, source_ids)
    metadata = build_metadata(rows)

    csv_temp = write_csv_temp(rows)
    metadata_temp = write_json_temp(metadata)
    try:
        os.replace(csv_temp, OUTFILE)
        os.replace(metadata_temp, METADATA_FILE)
    finally:
        csv_temp.unlink(missing_ok=True)
        metadata_temp.unlink(missing_ok=True)

    counts = metadata["counts"]
    print(
        f"Wrote {counts['restaurants']} restaurants, {counts['countries']} countries, "
        f"{counts['cities']} cities, and {counts['mapped_restaurants']} mapped rows."
    )
    print(f"CSV: {OUTFILE}")
    print(f"Metadata: {METADATA_FILE}")


if __name__ == "__main__":
    main()
