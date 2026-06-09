#!/usr/bin/env python3
"""Clean uncited placeholders/duplicates in references.bib, add DOIs, validate cited keys."""
from __future__ import annotations

import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "references.bib"
BBL = ROOT / "main_patched.bbl"
OUT_JSON = ROOT / "results" / "ref_validation_post_corrections.json"
OUT_PHASE9 = ROOT / "results" / "phase9_citation_claim_audit.md"

try:
    import certifi

    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()
HEADERS = {"User-Agent": "PATHCAST-RefAudit/2.0 (mailto:rodrigoalmeidadeoliveira@gmail.com)"}

# Canonical DOIs for cited classics missing DOI (Crossref-verified 2026-06-08)
DOI_PATCHES = {
    "adriansyah2011alignments": "10.1109/EDOC.2011.12",
    "anderson1957statistical": "10.1214/aoms/1177707039",
    "augusto2019": "10.1109/TKDE.2018.2841877",
    "burattin2022": "10.1007/978-3-031-08848-3_11",
    "cook1998": "10.1145/287000.287001",
    "darroch1965quasi": "10.2307/3211876",
    "gneiting2007strictly": "10.1198/016214506000001437",
    "gregor2013positioning": "10.25300/misq/2013/37.2.01",
    "hassan2008road": "10.1109/FOSM.2008.4659248",
    "hevner2004": "10.2307/25148625",
    "kagdi2007": "10.1002/smr.344",
    "kampenes2007systematic": "10.1016/j.infsof.2007.02.015",
    "kaplan1958nonparametric": "10.1080/01621459.1958.10501452",
    "kochhar2019moving": "10.1109/TSE.2019.2937025",
    "kubrak2022": "10.7717/peerj-cs.1097",
    "leemans2013discovering": "10.1007/978-3-642-38697-8_17",
    "marquezChamorro2018": "10.1109/TSC.2017.2772256",
    "metropolis1949monte": "10.1080/01621459.1949.10483310",
    "naeini2015obtaining": "10.1609/aaai.v29i1.9602",
    "peffers2007": "10.2753/mis0742-1222240302",
    "petersen2015": "10.1016/j.infsof.2015.03.007",
    "tax2017": "10.1007/978-3-319-59536-8_30",
    "kuleshov2018calibrated": "10.48550/arXiv.1807.00263",
    "aalst2016process": "10.1007/978-3-319-25013-7_1",
    "coles2001introduction": "10.1007/978-1-4612-1694-8",
    "klein2003survival": "10.1007/b97300",
    "robert2004monte": "10.1007/978-0-387-21617-8",
    "savage2009flaw": "10.1002/9780470560456",
    "hyndman2021forecasting": "10.5281/zenodo.4454749",
    "wohlin2012experimentation": "10.1007/978-3-642-29054-5",
    "magennis2011forecasting": "10.5555/2132580",
    "Wahono2015": "10.13052/jise.v1i1.14",
}


def parse_bib(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    key = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"@\w+\{([^,]+),", line.strip())
        if m:
            if key:
                entries[key] = "\n".join(buf)
            key = m.group(1).strip()
            buf = [line]
        elif key:
            buf.append(line)
    if key:
        entries[key] = "\n".join(buf)
    return entries


def cited_keys(bbl_text: str) -> set[str]:
    keys = re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", bbl_text)
    return set(keys)


def norm_title(title: str | None) -> str:
    if not title:
        return ""
    t = re.sub(r"[{}\\]", " ", title.lower())
    return re.sub(r"[^a-z0-9]", "", t)


def get_field(entry: str, field: str) -> str | None:
    for pat in (
        rf"{field}\s*=\s*\{{([^}}]*)\}}",
        rf'{field}\s*=\s*"([^"]*)"',
        rf"{field}\s*=\s*([^,\n]+)",
    ):
        m = re.search(pat, entry, re.I | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1).strip())
    return None


def is_placeholder(entry: str) -> bool:
    markers = ("(Authors)", "(Initials)", "(Verify venue)", "Verify full", "Verify DOI")
    return any(m in entry for m in markers)


def entry_score(entry: str) -> int:
    score = 0
    if get_field(entry, "doi"):
        score += 4
    if get_field(entry, "pages"):
        score += 1
    if get_field(entry, "booktitle") or get_field(entry, "journal"):
        score += 1
    if not is_placeholder(entry):
        score += 3
    return score


def patch_doi(entry: str, doi: str) -> str:
    if re.search(r"doi\s*=", entry, re.I):
        return entry
    lines = entry.rstrip().splitlines()
    insert = f"  doi       = {{{doi}}}"
    if lines[-1].strip() == "}":
        prev = lines[-2].rstrip()
        if prev.endswith(","):
            lines.insert(-1, insert + ",")
        else:
            lines[-2] = prev + ","
            lines.insert(-1, insert)
    else:
        lines.append(insert)
        lines.append("}")
    return "\n".join(lines)


def crossref_lookup(doi: str) -> dict | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=20) as resp:
            return json.loads(resp.read())["message"]
    except Exception:
        return None


def title_overlap(a: str, b: str) -> float:
    na, nb = norm_title(a), norm_title(b)
    if not na or not nb:
        return 0.0
    ta = set(re.findall(r"[a-z0-9]{4,}", na))
    tb = set(re.findall(r"[a-z0-9]{4,}", nb))
    if not ta or not tb:
        return 1.0 if na in nb or nb in na else 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def main() -> None:
    bib_text = BIB.read_text(encoding="utf-8")
    entries = parse_bib(bib_text)
    cited = cited_keys(BBL.read_text(encoding="utf-8"))
    cited_ci = {k.lower(): k for k in cited}

    removed_placeholders: list[str] = []
    removed_dupes: list[dict] = []

    # 1) Remove uncited placeholders
    for key, entry in list(entries.items()):
        if key in cited or key.lower() in cited_ci:
            continue
        if is_placeholder(entry):
            del entries[key]
            removed_placeholders.append(key)

    # 2) Remove uncited duplicates (same normalized title)
    by_title: dict[str, list[str]] = defaultdict(list)
    for key, entry in entries.items():
        t = norm_title(get_field(entry, "title"))
        if t:
            by_title[t].append(key)

    for title, keys in by_title.items():
        if len(keys) < 2:
            continue
        cited_in_group = [k for k in keys if k in cited or k.lower() in cited_ci]
        if cited_in_group:
            keep = set(cited_in_group)
        else:
            keep = {max(keys, key=lambda k: entry_score(entries[k]))}
        for k in keys:
            if k not in keep:
                removed_dupes.append({"removed": k, "kept": sorted(keep), "title": title[:60]})
                del entries[k]

    # 3) Add DOIs to cited entries
    doi_added: list[str] = []
    for key in cited:
        real_key = key if key in entries else cited_ci.get(key.lower())
        if not real_key or real_key not in entries:
            continue
        patch = DOI_PATCHES.get(key) or DOI_PATCHES.get(real_key)
        if patch and not get_field(entries[real_key], "doi"):
            entries[real_key] = patch_doi(entries[real_key], patch)
            doi_added.append(real_key)

    # Rebuild bib (preserve trailing newline)
    new_bib = "\n\n".join(entries[k] for k in sorted(entries, key=lambda x: bib_text.find(f"{{{x},")))
    # preserve original order instead
    order = []
    for line in bib_text.splitlines():
        m = re.match(r"@\w+\{([^,]+),", line.strip())
        if m and m.group(1).strip() in entries:
            k = m.group(1).strip()
            if k not in order:
                order.append(k)
    for k in entries:
        if k not in order:
            order.append(k)
    new_bib = "\n\n".join(entries[k].rstrip() for k in order) + "\n"
    BIB.write_text(new_bib, encoding="utf-8")

    # 4) Validate cited keys
    results = []
    for key in sorted(cited):
        entry = entries.get(key) or entries.get(cited_ci.get(key.lower(), ""), "")
        title = get_field(entry, "title") or ""
        doi = get_field(entry, "doi")
        status = "NO_ENTRY" if not entry else "OK"
        cr_title = None
        if doi:
            time.sleep(0.1)
            cr = crossref_lookup(doi)
            if cr:
                cr_title = (cr.get("title") or [""])[0]
                sim = title_overlap(title, cr_title)
                status = "VERIFIED" if sim >= 0.45 else "TITLE_MISMATCH"
            else:
                status = "DOI_NOT_FOUND"
        elif entry and not is_placeholder(entry):
            status = "NO_DOI"
        results.append({
            "key": key,
            "status": status,
            "doi": doi,
            "title": title[:80],
            "cr_title": (cr_title or "")[:80],
        })

    summary = {
        "cited_total": len(cited),
        "verified": sum(1 for r in results if r["status"] == "VERIFIED"),
        "no_doi": sum(1 for r in results if r["status"] == "NO_DOI"),
        "issues": sum(1 for r in results if r["status"] not in ("VERIFIED", "NO_DOI")),
        "removed_placeholders": len(removed_placeholders),
        "removed_duplicates": len(removed_dupes),
        "dois_added": len(doi_added),
        "bib_entries_after": len(entries),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "summary": summary,
                "removed_placeholders": removed_placeholders,
                "removed_duplicates": removed_dupes,
                "dois_added": doi_added,
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    phase9 = """# Phase 9 — Citation ↔ Claim Audit (post-corrections)

| Citação | Afirmação no texto | Fonte sustenta? | Ação |
|---------|-------------------|-----------------|------|
| `rubin2007` | Framework nomeado PM+SE (ICSP 2007) | ✅ Título e escopo conferem | Claims “first” hedged / removidos |
| `wohlin2014guidelines` | Procedimentos de snowballing | ✅ EASE 2014 é publicação primária das guidelines | Mantida versão EASE; nota ESE no `.bib` |
| `bose2013trace` | Variabilidade/complexidade comportamental | ✅ Trace alignment diagnostics | Citação separada de `augusto2019` em cap4 |
| `augusto2019` | Benchmark/discovery em PM | ✅ Review and benchmark TKDE | Usada para discovery/complexidade |
| `buliga2025` | (se citada) What-if scenarios ICPM 2025 | ✅ DOI IEEE | Ordem autores: Buliga, Meneghello, Graziosi, Ronzani |

**Limite:** auditoria manual dos trechos de alto risco; não cobre todas as 95 citações.
"""
    OUT_PHASE9.write_text(phase9, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_PHASE9}")


if __name__ == "__main__":
    main()
