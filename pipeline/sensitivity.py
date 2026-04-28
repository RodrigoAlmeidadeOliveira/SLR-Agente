"""Auxiliary-corpus sensitivity check for SLR PATHCAST.

Random-samples the deferred auxiliary corpus (papers in unique_papers.csv that
were *not* part of the operational working set), runs the T/A LLM screener on
the sample, and reports the include rate. The expected include count if the
full auxiliary corpus were screened can then be extrapolated.

Output:
  results/sensitivity/sample_aux.csv          — the random sample (n=N)
  results/sensitivity/sample_aux_screened.csv — LLM decisions
  results/sensitivity/sensitivity_report.txt
  results/sensitivity/sensitivity_report.tex
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

UNIQUE_CSV = Path("results/unique_papers.csv")
WS_CSV = Path("results/working_set/operational_screening_primary_unique.csv")
OUT_DIR = Path("results/sensitivity")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_CSV = OUT_DIR / "sample_aux.csv"
SCREENED_CSV = OUT_DIR / "sample_aux_screened.csv"
REPORT_TXT = OUT_DIR / "sensitivity_report.txt"
REPORT_TEX = OUT_DIR / "sensitivity_report.tex"

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512
N_WORKERS = 4
RANDOM_SEED = 20260428


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


def _load_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        for line in Path(".env").read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")
    return api_key


def build_sample(n: int = 200) -> None:
    unique = pd.read_csv(UNIQUE_CSV, encoding="utf-8-sig")
    ws = pd.read_csv(WS_CSV, encoding="utf-8-sig")
    ws_ids = set(ws["internal_id"].dropna().astype(str))
    aux = unique[~unique["internal_id"].astype(str).isin(ws_ids)].copy()
    logger.info(f"[Sens] Auxiliary corpus: {len(aux)} papers")

    sample = aux.sample(n=min(n, len(aux)), random_state=RANDOM_SEED).reset_index(drop=True)
    sample.to_csv(SAMPLE_CSV, index=False, encoding="utf-8")
    logger.info(f"[Sens] Sample of {len(sample)} saved to {SAMPLE_CSV}")


def _build_prompt(paper: dict) -> tuple[str, str]:
    from config.screening_criteria import SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    user = PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title") or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type=_safe(paper, "doc_type") or "N/A",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "N/A",
        abstract_source=_safe(paper, "abstract_source") or "missing_or_unverified",
    )
    return SYSTEM_PROMPT, user


def _parse_decision(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            d = str(data.get("decision", "")).lower().strip()
            if d not in ("include", "exclude", "maybe"):
                d = ""
            return {
                "decision": d,
                "rationale": str(data.get("rationale", ""))[:400],
                "matched_ic": "|".join(data.get("matched_ic") or []),
                "matched_ec": "|".join(data.get("matched_ec") or []),
            }
        except json.JSONDecodeError:
            pass
    return {"decision": "", "rationale": f"PARSE_ERROR: {text[:200]}", "matched_ic": "", "matched_ec": ""}


def screen_sample() -> None:
    import anthropic

    if not SAMPLE_CSV.exists():
        logger.error("Run --build first.")
        return

    sample = pd.read_csv(SAMPLE_CSV)
    existing = {}
    if SCREENED_CSV.exists():
        for r in pd.read_csv(SCREENED_CSV).to_dict("records"):
            d = str(r.get("ta_decision", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if d and raw != "ERROR":
                existing[r["internal_id"]] = r

    pending = [(i, row) for i, row in sample.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[Sens] {len(sample)} sample, {len(existing)} done, {len(pending)} pending")
    if not pending:
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        sys_p, user_p = _build_prompt(paper)
        for attempt in range(1, 4):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS, system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                )
                text = msg.content[0].text if msg.content else ""
                parsed = _parse_decision(text)
                return {
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    "year": paper.get("year", ""),
                    "source_db": paper.get("source_db", ""),
                    "ta_decision": parsed["decision"],
                    "ta_rationale": parsed["rationale"],
                    "ta_matched_ic": parsed["matched_ic"],
                    "ta_matched_ec": parsed["matched_ec"],
                    "raw": text[:500],
                }
            except Exception as exc:
                logger.warning(f"[Sens] iid={paper.get('internal_id')} attempt {attempt} failed: {exc}")
                time.sleep(2 * attempt)
        return {
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "year": paper.get("year", ""),
            "source_db": paper.get("source_db", ""),
            "ta_decision": "", "ta_rationale": "", "ta_matched_ic": "", "ta_matched_ec": "", "raw": "ERROR",
        }

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(score, ir): ir for ir in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 25 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[Sens] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(SCREENED_CSV, index=False)

    pd.DataFrame(results).to_csv(SCREENED_CSV, index=False)
    logger.info(f"[Sens] Saved: {SCREENED_CSV}")


def report(aux_total: int = 3807, ws_includes: int = 169) -> None:
    df = pd.read_csv(SCREENED_CSV)
    df["ta_decision"] = df["ta_decision"].fillna("").astype(str).str.lower().str.strip()
    n = len(df)
    inc = (df["ta_decision"] == "include").sum()
    exc = (df["ta_decision"] == "exclude").sum()
    mb = (df["ta_decision"] == "maybe").sum()
    err = ((df["ta_decision"] == "") | (df["raw"].astype(str) == "ERROR")).sum()

    inc_rate = inc / n if n else 0
    mb_rate = mb / n if n else 0
    expected_inc = inc_rate * aux_total
    expected_inc_ub = (inc + mb) / n * aux_total if n else 0  # upper bound assuming all maybe become include

    lines = [
        "SLR PATHCAST — Auxiliary-Corpus Sensitivity Check",
        "=" * 60,
        f"Sample size: {n} (random, seed={RANDOM_SEED})",
        f"Auxiliary corpus total: {aux_total}",
        f"Working-set confirmed includes: {ws_includes}",
        "",
        "T/A decisions on the sample:",
        f"  include: {inc} ({inc_rate*100:.1f}%)",
        f"  maybe:   {mb} ({mb_rate*100:.1f}%)",
        f"  exclude: {exc} ({exc/n*100:.1f}%)",
        f"  errors:  {err}",
        "",
        f"Expected new includes if full auxiliary screened: {expected_inc:.0f}",
        f"Upper bound (treating all maybe as potential include): {expected_inc_ub:.0f}",
        f"Sensitivity ratio (expected_new / current_includes): {expected_inc/ws_includes*100:.1f}%",
        f"Sensitivity ratio (upper bound / current_includes):  {expected_inc_ub/ws_includes*100:.1f}%",
        "",
        "Interpretation:",
    ]
    if expected_inc / ws_includes <= 0.05:
        lines.append("  Auxiliary corpus is unlikely to materially change the F1-F5 evidence base.")
    elif expected_inc / ws_includes <= 0.20:
        lines.append("  Auxiliary corpus may add a modest number of includes; consider full screening before camera-ready.")
    else:
        lines.append("  Auxiliary corpus likely contains a substantive number of additional includes; full screening recommended.")

    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Auxiliary-corpus sensitivity check. A random sample of $n$ papers from the deferred auxiliary corpus was re-screened with the same T/A LLM protocol used for the working set.}",
        "\\label{tab:sensitivity}",
        "\\begin{tabular}{lc}",
        "\\toprule",
        "Quantity & Value \\\\",
        "\\midrule",
        f"Sample size & {n} (seed={RANDOM_SEED}) \\\\",
        f"Auxiliary corpus total & {aux_total} \\\\",
        f"Working-set confirmed includes & {ws_includes} \\\\",
        f"Sample T/A include rate & {inc/n*100:.1f}\\% ($n_{{\\text{{inc}}}} = {inc}$) \\\\",
        f"Sample T/A maybe rate & {mb/n*100:.1f}\\% ($n_{{\\text{{maybe}}}} = {mb}$) \\\\",
        f"Sample T/A exclude rate & {exc/n*100:.1f}\\% ($n_{{\\text{{exc}}}} = {exc}$) \\\\",
        f"Expected new includes (point estimate) & {expected_inc:.0f} \\\\",
        f"Expected new includes (upper bound, maybe$\\to$include) & {expected_inc_ub:.0f} \\\\",
        f"Sensitivity ratio vs.\\ confirmed set (point) & {expected_inc/ws_includes*100:.1f}\\% \\\\",
        f"Sensitivity ratio vs.\\ confirmed set (upper) & {expected_inc_ub/ws_includes*100:.1f}\\% \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]
    REPORT_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--aux-total", type=int, default=3807)
    ap.add_argument("--ws-includes", type=int, default=169)
    args = ap.parse_args()

    if args.build:
        build_sample(n=args.n)
    if args.screen:
        screen_sample()
    if args.report:
        report(aux_total=args.aux_total, ws_includes=args.ws_includes)
    if not (args.build or args.screen or args.report):
        ap.print_help()


if __name__ == "__main__":
    main()
