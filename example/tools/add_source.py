#!/usr/bin/env python3
"""Add a paper to the review. A paper enters the review ONCE — duplicates are refused.

Usage:
  python tools/add_source.py --title "..." --authors "A B; C D" --year 2024 \
      --venue "..." --doi 10.9999/x --found-via search:Q-01

The tool assigns the next S-id, checks the DOI against every source already in the
review, and creates the record unscreened. Screening is a separate, recorded decision
(tools/screen.py).
"""
import argparse
import sys

import repo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--authors", required=True, help='semicolon-separated: "Hartwell R; Osei K"')
    ap.add_argument("--year", required=True, type=int)
    ap.add_argument("--venue", required=True)
    ap.add_argument("--doi", required=True)
    ap.add_argument("--found-via", required=True, dest="found_via",
                    help="seeded | search:Q-NN | citation:S-NNN")
    args = ap.parse_args()

    for existing in repo.load_all("sources"):
        if existing["doi"].lower() == args.doi.lower():
            origin = existing["found_via"]
            origin = "the client's flagged list" if origin == "seeded" else origin
            print(f"REFUSED: DOI already in the review ({existing['id']}, added from {origin}).")
            return 1

    new_id = repo.next_id("sources")
    record = {
        "id": new_id,
        "title": args.title,
        "authors": [a.strip() for a in args.authors.split(";") if a.strip()],
        "year": args.year,
        "venue": args.venue,
        "doi": args.doi,
        "found_via": args.found_via,
        "screening": {"status": "unscreened"},
    }
    repo.save("sources", record)
    print(f"Added {new_id}: {args.title[:60]}… (unscreened)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
