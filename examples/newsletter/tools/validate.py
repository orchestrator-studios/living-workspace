#!/usr/bin/env python3
"""validate.py — check every record in data/ against its schema. Part of the standard kit.

The kit ships the generic checker and the alignment backstop: a dependency-free
implementation of the JSON Schema subset workspace schemas use, run over every record in
each governed data/ folder. Which schema governs which folder is not declared here —
repo.py derives it from each schema's x-kind (the schema is the kind's single
declaration), and the backstop flags any data/ folder no schema declares. One thing is
the workspace's own, grown in place:

  - integrity_checks() — the cross-record rules no per-record schema can express
    (dedup, referential integrity, closure guarantees); grow them as the rules are stated

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
    """The workspace's cross-record rules (grown) — OVERVIEW rules 1–4: one record per
    URL; every verdict carries its reason; an issue cites only included, summarized
    stories; a final issue carries its assembled body. Plus provenance (every article
    traces to a run, every run to a config) and coverage (issue windows tile, never
    overlap). Validation reads the raw files on purpose — it checks the substrate
    itself, not a query's answer — but paths still come from repo."""
    def records(kind):
        folder = repo.DATA / kind
        return [load(p) for p in sorted(folder.glob("*.json"))] if folder.exists() else []

    configs = {c["id"]: c for c in records("retrieval_config")}

    runs = {r["id"]: r for r in records("run")}
    for r in runs.values():
        if r["config"] not in configs:
            errors.append(f"{r['id']}: config {r['config']} does not exist")

    articles = {}
    seen_urls = {}
    for a in records("article"):
        articles[a["id"]] = a
        url = a["url"].lower()
        if url in seen_urls:
            errors.append(f"{a['id']}: URL already held by {seen_urls[url]} — "
                          f"one record per URL, ever")
        seen_urls[url] = a["id"]
        if a["status"] != "candidate" and not (a.get("filter_reason") or "").strip():
            errors.append(f"{a['id']}: {a['status']} without a filter_reason — "
                          f"every verdict carries its reason")
        if a["run_id"] not in runs:
            errors.append(f"{a['id']}: run {a['run_id']} does not exist — "
                          f"every article traces to the run that landed it")

    for r in runs.values():
        for aid in r["added"]:
            if aid not in articles:
                errors.append(f"{r['id']}: added article {aid} does not exist")

    issues = sorted(records("issue"), key=lambda i: i["week_start"])
    for prev, cur in zip(issues, issues[1:]):
        if cur["week_start"] <= prev["week_end"]:
            errors.append(f"{cur['id']}: window overlaps {prev['id']} "
                          f"({cur['week_start']} <= {prev['week_end']}) — "
                          f"issue windows tile, never overlap")
    for issue in issues:
        if issue["status"] == "final" and not (issue.get("body") or "").strip():
            errors.append(f"{issue['id']}: final without an assembled body — "
                          f"run tools/assemble_issue.py {issue['id']}")
        for aid in issue["articles"]:
            a = articles.get(aid)
            if a is None:
                errors.append(f"{issue['id']}: references {aid} — no such article")
            elif a["status"] != "included":
                errors.append(f"{issue['id']}: cites {aid}, which is {a['status']} — "
                              f"an issue cites only included articles")
            elif not a.get("summary"):
                errors.append(f"{issue['id']}: cites {aid}, which has no summary")


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
    print(f"OK — {total} records valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
