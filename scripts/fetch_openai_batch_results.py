#!/usr/bin/env python3
"""Poll/download OpenAI Batch API results and write restaurant descriptions."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = ROOT / ".tmp" / "openai" / "batch_metadata.json"
DEFAULT_RAW = ROOT / ".tmp" / "openai" / "description_batch_results.jsonl"
DEFAULT_DESCRIPTIONS = ROOT / "data" / "restaurant_descriptions.json"
API_BASE = "https://api.openai.com/v1"


def api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is required")
    return key


def api_get(path: str, decode_json: bool = True):
    request = urllib.request.Request(f"{API_BASE}{path}", headers={"Authorization": f"Bearer {api_key()}"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"OpenAI API error {error.code}: {detail}") from error
    return json.loads(body) if decode_json else body


def batch_id_from_metadata(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("batch", {}).get("id") or data.get("id") or ""


def parse_json_content(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I | re.S).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"description": content, "confidence": "low", "notes": "Model returned non-JSON content"}


def extract_descriptions(raw_path: Path) -> dict[str, dict[str, str]]:
    descriptions: dict[str, dict[str, str]] = {}
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        custom_id = item.get("custom_id", "")
        if not custom_id.startswith("description:"):
            continue
        restaurant_id = custom_id.split(":", 1)[1]
        response = item.get("response", {}).get("body", {})
        choices = response.get("choices") or []
        if not choices:
            continue
        content = choices[0].get("message", {}).get("content", "")
        parsed = parse_json_content(content)
        description = str(parsed.get("description") or "").strip()
        if description:
            descriptions[restaurant_id] = {
                "description": description,
                "confidence": str(parsed.get("confidence") or ""),
                "notes": str(parsed.get("notes") or ""),
            }
    return descriptions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", nargs="?", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--raw-out", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--descriptions-out", type=Path, default=DEFAULT_DESCRIPTIONS)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    batch_id = batch_id_from_metadata(args.metadata)
    if not batch_id:
        raise SystemExit(f"Could not find batch id in {args.metadata}")

    batch = api_get(f"/batches/{batch_id}")
    status = batch.get("status")
    print(f"Batch {batch_id} status: {status}")
    if status != "completed" and not args.force_download:
        print(json.dumps(batch, indent=2))
        return

    output_file_id = batch.get("output_file_id")
    if not output_file_id:
        raise SystemExit("Batch has no output_file_id yet")

    raw = api_get(f"/files/{output_file_id}/content", decode_json=False)
    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    args.raw_out.write_text(raw, encoding="utf-8")
    descriptions = extract_descriptions(args.raw_out)
    args.descriptions_out.parent.mkdir(parents=True, exist_ok=True)
    args.descriptions_out.write_text(json.dumps(descriptions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote raw results to {args.raw_out}")
    print(f"Wrote {len(descriptions)} descriptions to {args.descriptions_out}")


if __name__ == "__main__":
    main()
