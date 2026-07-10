#!/usr/bin/env python3
"""Validate every record in data/ against its schema, plus the review's integrity rules.

The generic checker and the alignment backstop are the kit's; integrity_checks() is this
workspace's own, grown in place. Which schema governs which data/ folder is not declared
here — repo.py derives it from each schema's x-kind (the schema is the kind's single
declaration), and the backstop flags any data/ folder no schema declares. Dependency-free:
implements the subset of JSON Schema the schemas use, then checks the rules no per-record
schema can express:
  - DOI uniqueness (a paper enters the review once)
  - screening consistency (decisions carry criterion; exclusions carry reason)
  - citation closure: every finding cites a source that exists AND is included
  - referential integrity for themes and searches

Usage:  python tools/validate.py        (exit 0 = clean; exit 1 = violations, printed)
"""
import json
import re
import sys

import repo

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
    # utf-8-sig: tolerate a BOM from hand edits on Windows
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def alignment_checks(errors):
    """The kit's backstop for "the schema is the kind's single declaration":
    every schema declares its kind, and every data/ folder is governed by a schema —
    a folder outside the mapping would otherwise be skipped, silently unvalidated."""
    declared = set(repo.SCHEMA_FOR_KIND.values())
    if repo.SCHEMAS.exists():
        for path in sorted(repo.SCHEMAS.glob("*.schema.json")):
            if path.name not in declared:
                errors.append(f"schemas/{path.name}: declares no kind (missing x-kind)")
    if repo.DATA.exists():
        for folder in sorted(repo.DATA.iterdir()):
            if folder.is_dir() and folder.name not in repo.SCHEMA_FOR_KIND:
                errors.append(f"data/{folder.name}/: no schema declares this kind — "
                              f"its records would go unvalidated")


def integrity_checks(errors):
    # validation reads the raw files on purpose — it checks the substrate itself,
    # not a query's answer over it — but the paths still come from the data-access layer
    sources = {p.stem: load(p) for p in (repo.DATA / "sources").glob("*.json")}
    themes = {p.stem for p in (repo.DATA / "themes").glob("*.json")}
    searches = {p.stem for p in (repo.DATA / "searches").glob("*.json")}

    seen_dois = {}
    for sid, s in sources.items():
        doi = s["doi"].lower()
        if doi in seen_dois:
            errors.append(f"{sid}: duplicate DOI (already on {seen_dois[doi]})")
        seen_dois[doi] = sid
        st = s["screening"]
        if st["status"] in ("included", "excluded") and not st.get("criterion"):
            errors.append(f"{sid}: {st['status']} without recording the criterion")
        if st["status"] == "excluded" and not st.get("reason"):
            errors.append(f"{sid}: excluded without a reason")
        fv = s["found_via"]
        if fv.startswith("search:") and fv.split(":")[1] not in searches:
            errors.append(f"{sid}: found_via references unknown {fv}")

    for p in (repo.DATA / "findings").glob("*.json"):
        f = load(p)
        src = sources.get(f["source_id"])
        if src is None:
            errors.append(f"{f['id']}: cites {f['source_id']}, which does not exist")
        elif src["screening"]["status"] != "included":
            errors.append(f"{f['id']}: cites {f['source_id']}, which is "
                          f"{src['screening']['status']} — findings may only cite included sources")
        if f["theme_id"] and f["theme_id"] not in themes:
            errors.append(f"{f['id']}: theme {f['theme_id']} does not exist")

    for p in (repo.DATA / "searches").glob("*.json"):
        q = load(p)
        for sid in q["added"]:
            if sid not in sources:
                errors.append(f"{q['id']}: added source {sid} does not exist")


def main() -> int:
    errors: list[str] = []
    total = 0
    alignment_checks(errors)
    for kind, schema_file in sorted(repo.SCHEMA_FOR_KIND.items()):
        schema = load(repo.SCHEMAS / schema_file)
        folder = repo.DATA / kind
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
    print(f"OK — {total} records valid; citation closure holds "
          f"(no finding cites anything but an included source).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
