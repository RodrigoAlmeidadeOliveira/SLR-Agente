"""
Triagem de títulos e resumos (T/A) para a SLR PATHCAST.

Usa a Anthropic Message Batches API para processar em lote os papers da
working set operacional, aplicando os critérios IC/EC definidos em
config/screening_criteria.py.

Fluxo:
  1. Carrega working set CSV (operational_screening_primary_unique.csv)
  2. Filtra papers ainda não triados (campo ta_decision vazio)
  3. Envia batch para a API (até 10.000 por lote)
  4. Salva resultados incrementalmente em results/screening/
  5. Suporta polling (--poll) e reimportação de batch existente (--batch-id)

Saída:
  results/screening/ta_screening_results.csv   — decisões por paper
  results/screening/ta_screening_batches.json  — histórico de batch IDs
  results/screening/ta_screening_stats.txt     — resumo estatístico
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

# ------------------------------------------------------------------ #
#  Constantes                                                         #
# ------------------------------------------------------------------ #

SCREENING_DIR = Path("results/screening")
RESULTS_CSV = SCREENING_DIR / "ta_screening_results.csv"
BATCHES_LOG = SCREENING_DIR / "ta_screening_batches.json"
STATS_FILE = SCREENING_DIR / "ta_screening_stats.txt"

MODEL = "claude-haiku-4-5-20251001"          # Rápido e econômico para triagem em massa
MAX_TOKENS = 512                              # JSON de decisão com margem para rationale longa
BATCH_SIZE = 500                              # Tamanho de cada requisição HTTP à Batches API
                                              # (10k é o max teórico, mas ~13MB/req causa timeout)

ENRICHED_WS_CSV = SCREENING_DIR / "working_set_enriched.csv"

DECISION_EVIDENCE_TAGS = {
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

RESULT_COLUMNS = [
    "internal_id", "source_db", "source_query_id", "source_query_label",
    "doi", "title", "authors", "year", "abstract", "venue", "doc_type",
    "keywords", "url", "publisher", "abstract_source", "abstract_match_type",
    "ta_decision",       # include | exclude | maybe
    "ta_rationale",      # justificativa em 1-2 frases
    "ta_matched_ic",     # ICs atendidos (pipe-separated)
    "ta_matched_ec",     # ECs aplicados (pipe-separated)
    "ta_evidence_tags",  # tags estruturadas para filtros posteriores
    "ta_software_context",
    "ta_stochastic_method",
    "ta_forecast_target",
    "ta_process_data_source",
    "ta_confidence",
    "ta_evidence_status",       # verified_abstract | missing_abstract
    "ta_manual_review_required",  # true | false
    "ta_screened_at",    # timestamp ISO
    "ta_batch_id",       # batch ID da Anthropic
]


# ------------------------------------------------------------------ #
#  I/O helpers                                                        #
# ------------------------------------------------------------------ #

def load_working_set(csv_path: Path) -> list[dict]:
    """Carrega a working set CSV como lista de dicts (suporta UTF-8 com/sem BOM)."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_screening_results() -> dict[str, dict]:
    """Carrega resultados já triados, indexados por internal_id."""
    if not RESULTS_CSV.exists():
        return {}
    with open(RESULTS_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {row["internal_id"]: row for row in reader}


def save_screening_results(results: list[dict]) -> None:
    """Salva/atualiza o CSV de resultados de triagem."""
    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_screening_results()

    # Merge: novos resultados sobrescrevem os existentes
    for r in results:
        existing[r["internal_id"]] = r

    all_rows = list(existing.values())
    with open(RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"[Screening] {len(all_rows)} papers salvos em {RESULTS_CSV}")


def log_batch(batch_id: str, metadata: dict) -> None:
    """Registra um batch ID no log JSON."""
    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    if BATCHES_LOG.exists():
        try:
            existing = json.loads(BATCHES_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append({"batch_id": batch_id, "created_at": datetime.now(timezone.utc).isoformat(), **metadata})
    BATCHES_LOG.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


# ------------------------------------------------------------------ #
#  Enriquecimento de abstracts para a working set                    #
# ------------------------------------------------------------------ #

def enrich_working_set(papers: list[dict], delay: float = 3.0, *, s2_only: bool = False) -> tuple[list[dict], int]:
    """
    Busca abstracts para os papers da working set sem abstract.

    - Usa Semantic Scholar (primário) → OpenAlex (fallback).
    - Retoma de onde parou se ENRICHED_WS_CSV já existir (checkpoint).
    - Salva CSV ao final.
    - Retorna (papers_atualizados, n_enriquecidos).
    """
    from pipeline.enrich import enrich_abstracts

    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    cols = list(papers[0].keys()) if papers else []

    # --- Checkpoint: reaproveita abstracts de execuções anteriores ---
    if ENRICHED_WS_CSV.exists():
        checkpoint: dict[str, str] = {}
        with open(ENRICHED_WS_CSV, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ab = (row.get("abstract") or "").strip()
                if ab:
                    checkpoint[row["internal_id"]] = ab
        if checkpoint:
            logger.info(f"[Screening/Enrich] Checkpoint: {len(checkpoint):,} abstracts já salvos — retomando")
            for p in papers:
                if p["internal_id"] in checkpoint and not (p.get("abstract") or "").strip():
                    p["abstract"] = checkpoint[p["internal_id"]]

    sem = sum(1 for p in papers if not (p.get("abstract") or "").strip())
    com_doi = sum(1 for p in papers
                  if (p.get("doi") or "").strip() and not (p.get("abstract") or "").strip())
    logger.info(f"[Screening/Enrich] {sem:,} sem abstract | {com_doi:,} com DOI (buscáveis)")

    if com_doi == 0:
        _save_enriched_csv(papers, cols)
        return papers, 0

    # Importa funções internas para poder salvar checkpoint entre passos
    from pipeline.enrich import (_enrich_s2, _enrich_openalex, _normalize_doi,
                                  S2_DELAY, OA_DELAY)

    # Monta doi_index apenas para papers sem abstract com DOI
    doi_index: dict[str, dict] = {}
    for p in papers:
        if not (p.get("abstract") or "").strip() and (p.get("doi") or "").strip():
            doi = _normalize_doi(p["doi"])
            if doi:
                doi_index[doi] = p

    # ── Passo 1: Semantic Scholar ──────────────────────────────────
    n_s2 = _enrich_s2(doi_index, delay=delay)
    logger.info(f"[Screening/Enrich] S2: {n_s2:,} abstracts — salvando checkpoint...")
    _save_enriched_csv(papers, cols)  # checkpoint pós-S2: nunca perde esses abstracts

    # ── Passo 2: OpenAlex para os que S2 não cobriu ────────────────
    remaining = {doi: p for doi, p in doi_index.items()
                 if not (p.get("abstract") or "").strip()}
    n_oa = 0
    if remaining and not s2_only:
        logger.info(f"[Screening/Enrich] OA fallback: {len(remaining):,} papers restantes...")
        n_oa = _enrich_openalex(remaining, delay=delay)
    elif remaining and s2_only:
        logger.info(f"[Screening/Enrich] --s2-only: pulando OA fallback ({len(remaining):,} papers sem abstract)")

    n_enriched = n_s2 + n_oa
    _save_enriched_csv(papers, cols)
    logger.info(f"[Screening/Enrich] Total: {n_enriched:,} abstracts preenchidos — CSV salvo")
    return papers, n_enriched


def _save_enriched_csv(papers: list[dict], cols: list[str]) -> None:
    """Salva o CSV enriquecido (checkpoint ou final)."""
    with open(ENRICHED_WS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(papers)


# ------------------------------------------------------------------ #
#  Construção dos requests                                            #
# ------------------------------------------------------------------ #

def _build_user_prompt(paper: dict) -> str:
    from config.screening_criteria import PAPER_PROMPT_TEMPLATE
    abstract = (paper.get("abstract") or "").strip()
    abstract_text = abstract if abstract else "Resumo não disponível."
    return PAPER_PROMPT_TEMPLATE.format(
        title=paper.get("title", "").strip() or "(sem título)",
        abstract=abstract_text,
        venue=paper.get("venue", "") or "N/A",
        doc_type=paper.get("doc_type", "") or "N/A",
        year=paper.get("year", "") or "N/A",
        source_db=paper.get("source_db", "") or "N/A",
        abstract_source=paper.get("abstract_source", "") or "missing_or_unverified",
    )


def build_batch_requests(papers: list[dict]) -> list[dict]:
    """Constrói a lista de requests para a Batches API."""
    from config.screening_criteria import SYSTEM_PROMPT
    requests = []
    for p in papers:
        requests.append({
            "custom_id": p["internal_id"],
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": _build_user_prompt(p)}
                ],
            },
        })
    return requests


# ------------------------------------------------------------------ #
#  Parsing da resposta                                                #
# ------------------------------------------------------------------ #

def _parse_decision(text: str) -> dict:
    """Extrai JSON de decisão do texto retornado pelo modelo."""
    # Remove blocos de código markdown se presentes
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        data = json.loads(text)
        decision = data.get("decision", "maybe").lower()
        if decision not in ("include", "exclude", "maybe"):
            decision = "maybe"
        return {
            "ta_decision": decision,
            "ta_rationale": str(data.get("rationale", ""))[:500],
            "ta_matched_ic": "|".join(data.get("matched_ic") or []),
            "ta_matched_ec": "|".join(data.get("matched_ec") or []),
            "ta_evidence_tags": _normalize_tag_list(data.get("evidence_tags"), DECISION_EVIDENCE_TAGS),
            "ta_software_context": _normalize_enum(
                data.get("software_context"),
                SOFTWARE_CONTEXT_VALUES,
                default="unclear",
            ),
            "ta_stochastic_method": _normalize_enum(
                data.get("stochastic_method"),
                STOCHASTIC_METHOD_VALUES,
                default="unclear",
            ),
            "ta_forecast_target": _normalize_enum(
                data.get("forecast_target"),
                FORECAST_TARGET_VALUES,
                default="unclear",
            ),
            "ta_process_data_source": _normalize_enum(
                data.get("process_data_source"),
                PROCESS_DATA_SOURCE_VALUES,
                default="unclear",
            ),
            "ta_confidence": _normalize_enum(
                data.get("confidence"),
                CONFIDENCE_VALUES,
                default="low",
            ),
        }
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"[Screening] Falha ao parsear resposta: {text[:100]!r}")
        return {
            "ta_decision": "maybe",
            "ta_rationale": f"Erro de parsing: {text[:200]}",
            "ta_matched_ic": "",
            "ta_matched_ec": "",
            "ta_evidence_tags": "",
            "ta_software_context": "unclear",
            "ta_stochastic_method": "unclear",
            "ta_forecast_target": "unclear",
            "ta_process_data_source": "unclear",
            "ta_confidence": "low",
        }


from config.screening_criteria import _normalize_tag_list, _normalize_enum, _slugify  # noqa: E402


def _apply_ta_decision_policy(paper: dict, decision_data: dict) -> dict:
    has_verified_abstract = bool((paper.get("abstract") or "").strip())
    decision_data["ta_evidence_status"] = (
        "verified_abstract" if has_verified_abstract else "missing_abstract"
    )
    decision_data["ta_manual_review_required"] = "false"

    if not has_verified_abstract:
        tags = set(filter(None, (decision_data.get("ta_evidence_tags") or "").split("|")))
        tags.update({"insufficient_abstract", "full_text_required"})
        decision_data["ta_evidence_tags"] = "|".join(sorted(tags))
        decision_data["ta_confidence"] = "low"
        decision_data["ta_manual_review_required"] = "true"
        if decision_data.get("ta_decision") == "include":
            decision_data["ta_decision"] = "maybe"
            note = "Abstract ausente: include forte rebaixado para maybe; exige revisão manual ou full text."
            rationale = (decision_data.get("ta_rationale") or "").strip()
            decision_data["ta_rationale"] = f"{rationale} {note}".strip()

    return decision_data


# ------------------------------------------------------------------ #
#  Submissão do batch                                                 #
# ------------------------------------------------------------------ #

def submit_batch(papers: list[dict], api_key: str) -> str:
    """Envia um batch de papers para a Anthropic Batches API. Retorna o batch_id."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    requests = build_batch_requests(papers)

    logger.info(f"[Screening] Enviando batch com {len(requests)} papers...")

    batch = None
    for attempt in range(1, 6):
        try:
            batch = client.messages.batches.create(requests=requests)
            break
        except Exception as exc:
            logger.warning(f"[Screening] Erro ao criar batch (tentativa {attempt}/5): {exc}")
            if attempt < 5:
                wait = 10 * attempt
                logger.info(f"[Screening] Aguardando {wait}s antes de tentar novamente...")
                time.sleep(wait)
            else:
                raise

    batch_id = batch.id
    logger.info(f"[Screening] Batch criado: {batch_id} | status: {batch.processing_status}")

    log_batch(batch_id, {
        "n_papers": len(papers),
        "model": MODEL,
        "status": batch.processing_status,
    })
    return batch_id


# ------------------------------------------------------------------ #
#  Polling e coleta de resultados                                     #
# ------------------------------------------------------------------ #

def poll_batch(batch_id: str, api_key: str, poll_interval: int = 60) -> str:
    """
    Aguarda o batch terminar e retorna o status final.
    poll_interval em segundos (padrão: 60s).
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    print(f"  Aguardando batch {batch_id}... (ctrl+C para interromper)")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        counts = batch.request_counts
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {status} — "
              f"succeeded: {counts.succeeded} | errored: {counts.errored} | processing: {counts.processing}")
        if status == "ended":
            return status
        time.sleep(poll_interval)


def collect_batch_results(
    batch_id: str,
    api_key: str,
    working_set: list[dict],
    *,
    timestamp: Optional[str] = None,
) -> list[dict]:
    """
    Coleta resultados de um batch concluído e retorna lista de dicts com decisões.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    ts = timestamp or datetime.now(timezone.utc).isoformat()

    # Índice da working set por internal_id
    paper_index: dict[str, dict] = {p["internal_id"]: p for p in working_set}

    results = []
    for result in client.messages.batches.results(batch_id):
        paper_id = result.custom_id
        paper = paper_index.get(paper_id, {})

        if result.result.type == "succeeded":
            content = result.result.message.content
            text = content[0].text if content else ""
            decision_data = _parse_decision(text)
        else:
            decision_data = {
                "ta_decision": "maybe",
                "ta_rationale": f"Erro da API: {result.result.type}",
                "ta_matched_ic": "",
                "ta_matched_ec": "",
                "ta_evidence_tags": "",
                "ta_software_context": "unclear",
                "ta_stochastic_method": "unclear",
                "ta_forecast_target": "unclear",
                "ta_process_data_source": "unclear",
                "ta_confidence": "low",
            }
        decision_data = _apply_ta_decision_policy(paper, decision_data)

        row = {
            "internal_id": paper_id,
            "source_db": paper.get("source_db", ""),
            "source_query_id": paper.get("source_query_id", ""),
            "source_query_label": paper.get("source_query_label", ""),
            "doi": paper.get("doi", ""),
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "year": paper.get("year", ""),
            "abstract": paper.get("abstract", ""),
            "venue": paper.get("venue", ""),
            "doc_type": paper.get("doc_type", ""),
            "keywords": paper.get("keywords", ""),
            "url": paper.get("url", ""),
            "publisher": paper.get("publisher", ""),
            "abstract_source": paper.get("abstract_source", ""),
            "abstract_match_type": paper.get("abstract_match_type", ""),
            "ta_screened_at": ts,
            "ta_batch_id": batch_id,
            **decision_data,
        }
        results.append(row)

    logger.info(f"[Screening] {len(results)} resultados coletados do batch {batch_id}")
    return results


# ------------------------------------------------------------------ #
#  Relatório de triagem                                               #
# ------------------------------------------------------------------ #

def generate_stats_report(results_csv: Path = RESULTS_CSV) -> str:
    """Gera relatório estatístico da triagem T/A."""
    if not results_csv.exists():
        return "Nenhum resultado de triagem disponível ainda."

    rows = load_screening_results()
    total = len(rows)
    include = sum(1 for r in rows.values() if r.get("ta_decision") == "include")
    exclude = sum(1 for r in rows.values() if r.get("ta_decision") == "exclude")
    maybe = sum(1 for r in rows.values() if r.get("ta_decision") == "maybe")
    no_decision = total - include - exclude - maybe
    manual_review = sum(
        1 for r in rows.values() if (r.get("ta_manual_review_required") or "").strip().lower() == "true"
    )
    missing_abstract = sum(1 for r in rows.values() if r.get("ta_evidence_status") == "missing_abstract")

    ic_counts: dict[str, int] = {}
    ec_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    software_context_counts: dict[str, int] = {}
    for r in rows.values():
        for ic in (r.get("ta_matched_ic") or "").split("|"):
            if ic:
                ic_counts[ic] = ic_counts.get(ic, 0) + 1
        for ec in (r.get("ta_matched_ec") or "").split("|"):
            if ec:
                ec_counts[ec] = ec_counts.get(ec, 0) + 1
        confidence = (r.get("ta_confidence") or "").strip()
        if confidence:
            confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        context = (r.get("ta_software_context") or "").strip()
        if context:
            software_context_counts[context] = software_context_counts.get(context, 0) + 1

    lines = [
        "",
        "=" * 60,
        "TRIAGEM T/A — SLR PATHCAST",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        f"  Total triado:  {total:>6,}",
        f"  Include:       {include:>6,}  ({include/total*100:.1f}%)" if total else "  Include:            0",
        f"  Exclude:       {exclude:>6,}  ({exclude/total*100:.1f}%)" if total else "  Exclude:            0",
        f"  Maybe:         {maybe:>6,}  ({maybe/total*100:.1f}%)" if total else "  Maybe:              0",
        f"  Sem decisão:   {no_decision:>6,}",
        f"  Review manual: {manual_review:>6,}",
        f"  Sem abstract:  {missing_abstract:>6,}",
        "",
        "  Critérios de Inclusão acionados:",
    ]
    for ic, cnt in sorted(ic_counts.items()):
        lines.append(f"    {ic}: {cnt:,}")
    lines += ["", "  Critérios de Exclusão acionados:"]
    for ec, cnt in sorted(ec_counts.items()):
        lines.append(f"    {ec}: {cnt:,}")
    lines += ["", "  Confiança do LLM:"]
    for label, cnt in sorted(confidence_counts.items()):
        lines.append(f"    {label}: {cnt:,}")
    lines += ["", "  Contexto de software:"]
    for label, cnt in sorted(software_context_counts.items()):
        lines.append(f"    {label}: {cnt:,}")
    lines += ["", "=" * 60, ""]
    return "\n".join(lines)


def print_and_save_stats() -> None:
    report = generate_stats_report()
    print(report)
    SCREENING_DIR.mkdir(parents=True, exist_ok=True)
    STATS_FILE.write_text(report, encoding="utf-8")
    logger.info(f"[Screening] Estatísticas salvas em {STATS_FILE}")


# ------------------------------------------------------------------ #
#  Ponto de entrada principal                                         #
# ------------------------------------------------------------------ #

def run_screening(
    input_csv: Path,
    api_key: str,
    *,
    poll: bool = False,
    poll_interval: int = 60,
    batch_id: Optional[str] = None,
    dry_run: bool = False,
    limit: int = 0,
    force: bool = False,
    enrich: bool = False,
    enrich_delay: float = 0.2,
) -> None:
    """
    Orquestra a triagem T/A completa.

    Args:
        input_csv:     Caminho para operational_screening_primary_unique.csv
        api_key:       Chave Anthropic
        poll:          Se True, aguarda o batch terminar na mesma execução
        poll_interval: Segundos entre polls (padrão: 60)
        batch_id:      Coleta resultados de um batch_id já existente
        dry_run:       Prepara o batch sem enviar
        limit:         Processar apenas os primeiros N papers não triados (0=todos)
        force:         Re-triar papers já com decisão
        enrich:        Buscar abstracts no OpenAlex antes de enviar o batch
        enrich_delay:  Delay entre requisições OpenAlex (segundos)
    """
    from colorama import Fore, Style

    SCREENING_DIR.mkdir(parents=True, exist_ok=True)

    # --- Coleta de batch existente ---
    if batch_id:
        print(f"\n{Fore.CYAN}── Coletando resultados do batch {batch_id}...{Style.RESET_ALL}")
        working_set = load_working_set(input_csv)
        results = collect_batch_results(batch_id, api_key, working_set)
        save_screening_results(results)
        print_and_save_stats()
        return

    # --- Carrega working set e resultados existentes ---
    print(f"\n{Fore.CYAN}── Carregando working set: {input_csv.name}...{Style.RESET_ALL}")

    # Usa versão enriquecida se existir e --enrich não foi pedido agora
    effective_csv = ENRICHED_WS_CSV if (ENRICHED_WS_CSV.exists() and not enrich) else input_csv
    if effective_csv == ENRICHED_WS_CSV:
        print(f"  {Fore.GREEN}Usando working set enriquecida: {effective_csv.name}{Style.RESET_ALL}")

    working_set = load_working_set(effective_csv)
    print(f"  {len(working_set):,} papers no working set")

    # --- Enriquecimento de abstracts via OpenAlex ---
    if enrich:
        print(f"\n{Fore.CYAN}── Enriquecendo abstracts via OpenAlex...{Style.RESET_ALL}")
        sem_antes = sum(1 for p in working_set if not (p.get("abstract") or "").strip())
        print(f"  Sem abstract: {sem_antes:,} de {len(working_set):,}")
        working_set, n_enriquecidos = enrich_working_set(working_set, delay=enrich_delay)
        sem_depois = sum(1 for p in working_set if not (p.get("abstract") or "").strip())
        print(f"  {Fore.GREEN}✓ {n_enriquecidos:,} abstracts preenchidos "
              f"(ainda sem abstract: {sem_depois:,}){Style.RESET_ALL}")

    if not force:
        existing = load_screening_results()
        pending = [p for p in working_set if p["internal_id"] not in existing]
        print(f"  {len(existing):,} já triados → {len(pending):,} pendentes")
    else:
        pending = working_set
        print(f"  --force: re-triando todos os {len(pending):,} papers")

    if limit > 0:
        pending = pending[:limit]
        print(f"  {Fore.YELLOW}--limit {limit}: processando apenas {len(pending)} papers{Style.RESET_ALL}")

    if not pending:
        print(f"\n{Fore.GREEN}✓ Todos os papers já foram triados.{Style.RESET_ALL}")
        print_and_save_stats()
        return

    # --- Divide em lotes de até BATCH_SIZE ---
    batches_sent = []
    for start in range(0, len(pending), BATCH_SIZE):
        chunk = pending[start:start + BATCH_SIZE]
        chunk_n = start // BATCH_SIZE + 1
        print(f"\n{Fore.CYAN}── Lote {chunk_n}: {len(chunk):,} papers{Style.RESET_ALL}")

        if dry_run:
            print(f"  {Fore.YELLOW}--dry-run: batch NÃO enviado.{Style.RESET_ALL}")
            print(f"  Exemplo de prompt para '{chunk[0]['title'][:60]}':")
            print(_build_user_prompt(chunk[0])[:600])
            continue

        bid = submit_batch(chunk, api_key)
        batches_sent.append((bid, chunk))
        print(f"  {Fore.GREEN}✓ Batch enviado: {bid}{Style.RESET_ALL}")

        if poll:
            print(f"\n{Fore.CYAN}── Aguardando conclusão do batch {bid}...{Style.RESET_ALL}")
            poll_batch(bid, api_key, poll_interval=poll_interval)
            print(f"\n{Fore.CYAN}── Coletando resultados...{Style.RESET_ALL}")
            results = collect_batch_results(bid, api_key, chunk)
            save_screening_results(results)
            print(f"  {Fore.GREEN}✓ {len(results):,} decisões salvas{Style.RESET_ALL}")

    if not dry_run and not poll and batches_sent:
        print(f"\n{Fore.YELLOW}Batches enviados (sem --poll):{Style.RESET_ALL}")
        for bid, _ in batches_sent:
            print(f"  {bid}")
        print(
            f"\nPara coletar os resultados após processamento, execute:\n"
            f"  python main.py screen --collect <batch_id>\n"
            f"Ou re-execute com --poll para aguardar automaticamente."
        )

    if poll or not batches_sent:
        print_and_save_stats()
