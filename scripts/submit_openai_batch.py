#!/usr/bin/env python3
"""Submit a prepared JSONL file to the OpenAI Batch API."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METADATA = ROOT / ".tmp" / "openai" / "batch_metadata.json"
API_BASE = "https://api.openai.com/v1"


def api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is required")
    return key


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"OpenAI API error {error.code}: {detail}") from error


def upload_file(path: Path) -> dict:
    boundary = f"----michelin-{secrets.token_hex(12)}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="purpose"\r\n\r\n')
    body.extend(b"batch\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'.encode())
    body.extend(b"Content-Type: application/jsonl\r\n\r\n")
    body.extend(path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        f"{API_BASE}/files",
        data=bytes(body),
        method="POST",
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"OpenAI file upload error {error.code}: {detail}") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args()

    if not args.jsonl.exists() or args.jsonl.stat().st_size == 0:
        raise SystemExit(f"Batch input is missing or empty: {args.jsonl}")

    uploaded = upload_file(args.jsonl)
    batch = request_json(
        "POST",
        f"{API_BASE}/batches",
        {
            "input_file_id": uploaded["id"],
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
            "metadata": {"project": "michelin-restaurants", "task": "restaurant-descriptions"},
        },
    )
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps({"file": uploaded, "batch": batch}, indent=2) + "\n", encoding="utf-8")
    print(f"Submitted batch {batch['id']} with input file {uploaded['id']}")
    print(f"Metadata saved to {args.metadata}")


if __name__ == "__main__":
    main()
