"""
Revisão full-text dos papers Band D usando PDFs baixados manualmente.

Fluxo:
  1. python -m pipeline.pdf_band_d_review --match    # mostra mapeamento PDF→paper
  2. python -m pipeline.pdf_band_d_review --run      # extrai texto, submete batch Anthropic
  3. python -m pipeline.pdf_band_d_review --collect <batch_id>  # coleta resultados
  4. python main.py finalize                         # regenera artefatos finais

O script injeta o texto do PDF como 'abstract' e usa a infraestrutura de batch
da fase FT existente (pipeline/fulltext.py) para triagem LLM.
"""
from __future__ import annotations

import csv
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PDF_DIR      = Path("results/pdfs")
FT_CSV       = Path("results/screening/ft_screening_results.csv")
BATCHES_LOG  = Path("results/screening/ft_screening_batches.json")

MODEL      = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512

# ──────────────────────────────────────────────────────────────────────────────
# Mapeamento PDF → internal_id (Band D papers)
# Confirmado via inspeção do conteúdo de cada PDF.
# ──────────────────────────────────────────────────────────────────────────────
PDF_TO_PAPER: dict[str, str] = {
    # Matches por fragmento de DOI no nome do arquivo
    "s41060-025-01000-w.pdf":                            "2c1f1193",
    "s00500-026-11305-y.pdf":                            "43ad8506",
    "s10515-021-00319-5.pdf":                            "83421d8c",
    "s42979-021-00830-2.pdf":                            "c894f613",
    "s10639-021-10564-6.pdf":                            "6f295ec6",
    "978-3-642-45005-1_27.pdf":                          "0186248d",
    "131-142.pdf":                                       "c42be0aa",
    "751-759.pdf":                                       "1303e41e",
    "1-s2.0-S0164121217300365-main.pdf":                 "4409efef",
    "1-s2.0-S095058492200057X-main.pdf":                 "7e29a15e",
    "1-s2.0-S0950584925000199-main.pdf":                 "69029db6",
    "1-s2.0-S089571770500097X-main.pdf":                 "a20e7c58",
    "1-s2.0-S0377221713002221-main.pdf":                 "1bb6711a",
    "1-s2.0-S0950584900001208-main.pdf":                 "c496994b",
    # Matches por título/autor no nome do arquivo
    "Tyagi2021_Chapter_AgilePlanningAndTrackingOfSoft.pdf": "e89188a6",
    "Checking_Conformance_between_Colored_Petri_Nets_and_Event_Logs.pdf": "abfa5067",
    "KawalerowiczMadeyski21.pdf":                        "f59b10d5",
    "PROFES-2023-Declare_and_RuM.pdf":                   "7f6a881a",
    "Discovering_Modeling_and_Re-enacting_Open_Source_S.pdf": "be942093",
    "Jensen-Scacchi-SPW-2005.pdf":                       "2c280053",
    "CameraReady-LucasColucciandRaphaelAlbino.pdf":      "4c73b15f",
    "DAMDID_2024_paper_31.pdf":                          "1a59bb38",
    "Bottlenecks___ICAISC_2025_final_version_20250319.pdf": "9ea592cd",
    "A-Probabilistic-Approach-to-Building-Defect-Prediction-Model-for-Platform-based-Product-Lines.pdf": "3d967450",
    "Interval Estimation for Software Reliability Assessment based on MCMC Method.pdf": "cfbb1c3f",
    "Dumbachetal._ExplorationofProcessMiningOpportunitiesInEducationalSoftwareEngineering_TheGitLabAnalyser_EDM_2020.pdf": "6e572cbb",
    "C-GenCPN-Automatic-CPN-Model-Generation-of-Processes.pdf": "5034ff9d",
    "Horn17.pdf":                                        "a8576441",
    "816bb1177f05a68de943dd1c377e22a0.pdf":              "4082a5b1",
    "6f9a5a08_monitoring_the_software_development_process_with_p.pdf": "6f9a5a08",
    # Matches confirmados por inspeção do conteúdo
    "TR-2010-10.pdf":                                    "02f8b39e",
    "55bb1a9d65268.pdf":                                 "ba2ff831",
    "WCE2014_pp407-411.pdf":                             "c9cdb64d",
    "2016_CIMPS.pdf":                                    "3ef399e6",
    "keynote.pdf":                                       "f0b6a907",
    "p1203.pdf":                                         "9c4cc898",
}

# Papers sem PDF encontrado (marcados "não" pelo usuário)
# Para estes, ft_decision permanece "pending" se ainda vazio.
NO_PDF_PAPERS: set[str] = {
    "44d6a32e",  # An Approach Based on PM Techniques to Support Software Development
    "6778e0d5",  # Analyzing Side-Tracking of Developers Using OCPM
    "340129d0",  # An approach to discover accurate fix-time prediction models
    "5f44c077",  # Holistic processing and exploring event logs
    "d85e3fdf",  # Introduction to integration of PM to the knowledge framework
    "a21c9dff",  # Simkan: Training kanban practices
    "6f5e6f89",  # Agile estimation with monte carlo simulation
    "ae26dfd4",  # On-the-fly testing using TTCN-3 Markov chain
    "0906c3aa",  # Project scheduling with random fuzzy activity duration
    "bc4fb94a",  # Research of modular software system reliability based on HMM
    "2558a93a",  # 11th Issue LNCS Transactions on Petri Nets (proceedings book)
}


# ──────────────────────────────────────────────────────────────────────────────
# Extração de texto do PDF
# ──────────────────────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: Path, max_chars: int = 4000) -> str:
    """Extrai até max_chars caracteres das primeiras páginas do PDF."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError("pdfplumber não instalado — execute: pip install pdfplumber")

    text_parts: list[str] = []
    total = 0
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:6]:
                page_text = page.extract_text() or ""
                remaining = max_chars - total
                if remaining <= 0:
                    break
                chunk = page_text[:remaining]
                text_parts.append(chunk)
                total += len(chunk)
    except Exception as exc:
        logger.warning(f"[PDF] Erro ao extrair {pdf_path.name}: {exc}")
        return ""

    text = "\n".join(text_parts).strip()
    # Remove caracteres CID (PDFs escaneados com codificação problemática)
    text = re.sub(r"\(cid:\d+\)", " ", text)
    text = re.sub(r"\s{3,}", "\n", text).strip()
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Carregamento / salvamento do CSV FT
# ──────────────────────────────────────────────────────────────────────────────

def _load_ft_csv() -> list[dict]:
    from pipeline.fulltext import FT_COLUMNS
    if not FT_CSV.exists():
        raise FileNotFoundError(f"ft_screening_results.csv não encontrado em {FT_CSV}")
    with open(FT_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _save_ft_csv(papers: list[dict]) -> None:
    from pipeline.fulltext import FT_COLUMNS, save_ft_csv
    save_ft_csv(papers)


# ──────────────────────────────────────────────────────────────────────────────
# Construção do batch Anthropic
# ──────────────────────────────────────────────────────────────────────────────

def _build_prompt(paper: dict, pdf_text: str) -> str:
    from config.screening_criteria import FT_PAPER_PROMPT_TEMPLATE

    abstract = pdf_text if pdf_text.strip() else (paper.get("abstract") or "")
    abstract_source = "pdf_full_text" if pdf_text.strip() else (
        paper.get("abstract_source") or "missing_or_unverified"
    )
    return FT_PAPER_PROMPT_TEMPLATE.format(
        title=paper.get("title", "").strip() or "(sem título)",
        abstract=abstract or "Texto não disponível.",
        venue=paper.get("venue", "") or "N/A",
        doc_type=paper.get("doc_type", "") or "N/A",
        year=paper.get("year", "") or "N/A",
        source_db=paper.get("source_db", "") or "N/A",
        abstract_source=abstract_source,
        ta_decision=paper.get("ta_decision", "maybe"),
        ta_rationale=(paper.get("ta_rationale") or "N/A").strip(),
        ta_matched_ic=paper.get("ta_matched_ic", "") or "nenhum",
    )


def _parse_decision(text: str) -> dict:
    from pipeline.fulltext import _parse_ft_decision
    return _parse_ft_decision(text)


def _log_batch(batch_id: str, metadata: dict) -> None:
    existing: list = []
    if BATCHES_LOG.exists():
        try:
            existing = json.loads(BATCHES_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append({
        "batch_id": batch_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **metadata,
    })
    BATCHES_LOG.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# Subcomandos
# ──────────────────────────────────────────────────────────────────────────────

def cmd_match() -> None:
    """Exibe o mapeamento PDF → paper e identifica papers sem PDF."""
    papers_by_id = {p["internal_id"]: p for p in _load_ft_csv()}
    band_d = {pid: p for pid, p in papers_by_id.items()
              if p.get("ft_priority_band") == "D"}

    mapped   = {v: k for k, v in PDF_TO_PAPER.items()}   # id → filename
    unmapped = set(band_d) - set(mapped) - NO_PDF_PAPERS

    print(f"\n{'='*70}")
    print(f"Band D total: {len(band_d)}  |  com PDF: {len(mapped)}  "
          f"|  sem PDF declarado: {len(NO_PDF_PAPERS)}  |  não identificado: {len(unmapped)}")
    print(f"{'='*70}")

    print("\n── COM PDF MAPEADO ─────────────────────────────────────────────")
    for pid, filename in sorted(mapped.items()):
        p = band_d.get(pid, {})
        pdf_path = PDF_DIR / filename
        exists = "✓" if pdf_path.exists() else "✗ ARQUIVO NÃO ENCONTRADO"
        print(f"  {pid}  [{exists}]")
        print(f"    PDF:   {filename}")
        print(f"    Título: {(p.get('title') or '')[:70]}")
        print(f"    Decisão atual: {p.get('ft_decision') or '<sem decisão>'}")
        print()

    print("\n── SEM PDF (marcados 'não') ─────────────────────────────────────")
    for pid in sorted(NO_PDF_PAPERS):
        p = band_d.get(pid, {})
        if p:
            print(f"  {pid}  {(p.get('title') or '')[:70]}")
            print(f"         decisão atual: {p.get('ft_decision') or '<sem decisão>'}")

    if unmapped:
        print("\n── NÃO IDENTIFICADO (verificar manualmente) ─────────────────────")
        for pid in sorted(unmapped):
            p = band_d.get(pid, {})
            print(f"  {pid}  {(p.get('title') or '')[:70]}")
            print(f"         decisão atual: {p.get('ft_decision') or '<sem decisão>'}")


def cmd_run(api_key: str, *, dry_run: bool = False, force: bool = False) -> Optional[str]:
    """Extrai texto dos PDFs, submete batch Anthropic para triagem FT."""
    from config.screening_criteria import FT_SYSTEM_PROMPT
    import anthropic

    papers      = _load_ft_csv()
    papers_by_id = {p["internal_id"]: p for p in papers}
    id_to_pdf   = {v: k for k, v in PDF_TO_PAPER.items()}

    # Seleciona Band D sem decisão FT ou com "pending" (pode melhorar com PDF)
    candidates = []
    for pid, filename in id_to_pdf.items():
        p = papers_by_id.get(pid)
        if p is None:
            logger.warning(f"[PDF-Review] internal_id {pid} não encontrado no CSV FT")
            continue
        current = (p.get("ft_decision") or "").strip().lower()
        # "pending" significa sem texto completo antes — agora temos o PDF
        already_decided = bool(current) and current not in ("pending",)
        if already_decided and not force:
            continue
        pdf_path = PDF_DIR / filename
        if not pdf_path.exists():
            logger.warning(f"[PDF-Review] PDF não encontrado: {pdf_path}")
            continue
        candidates.append((pid, p, pdf_path))

    print(f"\n[PDF-Review] {len(candidates)} papers para triagem")
    if not candidates:
        print("  Nenhum paper pendente. Use --force para re-triar todos.")
        return None

    # Constrói requests do batch
    requests = []
    for pid, p, pdf_path in candidates:
        print(f"  Extraindo texto: {pdf_path.name[:60]}")
        pdf_text = extract_pdf_text(pdf_path)
        if not pdf_text.strip():
            logger.warning(f"  [!] Texto vazio para {pdf_path.name} — usando metadados apenas")
        prompt = _build_prompt(p, pdf_text)
        requests.append({
            "custom_id": pid,
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": FT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        })

    if dry_run:
        pid, p, pdf_path = candidates[0]
        print(f"\n[dry-run] Exemplo de prompt para '{p.get('title', '')[:60]}':")
        print(_build_prompt(p, extract_pdf_text(pdf_path))[:600])
        return None

    print(f"\n[PDF-Review] Submetendo batch com {len(requests)} papers...")
    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    for attempt in range(1, 6):
        try:
            batch = client.messages.batches.create(requests=requests)
            break
        except Exception as exc:
            logger.warning(f"  Tentativa {attempt}/5 falhou: {exc}")
            if attempt < 5:
                time.sleep(10 * attempt)
            else:
                raise

    _log_batch(batch.id, {
        "n_papers": len(requests),
        "model": MODEL,
        "status": batch.processing_status,
        "phase": "pdf_band_d",
    })
    print(f"  ✓ Batch criado: {batch.id}  (status: {batch.processing_status})")
    print(f"\nPara coletar quando terminar:")
    print(f"  python -m pipeline.pdf_band_d_review --collect {batch.id}")
    return batch.id


def cmd_collect(batch_id: str, api_key: str) -> int:
    """Coleta resultados do batch e atualiza ft_screening_results.csv."""
    from pipeline.fulltext import _parse_ft_decision, _apply_ft_decision_policy, save_ft_csv
    import anthropic

    papers      = _load_ft_csv()
    papers_by_id = {p["internal_id"]: p for p in papers}
    client = anthropic.Anthropic(api_key=api_key)

    print(f"\n[PDF-Review] Coletando batch {batch_id}...")

    # Verifica se batch terminou
    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        c = b.request_counts
        print(f"  Status: {b.processing_status}  "
              f"succeeded={c.succeeded} | errored={c.errored} | processing={c.processing}")
        print("  Batch ainda não finalizou. Tente novamente mais tarde.")
        return 0

    ts = datetime.now(timezone.utc).isoformat()
    updated = 0

    for result in client.messages.batches.results(batch_id):
        pid = result.custom_id
        if pid not in papers_by_id:
            continue
        p = papers_by_id[pid]
        if result.result.type == "succeeded":
            content = result.result.message.content
            text = content[0].text if content else ""
            decision_data = _parse_ft_decision(text)
        else:
            decision_data = {
                "ft_decision": "pending",
                "ft_rationale": f"Erro API: {result.result.type}",
                "ft_matched_ic": "",
                "ft_matched_ec": "",
                "ft_evidence_tags": "",
                "ft_software_context": "unclear",
                "ft_stochastic_method": "unclear",
                "ft_forecast_target": "unclear",
                "ft_process_data_source": "unclear",
                "ft_confidence": "low",
            }

        decision_data["ft_evidence_status"] = "pdf_full_text"
        decision_data["ft_manual_review_required"] = "false"
        p.update(decision_data)
        p["ft_screened_at"] = ts
        p["ft_screened_by"]  = "llm_pdf"
        p["ft_batch_id"]     = batch_id
        updated += 1
        print(f"  {pid}  → {decision_data.get('ft_decision')}  "
              f"(conf={decision_data.get('ft_confidence')})  "
              f"{(papers_by_id[pid].get('title') or '')[:50]}")

    save_ft_csv(papers)
    print(f"\n  ✓ {updated} decisões salvas em {FT_CSV}")
    return updated


def cmd_mark_no_pdf() -> int:
    """
    Marca como 'pending' (com nota) os papers sem PDF encontrado,
    apenas se ainda não têm decisão FT.
    """
    from pipeline.fulltext import save_ft_csv

    papers = _load_ft_csv()
    ts = datetime.now(timezone.utc).isoformat()
    updated = 0

    for p in papers:
        pid = p["internal_id"]
        if pid not in NO_PDF_PAPERS:
            continue
        if (p.get("ft_decision") or "").strip():
            continue  # já tem decisão, não sobrescreve
        p["ft_decision"]     = "pending"
        p["ft_rationale"]    = "PDF não localizado durante busca manual; texto completo inacessível."
        p["ft_screened_at"]  = ts
        p["ft_screened_by"]  = "manual_no_pdf"
        p["ft_confidence"]   = "low"
        p["ft_evidence_status"] = "missing_pdf"
        p["ft_manual_review_required"] = "true"
        updated += 1

    if updated:
        save_ft_csv(papers)
        print(f"[PDF-Review] {updated} papers sem PDF marcados como 'pending'")
    return updated


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    parser = argparse.ArgumentParser(description="Revisão full-text dos papers Band D via PDFs")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--match",   action="store_true", help="Mostra mapeamento PDF→paper")
    group.add_argument("--run",     action="store_true", help="Extrai texto e submete batch")
    group.add_argument("--collect", metavar="BATCH_ID",  help="Coleta resultados de um batch")
    group.add_argument("--mark-no-pdf", action="store_true",
                       help="Marca papers sem PDF como 'pending'")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force",   action="store_true",
                        help="Re-tria mesmo papers com decisão existente")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.match:
        cmd_match()
    elif args.run:
        if not api_key and not args.dry_run:
            print("ANTHROPIC_API_KEY não configurada.")
            return
        cmd_run(api_key, dry_run=args.dry_run, force=args.force)
    elif args.collect:
        if not api_key:
            print("ANTHROPIC_API_KEY não configurada.")
            return
        n = cmd_collect(args.collect, api_key)
        if n > 0:
            n_no_pdf = cmd_mark_no_pdf()
            print(f"\nPróximo passo:")
            print(f"  python main.py finalize")
    elif args.mark_no_pdf:
        cmd_mark_no_pdf()


if __name__ == "__main__":
    main()
