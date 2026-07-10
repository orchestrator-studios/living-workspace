#!/usr/bin/env python3
"""fetch_pubmed.py — the retrieval step (grown). Runs the active retrieval_config
against PubMed E-utilities for a date window, lands each new paper as a candidate
article record, and writes one run record — the provenance of coverage.

The stream query is NOT here: it lives in data/retrieval_config/ (the schema is the
law; refining the stream is a data edit, visible on the issues view). This tool reads
the active config for pubmed, or the one named with --config.

Carries OVERVIEW rule 1: one record per PMID, ever — a PMID already in the record is
skipped, not re-ingested, and the run records what was skipped.

Usage:  python tools/fetch_pubmed.py [--config C-01]
                                     [--mindate 2026/07/02 --maxdate 2026/07/09]
                                     [--retmax 40]
        Dates default to the config's trailing window ending today; retmax defaults
        to the config's.
"""
import argparse
import datetime
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import repo

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def active_config(config_id):
    """The config this fetch runs: --config wins; otherwise the single active pubmed one."""
    if config_id:
        if not repo.exists("retrieval_config", config_id):
            raise SystemExit(f"REFUSED: no retrieval_config '{config_id}'")
        return repo.load("retrieval_config", config_id)
    live = [c for c in repo.load_all("retrieval_config")
            if c["active"] and c["source"] == "pubmed"]
    if len(live) != 1:
        raise SystemExit(f"REFUSED: {len(live)} active pubmed configs — "
                         f"need exactly one, or name one with --config")
    return live[0]


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def search(query, mindate, maxdate, retmax):
    params = urllib.parse.urlencode({
        "db": "pubmed", "term": query, "retmode": "json", "retmax": retmax,
        "datetype": "edat", "mindate": mindate, "maxdate": maxdate})
    payload = json.loads(get(f"{EUTILS}/esearch.fcgi?{params}"))
    return payload["esearchresult"]["idlist"]


def text(node):
    return "".join(node.itertext()).strip() if node is not None else ""


def fetch_details(pmids):
    params = urllib.parse.urlencode({"db": "pubmed", "retmode": "xml",
                                     "id": ",".join(pmids)})
    root = ET.fromstring(get(f"{EUTILS}/efetch.fcgi?{params}"))
    for node in root.findall(".//PubmedArticle"):
        cite = node.find("MedlineCitation")
        article = cite.find("Article")
        pubdate = article.find("Journal/JournalIssue/PubDate")
        date_bits = [text(pubdate.find(part)) for part in ("Year", "Month", "Day")] \
            if pubdate is not None else []
        authors = article.findall("AuthorList/Author")
        first = ""
        if authors:
            first = " ".join(filter(None, [text(authors[0].find("LastName")),
                                           text(authors[0].find("Initials"))]))
            if len(authors) > 1:
                first += " et al."
        yield {
            "pmid": text(cite.find("PMID")),
            "title": text(article.find("ArticleTitle")),
            "journal": text(article.find("Journal/Title")),
            "pub_date": " ".join(filter(None, date_bits)) or text(pubdate.find("MedlineDate")) if pubdate is not None else "",
            "authors": first,
            "abstract": " ".join(text(a) for a in article.findall("Abstract/AbstractText")).strip(),
        }


def main():
    ap = argparse.ArgumentParser(description="Fetch the stream window from PubMed.")
    ap.add_argument("--config", help="retrieval_config id; default: the active one")
    ap.add_argument("--mindate", help="YYYY/MM/DD; default: window_days before maxdate")
    ap.add_argument("--maxdate", help="YYYY/MM/DD; default: today")
    ap.add_argument("--retmax", type=int, help="default: the config's")
    args = ap.parse_args()

    config = active_config(args.config)
    today = datetime.date.today()
    maxdate = args.maxdate or today.strftime("%Y/%m/%d")
    mindate = args.mindate or (
        datetime.datetime.strptime(maxdate, "%Y/%m/%d").date()
        - datetime.timedelta(days=int(config["window_days"]))).strftime("%Y/%m/%d")
    retmax = args.retmax or int(config["retmax"])

    known = {a["pmid"] for a in repo.load_all("article")}
    pmids = search(config["query"], mindate, maxdate, retmax)
    print(f"{config['id']} ({config['name']}): matched {len(pmids)} PubMed records "
          f"in {mindate}..{maxdate}")
    fresh = [p for p in pmids if p not in known]
    skipped = sorted(set(pmids) - set(fresh))
    for p in skipped:
        print(f"SKIP: PMID {p} already in the record")

    run_id = repo.next_id("run")
    added = []
    for details in fetch_details(fresh):
        rid = repo.next_id("article")
        repo.save("article", {"id": rid, "status": "candidate", "filter_reason": None,
                              "summary": None, "retrieved": today.isoformat(),
                              "run_id": run_id, **details})
        added.append(rid)
        print(f"OK {rid} — PMID {details['pmid']}: {details['title'][:70]}")

    repo.save("run", {"id": run_id, "date": today.isoformat(), "config": config["id"],
                      "window_start": mindate.replace("/", "-"),
                      "window_end": maxdate.replace("/", "-"),
                      "matched": len(pmids), "added": added,
                      "skipped_pmids": skipped})
    print(f"RUN {run_id}: {len(pmids)} matched, {len(added)} added, "
          f"{len(skipped)} already known — recorded")


if __name__ == "__main__":
    main()
