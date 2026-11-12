#!/usr/bin/env python3
"""Enrich venue + pub_type from local CSVs and OpenAlex (DOI).

Usage:
  python3 enrich_phase4_venues.py              # local harvest + OpenAlex for missing
  python3 enrich_phase4_venues.py --local-only
  python3 enrich_phase4_venues.py --limit 200
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

import requests

DIR = Path(__file__).resolve().parent
FULL = DIR / "phase4_rq3_extraction_template.csv"
PRIO = DIR / "phase4_rq3_priority_sheet.csv"
CACHE = DIR / "phase4_openalex_venue_cache.json"
ROOT = DIR.parents[1]  # SLR-Agente


def load_key() -> str:
    for p in (ROOT / ".env", DIR / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENALEX_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("OPENALEX_API_KEY", "")


def norm_doi(d: str) -> str:
    d = (d or "").strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I)
    return d.lower().rstrip(".")


def guess_pub_type(venue: str, oa_type: str = "") -> str:
    t = (oa_type or "").lower()
    if t in {"journal-article", "journal"}:
        return "journal"
    if t in {"proceedings-article", "proceedings", "conference"}:
        return "conference"
    if t in {"book-chapter", "book"}:
        return "other"
    if "dataset" in t or "posted-content" in t:
        return "other"
    v = (venue or "").lower()
    if not v:
        return ""
    if re.search(r"\bworkshop\b", v):
        return "workshop"
    if re.search(
        r"\b(journal|transactions|empir\.?\s*softw|information and software technology|"
        r"j\.\s*syst|software:\s*practice|acm comput\.?\s*surv|ieee trans)\b",
        v,
    ):
        return "journal"
    if re.search(
        r"\b(proceedings|conference|symposium|icse|icsme|msr|promise|ease|profes|xp |"
        r"agile|lecture notes)\b",
        v,
    ):
        return "conference"
    return ""


def harvest_local() -> dict[str, dict[str, str]]:
    meta: dict[str, dict[str, str]] = {}
    for p in DIR.rglob("*.csv"):
        try:
            rows = list(csv.DictReader(p.open(encoding="utf-8", errors="replace")))
        except Exception:
            continue
        if not rows:
            continue
        keys = rows[0].keys()
        idk = next((k for k in ("internal_id", "id", "study_id") if k in keys), None)
        vk = next(
            (
                k
                for k in (
                    "venue",
                    "container",
                    "container_title",
                    "source",
                    "journal",
                    "host_venue",
                )
                if k in keys
            ),
            None,
        )
        dk = "doi" if "doi" in keys else None
        if not vk:
            continue
        for r in rows:
            venue = (r.get(vk) or "").strip()
            if not venue:
                continue
            keys_out = []
            if idk and (r.get(idk) or "").strip():
                keys_out.append(r[idk].strip())
            if dk and norm_doi(r.get(dk) or ""):
                keys_out.append(norm_doi(r[dk]))
            for key in keys_out:
                cur = meta.setdefault(key, {})
                if not cur.get("venue"):
                    cur["venue"] = venue
    return meta


def oa_get(url: str, key: str) -> dict | None:
    headers = {"User-Agent": "mailto:rodrigoalmeidadeoliveira@gmail.com SLR-Agente venue enrich"}
    params = {"api_key": key} if key else None
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        if r.status_code == 404:
            return {"_error": "404"}
        if r.status_code != 200:
            return {"_error": f"HTTP {r.status_code}"}
        return r.json()
    except Exception as e:
        return {"_error": str(e)}


def venue_from_work(w: dict) -> tuple[str, str, str]:
    """return venue, oa_type, pub_type guess"""
    oa_type = (w.get("type") or "").replace("https://openalex.org/", "")
    # prefer primary_location source display_name
    loc = w.get("primary_location") or {}
    src = (loc.get("source") or {}) if isinstance(loc, dict) else {}
    venue = (src.get("display_name") or "").strip()
    if not venue:
        hv = w.get("host_venue") or {}
        venue = (hv.get("display_name") or "").strip()
    if not venue:
        # biblio
        venue = ((w.get("biblio") or {}).get("container") or "").strip()
    return venue, oa_type, guess_pub_type(venue, oa_type)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.05)
    args = ap.parse_args()

    key = load_key()
    local = harvest_local()
    cache: dict[str, dict] = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))

    rows = load_csv(FULL)
    filled_v = filled_p = oa_ok = oa_fail = 0
    todos = []
    for r in rows:
        need_v = not (r.get("venue") or "").strip()
        need_p = not (r.get("pub_type") or "").strip()
        if not need_v and not need_p:
            continue
        hit = local.get(r["internal_id"]) or local.get(norm_doi(r.get("doi") or ""))
        if hit and need_v and hit.get("venue"):
            r["venue"] = hit["venue"]
            need_v = False
            filled_v += 1
        if (r.get("venue") or "").strip() and need_p:
            g = guess_pub_type(r["venue"])
            if g:
                r["pub_type"] = g
                need_p = False
                filled_p += 1
        if (need_v or need_p) and norm_doi(r.get("doi") or ""):
            todos.append(r)

    print(f"local fill venue={filled_v} pub_type={filled_p}; OA queue={len(todos)}")
    if args.local_only:
        save_csv(FULL, rows)
        sync_priority(rows)
        summarize(rows)
        return

    if args.limit:
        todos = todos[: args.limit]

    for i, r in enumerate(todos, 1):
        doi = norm_doi(r.get("doi") or "")
        if doi in cache and not cache[doi].get("_error"):
            w = cache[doi]
        else:
            url = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}"
            w = oa_get(url, key) or {"_error": "empty"}
            cache[doi] = w
            if i % 50 == 0:
                CACHE.write_text(json.dumps(cache), encoding="utf-8")
                print(f"  … {i}/{len(todos)} cache={len(cache)}")
            time.sleep(args.sleep)

        if w.get("_error") or w.get("error"):
            oa_fail += 1
            continue
        venue, oa_type, ptype = venue_from_work(w)
        if venue and not (r.get("venue") or "").strip():
            r["venue"] = venue
            filled_v += 1
            oa_ok += 1
        if not (r.get("pub_type") or "").strip():
            g = ptype or guess_pub_type(r.get("venue") or "", oa_type)
            if g:
                r["pub_type"] = g
                filled_p += 1

    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    save_csv(FULL, rows)
    sync_priority(rows)
    print(f"done OA ok≈{oa_ok} fail={oa_fail}")
    summarize(rows)


def sync_priority(full_rows: list[dict[str, str]]) -> None:
    if not PRIO.exists():
        return
    by = {r["internal_id"]: r for r in full_rows}
    prio = load_csv(PRIO)
    for r in prio:
        src = by.get(r["internal_id"])
        if not src:
            continue
        for f in ("venue", "pub_type"):
            if src.get(f):
                r[f] = src[f]
    save_csv(PRIO, prio)


def summarize(rows: list[dict[str, str]]) -> None:
    from collections import Counter

    n = len(rows)
    nv = sum(1 for r in rows if (r.get("venue") or "").strip())
    np_ = sum(1 for r in rows if (r.get("pub_type") or "").strip())
    print(f"venue {nv}/{n} ({100*nv/n:.1f}%)  pub_type {np_}/{n} ({100*np_/n:.1f}%)")
    print("pub_type:", Counter((r.get("pub_type") or "∅") for r in rows).most_common())


if __name__ == "__main__":
    main()
