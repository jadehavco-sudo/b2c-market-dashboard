#!/usr/bin/env python3
"""Validate dashboard data files against the data contract.

Uses only the Python standard library.

Usage:
    python3 scripts/validate_data.py                         # validates data/latest.json
    python3 scripts/validate_data.py path/to/a.json          # validates given file(s)
    python3 scripts/validate_data.py --allow-legacy data/archive/*.json
                                                             # also accept schema 1.0 (old archives)

Exit code 0 when every file is valid, 1 otherwise.
See docs/data-contract.md for the full contract.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = REPO_ROOT / "data" / "latest.json"

CURRENT_SCHEMA_VERSION = "2.0"
LEGACY_SCHEMA_VERSIONS = {"1.0"}
EDITION_STATUSES = {"placeholder", "draft", "published"}

# ---------------------------------------------------------------------------
# Enums (schema 2.0)
# ---------------------------------------------------------------------------

SESSIONS = {"morning", "afternoon", "evening", "adhoc"}
SENTIMENTS = {"positive", "neutral", "negative", "mixed"}
DIRECTIONS = {"up", "down", "flat"}
STRENGTHS = {"strong", "moderate", "weak"}
LEVELS = {"high", "medium", "low"}
METRIC_CATEGORIES = {
    "fx", "gold", "equity", "rates", "commodity", "crypto",
    "macro", "retail", "ecommerce", "consumer", "camera", "other",
}
TRAFFIC_LIGHTS = {"green", "yellow", "red"}
TRENDS = {"improving", "stable", "worsening"}
SCENARIO_TYPES = {"base", "upside", "downside"}
CAMERA_MARKET_STATUSES = {"expanding", "stable", "contracting", "mixed"}
CAMERA_THEMES = {"camera", "smart_home", "security", "privacy", "technology", "regulation", "other"}
CAMERA_SIGNAL_TYPES = {"market", "consumer", "technology", "regulation", "supply", "other"}
CAMERA_SEGMENTS = {"home", "sme", "enterprise", "all", "other"}
CHANNEL_TYPES = {
    "ecommerce", "social_commerce", "retail_chain", "telco",
    "installer", "direct", "other",
}
PROMO_TYPES = {
    "discount", "bundle", "gift", "installment", "free_installation",
    "free_cloud", "voucher", "flash_sale", "other",
}
DEVELOPMENT_TYPES = {
    "product_launch", "pricing", "promotion", "channel", "partnership",
    "marketing", "service", "financial", "other",
}

MARKET_DASHBOARD_MAX = 12
MUST_READ_MAX = 5
SCENARIOS_COUNT = 3


# ---------------------------------------------------------------------------
# Tiny declarative schema engine
# ---------------------------------------------------------------------------
#
# Every field is a dict produced by one of the helpers below. Common options:
#   pub=True       -> must be non-null (and non-empty for strings/lists) when
#                     edition.status == "published". Otherwise null is allowed.
#   always=True    -> must be non-null (and non-empty) in every status.
#   optional=True  -> the key may be absent. By default every key must exist.
# Unknown keys are ignored so optional fields can be added later without a
# schema_version bump (see data contract, rule "field mới").


def _field(kind, **opts):
    opts["kind"] = kind
    return opts


def Text(**o):
    return _field("text", **o)


def Num(**o):
    return _field("number", **o)


def Int(**o):
    return _field("int", **o)


def Enum(values, **o):
    return _field("enum", values=values, **o)


def Date(**o):
    """ISO date (YYYY-MM-DD) or ISO datetime."""
    return _field("date", **o)


def DateTimeTZ(**o):
    """ISO datetime that includes a timezone."""
    return _field("datetime_tz", **o)


def Url(**o):
    return _field("url", **o)


def TextList(**o):
    return _field("text_list", **o)


def SourceIds(**o):
    """List of ids from `sources`; must be non-empty when published."""
    return _field("source_ids", **o)


def Obj(fields, check=None, **o):
    return _field("object", fields=fields, check=check, **o)


def List(fields, min_items=None, max_items=None, check=None, **o):
    return _field("list", fields=fields, min_items=min_items, max_items=max_items, check=check, **o)


# ---------------------------------------------------------------------------
# Item-level extra checks
# ---------------------------------------------------------------------------


def _check_metric(item, path, ctx):
    if not ctx["published"]:
        return
    if item.get("value") is None and not _nonempty(item.get("note")):
        ctx["errors"].append(
            f"{path}: 'value' là null trong bản tin 'published' thì phải có 'note' giải thích vì sao chưa có số liệu."
        )


def _check_pricing(item, path, ctx):
    if ctx["published"] and item.get("price") is None and not _nonempty(item.get("promo")):
        ctx["errors"].append(f"{path}: bản tin 'published' cần ít nhất 'price' hoặc 'promo' khác null.")


def _check_scenarios(items, path, ctx):
    types = [i.get("type") for i in items if isinstance(i, dict) and i.get("type") is not None]
    if len(types) != len(set(types)):
        ctx["errors"].append(f"{path}: 'type' của các kịch bản phải khác nhau (base/upside/downside).")
    if ctx["published"] and set(types) != SCENARIO_TYPES:
        ctx["errors"].append(f"{path}: bản tin 'published' phải có đủ 3 kịch bản base, upside, downside.")


# ---------------------------------------------------------------------------
# Schema 2.0
# ---------------------------------------------------------------------------

METRIC = {
    "id": Text(always=True),
    "label": Text(pub=True),
    "category": Enum(METRIC_CATEGORIES),
    "value": Num(),
    "unit": Text(),
    "change": Num(),
    "change_unit": Text(),
    "direction": Enum(DIRECTIONS),
    "period": Text(),
    "as_of": Date(optional=True),
    "note": Text(optional=True),
    "source_ids": SourceIds(),
}


def Metrics(**o):
    return List(METRIC, check_item=_check_metric, **o)


SCHEMA_V2 = {
    "schema_version": Text(always=True),
    "updated_at": DateTimeTZ(always=True),
    "edition": Obj({
        "id": Text(always=True),
        "number": Int(always=True),
        "title": Text(pub=True),
        "status": Enum(EDITION_STATUSES, always=True),
        "language": Text(),
        "session": Enum(SESSIONS, optional=True),
    }),
    "executive_summary": Obj({
        "headline": Text(pub=True),
        "summary": Text(pub=True),
        "key_points": TextList(pub=True),
        "overall_sentiment": Enum(SENTIMENTS),
        "data_gaps": TextList(),
    }),
    "market_dashboard": Metrics(max_items=MARKET_DASHBOARD_MAX, pub=True),
    "weekly_macro_watch": Obj({
        "period_start": Date(),
        "period_end": Date(),
        "summary": Text(pub=True),
        "themes": List({
            "id": Text(always=True),
            "theme": Text(pub=True),
            "detail": Text(pub=True),
            "direction": Enum(DIRECTIONS),
            "impact": Enum(LEVELS),
            "source_ids": SourceIds(),
        }),
        "key_metrics": Metrics(),
        "outlook": Text(),
    }),
    "macro_24h": Obj({
        "summary": Text(pub=True),
        "items": List({
            "id": Text(always=True),
            "title": Text(pub=True),
            "detail": Text(pub=True),
            "category": Text(),
            "impact": Enum(LEVELS),
            "occurred_at": Date(),
            "source_ids": SourceIds(),
        }),
    }),
    "financial_markets": Obj({
        "summary": Text(pub=True),
        "metrics": Metrics(),
        "highlights": List({
            "id": Text(always=True),
            "title": Text(pub=True),
            "detail": Text(pub=True),
            "impact": Enum(LEVELS),
            "source_ids": SourceIds(),
        }),
    }),
    "retail_consumer": Obj({
        "summary": Text(pub=True),
        "metrics": Metrics(),
        "trends": List({
            "id": Text(always=True),
            "trend": Text(pub=True),
            "detail": Text(pub=True),
            "direction": Enum(DIRECTIONS),
            "strength": Enum(STRENGTHS),
            "source_ids": SourceIds(),
        }),
    }),
    "b2c_traffic_lights": List({
        "id": Text(always=True),
        "name": Text(pub=True),
        "status": Enum(TRAFFIC_LIGHTS, pub=True),
        "trend": Enum(TRENDS),
        "explanation": Text(pub=True),
        "action": Text(pub=True),
        "source_ids": SourceIds(),
    }),
    "recommendations": List({
        "id": Text(always=True),
        "priority": Enum(LEVELS, pub=True),
        "issue": Text(pub=True),
        "evidence": Text(pub=True),
        "action": Text(pub=True),
        "owner": Text(pub=True),
        "deadline": Date(pub=True),
        "kpi": Text(pub=True),
        "source_ids": SourceIds(),
    }),
    "scenarios_7d": List({
        "id": Text(always=True),
        "type": Enum(SCENARIO_TYPES, pub=True),
        "scenario": Text(pub=True),
        "likelihood": Enum(LEVELS),
        "conditions": Text(pub=True),
        "consumer_impact": Text(pub=True),
        "b2c_impact": Text(pub=True),
        "fpt_camera_impact": Text(),
        "action": Text(pub=True),
        "source_ids": SourceIds(),
    }, min_items=SCENARIOS_COUNT, max_items=SCENARIOS_COUNT, check=_check_scenarios),
    "must_read": List({
        "id": Text(always=True),
        "title": Text(pub=True),
        "publisher": Text(pub=True),
        "url": Url(pub=True),
        "published_at": Date(),
        "summary": Text(pub=True),
        "why_read": Text(pub=True),
    }, max_items=MUST_READ_MAX),
    "events_next_24h": List({
        "id": Text(always=True),
        "event": Text(pub=True),
        "scheduled_at": Date(),
        "category": Text(),
        "importance": Enum(LEVELS, pub=True),
        "why_it_matters": Text(pub=True),
        "watch_for": Text(),
        "source_ids": SourceIds(),
    }),
    "decisions_today": List({
        "id": Text(always=True),
        "decision": Text(pub=True),
        "context": Text(pub=True),
        "options": TextList(),
        "recommended_option": Text(),
        "owner": Text(pub=True),
        "deadline": Date(pub=True),
        "urgency": Enum(LEVELS, pub=True),
        "source_ids": SourceIds(),
    }),
    "camera_market_watch": Obj({
        "summary": Text(pub=True),
        "market_status": Enum(CAMERA_MARKET_STATUSES),
        "key_metrics": Metrics(),
        "signals": List({
            "id": Text(always=True),
            "signal": Text(pub=True),
            "detail": Text(pub=True),
            "theme": Enum(CAMERA_THEMES, pub=True),
            "signal_type": Enum(CAMERA_SIGNAL_TYPES),
            "segment": Enum(CAMERA_SEGMENTS),
            "direction": Enum(DIRECTIONS),
            "strength": Enum(STRENGTHS),
            "source_ids": SourceIds(),
        }),
        "pricing_watch": List({
            "id": Text(always=True),
            "brand": Text(pub=True),
            "product": Text(pub=True),
            "segment": Enum(CAMERA_SEGMENTS),
            "channel": Text(),
            "price": Num(),
            "previous_price": Num(),
            "currency": Text(),
            "change_pct": Num(),
            "promo": Text(),
            "promo_type": Enum(PROMO_TYPES),
            "valid_until": Date(),
            "observed_at": Date(pub=True),
            "source_ids": SourceIds(),
        }, check_item=_check_pricing),
        "channel_watch": List({
            "id": Text(always=True),
            "channel": Text(pub=True),
            "channel_type": Enum(CHANNEL_TYPES),
            "development": Text(pub=True),
            "direction": Enum(DIRECTIONS),
            "implication_for_fpt_camera": Text(pub=True),
            "source_ids": SourceIds(),
        }),
        "demand_watch": List({
            "id": Text(always=True),
            "indicator": Text(pub=True),
            "detail": Text(pub=True),
            "segment": Enum(CAMERA_SEGMENTS),
            "value": Num(),
            "unit": Text(),
            "period": Text(),
            "direction": Enum(DIRECTIONS),
            "strength": Enum(STRENGTHS),
            "source_ids": SourceIds(),
        }),
        "fpt_camera_impact": Obj({
            "overall": Enum(SENTIMENTS, pub=True),
            "summary": Text(pub=True),
            "opportunities": TextList(),
            "risks": TextList(),
            "source_ids": SourceIds(),
        }),
    }),
    "competitor_watch": List({
        "id": Text(always=True),
        "competitor": Text(pub=True),
        "development": Text(pub=True),
        "development_type": Enum(DEVELOPMENT_TYPES),
        "channel": Text(),
        "pricing_or_promo": Text(),
        "threat_level": Enum(LEVELS, pub=True),
        "implication_for_fpt_camera": Text(pub=True),
        "suggested_response": Text(),
        "observed_at": Date(),
        "source_ids": SourceIds(),
    }),
    "sources": List({
        "id": Text(always=True),
        "title": Text(pub=True),
        "publisher": Text(pub=True),
        "url": Url(pub=True),
        "published_at": Date(optional=True),
        "accessed_at": Date(pub=True),
    }, pub=True),
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def parse_iso8601(value):
    """Return a datetime for an ISO 8601 date/datetime string, or None if invalid."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _nonempty(value):
    if value is None:
        return False
    if isinstance(value, (str, list)):
        return bool(value.strip() if isinstance(value, str) else value)
    return True


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_value(value, spec, path, ctx):
    errors = ctx["errors"]
    kind = spec["kind"]
    must_fill = spec.get("always") or (spec.get("pub") and ctx["published"])

    if value is None:
        if must_fill:
            reason = "" if spec.get("always") else " trong bản tin 'published'"
            errors.append(f"{path} không được null{reason}.")
        return

    if kind == "text":
        if not isinstance(value, str):
            errors.append(f"{path} phải là chuỗi hoặc null.")
        elif must_fill and not value.strip():
            errors.append(f"{path} không được rỗng.")
    elif kind == "number":
        if not _is_number(value):
            errors.append(f"{path} phải là số hoặc null.")
    elif kind == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{path} phải là số nguyên.")
    elif kind == "enum":
        if value not in spec["values"]:
            errors.append(f"{path} phải thuộc {sorted(spec['values'])} hoặc null, nhận {value!r}.")
    elif kind == "date":
        if parse_iso8601(value) is None:
            errors.append(f"{path} phải là ngày ISO 8601 (YYYY-MM-DD hoặc datetime), nhận {value!r}.")
    elif kind == "datetime_tz":
        parsed = parse_iso8601(value)
        if parsed is None or "T" not in value:
            errors.append(f"{path} phải là datetime ISO 8601, ví dụ 2026-09-23T00:00:00Z.")
        elif parsed.tzinfo is None:
            errors.append(f"{path} phải có múi giờ (khuyến nghị UTC, hậu tố 'Z').")
    elif kind == "url":
        if not isinstance(value, str) or not value.startswith(("http://", "https://")):
            errors.append(f"{path} phải là URL http(s).")
    elif kind in ("text_list", "source_ids"):
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            errors.append(f"{path} phải là list chuỗi.")
            return
        if kind == "source_ids":
            if ctx["published"] and not value:
                errors.append(f"{path} không được rỗng trong bản tin 'published' (mọi nội dung phải có nguồn).")
            for ref in value:
                ctx["refs"].append((path, ref))
        elif must_fill and not value:
            errors.append(f"{path} không được rỗng trong bản tin 'published'.")
    elif kind == "object":
        if not isinstance(value, dict):
            errors.append(f"{path} phải là object.")
            return
        check_fields(value, spec["fields"], path, ctx)
        if spec.get("check"):
            spec["check"](value, path, ctx)
    elif kind == "list":
        check_list(value, spec, path, ctx)
    else:  # pragma: no cover - programming error in the schema above
        raise ValueError(f"unknown kind {kind!r}")


def check_fields(obj, fields, path, ctx):
    for key, spec in fields.items():
        sub = f"{path}.{key}" if path else key
        if key not in obj:
            if not spec.get("optional"):
                ctx["errors"].append(f"Thiếu field bắt buộc: '{sub}'.")
            continue
        check_value(obj[key], spec, sub, ctx)


def check_list(value, spec, path, ctx):
    errors = ctx["errors"]
    if not isinstance(value, list):
        errors.append(f"{path} phải là list.")
        return
    if spec.get("pub") and ctx["published"] and not value:
        errors.append(f"{path} không được rỗng trong bản tin 'published'.")
    if spec.get("min_items") is not None and len(value) < spec["min_items"]:
        errors.append(f"{path} phải có ít nhất {spec['min_items']} phần tử (hiện có {len(value)}).")
    if spec.get("max_items") is not None and len(value) > spec["max_items"]:
        errors.append(f"{path} có tối đa {spec['max_items']} phần tử (hiện có {len(value)}).")

    seen_ids = set()
    for index, item in enumerate(value):
        where = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where} phải là object.")
            continue
        check_fields(item, spec["fields"], where, ctx)
        item_id = item.get("id")
        if item_id is not None:
            if item_id in seen_ids:
                errors.append(f"{where} có id trùng: {item_id!r}.")
            seen_ids.add(item_id)
        if spec.get("check_item"):
            spec["check_item"](item, where, ctx)
    if spec.get("check"):
        spec["check"](value, path, ctx)


def validate_v2(data):
    edition = data.get("edition")
    status = edition.get("status") if isinstance(edition, dict) else None
    ctx = {"errors": [], "refs": [], "published": status == "published"}

    check_fields(data, SCHEMA_V2, "", ctx)

    # Every referenced source must exist in `sources`.
    sources = data.get("sources")
    known = {s.get("id") for s in sources if isinstance(s, dict)} if isinstance(sources, list) else set()
    for path, ref in ctx["refs"]:
        if ref not in known:
            ctx["errors"].append(f"{path} tham chiếu nguồn không tồn tại: {ref!r}.")

    return ctx["errors"]


# ---------------------------------------------------------------------------
# Schema 1.0 (legacy, only for files already in data/archive/)
# ---------------------------------------------------------------------------

V1_REQUIRED_TOP_LEVEL = {
    "updated_at": str,
    "edition": dict,
    "executive_summary": dict,
    "market_metrics": list,
    "insights": list,
    "b2c_signals": list,
    "sources": list,
}

V1_REQUIRED_ITEM_KEYS = {
    "market_metrics": ("id", "label", "value", "unit", "change", "period", "source_ids"),
    "insights": ("id", "title", "description", "source_ids"),
    "b2c_signals": ("id", "signal", "description", "source_ids"),
    "sources": ("id", "title", "publisher", "url", "accessed_at"),
}


def validate_v1(data):
    errors = []
    for field, expected_type in V1_REQUIRED_TOP_LEVEL.items():
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

    for section, keys in V1_REQUIRED_ITEM_KEYS.items():
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

    source_ids = {s.get("id") for s in data["sources"] if isinstance(s, dict)}
    for section in ("market_metrics", "insights", "b2c_signals"):
        for index, item in enumerate(data[section]):
            if not isinstance(item, dict):
                continue
            for ref in item.get("source_ids") or []:
                if ref not in source_ids:
                    errors.append(f"{section}[{index}] tham chiếu nguồn không tồn tại: {ref!r}.")

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


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def validate(data, allow_legacy=False):
    """Return a list of error messages (empty when valid)."""
    if not isinstance(data, dict):
        return ["Root phải là một JSON object."]

    version = data.get("schema_version")
    if version == CURRENT_SCHEMA_VERSION:
        return validate_v2(data)
    if version in LEGACY_SCHEMA_VERSIONS:
        if allow_legacy:
            return validate_v1(data)
        return [
            f"schema_version {version!r} đã cũ; dữ liệu mới phải dùng {CURRENT_SCHEMA_VERSION!r}. "
            "Chỉ file archive cũ mới được kiểm tra với --allow-legacy."
        ]
    supported = sorted({CURRENT_SCHEMA_VERSION} | (LEGACY_SCHEMA_VERSIONS if allow_legacy else set()))
    return [f"schema_version không hợp lệ: {version!r} (hỗ trợ: {supported})."]


def check_archive_name(path, data):
    """Archive files must be named after `updated_at` (UTC, YYYY-MM-DDTHHMMSSZ.json)."""
    if path.parent.name != "archive" or not isinstance(data, dict):
        return []
    parsed = parse_iso8601(data.get("updated_at"))
    if parsed is None or parsed.tzinfo is None:
        return []  # already reported by the schema check
    expected = parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ") + ".json"
    if path.name != expected:
        return [f"Tên file archive phải khớp 'updated_at': mong đợi {expected!r}, nhận {path.name!r}."]
    return []


def validate_file(path, allow_legacy=False):
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return [f"Không tìm thấy file: {path}"]
    except json.JSONDecodeError as exc:
        return [f"JSON không hợp lệ (dòng {exc.lineno}, cột {exc.colno}): {exc.msg}"]
    return validate(data, allow_legacy=allow_legacy) + check_archive_name(Path(path), data)


def main(argv):
    args = argv[1:]
    allow_legacy = "--allow-legacy" in args
    paths = [Path(arg) for arg in args if arg != "--allow-legacy"] or [DEFAULT_FILE]
    failed = False
    for path in paths:
        errors = validate_file(path, allow_legacy=allow_legacy)
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
