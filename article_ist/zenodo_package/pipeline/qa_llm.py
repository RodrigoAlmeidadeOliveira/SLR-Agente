"""LLM-assisted Quality Assessment for SLR PATHCAST.

Scores each of the 169 confirmed includes against the 8 QA criteria
(Dyba & Dingsoyr 2008, adapted) using Claude Haiku 4.5 via real-time API.

Inputs per study: title, abstract, ft_rationale, ft_evidence_tags.
Output: qa_assessment_llm.csv with QA1..QA8 (binary) + per-item rationale.

Usage:
    python -m pipeline.qa_llm --run             # score all 169
    python -m pipeline.qa_llm --run --limit 5   # smoke test
    python -m pipeline.qa_llm --merge           # merge into qa_assessment.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

FT_CSV = Path("results/screening/ft_screening_results.csv")
INCLUDED_CSV = Path("results/final_review/included_studies_current.csv")
QA_LLM_CSV = Path("results/qa_assessment_llm.csv")
QA_LLM_RAW_JSONL = Path("results/qa_assessment_llm_raw.jsonl")
QA_CSV = Path("results/qa_assessment.csv")
QA_XLSX = Path("results/qa_assessment.xlsx")
QA_SUMMARY_TXT = Path("results/qa_assessment_summary.txt")
QA_SUMMARY_TEX = Path("results/qa_assessment_summary.tex")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 700
N_WORKERS = 5
QA_KEYS = [f"QA{i}" for i in range(1, 9)]

SYSTEM_PROMPT = """You are an expert in evidence-based software engineering performing systematic literature review (SLR) quality assessment.

You score each study against 8 binary criteria (0 or 1) adapted from Dyba & Dingsoyr (2008). Be strict but fair: a 1 requires clear evidence in the provided text; ambiguity defaults to 0.

Criteria:
- QA1: Are the research objectives clearly stated? (1 if abstract or rationale states a research aim/question/goal)
- QA2: Is the software engineering context described in detail? (1 if specific SE setting is named: development, testing, CI/CD, repository mining, project management, etc.)
- QA3: Is the data source (event log / repository / dataset) described reproducibly? (1 if data origin is named: GitHub, Jira, SVN, specific projects, named industry partner, public dataset, etc.)
- QA4: Is the PM or stochastic technique formally defined? (1 if a specific technique is named: alpha miner, inductive miner, Markov chain, Petri net, conformance checking, Monte Carlo, etc.)
- QA5: Are results validated empirically? (1 if there is empirical evaluation: case study, experiment, real-data application; not pure conceptual/position paper)
- QA6: Are threats to validity discussed? (1 if limitations, threats, or generalizability concerns are mentioned)
- QA7: Is the study reproducible (data and/or code available)? (1 if dataset/code/replication package is mentioned, or open-source software is used; 0 if not stated)
- QA8: Are process model quality metrics reported? (1 if fitness, precision, generalization, recall, F1, accuracy, MAPE, RMSE, or similar evaluation metric is mentioned)

Output STRICTLY a single JSON object — no markdown, no preface — of the form:
{
  "QA1": 0,
  "QA2": 1,
  "QA3": 0,
  "QA4": 1,
  "QA5": 1,
  "QA6": 0,
  "QA7": 0,
  "QA8": 1,
  "rationale": "Short 1-2 sentence justification covering main signals used."
}
"""

USER_PROMPT_TEMPLATE = """Study to assess:

Title: {title}

Abstract:
{abstract}

Full-text screening rationale (from prior LLM screening):
{rationale}

Evidence tags identified: {tags}
Software context: {sw_ctx}
Stochastic method: {stoch}
Process data source: {data_src}

Score the 8 QA criteria. Return JSON only."""


def _sanitize(s: str, max_len: int = 2500) -> str:
    if not s:
        return "(not available)"
    s = str(s).strip()
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def build_user_prompt(paper: dict) -> str:
    return USER_PROMPT_TEMPLATE.format(
        title=_sanitize(paper.get("title", ""), 300),
        abstract=_sanitize(paper.get("abstract", ""), 2500),
        rationale=_sanitize(paper.get("ft_rationale", ""), 800),
        tags=_sanitize(paper.get("ft_evidence_tags", "") or paper.get("ta_evidence_tags", ""), 300),
        sw_ctx=_sanitize(paper.get("ft_software_context", "") or paper.get("ta_software_context", ""), 100),
        stoch=_sanitize(paper.get("ft_stochastic_method", "") or paper.get("ta_stochastic_method", ""), 100),
        data_src=_sanitize(paper.get("ft_process_data_source", "") or paper.get("ta_process_data_source", ""), 100),
    )


def _parse_response(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    blob = m.group(0) if m else text
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return {**{k: None for k in QA_KEYS}, "rationale": f"PARSE_ERROR: {text[:200]}"}
    out = {}
    for k in QA_KEYS:
        v = data.get(k)
        try:
            v_int = int(v)
            out[k] = 1 if v_int >= 1 else 0
        except (TypeError, ValueError):
            out[k] = None
    out["rationale"] = str(data.get("rationale", ""))[:600]
    return out


def score_one(paper: dict, client) -> dict:
    user_prompt = build_user_prompt(paper)
    last_err = None
    for attempt in range(1, 4):
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = msg.content[0].text if msg.content else ""
            parsed = _parse_response(text)
            parsed["raw_response"] = text
            return parsed
        except Exception as exc:
            last_err = exc
            logger.warning(f"[QA] {paper.get('internal_id')} attempt {attempt}/3 failed: {exc}")
            time.sleep(2 * attempt)
    return {**{k: None for k in QA_KEYS}, "rationale": f"API_ERROR: {last_err}", "raw_response": ""}


def _norm_doi(s: str) -> str:
    return (s or "").strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _norm_title(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def load_includes() -> list[dict]:
    """Includes the 169 confirmed studies, merged with FT screening abstracts.

    The canonical id source is `included_studies_current.csv` (has internal_id).
    Abstracts come from ft_screening_results.csv (matched by DOI or title).
    """
    if not INCLUDED_CSV.exists():
        raise FileNotFoundError(INCLUDED_CSV)
    if not FT_CSV.exists():
        raise FileNotFoundError(FT_CSV)

    # FT screening: index by DOI and by title for fuzzy enrichment
    ft_by_doi: dict[str, dict] = {}
    ft_by_title: dict[str, dict] = {}
    with open(FT_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            doi_n = _norm_doi(r.get("doi", ""))
            title_n = _norm_title(r.get("title", ""))
            if doi_n:
                ft_by_doi[doi_n] = r
            if title_n:
                ft_by_title[title_n] = r

    rows: list[dict] = []
    with open(INCLUDED_CSV, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            doi_n = _norm_doi(r.get("doi", ""))
            title_n = _norm_title(r.get("title", ""))
            ft = ft_by_doi.get(doi_n) or ft_by_title.get(title_n) or {}
            merged = dict(r)
            for k in (
                "abstract", "venue", "authors",
                "ft_rationale", "ft_evidence_tags", "ft_software_context",
                "ft_stochastic_method", "ft_forecast_target", "ft_process_data_source",
                "ta_evidence_tags", "ta_software_context",
                "ta_stochastic_method", "ta_forecast_target", "ta_process_data_source",
            ):
                if not (merged.get(k) or "").strip():
                    merged[k] = ft.get(k, "")
            rows.append(merged)
    return rows


def load_existing_llm() -> dict[str, dict]:
    if not QA_LLM_CSV.exists():
        return {}
    with open(QA_LLM_CSV, encoding="utf-8", newline="") as f:
        return {r["internal_id"]: r for r in csv.DictReader(f)}


def save_llm_csv(rows: list[dict]) -> None:
    QA_LLM_CSV.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "internal_id", "title", "doi", "year",
        *QA_KEYS, "qa_total", "qa_include",
        "qa_rationale", "qa_scored_at", "qa_model",
    ]
    with open(QA_LLM_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def append_raw(record: dict) -> None:
    QA_LLM_RAW_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(QA_LLM_RAW_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_scoring(limit: int | None = None, force: bool = False) -> None:
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed. pip install anthropic")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)

    includes = load_includes()
    existing = load_existing_llm() if not force else {}
    pending = [p for p in includes if p["internal_id"] not in existing]
    if limit:
        pending = pending[:limit]

    logger.info(f"[QA] {len(includes)} includes total, {len(existing)} already scored, {len(pending)} pending")
    if not pending:
        logger.info("[QA] Nothing to do.")
        return

    scored = list(existing.values())
    completed = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(score_one, p, client): p for p in pending}
        for fut in as_completed(futs):
            paper = futs[fut]
            res = fut.result()
            qa_vals = [res.get(k) for k in QA_KEYS]
            qa_clean = [v for v in qa_vals if v is not None]
            qa_total = sum(qa_clean) if qa_clean else None
            qa_include = (qa_total is not None and qa_total >= 4)

            row = {
                "internal_id": paper["internal_id"],
                "title": paper.get("title", ""),
                "doi": paper.get("doi", ""),
                "year": paper.get("year", ""),
                **{k: ("" if res.get(k) is None else res.get(k)) for k in QA_KEYS},
                "qa_total": "" if qa_total is None else qa_total,
                "qa_include": qa_include if qa_total is not None else "",
                "qa_rationale": res.get("rationale", ""),
                "qa_scored_at": datetime.now(timezone.utc).isoformat(),
                "qa_model": MODEL,
            }
            scored.append(row)
            append_raw({"paper_id": paper["internal_id"], **res})
            completed += 1
            if completed % 10 == 0 or completed == len(pending):
                elapsed = time.time() - t0
                rate = completed / elapsed if elapsed else 0
                eta = (len(pending) - completed) / rate if rate else 0
                logger.info(f"[QA] {completed}/{len(pending)} done | {rate:.2f}/s | ETA {eta:.0f}s")

            if completed % 25 == 0:
                save_llm_csv(scored)
                logger.info(f"[QA] checkpoint saved ({len(scored)} rows)")

    save_llm_csv(scored)
    logger.info(f"[QA] Done. {len(scored)} rows in {QA_LLM_CSV}")


def merge_into_qa_csv() -> None:
    """Merge LLM scores into the canonical qa_assessment.csv (preserves existing manual scores)."""
    import pandas as pd

    if not QA_LLM_CSV.exists():
        logger.error("Run scoring first.")
        sys.exit(1)

    llm = pd.read_csv(QA_LLM_CSV)
    logger.info(f"[QA] LLM scores: {len(llm)} rows")

    if QA_CSV.exists():
        canon = pd.read_csv(QA_CSV)
    else:
        ft = pd.read_csv(FT_CSV)
        inc = ft[ft["ft_decision"].astype(str).str.lower() == "include"].copy()
        canon = pd.DataFrame({
            "internal_id": inc["internal_id"],
            "nome_do_artigo": inc["title"],
            "doi": inc["doi"],
            "ano": inc["year"],
            "venue": inc["venue"],
            "fonte": inc["source_db"],
            "ft_decision": inc["ft_decision"],
            "ft_rationale": inc["ft_rationale"],
            "ft_matched_ic": inc["ft_matched_ic"],
            "ft_matched_ec": inc["ft_matched_ec"],
        })
        for k in QA_KEYS + ["qa_total", "qa_include", "qa_status", "qa_notes"]:
            canon[k] = pd.NA

    canon = canon.set_index("internal_id")
    llm_idx = llm.set_index("internal_id")

    new_canon_ids = [i for i in llm_idx.index if i not in canon.index]
    if new_canon_ids:
        from pathlib import Path
        ft = pd.read_csv(FT_CSV).set_index("internal_id")
        for nid in new_canon_ids:
            if nid in ft.index:
                row = ft.loc[nid]
                canon.loc[nid, "nome_do_artigo"] = row["title"]
                canon.loc[nid, "doi"] = row.get("doi", "")
                canon.loc[nid, "ano"] = row.get("year", "")
                canon.loc[nid, "venue"] = row.get("venue", "")
                canon.loc[nid, "fonte"] = row.get("source_db", "")
                canon.loc[nid, "ft_decision"] = row.get("ft_decision", "")
                canon.loc[nid, "ft_rationale"] = row.get("ft_rationale", "")
                canon.loc[nid, "ft_matched_ic"] = row.get("ft_matched_ic", "")
                canon.loc[nid, "ft_matched_ec"] = row.get("ft_matched_ec", "")

    for k in QA_KEYS:
        canon[k] = pd.to_numeric(canon[k], errors="coerce")

    overrides_kept = 0
    for iid, row in llm_idx.iterrows():
        canon_row_exists = iid in canon.index
        existing_status = str(canon.loc[iid, "qa_status"]) if canon_row_exists and "qa_status" in canon.columns else ""
        is_manual = canon_row_exists and existing_status in ("manual", "avaliado_manual")
        if is_manual:
            overrides_kept += 1
            continue
        for k in QA_KEYS:
            v = row.get(k)
            if pd.notna(v) and str(v).strip() != "":
                try:
                    canon.loc[iid, k] = int(v)
                except (TypeError, ValueError):
                    pass
        canon.loc[iid, "qa_notes"] = f"LLM-scored ({MODEL}): {row.get('qa_rationale', '')}"
        canon.loc[iid, "qa_status"] = "avaliado_llm"

    canon[QA_KEYS] = canon[QA_KEYS].apply(pd.to_numeric, errors="coerce")
    has_any = canon[QA_KEYS].notna().any(axis=1)
    canon.loc[has_any, "qa_total"] = canon.loc[has_any, QA_KEYS].fillna(0).sum(axis=1)
    canon.loc[~has_any, "qa_total"] = pd.NA
    qt = pd.to_numeric(canon["qa_total"], errors="coerce")
    canon["qa_include"] = qt.ge(4).where(qt.notna(), pd.NA)

    canon = canon.reset_index()
    canon.to_csv(QA_CSV, index=False, encoding="utf-8-sig")
    canon.to_excel(QA_XLSX, index=False)
    logger.info(f"[QA] Merged. {len(canon)} rows. Manual overrides preserved: {overrides_kept}")

    summary = compute_summary(canon)
    QA_SUMMARY_TXT.write_text(format_summary(summary), encoding="utf-8")
    QA_SUMMARY_TEX.write_text(format_summary_latex(summary), encoding="utf-8")
    print(format_summary(summary))


def compute_summary(df) -> dict:
    import math
    import pandas as pd
    df = df.copy()
    for k in QA_KEYS:
        df[k] = pd.to_numeric(df[k], errors="coerce")
    qt = pd.to_numeric(df["qa_total"], errors="coerce")
    assessed = qt.notna().sum()
    retained = (qt >= 4).sum()
    excluded = (qt < 4).sum()
    total = len(df)

    return {
        "studies_assessed": int(assessed),
        "studies_assessed_pct": float(assessed / total * 100) if total else 0.0,
        "score_gte_4": int(retained),
        "score_lt_4": int(excluded),
        "mean": float(qt.mean()) if assessed else math.nan,
        "std": float(qt.std(ddof=1)) if assessed > 1 else math.nan,
        "median": float(qt.median()) if assessed else math.nan,
        "q1": float(qt.quantile(0.25)) if assessed else math.nan,
        "q3": float(qt.quantile(0.75)) if assessed else math.nan,
        "total_included_set": int(total),
    }


def format_summary(s: dict) -> str:
    import math

    def f(v):
        return "TBD" if (v is None or (isinstance(v, float) and math.isnan(v))) else f"{v:.2f}"

    return "\n".join([
        f"Studies assessed: {s['studies_assessed']} ({s['studies_assessed_pct']:.1f}% of included set)",
        f"Studies with score >= 4/8: {s['score_gte_4']}",
        f"Studies with score < 4/8: {s['score_lt_4']}",
        f"Mean QA score: {f(s['mean'])} (SD = {f(s['std'])})",
        f"Median QA score: {f(s['median'])} (IQR = {f(s['q1'])}--{f(s['q3'])})",
        f"Total included set considered for QA: {s['total_included_set']}",
    ])


def format_summary_latex(s: dict) -> str:
    import math

    def f(v):
        return "TBD" if (v is None or (isinstance(v, float) and math.isnan(v))) else f"{v:.2f}"

    rows = [
        f"Studies assessed & {s['studies_assessed']} & Absolute count and {s['studies_assessed_pct']:.1f}\\% of included set \\\\",
        f"Studies with score $\\geq 4/8$ & {s['score_gte_4']} & Retained for synthesis \\\\",
        f"Studies with score $< 4/8$ & {s['score_lt_4']} & Excluded after QA \\\\",
        f"Mean QA score & {f(s['mean'])} & Mean and standard deviation ({f(s['std'])}) \\\\",
        f"Median QA score & {f(s['median'])} & Median and interquartile range ({f(s['q1'])}--{f(s['q3'])}) \\\\",
    ]
    return "\n".join([
        "\\begin{table}[htbp]",
        "\\centering",
        f"\\caption{{Quality-assessment results for the confirmed included set ($n = {s['total_included_set']}$; full QA applied). Auto-generated from \\texttt{{pipeline/qa\\_llm.py}}.}}",
        "\\label{tab:qa-results}",
        "\\begin{tabular}{lcp{6.5cm}}",
        "\\toprule",
        "\\textbf{QA Outcome} & \\textbf{Count} & \\textbf{Notes} \\\\",
        "\\midrule",
        *rows,
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="Score includes via LLM")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of papers (smoke test)")
    ap.add_argument("--force", action="store_true", help="Re-score all (ignore existing LLM CSV)")
    ap.add_argument("--merge", action="store_true", help="Merge LLM CSV into qa_assessment.csv")
    args = ap.parse_args()

    if args.run:
        run_scoring(limit=args.limit, force=args.force)
    if args.merge:
        merge_into_qa_csv()
    if not (args.run or args.merge):
        ap.print_help()


if __name__ == "__main__":
    main()
