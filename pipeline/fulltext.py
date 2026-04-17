"""
Full-text screening pipeline — SLR PATHCAST.

Fase 2 da seleção: revisão do texto completo dos papers que passaram pela
triagem T/A (include + maybe). Opera sobre results/screening/ta_screening_results.csv.

Fluxo recomendado:
  1. python main.py fulltext --export          # gera fila priorizada ft_screening_results.csv
  2. python main.py fulltext --enrich-urls     # busca PDFs open-access via Semantic Scholar
  3. python main.py fulltext --llm-rescreen    # LLM re-triagem dos "maybe" com abstract
  4. python main.py fulltext --collect BATCH   # coleta resultado do lote LLM
  5. python main.py fulltext --stats           # progresso atual

Critérios de prioridade:
  Band A  score ≥ 120  include + múltiplos ICs
  Band B  score ≥ 100  include + IC simples
  Band C  score  60-99 maybe com abstract disponível
  Band D  score  55-59 maybe com IC, sem abstract
  Band E  score  50-54 maybe sem IC nem abstract (necessita texto completo)

Saída:
  results/screening/ft_screening_results.csv  — fila priorizada + decisões FT
  results/screening/ft_screening_batches.json — log de batches LLM
  results/screening/ft_screening_stats.txt    — relatório de progresso
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

# ── caminhos ──────────────────────────────────────────────────────────
SCREENING_DIR   = Path("results/screening")
TA_RESULTS_CSV  = SCREENING_DIR / "ta_screening_results.csv"
FT_RESULTS_CSV  = SCREENING_DIR / "ft_screening_results.csv"
FT_BATCHES_LOG  = SCREENING_DIR / "ft_screening_batches.json"
FT_STATS_FILE   = SCREENING_DIR / "ft_screening_stats.txt"
ABSTRACT_SUMMARY_CSV = SCREENING_DIR / "abstract_enrichment_summary.csv"
ABSTRACT_SUMMARY_TXT = SCREENING_DIR / "abstract_enrichment_summary.txt"
ABSTRACT_RUN_SUMMARY_CSV = SCREENING_DIR / "abstract_enrichment_last_run.csv"
ABSTRACT_RUN_SUMMARY_TXT = SCREENING_DIR / "abstract_enrichment_last_run.txt"

# ── modelo ────────────────────────────────────────────────────────────
MODEL      = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512
BATCH_SIZE = 500

# ── colunas do CSV de saída ───────────────────────────────────────────
FT_COLUMNS = [
    # herdado da triagem T/A
    "internal_id", "source_db", "source_query_id", "source_query_label",
    "doi", "title", "authors", "year", "abstract", "venue", "doc_type",
    "keywords", "url", "publisher", "abstract_source", "abstract_match_type",
    "ta_decision", "ta_rationale", "ta_matched_ic", "ta_matched_ec",
    "ta_evidence_tags", "ta_software_context", "ta_stochastic_method",
    "ta_forecast_target", "ta_process_data_source", "ta_confidence",
    "ta_evidence_status", "ta_manual_review_required",
    "ta_screened_at", "ta_batch_id",
    # prioridade
    "ft_priority_score", "ft_priority_rank", "ft_priority_band",
    # URL open-access (Semantic Scholar)
    "ft_oa_url",
    # decisão full-text
    "ft_decision",      # include | exclude | pending
    "ft_rationale",
    "ft_matched_ic",
    "ft_matched_ec",
    "ft_evidence_tags",
    "ft_software_context",
    "ft_stochastic_method",
    "ft_forecast_target",
    "ft_process_data_source",
    "ft_confidence",
    "ft_evidence_status",
    "ft_manual_review_required",
    "ft_screened_at",
    "ft_screened_by",   # 'llm' | 'manual'
    "ft_batch_id",
]

EVIDENCE_TAGS = {
    "process_mining",
    "software_process",
    "repository_mining",
    "stochastic_modeling",
    "forecasting",
    "event_log",
    "version_control",
    "issue_tracking",
    "pull_requests",
    "ci_cd",
    "markov",
    "hidden_markov_model",
    "monte_carlo",
    "stochastic_petri_net",
    "bayesian_model",
    "simulation",
    "lead_time",
    "cycle_time",
    "remaining_time",
    "throughput",
    "defect_prediction",
    "build_prediction",
    "reliability",
    "insufficient_abstract",
    "full_text_required",
}

SOFTWARE_CONTEXT_VALUES = {
    "software_development_process",
    "repository_mining",
    "ci_cd",
    "issue_bug_workflow",
    "software_testing",
    "requirements_engineering",
    "software_project_management",
    "unclear",
    "not_software_process",
}

STOCHASTIC_METHOD_VALUES = {
    "none",
    "markov_chain",
    "hidden_markov_model",
    "monte_carlo",
    "stochastic_petri_net",
    "bayesian_model",
    "probabilistic_model",
    "simulation",
    "queueing_model",
    "other_stochastic",
    "unclear",
}

FORECAST_TARGET_VALUES = {
    "none",
    "lead_time",
    "cycle_time",
    "remaining_time",
    "throughput",
    "defect_rate",
    "build_outcome",
    "reliability",
    "completion_time",
    "other_process_metric",
    "unclear",
}

PROCESS_DATA_SOURCE_VALUES = {
    "none",
    "event_logs",
    "version_control",
    "issue_tracker",
    "pull_requests",
    "ci_cd_logs",
    "software_repository_mixed",
    "synthetic_data",
    "simulated_process",
    "survey_or_secondary",
    "unclear",
}

CONFIDENCE_VALUES = {"low", "medium", "high"}


# ================================================================== #
#  Scoring e priorização                                              #
# ================================================================== #

def _count_ic(ic_str: str) -> int:
    if not ic_str:
        return 0
    return len([x for x in ic_str.split("|") if x.strip().startswith("IC")])


def _score_paper(paper: dict) -> int:
    score = 0

    # ── base por decisão T/A ──────────────────────────────────────
    decision = paper.get("ta_decision", "")
    if decision == "include":
        score += 100
    elif decision == "maybe":
        score += 50

    # ── força do sinal IC (0-20 pts) ─────────────────────────────
    score += _count_ic(paper.get("ta_matched_ic", "")) * 5

    # ── disponibilidade de conteúdo para revisão ──────────────────
    if (paper.get("abstract") or "").strip():
        score += 8   # abstract disponível = decisão mais fácil
    if (paper.get("ft_oa_url") or "").strip():
        score += 5   # PDF open-access disponível
    elif (paper.get("doi") or "").strip():
        score += 3   # DOI = recuperável (mas pode ter paywall)
    elif (paper.get("url") or "").strip():
        score += 1

    # ── recência ──────────────────────────────────────────────────
    try:
        year = int(paper.get("year") or 0)
        if year >= 2020:
            score += 5
        elif year >= 2018:
            score += 3
        elif year >= 2015:
            score += 1
    except (ValueError, TypeError):
        pass

    # ── tipo do documento ─────────────────────────────────────────
    doc_type = (paper.get("doc_type") or "").lower()
    if doc_type in ("article", "review"):
        score += 3  # artigos de periódico têm maior rigor metodológico

    return score


def _band(score: int, ta_decision: str, paper: dict | None = None) -> str:
    if ta_decision == "include" and score >= 120:
        return "A"
    if ta_decision == "include":
        return "B"
    # Para papers "maybe": banda determinada por conteúdo disponível
    if paper is not None:
        has_abstract = bool((paper.get("abstract") or "").strip())
        has_ic       = _count_ic(paper.get("ta_matched_ic", "")) > 0
        if has_abstract:
            return "C"   # LLM pode re-triar com abstract disponível
        if has_ic:
            return "D"   # IC identificado na T/A, precisa texto completo
        return "E"       # sem IC nem abstract — leitura integral necessária
    # fallback score-based (sem paper dict)
    if score >= 60:
        return "C"
    if score >= 55:
        return "D"
    return "E"


# ================================================================== #
#  I/O                                                                #
# ================================================================== #

def load_ft_queue() -> list[dict]:
    """Carrega ft_screening_results.csv existente."""
    if not FT_RESULTS_CSV.exists():
        return []
    with open(FT_RESULTS_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_ft_csv(papers: list[dict]) -> None:
    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    with open(FT_RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(papers)
    logger.info(f"[FT] {len(papers)} papers salvos em {FT_RESULTS_CSV}")


def save_abstract_summary(papers: list[dict]) -> None:
    summary_rows = []

    total = len(papers)
    with_abstract = sum(1 for p in papers if (p.get("abstract") or "").strip())
    source_counts: dict[tuple[str, str], int] = {}
    source_totals: dict[str, int] = {}

    for paper in papers:
        source = (paper.get("abstract_source") or "").strip() or "preexisting_or_unknown"
        match_type = (paper.get("abstract_match_type") or "").strip() or "preexisting_or_unknown"
        if not (paper.get("abstract") or "").strip():
            continue
        source_counts[(source, match_type)] = source_counts.get((source, match_type), 0) + 1
        source_totals[source] = source_totals.get(source, 0) + 1

    for (source, match_type), count in sorted(
        source_counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    ):
        summary_rows.append({
            "abstract_source": source,
            "abstract_match_type": match_type,
            "count": count,
            "pct_of_abstracts": f"{(count / with_abstract * 100):.2f}" if with_abstract else "0.00",
            "pct_of_queue": f"{(count / total * 100):.2f}" if total else "0.00",
        })

    with open(ABSTRACT_SUMMARY_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["abstract_source", "abstract_match_type", "count", "pct_of_abstracts", "pct_of_queue"],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    lines = [
        "SLR PATHCAST — Abstract Enrichment Summary",
        "=" * 50,
        f"Queue total: {total}",
        f"With abstract: {with_abstract}",
        f"Without abstract: {total - with_abstract}",
        "",
        "By source:",
    ]
    for source, count in sorted(source_totals.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"  {source}: {count} ({count / with_abstract * 100:.2f}%)" if with_abstract else f"  {source}: {count}")
    lines += ["", f"CSV detail: {ABSTRACT_SUMMARY_CSV}", ""]
    ABSTRACT_SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"[FT/Abstract] Resumo salvo em {ABSTRACT_SUMMARY_CSV}")


def save_abstract_run_summary(
    *,
    before: int,
    after: int,
    source_counts: dict[str, int],
    total_queue: int,
) -> None:
    rows = []
    recovered = after - before
    for source_name, count in sorted(source_counts.items(), key=lambda item: (-item[1], item[0])):
        rows.append({
            "source_step": source_name,
            "count": count,
            "pct_of_recovered": f"{(count / recovered * 100):.2f}" if recovered else "0.00",
            "pct_of_queue": f"{(count / total_queue * 100):.2f}" if total_queue else "0.00",
        })

    with open(ABSTRACT_RUN_SUMMARY_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_step", "count", "pct_of_recovered", "pct_of_queue"])
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "SLR PATHCAST — Abstract Enrichment Last Run",
        "=" * 50,
        f"Queue total: {total_queue}",
        f"With abstract before run: {before}",
        f"With abstract after run: {after}",
        f"Recovered in run: {recovered}",
        "",
        "Recovered by source step:",
    ]
    for source_name, count in sorted(source_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"  {source_name}: {count} ({count / recovered * 100:.2f}%)" if recovered else f"  {source_name}: {count}")
    lines += ["", f"CSV detail: {ABSTRACT_RUN_SUMMARY_CSV}", ""]
    ABSTRACT_RUN_SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"[FT/Abstract] Resumo da última rodada salvo em {ABSTRACT_RUN_SUMMARY_CSV}")


def _log_batch(batch_id: str, metadata: dict) -> None:
    existing = []
    if FT_BATCHES_LOG.exists():
        try:
            existing = json.loads(FT_BATCHES_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append({
        "batch_id": batch_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **metadata,
    })
    FT_BATCHES_LOG.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


# ================================================================== #
#  Construção da fila priorizada                                      #
# ================================================================== #

def build_ft_queue(force: bool = False) -> list[dict]:
    """
    Carrega ta_screening_results.csv, filtra include+maybe, pontua, ordena
    e cria (ou atualiza) ft_screening_results.csv.

    Se ft_screening_results.csv já existe e force=False, preserva as
    decisões FT já registradas e apenas recalcula scores e ranks.
    """
    if not TA_RESULTS_CSV.exists():
        raise FileNotFoundError(f"Arquivo de triagem T/A não encontrado: {TA_RESULTS_CSV}")

    # Carrega T/A completo
    with open(TA_RESULTS_CSV, encoding="utf-8", newline="") as f:
        all_ta = {row["internal_id"]: row for row in csv.DictReader(f)}

    # Decisões FT já existentes (preservar progresso)
    existing_ft: dict[str, dict] = {}
    if FT_RESULTS_CSV.exists() and not force:
        existing_ft = {row["internal_id"]: row for row in load_ft_queue()}
        logger.info(f"[FT] {len(existing_ft)} papers já na fila FT — preservando decisões existentes")

    # Filtra apenas include + maybe
    queue_ids = [pid for pid, p in all_ta.items() if p.get("ta_decision") in ("include", "maybe")]
    logger.info(f"[FT] {len(queue_ids)} papers na fila (include + maybe)")

    # Monta rows com score e campos FT
    rows = []
    for pid in queue_ids:
        p = dict(all_ta[pid])
        ex = existing_ft.get(pid, {})

        # Herda OA URL e decisão FT se já existirem
        p["ft_oa_url"]       = ex.get("ft_oa_url", "")
        p["ft_decision"]     = ex.get("ft_decision", "")
        p["ft_rationale"]    = ex.get("ft_rationale", "")
        p["ft_matched_ic"]   = ex.get("ft_matched_ic", "")
        p["ft_matched_ec"]   = ex.get("ft_matched_ec", "")
        p["ft_evidence_tags"] = ex.get("ft_evidence_tags", "")
        p["ft_software_context"] = ex.get("ft_software_context", "")
        p["ft_stochastic_method"] = ex.get("ft_stochastic_method", "")
        p["ft_forecast_target"] = ex.get("ft_forecast_target", "")
        p["ft_process_data_source"] = ex.get("ft_process_data_source", "")
        p["ft_confidence"] = ex.get("ft_confidence", "")
        p["ft_evidence_status"] = ex.get("ft_evidence_status", "")
        p["ft_manual_review_required"] = ex.get("ft_manual_review_required", "")
        p["ft_screened_at"]  = ex.get("ft_screened_at", "")
        p["ft_screened_by"]  = ex.get("ft_screened_by", "")
        p["ft_batch_id"]     = ex.get("ft_batch_id", "")

        p["ft_priority_score"] = _score_paper(p)
        rows.append(p)

    # Ordena: score desc, depois alfabético por título (desempate estável)
    rows.sort(key=lambda r: (-int(r["ft_priority_score"]), (r.get("title") or "")))

    for rank, p in enumerate(rows, start=1):
        p["ft_priority_rank"]  = rank
        p["ft_priority_band"] = _band(int(p["ft_priority_score"]), p.get("ta_decision", ""), p)

    save_ft_csv(rows)
    return rows


# ================================================================== #
#  Enriquecimento de URLs open-access via Semantic Scholar           #
# ================================================================== #

def enrich_oa_urls(papers: list[dict], delay: float = 3.0) -> int:
    """
    Busca URLs de PDF open-access via Semantic Scholar Batch API.
    Atualiza ft_oa_url nos papers e re-pontua (impacta score e band).
    Retorna quantidade enriquecida.
    """
    import requests as _req
    from tqdm import tqdm

    need = [
        p for p in papers
        if (p.get("doi") or "").strip() and not (p.get("ft_oa_url") or "").strip()
    ]
    if not need:
        logger.info("[FT/OA] Nenhum paper elegível para enriquecimento de URL")
        return 0

    logger.info(f"[FT/OA] Buscando URLs OA para {len(need):,} papers com DOI...")

    api_key = os.getenv("S2_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    # Normaliza DOIs para índice
    def _norm(doi: str) -> str:
        doi = doi.strip().lower()
        for pfx in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
            if doi.startswith(pfx):
                doi = doi[len(pfx):]
        return doi

    doi_to_paper = {_norm(p["doi"]): p for p in need if _norm(p.get("doi", ""))}
    doi_list = list(doi_to_paper.keys())
    enriched = 0

    S2_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
    wait = 10.0

    with tqdm(total=len(doi_list), desc="S2/openAccessPdf", unit="paper") as pbar:
        for i in range(0, len(doi_list), 500):
            batch = doi_list[i : i + 500]
            ids = [f"DOI:{d}" for d in batch]
            for attempt in range(5):
                try:
                    resp = _req.post(
                        S2_URL,
                        json={"ids": ids},
                        params={"fields": "externalIds,openAccessPdf"},
                        headers=headers,
                        timeout=60,
                    )
                    if resp.status_code == 429:
                        logger.warning(f"[FT/OA] S2 429 — aguardando {wait:.0f}s")
                        time.sleep(wait)
                        wait = min(wait * 2, 120)
                        continue
                    if resp.status_code in (400, 404):
                        break
                    resp.raise_for_status()
                    for work in (resp.json() or []):
                        if not work:
                            continue
                        ext = work.get("externalIds") or {}
                        doi = _norm(ext.get("DOI") or "")
                        if doi and doi in doi_to_paper:
                            oa = work.get("openAccessPdf") or {}
                            url = oa.get("url", "")
                            if url:
                                doi_to_paper[doi]["ft_oa_url"] = url
                                enriched += 1
                    wait = 10.0
                    break
                except Exception as exc:
                    logger.warning(f"[FT/OA] Erro: {exc}")
                    if attempt < 4:
                        time.sleep(wait)
                        wait = min(wait * 2, 60)
            pbar.update(len(batch))
            time.sleep(delay)

    # Re-pontua e re-rankeia (OA URL afeta score)
    for p in papers:
        p["ft_priority_score"] = _score_paper(p)
    papers.sort(key=lambda r: (-int(r["ft_priority_score"]), (r.get("title") or "")))
    for rank, p in enumerate(papers, start=1):
        p["ft_priority_rank"] = rank
        p["ft_priority_band"] = _band(int(p["ft_priority_score"]), p.get("ta_decision", ""), p)

    save_ft_csv(papers)
    logger.info(f"[FT/OA] {enriched:,} URLs OA encontradas — CSV atualizado")
    return enriched


def enrich_ft_abstracts(papers: list[dict], delay: float = 3.0) -> int:
    """
    Enriquece abstracts da fila FT usando a cascata de fontes.
    Recalcula score/rank/band e salva ft_screening_results.csv.
    """
    from pipeline.enrich import enrich_abstracts_with_checkpoints as _cascade_enrich

    before = sum(1 for p in papers if (p.get("abstract") or "").strip())
    source_counts: dict[str, int] = {}

    def _save_checkpoint(
        current_papers: list[dict],
        source_name: str,
        source_enriched: int,
        total_enriched: int,
    ) -> None:
        source_counts[source_name] = source_enriched
        for p in current_papers:
            p["ft_priority_score"] = _score_paper(p)
        current_papers.sort(key=lambda r: (-int(r["ft_priority_score"]), (r.get("title") or "")))
        for rank, p in enumerate(current_papers, start=1):
            p["ft_priority_rank"] = rank
            p["ft_priority_band"] = _band(int(p["ft_priority_score"]), p.get("ta_decision", ""), p)
        save_ft_csv(current_papers)
        save_abstract_summary(current_papers)
        logger.info(
            "[FT/Abstract] Checkpoint salvo após %s: +%s nesta fonte | total +%s",
            source_name,
            f"{source_enriched:,}",
            f"{total_enriched:,}",
        )

    papers, enriched = _cascade_enrich(papers, delay=delay, after_source=_save_checkpoint)

    after = sum(1 for p in papers if (p.get("abstract") or "").strip())
    _save_checkpoint(papers, "final", 0, enriched)
    source_counts.pop("final", None)
    save_abstract_run_summary(before=before, after=after, source_counts=source_counts, total_queue=len(papers))
    logger.info(f"[FT/Abstract] {enriched:,} abstracts adicionados ({before:,} -> {after:,})")
    return enriched


# ================================================================== #
#  Re-triagem LLM (maybe + abstract)                                 #
# ================================================================== #

def _build_ft_prompt(paper: dict) -> str:
    from config.screening_criteria import FT_PAPER_PROMPT_TEMPLATE
    abstract = (paper.get("abstract") or "").strip()
    ta_rationale = (paper.get("ta_rationale") or "").strip()
    return FT_PAPER_PROMPT_TEMPLATE.format(
        title=paper.get("title", "").strip() or "(sem título)",
        abstract=abstract or "Resumo não disponível.",
        venue=paper.get("venue", "") or "N/A",
        doc_type=paper.get("doc_type", "") or "N/A",
        year=paper.get("year", "") or "N/A",
        source_db=paper.get("source_db", "") or "N/A",
        abstract_source=paper.get("abstract_source", "") or "missing_or_unverified",
        ta_decision=paper.get("ta_decision", "maybe"),
        ta_rationale=ta_rationale or "N/A",
        ta_matched_ic=paper.get("ta_matched_ic", "") or "nenhum",
    )


def _build_ft_requests(papers: list[dict]) -> list[dict]:
    from config.screening_criteria import FT_SYSTEM_PROMPT
    reqs = []
    for p in papers:
        reqs.append({
            "custom_id": p["internal_id"],
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": FT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": _build_ft_prompt(p)}],
            },
        })
    return reqs


def _parse_ft_decision(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        data = json.loads(text)
        decision = data.get("decision", "pending").lower()
        if decision not in ("include", "exclude", "pending"):
            decision = "pending"
        return {
            "ft_decision": decision,
            "ft_rationale": str(data.get("rationale", ""))[:500],
            "ft_matched_ic": "|".join(data.get("matched_ic") or []),
            "ft_matched_ec": "|".join(data.get("matched_ec") or []),
            "ft_evidence_tags": _normalize_tag_list(data.get("evidence_tags"), EVIDENCE_TAGS),
            "ft_software_context": _normalize_enum(
                data.get("software_context"),
                SOFTWARE_CONTEXT_VALUES,
                default="unclear",
            ),
            "ft_stochastic_method": _normalize_enum(
                data.get("stochastic_method"),
                STOCHASTIC_METHOD_VALUES,
                default="unclear",
            ),
            "ft_forecast_target": _normalize_enum(
                data.get("forecast_target"),
                FORECAST_TARGET_VALUES,
                default="unclear",
            ),
            "ft_process_data_source": _normalize_enum(
                data.get("process_data_source"),
                PROCESS_DATA_SOURCE_VALUES,
                default="unclear",
            ),
            "ft_confidence": _normalize_enum(
                data.get("confidence"),
                CONFIDENCE_VALUES,
                default="low",
            ),
        }
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"[FT/LLM] Falha ao parsear resposta: {text[:100]!r}")
        return {
            "ft_decision": "pending",
            "ft_rationale": f"Erro de parsing: {text[:200]}",
            "ft_matched_ic": "",
            "ft_matched_ec": "",
            "ft_evidence_tags": "",
            "ft_software_context": "unclear",
            "ft_stochastic_method": "unclear",
            "ft_forecast_target": "unclear",
            "ft_process_data_source": "unclear",
            "ft_confidence": "low",
        }


from config.screening_criteria import _normalize_tag_list, _normalize_enum, _slugify  # noqa: E402


def _apply_ft_decision_policy(paper: dict, decision_data: dict) -> dict:
    has_verified_abstract = bool((paper.get("abstract") or "").strip())
    decision_data["ft_evidence_status"] = (
        "verified_abstract" if has_verified_abstract else "missing_abstract"
    )
    decision_data["ft_manual_review_required"] = "false"

    if not has_verified_abstract:
        tags = set(filter(None, (decision_data.get("ft_evidence_tags") or "").split("|")))
        tags.update({"insufficient_abstract", "full_text_required"})
        decision_data["ft_evidence_tags"] = "|".join(sorted(tags))
        decision_data["ft_confidence"] = "low"
        decision_data["ft_manual_review_required"] = "true"
        if decision_data.get("ft_decision") == "include":
            decision_data["ft_decision"] = "pending"
            note = "Abstract ausente: include forte rebaixado para pending; exige revisão manual/full text."
            rationale = (decision_data.get("ft_rationale") or "").strip()
            decision_data["ft_rationale"] = f"{rationale} {note}".strip()

    return decision_data


def _submit_ft_batch(papers: list[dict], api_key: str) -> str:
    """Envia batch FT para a Anthropic Batches API. Retorna batch_id."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    reqs = _build_ft_requests(papers)
    logger.info(f"[FT/LLM] Enviando batch com {len(reqs)} papers...")

    batch = None
    for attempt in range(1, 6):
        try:
            batch = client.messages.batches.create(requests=reqs)
            break
        except Exception as exc:
            logger.warning(f"[FT/LLM] Erro ao criar batch (tentativa {attempt}/5): {exc}")
            if attempt < 5:
                time.sleep(10 * attempt)
            else:
                raise

    _log_batch(batch.id, {
        "n_papers": len(papers),
        "model": MODEL,
        "status": batch.processing_status,
        "phase": "fulltext",
    })
    logger.info(f"[FT/LLM] Batch criado: {batch.id}")
    return batch.id


def _poll_ft_batch(batch_id: str, api_key: str, poll_interval: int = 60) -> None:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    print(f"  Aguardando batch {batch_id}... (Ctrl+C para interromper)")
    while True:
        b = client.messages.batches.retrieve(batch_id)
        c = b.request_counts
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {b.processing_status} — "
              f"succeeded: {c.succeeded} | errored: {c.errored} | processing: {c.processing}")
        if b.processing_status == "ended":
            return
        time.sleep(poll_interval)


def collect_ft_results(batch_id: str, api_key: str, papers: list[dict]) -> int:
    """
    Coleta resultados de um batch FT concluído e atualiza ft_screening_results.csv.
    Retorna quantidade de decisões salvas.
    """
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    paper_index = {p["internal_id"]: p for p in papers}
    ts = datetime.now(timezone.utc).isoformat()
    updated = 0

    for result in client.messages.batches.results(batch_id):
        pid = result.custom_id
        if pid not in paper_index:
            continue
        p = paper_index[pid]
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
        decision_data = _apply_ft_decision_policy(p, decision_data)
        p.update(decision_data)
        p["ft_screened_at"] = ts
        p["ft_screened_by"] = "llm"
        p["ft_batch_id"] = batch_id
        updated += 1

    save_ft_csv(papers)
    logger.info(f"[FT/LLM] {updated} decisões FT salvas")
    return updated


def run_llm_rescreen(
    papers: list[dict],
    api_key: str,
    *,
    poll: bool = False,
    poll_interval: int = 60,
    batch_id: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    confirm_includes: bool = False,
) -> None:
    """
    Re-triagem LLM dos papers com abstract disponível.

    Alvo padrão: ta_decision='maybe' AND abstract não-vazio AND ft_decision vazio.
    Com confirm_includes=True: também inclui ta_decision='include' com abstract.

    Se batch_id fornecido: apenas coleta resultados de batch já submetido.
    """
    from colorama import Fore, Style

    # ── Coleta de batch existente ─────────────────────────────────
    if batch_id:
        print(f"\n{Fore.CYAN}── Coletando resultados FT do batch {batch_id}...{Style.RESET_ALL}")
        n = collect_ft_results(batch_id, api_key, papers)
        print(f"  {Fore.GREEN}✓ {n} decisões salvas{Style.RESET_ALL}")
        _print_ft_stats(papers)
        return

    # ── Seleciona alvo ────────────────────────────────────────────
    target_decisions = {"maybe"}
    if confirm_includes:
        target_decisions.add("include")

    candidates = []
    for p in papers:
        has_abstract = bool((p.get("abstract") or "").strip())
        already_decided = bool((p.get("ft_decision") or "").strip())
        ta = p.get("ta_decision", "")
        if ta in target_decisions and has_abstract and (not already_decided or force):
            candidates.append(p)

    if not candidates:
        msg = "maybe" if not confirm_includes else "maybe/include"
        print(f"\n{Fore.YELLOW}Nenhum paper '{msg}' com abstract pendente de re-triagem.{Style.RESET_ALL}")
        return

    label = f"maybe + abstract" if not confirm_includes else \
            f"{sum(1 for p in candidates if p.get('ta_decision')=='include')} includes + " \
            f"{sum(1 for p in candidates if p.get('ta_decision')=='maybe')} maybe (com abstract)"
    print(f"\n{Fore.CYAN}── LLM re-triagem FT: {len(candidates)} papers ({label})...{Style.RESET_ALL}")

    if dry_run:
        p0 = candidates[0]
        print(f"\n{Fore.YELLOW}--dry-run — exemplo de prompt para '{p0['title'][:60]}'::{Style.RESET_ALL}")
        print(_build_ft_prompt(p0)[:800])
        return

    batches_sent = []
    for start in range(0, len(candidates), BATCH_SIZE):
        chunk = candidates[start : start + BATCH_SIZE]
        bid = _submit_ft_batch(chunk, api_key)
        batches_sent.append((bid, chunk))
        print(f"  {Fore.GREEN}✓ Batch enviado: {bid}  ({len(chunk)} papers){Style.RESET_ALL}")

        if poll:
            print(f"\n{Fore.CYAN}── Aguardando batch {bid}...{Style.RESET_ALL}")
            _poll_ft_batch(bid, api_key, poll_interval)
            print(f"\n{Fore.CYAN}── Coletando...{Style.RESET_ALL}")
            collect_ft_results(bid, api_key, papers)
            print(f"  {Fore.GREEN}✓ Resultados salvos{Style.RESET_ALL}")

    if not poll and batches_sent:
        print(f"\n{Fore.YELLOW}Batches enviados (sem --poll):{Style.RESET_ALL}")
        for bid, _ in batches_sent:
            print(f"  {bid}")
        print(f"\nPara coletar:\n  python main.py fulltext --collect <batch_id>")

    if poll:
        _print_ft_stats(papers)


# ================================================================== #
#  Estatísticas                                                       #
# ================================================================== #

def _print_ft_stats(papers: list[dict]) -> None:
    report = generate_ft_stats(papers)
    print(report)
    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    FT_STATS_FILE.write_text(report, encoding="utf-8")


def generate_ft_stats(papers: list[dict]) -> str:
    total = len(papers)
    if total == 0:
        return "Nenhum paper na fila FT."

    # T/A breakdown
    ta_inc   = sum(1 for p in papers if p.get("ta_decision") == "include")
    ta_maybe = sum(1 for p in papers if p.get("ta_decision") == "maybe")

    # Abstract e OA coverage
    with_abs = sum(1 for p in papers if (p.get("abstract") or "").strip())
    with_oa  = sum(1 for p in papers if (p.get("ft_oa_url") or "").strip())
    with_doi = sum(1 for p in papers if (p.get("doi") or "").strip())

    # FT decision breakdown
    ft_inc     = sum(1 for p in papers if p.get("ft_decision") == "include")
    ft_exc     = sum(1 for p in papers if p.get("ft_decision") == "exclude")
    ft_pend    = sum(1 for p in papers if p.get("ft_decision") == "pending")
    ft_blank   = sum(1 for p in papers if not (p.get("ft_decision") or "").strip())
    ft_decided = ft_inc + ft_exc + ft_pend
    ft_manual_review = sum(
        1 for p in papers if (p.get("ft_manual_review_required") or "").strip().lower() == "true"
    )
    confidence_counts: dict[str, int] = {}
    for p in papers:
        confidence = (p.get("ft_confidence") or "").strip()
        if confidence:
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1

    # By band
    band_counts: dict[str, int] = {}
    for p in papers:
        b = p.get("ft_priority_band", "?")
        band_counts[b] = band_counts.get(b, 0) + 1

    lines = [
        "",
        "=" * 60,
        "FULL-TEXT SCREENING — SLR PATHCAST",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        f"  Fila total:      {total:>5,}",
        f"    T/A include:   {ta_inc:>5,}  (alta confiança)",
        f"    T/A maybe:     {ta_maybe:>5,}  (precisa revisão)",
        "",
        "  Cobertura de conteúdo:",
        f"    Com abstract:  {with_abs:>5,}  ({with_abs/total*100:.1f}%)",
        f"    Com OA PDF:    {with_oa:>5,}  ({with_oa/total*100:.1f}%)",
        f"    Com DOI:       {with_doi:>5,}  ({with_doi/total*100:.1f}%)",
        "",
        "  Decisões FT registradas:",
        f"    include:       {ft_inc:>5,}",
        f"    exclude:       {ft_exc:>5,}",
        f"    pending:       {ft_pend:>5,}",
        f"    sem decisão:   {ft_blank:>5,}",
        f"    review manual: {ft_manual_review:>5,}",
        f"    PROGRESSO:     {ft_decided:>5,} / {total:,}  ({ft_decided/total*100:.1f}%)",
        "",
        "  Confiança FT do LLM:",
    ]
    for label in sorted(confidence_counts):
        lines.append(f"    {label}:         {confidence_counts[label]:>5,}")
    lines += [
        "",
        "  Por banda de prioridade:",
    ]
    for band in sorted(band_counts):
        desc = {
            "A": "include + múltiplos ICs",
            "B": "include + IC simples",
            "C": "maybe + abstract disponível",
            "D": "maybe + IC, sem abstract",
            "E": "maybe sem IC nem abstract",
        }.get(band, "")
        lines.append(f"    Banda {band}: {band_counts[band]:>4,}  {desc}")

    lines += ["", "=" * 60, ""]
    return "\n".join(lines)


# ================================================================== #
#  Ponto de entrada                                                   #
# ================================================================== #

def run_fulltext(
    *,
    export: bool = False,
    enrich_abstracts: bool = False,
    enrich_urls: bool = False,
    llm_rescreen: bool = False,
    confirm_includes: bool = False,
    collect: Optional[str] = None,
    stats: bool = False,
    poll: bool = False,
    poll_interval: int = 60,
    dry_run: bool = False,
    force: bool = False,
    api_key: str = "",
    delay: float = 3.0,
) -> None:
    from colorama import Fore, Style

    # ── Garante que a fila existe ─────────────────────────────────
    need_queue = export or enrich_abstracts or enrich_urls or llm_rescreen or bool(collect) or stats
    if need_queue:
        if not FT_RESULTS_CSV.exists() or export or force:
            print(f"\n{Fore.CYAN}── Construindo fila priorizada...{Style.RESET_ALL}")
            papers = build_ft_queue(force=force)
            _summarize_queue(papers)
        else:
            papers = load_ft_queue()
            logger.info(f"[FT] {len(papers)} papers carregados de {FT_RESULTS_CSV}")
    else:
        papers = []

    if not need_queue:
        print(f"{Fore.YELLOW}Nenhuma ação especificada. Use --export, --stats, "
              f"--llm-rescreen ou --collect.{Style.RESET_ALL}")
        return

    if enrich_abstracts:
        print(f"\n{Fore.CYAN}── Buscando abstracts via cascata (S2 → OpenAlex → Crossref → CORE)...{Style.RESET_ALL}")
        n = enrich_ft_abstracts(papers, delay=delay)
        print(f"  {Fore.GREEN}✓ {n:,} abstracts encontrados{Style.RESET_ALL}")

    # ── Enriquecimento de URLs OA ─────────────────────────────────
    if enrich_urls:
        print(f"\n{Fore.CYAN}── Buscando PDFs open-access (Semantic Scholar)...{Style.RESET_ALL}")
        n = enrich_oa_urls(papers, delay=delay)
        print(f"  {Fore.GREEN}✓ {n:,} URLs open-access encontradas{Style.RESET_ALL}")

    # ── LLM re-triagem ────────────────────────────────────────────
    if llm_rescreen or collect:
        if not api_key and not dry_run:
            print(f"{Fore.RED}✗ ANTHROPIC_API_KEY não configurada.{Style.RESET_ALL}")
            return
        run_llm_rescreen(
            papers, api_key,
            poll=poll,
            poll_interval=poll_interval,
            batch_id=collect,
            dry_run=dry_run,
            force=force,
            confirm_includes=confirm_includes,
        )

    # ── Estatísticas ──────────────────────────────────────────────
    if stats or export:
        _print_ft_stats(papers)


def _summarize_queue(papers: list[dict]) -> None:
    from colorama import Fore, Style
    total = len(papers)
    bands = {}
    for p in papers:
        b = p.get("ft_priority_band", "?")
        bands[b] = bands.get(b, 0) + 1
    print(f"  {Fore.GREEN}✓ {total} papers na fila:{Style.RESET_ALL}")
    for b in sorted(bands):
        desc = {
            "A": "include, múltiplos ICs",
            "B": "include, IC simples",
            "C": "maybe + abstract",
            "D": "maybe + IC, sem abstract",
            "E": "maybe, sem IC/abstract",
        }.get(b, "")
        print(f"    Banda {b}: {bands[b]:>4}  ({desc})")
    print(f"\n  Arquivo: {FT_RESULTS_CSV}")
