"""EC5 PDF recovery — re-attempt OA retrieval for the 148 inaccessible papers.

Queries Semantic Scholar, OpenAlex, CORE, and Unpaywall (DOI-based) to find
open-access URLs for papers closed under EC5 (full text inaccessible despite
all retrieval attempts). Reports recovery rate.

No LLM calls; all sources are public OA discovery APIs.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

EC5_CSV = Path("results/final_review/pending_inaccessible_closed.csv")
OUT_DIR = Path("results/ec5_recovery")
OUT_DIR.mkdir(parents=True, exist_ok=True)
RECOVERY_CSV = OUT_DIR / "ec5_recovery_results.csv"
REPORT_TXT = OUT_DIR / "ec5_recovery_report.txt"
REPORT_TEX = OUT_DIR / "ec5_recovery_report.tex"

USER_AGENT = "SLR-PATHCAST/1.0 (mailto:rodrigoalmeidadeoliveira@gmail.com)"
TIMEOUT = 12
N_WORKERS = 4


def _safe(d: dict, k: str) -> str:
    v = d.get(k, "")
    if v is None:
        return ""
    try:
        import math
        if isinstance(v, float) and math.isnan(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _norm_doi(s: str) -> str:
    return s.lower().replace("https://doi.org/", "").replace("http://doi.org/", "").strip()


def query_unpaywall(doi: str) -> tuple[bool, str]:
    if not doi:
        return False, ""
    url = f"https://api.unpaywall.org/v2/{quote(doi)}?email=rodrigoalmeidadeoliveira@gmail.com"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        if r.status_code != 200:
            return False, ""
        data = r.json()
        oa_loc = data.get("best_oa_location") or {}
        pdf = oa_loc.get("url_for_pdf") or oa_loc.get("url") or ""
        if pdf:
            return True, pdf
    except Exception:
        return False, ""
    return False, ""


def query_semantic_scholar(doi: str, title: str) -> tuple[bool, str]:
    base = "https://api.semanticscholar.org/graph/v1/paper"
    url = ""
    if doi:
        url = f"{base}/DOI:{quote(doi)}"
    elif title:
        url = f"{base}/search?query={quote(title[:200])}&limit=1"
    if not url:
        return False, ""
    try:
        r = requests.get(
            url,
            params={"fields": "openAccessPdf,externalIds"},
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        if r.status_code != 200:
            return False, ""
        data = r.json()
        if "data" in data and data["data"]:
            data = data["data"][0]
        oa = data.get("openAccessPdf") or {}
        pdf = oa.get("url") or ""
        if pdf:
            return True, pdf
    except Exception:
        return False, ""
    return False, ""


def query_openalex(doi: str) -> tuple[bool, str]:
    if not doi:
        return False, ""
    url = f"https://api.openalex.org/works/doi:{quote(doi)}"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        if r.status_code != 200:
            return False, ""
        data = r.json()
        oa = data.get("open_access") or {}
        pdf = oa.get("oa_url") or ""
        if pdf:
            return True, pdf
        for loc in data.get("locations", []):
            if loc.get("is_oa") and loc.get("pdf_url"):
                return True, loc["pdf_url"]
    except Exception:
        return False, ""
    return False, ""


def query_core(title: str) -> tuple[bool, str]:
    if not title:
        return False, ""
    url = "https://api.core.ac.uk/v3/search/works"
    try:
        r = requests.post(
            url,
            json={"q": title[:200], "limit": 3},
            timeout=TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        if r.status_code != 200:
            return False, ""
        data = r.json()
        for hit in data.get("results", []):
            for url_field in ("downloadUrl", "fullTextLink", "fullText"):
                u = hit.get(url_field)
                if u and ".pdf" in u.lower():
                    return True, u
    except Exception:
        return False, ""
    return False, ""


def attempt_recover(paper: dict) -> dict:
    iid = _safe(paper, "internal_id")
    doi = _norm_doi(_safe(paper, "doi"))
    title = _safe(paper, "title")
    out = {
        "internal_id": iid,
        "title": title,
        "doi": doi,
        "year": _safe(paper, "year"),
        "unpaywall_found": False, "unpaywall_url": "",
        "semantic_scholar_found": False, "semantic_scholar_url": "",
        "openalex_found": False, "openalex_url": "",
        "core_found": False, "core_url": "",
        "recovered": False,
        "best_url": "",
    }
    for source, fn, args in (
        ("unpaywall", query_unpaywall, (doi,)),
        ("semantic_scholar", query_semantic_scholar, (doi, title)),
        ("openalex", query_openalex, (doi,)),
        ("core", query_core, (title,)),
    ):
        try:
            ok, url = fn(*args)
            out[f"{source}_found"] = ok
            out[f"{source}_url"] = url
            if ok and not out["best_url"]:
                out["best_url"] = url
                out["recovered"] = True
        except Exception:
            pass
        time.sleep(0.5)
    return out


def run() -> None:
    if not EC5_CSV.exists():
        logger.error(f"{EC5_CSV} not found")
        return
    ec5 = pd.read_csv(EC5_CSV)
    logger.info(f"[EC5] {len(ec5)} papers to attempt")

    existing = {}
    if RECOVERY_CSV.exists():
        for r in pd.read_csv(RECOVERY_CSV).to_dict("records"):
            existing[r["internal_id"]] = r

    pending = [r for _, r in ec5.iterrows() if r["internal_id"] not in existing]
    logger.info(f"[EC5] {len(existing)} done, {len(pending)} pending")
    if not pending:
        return

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(attempt_recover, p.to_dict()): p for p in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 10 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[EC5] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 25 == 0:
                pd.DataFrame(results).to_csv(RECOVERY_CSV, index=False)

    pd.DataFrame(results).to_csv(RECOVERY_CSV, index=False)
    logger.info(f"[EC5] Saved: {RECOVERY_CSV}")


def report() -> None:
    if not RECOVERY_CSV.exists():
        logger.error("Run --run first")
        return
    df = pd.read_csv(RECOVERY_CSV)
    n = len(df)
    rec = int(df["recovered"].fillna(False).astype(bool).sum())
    by_src = {}
    for src in ("unpaywall", "semantic_scholar", "openalex", "core"):
        by_src[src] = int(df[f"{src}_found"].fillna(False).astype(bool).sum())
    lines = [
        "SLR PATHCAST — EC5 (full-text inaccessible) Recovery Attempt",
        "=" * 60,
        f"EC5 papers re-checked: {n}",
        f"Recovered (at least one OA URL found): {rec} ({rec/n*100:.1f}%)",
        f"Still inaccessible: {n - rec} ({(n - rec)/n*100:.1f}%)",
        "",
        "By source (non-exclusive; a paper may be found in multiple sources):",
    ]
    for src, cnt in by_src.items():
        lines.append(f"  {src}: {cnt} ({cnt/n*100:.1f}%)")
    lines += [
        "",
        "Methodology:",
        "  Each EC5 paper was queried against four open-access discovery APIs",
        "  (Unpaywall, Semantic Scholar Graph API, OpenAlex, CORE). A paper is",
        "  marked as recovered if any source returns an OA URL.",
        "",
        "Note: recovery here means an OA URL was *discovered*. Actual download",
        "  and full-text screening of recovered URLs is the next step before",
        "  these papers can re-enter the included set.",
    ]
    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{EC5 recovery attempt against four open-access discovery APIs.}",
        "\\label{tab:ec5-recovery}",
        "\\begin{tabular}{lcc}",
        "\\toprule",
        "Source & Recovered & \\% of EC5 \\\\",
        "\\midrule",
    ]
    for src, cnt in by_src.items():
        label = src.replace("_", "\\_").title()
        tex.append(f"{label} & {cnt} & {cnt/n*100:.1f}\\% \\\\")
    tex += [
        "\\midrule",
        f"\\textbf{{Any source}} & \\textbf{{{rec}}} & \\textbf{{{rec/n*100:.1f}\\%}} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]
    REPORT_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.run:
        run()
    if args.report:
        report()
    if not (args.run or args.report):
        ap.print_help()


if __name__ == "__main__":
    main()
