#!/usr/bin/env python3
"""Validate dashboard data files against the data contract.

Uses only the Python standard library.

Usage:
    python3 scripts/validate_data.py                 # validates data/latest.json
    python3 scripts/validate_data.py path/to/a.json  # validates given file(s)

Exit code 0 when every file is valid, 1 otherwise.
See docs/data-contract.md for the full contract.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = REPO_ROOT / "data" / "latest.json"

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
EDITION_STATUSES = {"placeholder", "draft", "published"}

REQUIRED_TOP_LEVEL = {
    "updated_at": str,
    "edition": dict,
    "executive_summary": dict,
    "market_metrics": list,
    "insights": list,
    "b2c_signals": list,
    "sources": list,
}

# Required keys for each item in the list sections.
REQUIRED_ITEM_KEYS = {
    "market_metrics": ("id", "label", "value", "unit", "change", "period", "source_ids"),
    "insights": ("id", "title", "description", "source_ids"),
    "b2c_signals": ("id", "signal", "description", "source_ids"),
    "sources": ("id", "title", "publisher", "url", "accessed_at"),
}


def parse_iso8601(value):
    """Return a datetime for an ISO 8601 string, or None if invalid."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate(data):
    """Return a list of error messages (empty when valid)."""
    errors = []

    if not isinstance(data, dict):
        return ["Root phải là một JSON object."]

    version = data.get("schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"schema_version không hợp lệ: {version!r} "
            f"(hỗ trợ: {sorted(SUPPORTED_SCHEMA_VERSIONS)})."
        )

    for field, expected_type in REQUIRED_TOP_LEVEL.items():
        if field not in data:
            errors.append(f"Thiếu field bắt buộc: '{field}'.")
        elif not isinstance(data[field], expected_type):
            errors.append(
                f"Field '{field}' phải có kiểu {expected_type.__name__}, "
                f"nhận được {type(data[field]).__name__}."
            )
    if errors:
        return errors

    updated_at = parse_iso8601(data["updated_at"])
    if updated_at is None:
        errors.append("'updated_at' phải là chuỗi ISO 8601, ví dụ 2026-09-23T00:00:00Z.")
    elif updated_at.tzinfo is None:
        errors.append("'updated_at' phải có múi giờ (khuyến nghị UTC, hậu tố 'Z').")

    edition = data["edition"]
    for key in ("id", "number", "title", "status"):
        if key not in edition:
            errors.append(f"Thiếu 'edition.{key}'.")
    status = edition.get("status")
    if "status" in edition and status not in EDITION_STATUSES:
        errors.append(f"'edition.status' phải thuộc {sorted(EDITION_STATUSES)}, nhận {status!r}.")

    summary = data["executive_summary"]
    for key in ("headline", "summary"):
        if not isinstance(summary.get(key), str):
            errors.append(f"'executive_summary.{key}' phải là chuỗi.")
    if not isinstance(summary.get("key_points", []), list):
        errors.append("'executive_summary.key_points' phải là list.")

    for section, keys in REQUIRED_ITEM_KEYS.items():
        seen_ids = set()
        for index, item in enumerate(data[section]):
            where = f"{section}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{where} phải là object.")
                continue
            for key in keys:
                if key not in item:
                    errors.append(f"{where} thiếu key '{key}'.")
            item_id = item.get("id")
            if item_id in seen_ids:
                errors.append(f"{where} có id trùng: {item_id!r}.")
            seen_ids.add(item_id)
            if "source_ids" in item and not isinstance(item["source_ids"], list):
                errors.append(f"{where}.source_ids phải là list.")

    # Every referenced source must exist in `sources`.
    source_ids = {s.get("id") for s in data["sources"] if isinstance(s, dict)}
    for section in ("market_metrics", "insights", "b2c_signals"):
        for index, item in enumerate(data[section]):
            if not isinstance(item, dict):
                continue
            for ref in item.get("source_ids") or []:
                if ref not in source_ids:
                    errors.append(f"{section}[{index}] tham chiếu nguồn không tồn tại: {ref!r}.")

    # A published edition must be backed by real data and sources.
    if status == "published":
        if not data["sources"]:
            errors.append("Bản tin 'published' phải có ít nhất một nguồn trong 'sources'.")
        for index, metric in enumerate(data["market_metrics"]):
            if isinstance(metric, dict):
                if metric.get("value") is None:
                    errors.append(f"market_metrics[{index}] 'published' nhưng 'value' là null.")
                if not metric.get("source_ids"):
                    errors.append(f"market_metrics[{index}] 'published' nhưng không có source_ids.")
        for section in ("insights", "b2c_signals"):
            for index, item in enumerate(data[section]):
                if isinstance(item, dict) and not item.get("source_ids"):
                    errors.append(f"{section}[{index}] 'published' nhưng không có source_ids.")
        for index, source in enumerate(data["sources"]):
            if isinstance(source, dict) and not str(source.get("url", "")).startswith(("http://", "https://")):
                errors.append(f"sources[{index}].url phải là URL http(s).")

    return errors


def validate_file(path):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return [f"Không tìm thấy file: {path}"]
    except json.JSONDecodeError as exc:
        return [f"JSON không hợp lệ (dòng {exc.lineno}, cột {exc.colno}): {exc.msg}"]
    return validate(data)


def main(argv):
    paths = [Path(arg) for arg in argv[1:]] or [DEFAULT_FILE]
    failed = False
    for path in paths:
        errors = validate_file(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
