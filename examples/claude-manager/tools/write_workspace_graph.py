#!/usr/bin/env python3
"""write_workspace_graph.py — store the agent-mapped semantic edges for a workspace
(grown). The write path for the delegated map-workspace-references capability.

The deterministic reach graph is computed live in repo.workspace(); this persists the
extra edges an agent read out of capability prose. One record per workspace; writing again
replaces it (a re-map). workspace() merges these in, drawn dashed as source=agent.

Usage:  python tools/write_workspace_graph.py <workspace_id> --file edges.json [--model ...]
        edges.json = [{"from": "cap:research-row", "to": "schema:table", "kind": "about",
                       "note": "..."}, ...]  (node ids as they appear in the live graph)
"""
import argparse
import json
import sys
import time

import repo


def main() -> int:
    ap = argparse.ArgumentParser(description="Store a workspace's agent-mapped graph edges.")
    ap.add_argument("workspace_id")
    ap.add_argument("--file", required=True, help="JSON file: a list of edge objects")
    ap.add_argument("--model")
    args = ap.parse_args()

    known = {p.name for p in repo._discover_workspaces()}
    if args.workspace_id not in known:
        print(f"REFUSED: no workspace '{args.workspace_id}' (known: {sorted(known)})")
        return 1
    try:
        edges = json.loads(open(args.file, encoding="utf-8-sig").read())
    except (OSError, ValueError) as err:
        print(f"REFUSED: could not read edges: {err}")
        return 1
    if not isinstance(edges, list):
        print("REFUSED: edges file must be a JSON list")
        return 1

    # keep only well-formed edges whose endpoints are real nodes in the live graph
    node_ids = {n["id"] for n in repo.workspace(args.workspace_id)["graph"]["nodes"]}
    clean = []
    for e in edges:
        if not isinstance(e, dict) or not {"from", "to", "kind"} <= set(e):
            continue
        if e["from"] in node_ids and e["to"] in node_ids and e["from"] != e["to"]:
            clean.append({"from": e["from"], "to": e["to"], "kind": str(e["kind"]),
                          "note": e.get("note")})
    if not clean:
        print("REFUSED: no valid edges (endpoints must be node ids in the live graph)")
        return 1

    repo.save("wsgraph", {"id": args.workspace_id, "edges": clean,
                          "generated_at": repo._iso(time.time()), "model": args.model})
    print(f"OK mapped {len(clean)} semantic edges for {args.workspace_id} "
          f"({len(edges) - len(clean)} dropped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
