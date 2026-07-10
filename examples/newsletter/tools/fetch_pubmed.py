#!/usr/bin/env python3
"""fetch_pubmed.py — the retrieval step (grown). Runs the stream query against PubMed
E-utilities for a date window and lands each new paper as a candidate article record.

Carries OVERVIEW rule 1: one record per PMID, ever — a PMID already in the record is
skipped, not re-ingested. The stream query below is this workspace's understanding of
"talc/asbestos litigation science" at retrieval time (KH's stream 10 analog); refine it
here, in place.

Usage:  python tools/fetch_pubmed.py --mindate 2026/07/02 --maxdate 2026/07/09 [--retmax 40]
"""
import argparse
import datetime
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import repo

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# The stream query: substance × litigation-relevant science.
QUERY = ('(talc[tiab] OR asbestos[tiab]) AND '
         '(mesothelioma[tiab] OR "ovarian cancer"[tiab] OR cancer[tiab] OR '
         'carcinogen*[tiab] OR exposure[tiab] OR litigation[tiab])')


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def search(mindate, maxdate, retmax):
    params = urllib.parse.urlencode({
        "db": "pubmed", "term": QUERY, "retmode": "json", "retmax": retmax,
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
    ap = argparse.ArgumentParser(description="Fetch the stream query window from PubMed.")
    ap.add_argument("--mindate", required=True, help="YYYY/MM/DD")
    ap.add_argument("--maxdate", required=True, help="YYYY/MM/DD")
    ap.add_argument("--retmax", type=int, default=40)
    args = ap.parse_args()

    known = {a["pmid"] for a in repo.load_all("article")}
    pmids = search(args.mindate, args.maxdate, args.retmax)
    print(f"query matched {len(pmids)} PubMed records in window")
    fresh = [p for p in pmids if p not in known]
    for p in set(pmids) - set(fresh):
        print(f"SKIP: PMID {p} already in the record")
    if not fresh:
        return
    today = datetime.date.today().isoformat()
    for details in fetch_details(fresh):
        rid = repo.next_id("article")
        repo.save("article", {"id": rid, "status": "candidate", "filter_reason": None,
                              "summary": None, "retrieved": today, **details})
        print(f"OK {rid} — PMID {details['pmid']}: {details['title'][:70]}")


if __name__ == "__main__":
    main()
