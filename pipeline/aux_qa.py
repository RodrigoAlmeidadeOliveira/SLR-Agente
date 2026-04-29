"""QA scoring for the 212 auxiliary-tier confirmed includes.

Mirrors pipeline/qa_llm.py rubric but operates on aux_ft_screened.csv
(papers with ft_decision=include) using their abstracts. Produces
results/auxiliary/aux_qa.csv and merges into a combined 381-paper QA view.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

AUX_FT_CSV = Path("results/auxiliary/aux_ft_screened.csv")
AUX_TA_CSV = Path("results/auxiliary/aux_ta_screened.csv")
QA_LLM_CSV = Path("results/qa_assessment_llm.csv")  # ws QA
AUX_QA_CSV = Path("results/auxiliary/aux_qa.csv")
COMBINED_QA_CSV = Path("results/auxiliary/qa_combined_381.csv")
SUMMARY_TXT = Path("results/auxiliary/aux_qa_summary.txt")
SUMMARY_TEX = Path("results/auxiliary/aux_qa_summary.tex")

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
{"QA1": 0, "QA2": 1, "QA3": 0, "QA4": 1, "QA5": 1, "QA6": 0, "QA7": 0, "QA8": 1, "rationale": "..."}
"""

USER_TEMPLATE = """Study to assess:

Title: {title}

Abstract:
{abstract}

Full-text screening rationale (from prior LLM screening):
{rationale}

ICs matched: {ic}

Score the 8 QA criteria. Return JSON only."""


def _safe(d, k):
    v = d.get(k, "")
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


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


def _build_user(paper):
    title = _safe(paper, "title")[:300]
    abstract = _safe(paper, "abstract")[:2500] or "(not available)"
    rationale = _safe(paper, "ft_rationale")[:800]
    ic = _safe(paper, "ft_matched_ic")
    return USER_TEMPLATE.format(title=title, abstract=abstract, rationale=rationale, ic=ic)


def _parse(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    blob = m.group(0) if m else text
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return {**{k: None for k in QA_KEYS}, "rationale": f"PARSE_ERROR: {text[:200]}"}
    out = {}
    for k in QA_KEYS:
        try:
            v = int(data.get(k))
            out[k] = 1 if v >= 1 else 0
        except (TypeError, ValueError):
            out[k] = None
    out["rationale"] = str(data.get("rationale", ""))[:600]
    return out


def run():
    import anthropic
    if not AUX_FT_CSV.exists():
        logger.error("Run aux FT first")
        return
    ft = pd.read_csv(AUX_FT_CSV)
    ft["ft_decision"] = ft["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    targets = ft[ft["ft_decision"] == "include"].copy()
    if AUX_TA_CSV.exists():
        ta = pd.read_csv(AUX_TA_CSV).set_index("internal_id")
        targets["abstract"] = targets["internal_id"].map(ta.get("abstract", pd.Series(dtype=object)))
    logger.info(f"[AuxQA] {len(targets)} papers")
    existing = {}
    if AUX_QA_CSV.exists():
        for r in pd.read_csv(AUX_QA_CSV).to_dict("records"):
            if r.get("qa_total", "") != "":
                existing[r["internal_id"]] = r
    pending = [(i, row) for i, row in targets.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[AuxQA] {len(existing)} done, {len(pending)} pending")
    if not pending:
        report()
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        user = _build_user(paper)
        for attempt in range(1, 4):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user}],
                )
                text = msg.content[0].text if msg.content else ""
                parsed = _parse(text)
                qa_vals = [parsed.get(k) for k in QA_KEYS]
                qa_clean = [v for v in qa_vals if v is not None]
                qa_total = sum(qa_clean) if qa_clean else None
                qa_inc = (qa_total is not None and qa_total >= 4)
                return {
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    "year": paper.get("year", ""),
                    **{k: ("" if parsed.get(k) is None else parsed.get(k)) for k in QA_KEYS},
                    "qa_total": "" if qa_total is None else qa_total,
                    "qa_include": qa_inc if qa_total is not None else "",
                    "qa_rationale": parsed.get("rationale", ""),
                    "qa_scored_at": datetime.now(timezone.utc).isoformat(),
                    "qa_model": MODEL,
                }
            except Exception as exc:
                logger.warning(f"[AuxQA] {paper.get('internal_id')} attempt {attempt}: {exc}")
                time.sleep(2 * attempt)
        return {"internal_id": paper.get("internal_id", ""), "qa_total": "", "qa_rationale": "API_ERROR"}

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
                logger.info(f"[AuxQA] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(AUX_QA_CSV, index=False)

    pd.DataFrame(results).to_csv(AUX_QA_CSV, index=False)
    logger.info(f"[AuxQA] Saved: {AUX_QA_CSV}")
    report()


def report():
    if not AUX_QA_CSV.exists():
        logger.error("Run --run first")
        return
    aux = pd.read_csv(AUX_QA_CSV)
    aux["qa_total"] = pd.to_numeric(aux["qa_total"], errors="coerce")
    n_aux = len(aux)
    aux_assessed = aux["qa_total"].notna().sum()
    aux_pass = (aux["qa_total"] >= 4).sum()
    aux_fail = (aux["qa_total"] < 4).sum()
    aux_mean = aux["qa_total"].mean()
    aux_sd = aux["qa_total"].std()

    # Combined
    combined = None
    ws_n = ws_pass = ws_fail = 0
    ws_mean = ws_sd = math.nan
    if QA_LLM_CSV.exists():
        ws = pd.read_csv(QA_LLM_CSV)
        ws["qa_total"] = pd.to_numeric(ws["qa_total"], errors="coerce")
        ws_n = len(ws)
        ws_pass = (ws["qa_total"] >= 4).sum()
        ws_fail = (ws["qa_total"] < 4).sum()
        ws_mean = ws["qa_total"].mean()
        ws_sd = ws["qa_total"].std()
        combined = pd.concat([ws.assign(origin="working_set"), aux.assign(origin="auxiliary")], ignore_index=True)
        combined.to_csv(COMBINED_QA_CSV, index=False)

    total_n = n_aux + ws_n
    total_pass = aux_pass + ws_pass
    total_fail = aux_fail + ws_fail
    if combined is not None:
        c = combined["qa_total"]
        total_mean = c.mean()
        total_sd = c.std()
    else:
        total_mean = total_sd = math.nan

    def f(v):
        return "TBD" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.2f}"

    lines = [
        "SLR PATHCAST — Combined QA (working-set + auxiliary)",
        "=" * 60,
        f"Working-set ({ws_n}): mean {f(ws_mean)} SD {f(ws_sd)} | pass {ws_pass} fail {ws_fail}",
        f"Auxiliary ({n_aux}):  mean {f(aux_mean)} SD {f(aux_sd)} | pass {aux_pass} fail {aux_fail}",
        f"Combined ({total_n}): mean {f(total_mean)} SD {f(total_sd)} | pass {total_pass} fail {total_fail}",
        "",
        f"Combined retention rate: {total_pass/total_n*100:.1f}% (>= 4/8 threshold)",
    ]
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Quality assessment combined across working-set and auxiliary tiers ($n = " + str(total_n) + "$).}",
        "\\label{tab:qa-combined}",
        "\\begin{tabular}{lrcccc}",
        "\\toprule",
        "Tier & $N$ & Mean & SD & $\\geq 4/8$ (pass) & $< 4/8$ (fail) \\\\",
        "\\midrule",
        f"Working-set & {ws_n} & {f(ws_mean)} & {f(ws_sd)} & {ws_pass} & {ws_fail} \\\\",
        f"Auxiliary   & {n_aux} & {f(aux_mean)} & {f(aux_sd)} & {aux_pass} & {aux_fail} \\\\",
        "\\midrule",
        f"\\textbf{{Combined}} & \\textbf{{{total_n}}} & \\textbf{{{f(total_mean)}}} & \\textbf{{{f(total_sd)}}} & \\textbf{{{total_pass}}} & \\textbf{{{total_fail}}} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]
    SUMMARY_TEX.write_text("\n".join(tex), encoding="utf-8")
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
