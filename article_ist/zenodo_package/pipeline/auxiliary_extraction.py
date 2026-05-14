"""Real-time data extraction for the 212 auxiliary-corpus FT-confirmed includes.

Mirrors pipeline/extract_llm.py prompt structure but uses sync API (faster
turnaround for ~200 papers). Output: results/auxiliary/aux_extraction.csv —
same column structure as results/extraction/extraction_template.csv.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

AUX_FT_CSV = Path("results/auxiliary/aux_ft_screened.csv")
AUX_TA_CSV = Path("results/auxiliary/aux_ta_screened.csv")  # for abstract source
OUT_CSV = Path("results/auxiliary/aux_extraction.csv")
COMBINED_CSV = Path("results/auxiliary/extraction_combined_381.csv")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
N_WORKERS = 2

EXTRACTION_FIELDS = [
    "research_question", "study_type", "research_contribution",
    "pm_technique", "stochastic_technique", "software_artifact",
    "software_process", "dataset_source", "dataset_public",
    "tool_used", "main_finding", "limitations", "replication_package",
]


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


def _build_prompt(paper: dict) -> str:
    title = _safe(paper, "title")
    authors = _safe(paper, "authors") or "não disponível"
    year = _safe(paper, "year")
    venue = _safe(paper, "venue") or "não disponível"
    ics = _safe(paper, "ft_matched_ic") or _safe(paper, "ta_matched_ic")
    abstract = _safe(paper, "abstract")

    if abstract:
        content = f"\n**Resumo:**\n{abstract}\n"
    else:
        content = "\n*(Resumo indisponível — usar título/venue/ICs)*\n"

    return f"""Você é um pesquisador fazendo extração de dados para a SLR PATHCAST sobre Process Mining e Modelagem Estocástica em Processos de Software.

**Título:** {title}
**Autores:** {authors}
**Ano:** {year}  |  **Venue:** {venue}
**Critérios de inclusão atendidos:** {ics}
{content}
Retorne SOMENTE um objeto JSON válido com exatamente estes campos:

{{
  "research_question": "pergunta de pesquisa principal (1-2 frases)",
  "study_type": "case_study | experiment | survey | tool | theoretical | simulation | mixed",
  "research_contribution": "discovery | conformance | enhancement | prediction | simulation | framework | hybrid (múltiplos separados por |)",
  "pm_technique": "alpha | inductive_miner | heuristic | conformance_checking | social_network | declarative | other | none (múltiplos por |)",
  "stochastic_technique": "markov_chain | stochastic_petri_net | monte_carlo | system_dynamics | other | none (múltiplos por |)",
  "software_artifact": "commits | issues | ci_cd | ide_logs | vcs | jira | github | other | none (múltiplos por |)",
  "software_process": "development | testing | maintenance | code_review | bug_fixing | deployment | requirements | other (múltiplos por |)",
  "dataset_source": "open_source | industrial | academic | synthetic | not_specified",
  "dataset_public": "sim | não | parcial | não_mencionado",
  "tool_used": "nomes das ferramentas (ex: ProM, pm4py, Disco) ou não_mencionado",
  "main_finding": "principal resultado/contribuição (2-3 frases)",
  "limitations": "limitações reportadas (1-2 frases) ou não_mencionado",
  "replication_package": "sim | não | parcial | não_mencionado"
}}

Responda APENAS com o JSON, sem texto adicional."""


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    blob = m.group(0) if m else text
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {}


def run() -> None:
    import anthropic

    if not AUX_FT_CSV.exists():
        logger.error("Run aux FT first")
        return

    ft = pd.read_csv(AUX_FT_CSV)
    ft["ft_decision"] = ft["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    targets = ft[ft["ft_decision"] == "include"].copy()

    # enrich with abstract from aux_ta
    if AUX_TA_CSV.exists():
        ta = pd.read_csv(AUX_TA_CSV).set_index("internal_id")
        targets["abstract"] = targets["internal_id"].map(ta.get("abstract", pd.Series(dtype=object)))
        targets["authors"] = targets["internal_id"].map(ta.get("authors", pd.Series(dtype=object)) if "authors" in ta.columns else pd.Series(dtype=object))
        targets["venue"] = targets["internal_id"].map(ta.get("venue", pd.Series(dtype=object)) if "venue" in ta.columns else pd.Series(dtype=object))

    logger.info(f"[AuxExt] {len(targets)} papers to extract")

    existing = {}
    if OUT_CSV.exists():
        for r in pd.read_csv(OUT_CSV).to_dict("records"):
            if str(r.get("main_finding", "")).strip():
                existing[r["internal_id"]] = r

    pending = [(i, row) for i, row in targets.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[AuxExt] {len(existing)} done, {len(pending)} pending")
    if not pending:
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def extract(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        prompt = _build_prompt(paper)
        for attempt in range(1, 5):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = msg.content[0].text if msg.content else ""
                data = _parse(text)
                out = {
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    "year": paper.get("year", ""),
                    "source_db": paper.get("source_db", ""),
                    "ft_matched_ic": paper.get("ft_matched_ic", ""),
                    "abstract": paper.get("abstract", ""),
                }
                for f in EXTRACTION_FIELDS:
                    v = data.get(f, "")
                    out[f] = str(v).strip() if v else ""
                out["raw"] = text[:600]
                return out
            except Exception as exc:
                logger.warning(f"[AuxExt] iid={paper.get('internal_id')} attempt {attempt} failed: {exc}")
                time.sleep(3 * attempt)
        return {
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "raw": "ERROR",
        }

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(extract, ir): ir for ir in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 25 == 0 or completed == len(pending):
                el = time.time() - t0
                rate = completed / el if el else 0
                eta = (len(pending) - completed) / rate if rate else 0
                logger.info(f"[AuxExt] {completed}/{len(pending)} | {rate:.2f}/s | ETA {eta/60:.1f}min")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(OUT_CSV, index=False)

    pd.DataFrame(results).to_csv(OUT_CSV, index=False)
    logger.info(f"[AuxExt] Saved: {OUT_CSV}")


def merge_with_working_set() -> None:
    """Merge aux extraction with the working-set extraction_template.csv to produce
    a unified 381-paper extraction view."""
    ws = pd.read_csv("results/extraction/extraction_template.csv", encoding="utf-8-sig")
    ws["origin"] = "working_set"

    if not OUT_CSV.exists():
        logger.error("Run aux extraction first")
        return
    aux = pd.read_csv(OUT_CSV)
    aux["origin"] = "auxiliary"

    common_cols = [c for c in ws.columns if c in aux.columns]
    combined = pd.concat([ws[common_cols + ["origin"]], aux[common_cols + ["origin"]]], ignore_index=True)
    combined.to_csv(COMBINED_CSV, index=False, encoding="utf-8")
    logger.info(f"[AuxExt] combined {len(combined)} rows saved to {COMBINED_CSV}")
    print(f"Combined extraction: {len(combined)} rows ({(combined['origin']=='working_set').sum()} ws + {(combined['origin']=='auxiliary').sum()} aux)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--merge", action="store_true")
    args = ap.parse_args()
    if args.run:
        run()
    if args.merge:
        merge_with_working_set()
    if not (args.run or args.merge):
        ap.print_help()


if __name__ == "__main__":
    main()
