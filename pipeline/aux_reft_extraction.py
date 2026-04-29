"""Extract data + QA-score the 23 re-FT includes (post-enrichment confirmations)."""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REFT_CSV = Path("results/auxiliary/aux_reft_enriched.csv")
EXTRACT_OUT = Path("results/auxiliary/aux_reft_extraction.csv")
QA_OUT = Path("results/auxiliary/aux_reft_qa.csv")

MODEL = "claude-haiku-4-5-20251001"
N_WORKERS = 2


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


def _ext_prompt(paper):
    return f"""Você é um pesquisador fazendo extração de dados para a SLR PATHCAST.

**Título:** {_safe(paper, 'title')}
**Ano:** {_safe(paper, 'year')}
**ICs:** {_safe(paper, 'ft_matched_ic')}
**Resumo:** {_safe(paper, 'abstract') or '(indisponível)'}

Retorne SOMENTE JSON válido:
{{
  "research_question": "1-2 frases",
  "study_type": "case_study | experiment | survey | tool | theoretical | simulation | mixed",
  "research_contribution": "discovery | conformance | enhancement | prediction | simulation | framework | hybrid",
  "pm_technique": "alpha | inductive_miner | heuristic | conformance_checking | social_network | declarative | other | none",
  "stochastic_technique": "markov_chain | stochastic_petri_net | monte_carlo | system_dynamics | other | none",
  "software_artifact": "commits | issues | ci_cd | ide_logs | vcs | jira | github | other | none",
  "software_process": "development | testing | maintenance | code_review | bug_fixing | deployment | requirements | other",
  "dataset_source": "open_source | industrial | academic | synthetic | not_specified",
  "dataset_public": "sim | não | parcial | não_mencionado",
  "tool_used": "nomes ou não_mencionado",
  "main_finding": "2-3 frases",
  "limitations": "1-2 frases ou não_mencionado",
  "replication_package": "sim | não | parcial | não_mencionado"
}}"""


QA_SYSTEM = """You are an expert in evidence-based software engineering performing systematic literature review (SLR) quality assessment. Score each study against 8 binary criteria (0 or 1) adapted from Dyba & Dingsoyr (2008).

Criteria QA1..QA8 (objectives, SE context, data source, technique, empirical, threats, reproducibility, metrics).

Output STRICTLY JSON: {"QA1":0,"QA2":1,"QA3":0,"QA4":1,"QA5":1,"QA6":0,"QA7":0,"QA8":1,"rationale":"..."}"""


QA_USER_TPL = """Title: {title}
Abstract: {abstract}
Rationale: {rationale}
Score JSON only."""


def _parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    blob = m.group(0) if m else text
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {}


def run():
    import anthropic
    if not REFT_CSV.exists():
        logger.error("re-FT csv missing")
        return
    reft = pd.read_csv(REFT_CSV)
    reft["ft_decision"] = reft["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    targets = reft[reft["ft_decision"] == "include"].copy()
    logger.info(f"[ReFTExt] targets: {len(targets)}")

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def both(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        # Extraction
        try:
            msg = client.messages.create(
                model=MODEL, max_tokens=900,
                messages=[{"role": "user", "content": _ext_prompt(paper)}],
            )
            ext_text = msg.content[0].text if msg.content else ""
            ext = _parse_json(ext_text)
        except Exception as e:
            ext = {}
            ext_text = f"ERROR: {e}"
        # QA
        try:
            user = QA_USER_TPL.format(
                title=_safe(paper, "title")[:300],
                abstract=_safe(paper, "abstract")[:2500],
                rationale=_safe(paper, "ft_rationale")[:600],
            )
            msg = client.messages.create(
                model=MODEL, max_tokens=600, system=QA_SYSTEM,
                messages=[{"role": "user", "content": user}],
            )
            qa_text = msg.content[0].text if msg.content else ""
            qa = _parse_json(qa_text)
        except Exception as e:
            qa = {}
            qa_text = f"ERROR: {e}"

        ext_row = {
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "year": paper.get("year", ""),
            "ft_matched_ic": paper.get("ft_matched_ic", ""),
            "abstract": paper.get("abstract", ""),
            **{k: str(ext.get(k, "")).strip() for k in ["research_question","study_type","research_contribution","pm_technique","stochastic_technique","software_artifact","software_process","dataset_source","dataset_public","tool_used","main_finding","limitations","replication_package"]},
            "raw": ext_text[:500],
        }
        qa_keys = [f"QA{i}" for i in range(1, 9)]
        qa_vals = []
        for k in qa_keys:
            try:
                v = int(qa.get(k))
                qa_vals.append(1 if v >= 1 else 0)
            except (TypeError, ValueError):
                qa_vals.append(None)
        qa_clean = [v for v in qa_vals if v is not None]
        qa_total = sum(qa_clean) if qa_clean else None
        qa_row = {
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "year": paper.get("year", ""),
            **{f"QA{i+1}": ("" if qa_vals[i] is None else qa_vals[i]) for i in range(8)},
            "qa_total": "" if qa_total is None else qa_total,
            "qa_include": (qa_total is not None and qa_total >= 4),
            "qa_rationale": str(qa.get("rationale", ""))[:600],
            "qa_scored_at": datetime.now(timezone.utc).isoformat(),
            "qa_model": MODEL,
        }
        return ext_row, qa_row

    ext_results = []
    qa_results = []
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(both, ir): ir for ir in targets.iterrows()}
        for fut in as_completed(futs):
            e, q = fut.result()
            ext_results.append(e)
            qa_results.append(q)
            completed += 1
            if completed % 5 == 0 or completed == len(targets):
                el = time.time() - t0
                logger.info(f"[ReFTExt] {completed}/{len(targets)} | {completed/el:.2f}/s")

    pd.DataFrame(ext_results).to_csv(EXTRACT_OUT, index=False)
    pd.DataFrame(qa_results).to_csv(QA_OUT, index=False)
    logger.info(f"[ReFTExt] Saved: {EXTRACT_OUT} + {QA_OUT}")

    # quick report
    qa_df = pd.DataFrame(qa_results)
    qa_df["qa_total"] = pd.to_numeric(qa_df["qa_total"], errors="coerce")
    print(f"\nReFT Extraction: {len(ext_results)} done")
    print(f"ReFT QA: mean {qa_df['qa_total'].mean():.2f} | pass {(qa_df['qa_total']>=4).sum()} | fail {(qa_df['qa_total']<4).sum()}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.run or True:
        run()
