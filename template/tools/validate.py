#!/usr/bin/env python3
"""validate.py — check every record in data/ against its schema. Part of the standard kit.

The kit ships the generic checker: a dependency-free implementation of the JSON Schema
subset workspace schemas use, run over every record in each mapped data/ folder. Two
things are the workspace's own, grown in place:

  - SCHEMA_FOR_DIR — which schema governs which folder; add a line as each schema lands
  - integrity_checks() — the cross-record rules no per-record schema can express
    (dedup, referential integrity, closure guarantees); grow them as the rules are stated

Usage:  python tools/validate.py        (exit 0 = clean; exit 1 = violations, printed)
"""
import json
import re
import sys

import repo

# data/<dir> → schemas/<file>. Grown as the workspace's schemas land.
SCHEMA_FOR_DIR = {}

TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def check(value, schema, path, errors):
    t = schema.get("type")
    if t == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{path}: expected number"); return
    elif t is not None:
        if t == "boolean" and not isinstance(value, bool):
            errors.append(f"{path}: expected boolean"); return
        if t != "boolean" and not isinstance(value, TYPES[t]):
            errors.append(f"{path}: expected {t}, got {type(value).__name__}"); return
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
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} above maximum {schema['maximum']}")
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


def integrity_checks(errors):
    # (grown: the workspace's cross-record rules — dedup, referential integrity,
    #  closure guarantees. Validation reads the raw files on purpose — it checks the
    #  substrate itself, not a query's answer — but paths still come from repo.)
    pass


def main() -> int:
    errors: list[str] = []
    total = 0
    for subdir, schema_file in SCHEMA_FOR_DIR.items():
        schema = load(repo.SCHEMAS / schema_file)
        folder = repo.DATA / subdir
        if not folder.exists():
            continue
        for record_path in sorted(folder.glob("*.json")):
            total += 1
            check(load(record_path), schema, record_path.stem, errors)
    integrity_checks(errors)
    if errors:
        print(f"INVALID — {len(errors)} violation(s) across {total} records:")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK — {total} records valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
