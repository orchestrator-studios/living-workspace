#!/usr/bin/env python3
"""Validate every record in data/ against its schema in schemas/.

Dependency-free: implements the subset of JSON Schema the schemas use
(type, required, additionalProperties, enum, pattern, multipleOf, minimum,
maximum, exclusiveMinimum, minLength, minItems, oneOf, items, properties).

Usage:  python tools/validate.py
Exit 0 = all records valid; exit 1 = violations (printed).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FOR_DIR = {
    "clients": "client.schema.json",
    "projects": "project.schema.json",
    "time": "time_entry.schema.json",
    "invoices": "invoice.schema.json",
}

TYPES = {
    "object": dict, "array": list, "string": str,
    "boolean": bool, "null": type(None),
}


def check(value, schema, path, errors):
    t = schema.get("type")
    if t == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{path}: expected number, got {type(value).__name__}")
            return
    elif t is not None:
        if t == "boolean" and not isinstance(value, bool):
            errors.append(f"{path}: expected boolean")
            return
        if t != "boolean" and not isinstance(value, TYPES[t]):
            errors.append(f"{path}: expected {t}, got {type(value).__name__}")
            return

    if "oneOf" in schema:
        for sub in schema["oneOf"]:
            sub_errors: list[str] = []
            check(value, sub, path, sub_errors)
            if not sub_errors:
                break
        else:
            errors.append(f"{path}: matches no allowed alternative")
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if "pattern" in schema and isinstance(value, str) and not re.match(schema["pattern"], value):
        errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if "minLength" in schema and isinstance(value, str) and len(value) < schema["minLength"]:
        errors.append(f"{path}: shorter than minLength {schema['minLength']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "multipleOf" in schema and round(value / schema["multipleOf"], 9) % 1 != 0:
            errors.append(f"{path}: {value} not a multiple of {schema['multipleOf']}")
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: {value} not above {schema['exclusiveMinimum']}")

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing required field '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: unexpected field '{key}'")
        for key, sub in props.items():
            if key in value:
                check(value[key], sub, f"{path}.{key}", errors)

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                check(item, schema["items"], f"{path}[{i}]", errors)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def referential_checks(errors):
    """Cross-record rules the schemas alone can't express."""
    clients = {p.stem for p in (ROOT / "data/clients").glob("*.json")}
    projects = {p.stem: load(p) for p in (ROOT / "data/projects").glob("*.json")}
    invoices = {p.stem for p in (ROOT / "data/invoices").glob("*.json")}
    for pid, pr in projects.items():
        if pr["client_id"] not in clients:
            errors.append(f"{pid}: client_id {pr['client_id']} does not exist")
    for p in (ROOT / "data/time").glob("*.json"):
        te = load(p)
        if te["project_id"] not in projects:
            errors.append(f"{te['id']}: project_id {te['project_id']} does not exist")
        if te["billed"] and not te["invoice_id"]:
            errors.append(f"{te['id']}: billed but no invoice_id")
        if te["invoice_id"] and te["invoice_id"] not in invoices:
            errors.append(f"{te['id']}: invoice_id {te['invoice_id']} does not exist")


def main() -> int:
    errors: list[str] = []
    total = 0
    for subdir, schema_file in SCHEMA_FOR_DIR.items():
        schema = load(ROOT / "schemas" / schema_file)
        folder = ROOT / "data" / subdir
        if not folder.exists():
            continue
        for record_path in sorted(folder.glob("*.json")):
            total += 1
            check(load(record_path), schema, record_path.stem, errors)
    referential_checks(errors)
    if errors:
        print(f"INVALID — {len(errors)} violation(s) across {total} records:")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK — {total} records valid, referential integrity holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
