"""Snowballing v2 (Wohlin 2014) via Semantic Scholar Graph API.

Distinct from pipeline/snowball.py (OpenAlex-based) — this version uses S2
forward+backward citations with a larger seed set, then runs the same T/A
LLM screener on dedup'd candidates. Outputs to results/snowball_v2/.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

INCLUDED_CSV = Path("results/final_review/included_studies_current.csv")
QA_CSV = Path("results/qa_assessment.csv")
UNIQUE_CSV = Path("results/unique_papers.csv")

OUT_DIR = Path("results/snowball_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SEEDS_CSV = OUT_DIR / "seeds.csv"
RAW_CITATIONS = OUT_DIR / "raw_citations.csv"
CANDIDATES_CSV = OUT_DIR / "candidates_unique.csv"
SCREENED_CSV = OUT_DIR / "candidates_screened.csv"
SUMMARY_TXT = OUT_DIR / "snowball_summary.txt"
SUMMARY_TEX = OUT_DIR / "snowball_summary.tex"

S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"
USER_AGENT = "SLR-PATHCAST/1.0 (mailto:rodrigoalmeidadeoliveira@gmail.com)"
TIMEOUT = 15
MODEL = "claude-haiku-4-5-20251001"


def _safe(d, k):
    v = d.get(k, "")
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def _norm_doi(doi: str) -> str:
    return doi.lower().strip().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _norm_title(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").lower().strip())[:120]


def build_seeds(top_n: int = 20):
    if not INCLUDED_CSV.exists():
        logger.error("included_studies_current.csv missing")
        return
    inc = pd.read_csv(INCLUDED_CSV, encoding="utf-8-sig")
    if QA_CSV.exists():
        qa = pd.read_csv(QA_CSV)
        qa["qa_total"] = pd.to_numeric(qa["qa_total"], errors="coerce")
        inc = inc.merge(qa[["internal_id", "qa_total"]], on="internal_id", how="left")
    else:
        inc["qa_total"] = 0
    inc = inc[inc["doi"].fillna("").astype(str).str.strip() != ""]
    inc = inc.sort_values(["qa_total", "year"], ascending=[False, False]).head(top_n)
    seeds = inc[["internal_id", "title", "doi", "year"]].copy()
    seeds.to_csv(SEEDS_CSV, index=False, encoding="utf-8")
    logger.info(f"[Snow2] seeds: {len(seeds)} top by QA score")
    print(seeds[["internal_id", "title", "year"]].to_string())


def _s2_get(endpoint: str, params: dict, max_retries: int = 4) -> dict | None:
    headers = {"User-Agent": USER_AGENT}
    api_key = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    for attempt in range(max_retries):
        try:
            r = requests.get(endpoint, headers=headers, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                time.sleep(5 + attempt * 5)
                continue
            return None
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def fetch_citations():
    if not SEEDS_CSV.exists():
        logger.error("Run --build-seeds first")
        return
    seeds = pd.read_csv(SEEDS_CSV)
    rows = []
    for _, seed in seeds.iterrows():
        doi = _norm_doi(_safe(seed, "doi"))
        if not doi:
            continue
        sid = f"DOI:{doi}"
        for direction, endpoint, key in (
            ("forward", "citations", "citingPaper"),
            ("backward", "references", "citedPaper"),
        ):
            res = _s2_get(f"{S2_BASE}/{quote(sid)}/{endpoint}",
                          {"fields": "title,year,authors,externalIds,abstract,venue", "limit": 1000})
            data = (res or {}).get("data") if res else None
            if not data:
                continue
            for hit in data:
                p = hit.get(key, {}) or {}
                rows.append({
                    "seed_iid": seed["internal_id"],
                    "direction": direction,
                    "title": p.get("title", ""),
                    "year": p.get("year", ""),
                    "doi": (p.get("externalIds") or {}).get("DOI", ""),
                    "abstract": p.get("abstract", ""),
                    "venue": p.get("venue", ""),
                })
        time.sleep(1)
        logger.info(f"[Snow2] seed {seed['internal_id']} | cumulative {len(rows)}")

    df = pd.DataFrame(rows)
    df.to_csv(RAW_CITATIONS, index=False)
    logger.info(f"[Snow2] raw citations: {len(df)}")


def deduplicate():
    if not RAW_CITATIONS.exists():
        return
    raw = pd.read_csv(RAW_CITATIONS)
    raw["doi_norm"] = raw["doi"].fillna("").astype(str).apply(_norm_doi)
    raw["title_norm"] = raw["title"].fillna("").astype(str).apply(_norm_title)

    unique = pd.read_csv(UNIQUE_CSV, encoding="utf-8-sig")
    unique["doi_norm"] = unique["doi"].fillna("").astype(str).apply(_norm_doi)
    unique["title_norm"] = unique["title"].fillna("").astype(str).apply(_norm_title)
    existing_dois = set(unique["doi_norm"]) - {""}
    existing_titles = set(unique["title_norm"]) - {""}

    raw["is_existing"] = (
        raw["doi_norm"].isin(existing_dois) |
        raw["title_norm"].isin(existing_titles)
    )
    new = raw[~raw["is_existing"]].copy()
    new = new.drop_duplicates(subset=["doi_norm"], keep="first")
    new = new.drop_duplicates(subset=["title_norm"], keep="first")
    new = new[new["title"].fillna("").astype(str).str.strip() != ""]
    new = new[new["title_norm"].astype(str).str.len() > 5]

    new["internal_id"] = ["snow_" + f"{i:05d}" for i in range(len(new))]
    new["source_db"] = "snowball_v2"
    cols = ["internal_id", "seed_iid", "direction", "title", "year", "doi", "abstract", "venue", "source_db"]
    new[cols].to_csv(CANDIDATES_CSV, index=False)
    logger.info(f"[Snow2] new candidates: {len(new)} (raw={len(raw)})")


def _load_api_key():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        for line in Path(".env").read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")
    return api_key


def _build_prompt(paper):
    from config.screening_criteria import SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    return SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title") or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type="article",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "snowball",
        abstract_source="snowball_s2",
    )


def _parse(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(0))
            return {
                "decision": str(d.get("decision", "")).lower().strip(),
                "rationale": str(d.get("rationale", ""))[:400],
                "matched_ic": "|".join(d.get("matched_ic") or []),
                "matched_ec": "|".join(d.get("matched_ec") or []),
            }
        except json.JSONDecodeError:
            pass
    return {"decision": "", "rationale": text[:200], "matched_ic": "", "matched_ec": ""}


def screen():
    import anthropic
    if not CANDIDATES_CSV.exists():
        deduplicate()
    if not CANDIDATES_CSV.exists():
        return
    cand = pd.read_csv(CANDIDATES_CSV)
    existing = {}
    if SCREENED_CSV.exists():
        for r in pd.read_csv(SCREENED_CSV).to_dict("records"):
            d = str(r.get("ta_decision", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if d and raw != "ERROR":
                existing[r["internal_id"]] = r
    pending = [(i, row) for i, row in cand.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[Snow2] screen: {len(cand)} candidates, {len(existing)} done, {len(pending)} pending")
    if not pending:
        report()
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        sys_p, user_p = _build_prompt(paper)
        for attempt in range(1, 4):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=512, system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                )
                text = msg.content[0].text if msg.content else ""
                p = _parse(text)
                return {
                    "internal_id": paper["internal_id"],
                    "seed_iid": paper.get("seed_iid", ""),
                    "direction": paper.get("direction", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    "year": paper.get("year", ""),
                    "abstract": paper.get("abstract", ""),
                    "ta_decision": p["decision"],
                    "ta_rationale": p["rationale"],
                    "ta_matched_ic": p["matched_ic"],
                    "ta_matched_ec": p["matched_ec"],
                    "raw": text[:500],
                }
            except Exception as exc:
                logger.warning(f"[Snow2] {paper['internal_id']} attempt {attempt}: {exc}")
                time.sleep(3 * attempt)
        return {"internal_id": paper["internal_id"], "ta_decision": "", "raw": "ERROR"}

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(score, ir): ir for ir in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 25 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[Snow2] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(SCREENED_CSV, index=False)
    pd.DataFrame(results).to_csv(SCREENED_CSV, index=False)
    report()


def report():
    if not SCREENED_CSV.exists():
        return
    df = pd.read_csv(SCREENED_CSV)
    df["ta_decision"] = df["ta_decision"].fillna("").astype(str).str.lower().str.strip()
    n = len(df)
    inc = (df["ta_decision"] == "include").sum()
    mb = (df["ta_decision"] == "maybe").sum()
    exc = (df["ta_decision"] == "exclude").sum()
    err = ((df["ta_decision"] == "") | (df["raw"].astype(str) == "ERROR")).sum()
    raw_n = pd.read_csv(RAW_CITATIONS).shape[0] if RAW_CITATIONS.exists() else 0
    cand_n = pd.read_csv(CANDIDATES_CSV).shape[0] if CANDIDATES_CSV.exists() else 0
    seeds_n = pd.read_csv(SEEDS_CSV).shape[0] if SEEDS_CSV.exists() else 0
    lines = [
        "SLR PATHCAST — Snowballing v2 (Wohlin 2014, Semantic Scholar)",
        "=" * 60,
        f"Seeds: {seeds_n} (top-N by QA score)",
        f"Raw citations (forward + backward): {raw_n}",
        f"After dedup: {cand_n}",
        f"T/A screened: {n}",
        f"  include: {inc}",
        f"  maybe:   {mb}",
        f"  exclude: {exc}",
        f"  errors:  {err}",
        "",
        f"NEW snowball includes (T/A): {inc}",
    ]
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    tex = [
        "\\begin{table}[htbp]", "\\centering",
        "\\caption{Snowballing pass (Wohlin 2014, S2 Graph API): forward + backward citation expansion from a seed set of top-QA working-set includes.}",
        "\\label{tab:snowball}",
        "\\begin{tabular}{lr}", "\\toprule",
        "Stage & Count \\\\", "\\midrule",
        f"Seeds (top-QA) & {seeds_n} \\\\",
        f"Raw citations & {raw_n} \\\\",
        f"After dedup vs primary corpus & {cand_n} \\\\",
        f"T/A include & {inc} \\\\",
        f"T/A maybe   & {mb} \\\\",
        f"T/A exclude & {exc} \\\\",
        "\\bottomrule", "\\end{tabular}", "\\end{table}",
    ]
    SUMMARY_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-seeds", action="store_true")
    ap.add_argument("--top-n", type=int, default=20)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--dedup", action="store_true")
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.build_seeds:
        build_seeds(args.top_n)
    if args.fetch:
        fetch_citations()
    if args.dedup:
        deduplicate()
    if args.screen:
        screen()
    if args.report:
        report()


if __name__ == "__main__":
    main()
