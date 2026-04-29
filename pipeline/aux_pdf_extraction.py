"""Re-extract data from the 49 PDFs downloaded for EC5-recovered + auxiliary includes.

Produces full-PDF extraction (vs abstract-only) for those papers, then merges
into a unified extraction view.
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

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MANIFEST = Path("results/auxiliary/pdfs/download_manifest.csv")
PDF_DIRS = [Path("results/pdfs"), Path("results/auxiliary/pdfs")]
AUX_FT = Path("results/auxiliary/aux_ft_screened.csv")
EC5_REC = Path("results/ec5_recovery/ec5_recovery_results.csv")
OUT_CSV = Path("results/auxiliary/aux_pdf_extraction.csv")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
PDF_MAX_CHARS = 6000
N_WORKERS = 2

EXTRACTION_FIELDS = [
    "research_question", "study_type", "research_contribution",
    "pm_technique", "stochastic_technique", "software_artifact",
    "software_process", "dataset_source", "dataset_public",
    "tool_used", "main_finding", "limitations", "replication_package",
]


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


def _find_pdf(filename: str) -> Path | None:
    for d in PDF_DIRS:
        p = d / filename
        if p.exists():
            return p
    return None


def _extract_pdf_text(pdf_path: Path, max_chars: int = PDF_MAX_CHARS) -> str:
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber missing")
        return ""
    parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:8]:
                t = page.extract_text() or ""
                t = re.sub(r"\(cid:\d+\)", "", t)
                parts.append(t)
                if sum(len(x) for x in parts) >= max_chars:
                    break
    except Exception as exc:
        logger.warning(f"PDF read err {pdf_path.name}: {exc}")
        return ""
    return "\n".join(parts)[:max_chars].strip()


def _build_prompt(paper, text):
    title = _safe(paper, "title")
    year = _safe(paper, "year")
    venue = _safe(paper, "venue")
    ic = _safe(paper, "ft_matched_ic")
    if text:
        body = f"\n**Texto do paper (primeiras páginas):**\n{text}\n"
    else:
        body = "\n*(PDF unreadable)*\n"
    return f"""Você é um pesquisador fazendo extração de dados para a SLR PATHCAST sobre Process Mining e Modelagem Estocástica em Processos de Software.

**Título:** {title}
**Ano:** {year}  |  **Venue:** {venue}
**Critérios de inclusão atendidos:** {ic}
{body}
Retorne SOMENTE um objeto JSON válido com exatamente estes campos:

{{
  "research_question": "pergunta de pesquisa principal (1-2 frases)",
  "study_type": "case_study | experiment | survey | tool | theoretical | simulation | mixed",
  "research_contribution": "discovery | conformance | enhancement | prediction | simulation | framework | hybrid",
  "pm_technique": "alpha | inductive_miner | heuristic | conformance_checking | social_network | declarative | other | none",
  "stochastic_technique": "markov_chain | stochastic_petri_net | monte_carlo | system_dynamics | other | none",
  "software_artifact": "commits | issues | ci_cd | ide_logs | vcs | jira | github | other | none",
  "software_process": "development | testing | maintenance | code_review | bug_fixing | deployment | requirements | other",
  "dataset_source": "open_source | industrial | academic | synthetic | not_specified",
  "dataset_public": "sim | não | parcial | não_mencionado",
  "tool_used": "nomes ou não_mencionado",
  "main_finding": "principal resultado (2-3 frases)",
  "limitations": "limitações (1-2 frases) ou não_mencionado",
  "replication_package": "sim | não | parcial | não_mencionado"
}}

Responda APENAS com o JSON."""


def _parse(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    blob = m.group(0) if m else text
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {}


def collect_targets() -> list[dict]:
    if not MANIFEST.exists():
        logger.error("Manifest missing")
        return []
    m = pd.read_csv(MANIFEST)
    d = m[m["pdf_status"] == "downloaded"].copy()

    # Enrich with paper metadata
    aux_ft = pd.read_csv(AUX_FT) if AUX_FT.exists() else pd.DataFrame()
    ec5 = pd.read_csv(EC5_REC) if EC5_REC.exists() else pd.DataFrame()

    targets = []
    for _, r in d.iterrows():
        iid = str(r.get("internal_id", ""))
        pdf_file = str(r.get("pdf_file", ""))
        pdf_path = _find_pdf(pdf_file)
        if not pdf_path:
            logger.warning(f"PDF not on disk: {pdf_file}")
            continue
        # try to fetch metadata
        meta = {}
        if r.get("source_db") == "aux_include" and len(aux_ft):
            row = aux_ft[aux_ft["internal_id"].astype(str) == iid]
            if len(row):
                meta = row.iloc[0].to_dict()
        elif r.get("source_db") == "ec5_recovered" and len(ec5):
            row = ec5[ec5["internal_id"].astype(str) == iid]
            if len(row):
                meta = row.iloc[0].to_dict()
        targets.append({
            "internal_id": iid,
            "title": _safe(meta, "title") or _safe(r, "title"),
            "doi": _safe(meta, "doi") or _safe(r, "doi"),
            "year": _safe(meta, "year") or _safe(r, "year"),
            "venue": _safe(meta, "venue"),
            "source_db": _safe(r, "source_db"),
            "ft_matched_ic": _safe(meta, "ft_matched_ic") or _safe(meta, "ta_matched_ic"),
            "pdf_path": str(pdf_path),
        })
    logger.info(f"[AuxPDFExt] targets: {len(targets)}")
    return targets


def run():
    import anthropic
    targets = collect_targets()
    existing = {}
    if OUT_CSV.exists():
        for r in pd.read_csv(OUT_CSV).to_dict("records"):
            if str(r.get("main_finding", "")).strip():
                existing[r["internal_id"]] = r
    pending = [t for t in targets if t["internal_id"] not in existing]
    logger.info(f"[AuxPDFExt] {len(existing)} done, {len(pending)} pending")
    if not pending:
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def extract(paper):
        text = _extract_pdf_text(Path(paper["pdf_path"]))
        prompt = _build_prompt(paper, text)
        for attempt in range(1, 5):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                )
                resp = msg.content[0].text if msg.content else ""
                data = _parse(resp)
                out = {
                    "internal_id": paper["internal_id"],
                    "title": paper["title"],
                    "doi": paper["doi"],
                    "year": paper["year"],
                    "source_db": paper["source_db"],
                    "ft_matched_ic": paper["ft_matched_ic"],
                    "pdf_file": Path(paper["pdf_path"]).name,
                    "pdf_chars_used": len(text),
                }
                for f in EXTRACTION_FIELDS:
                    out[f] = str(data.get(f, "")).strip()
                out["raw"] = resp[:600]
                return out
            except Exception as exc:
                logger.warning(f"[AuxPDFExt] {paper['internal_id']} attempt {attempt}: {exc}")
                time.sleep(3 * attempt)
        return {"internal_id": paper["internal_id"], "raw": "ERROR"}

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(extract, t): t for t in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 10 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[AuxPDFExt] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 25 == 0:
                pd.DataFrame(results).to_csv(OUT_CSV, index=False)

    pd.DataFrame(results).to_csv(OUT_CSV, index=False)
    logger.info(f"[AuxPDFExt] Saved: {OUT_CSV}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.run or True:
        run()


if __name__ == "__main__":
    main()
