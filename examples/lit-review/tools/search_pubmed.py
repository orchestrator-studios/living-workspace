#!/usr/bin/env python3
"""Search PubMed and record the raw results — the workspace's path to the database.

Runs a query against PubMed via NCBI E-utilities (esearch for PMIDs, efetch for the
records) and writes one result record: the query, the date, the hit count, and every
hit verbatim — title, authors, year, venue, PMID, DOI, abstract, publication types.
Nothing is judged here; judging is the filters' job.

Usage:
    python tools/search_pubmed.py --query Q-01            # run a stored query record
    python tools/search_pubmed.py --term "..." [--out F]  # ad-hoc term
Options:
    --retmax N   cap on PMIDs retrieved (default 200)
    --out PATH   write the result record here instead of the next data/results/R-*.json
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERIES = ROOT / "data" / "queries"
RESULTS = ROOT / "data" / "results"

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
FETCH_BATCH = 100
PAUSE = 0.34  # stay under NCBI's 3-requests/second courtesy limit (no API key)


def _get(endpoint: str, params: dict) -> bytes:
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read()
        except Exception as err:  # transient NCBI hiccups are common; retry briefly
            last_err = err
            time.sleep(1 + attempt)
    raise SystemExit(f"PubMed request failed after 3 attempts: {last_err}")


def esearch(term: str, retmax: int) -> tuple[list[str], int]:
    """Return (pmids, total_count) for a PubMed query term."""
    raw = _get("esearch.fcgi", {"db": "pubmed", "term": term,
                                "retmax": retmax, "retmode": "json"})
    result = json.loads(raw)["esearchresult"]
    return result["idlist"], int(result["count"])


def _text(node) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def _parse_article(art: ET.Element) -> dict:
    year = _text(art.find(".//Journal/JournalIssue/PubDate/Year"))
    if not year:
        year = _text(art.find(".//Journal/JournalIssue/PubDate/MedlineDate"))[:4]
    authors = []
    for au in art.findall(".//AuthorList/Author"):
        last, initials = _text(au.find("LastName")), _text(au.find("Initials"))
        if last:
            authors.append(f"{last} {initials}".strip())
    doi = ""
    for aid in art.findall(".//ArticleIdList/ArticleId"):
        if aid.get("IdType") == "doi":
            doi = _text(aid)
    return {
        "pmid": _text(art.find(".//PMID")),
        "title": _text(art.find(".//Article/ArticleTitle")),
        "authors": authors,
        "year": year,
        "venue": _text(art.find(".//Journal/Title")),
        "doi": doi,
        "abstract": " ".join(_text(t) for t in art.findall(".//Abstract/AbstractText")).strip(),
        "publication_types": [_text(pt) for pt in art.findall(".//PublicationTypeList/PublicationType")],
    }


def efetch(pmids: list[str]) -> list[dict]:
    hits = []
    for i in range(0, len(pmids), FETCH_BATCH):
        time.sleep(PAUSE)
        raw = _get("efetch.fcgi", {"db": "pubmed", "retmode": "xml",
                                   "id": ",".join(pmids[i:i + FETCH_BATCH])})
        for art in ET.fromstring(raw).findall(".//PubmedArticle"):
            hits.append(_parse_article(art))
    return hits


def next_result_id() -> str:
    existing = [int(p.stem[2:]) for p in RESULTS.glob("R-*.json") if p.stem[2:].isdigit()]
    return f"R-{max(existing, default=0) + 1:02d}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--query", help="id of a query record in data/queries/ (e.g. Q-01)")
    src.add_argument("--term", help="ad-hoc PubMed query term")
    ap.add_argument("--retmax", type=int, default=200)
    ap.add_argument("--out", help="explicit output path (default: next data/results/R-*.json)")
    args = ap.parse_args()

    query_id = None
    term = args.term
    if args.query:
        query_file = QUERIES / f"{args.query}.json"
        if not query_file.exists():
            raise SystemExit(f"No query record {query_file.relative_to(ROOT)}")
        record = json.loads(query_file.read_text(encoding="utf-8"))
        query_id, term = record["id"], record["query"]

    pmids, count = esearch(term, args.retmax)
    hits = efetch(pmids)

    result_id = next_result_id()
    out = Path(args.out) if args.out else RESULTS / f"{result_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "id": result_id,
        "query_id": query_id,
        "database": "pubmed",
        "term": term,
        "date": date.today().isoformat(),
        "count": count,
        "returned": len(hits),
        "hits": hits,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    label = query_id or result_id
    suffix = f" (of {count} total)" if count > len(hits) else ""
    print(f"{label} → esearch: {count} PMIDs · efetch: {len(hits)} records{suffix} → {out}")


if __name__ == "__main__":
    main()
