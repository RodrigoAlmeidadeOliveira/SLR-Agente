"""
Validação do conjunto de controle (10 papers) contra os resultados extraídos.
Threshold: >= 8/10 capturados.

Para cada paper de controle, verifica:
  1. Correspondência por DOI exato
  2. Correspondência por título fuzzy (≥ 90%)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from rapidfuzz import fuzz

from config.control_papers import CONTROL_PAPERS
from extractors.base import Paper

logger = logging.getLogger(__name__)

TITLE_MATCH_THRESHOLD = 88  # Threshold mais baixo que dedup (títulos longos variam)
ACCEPTANCE_THRESHOLD = 8    # Mínimo de papers de controle capturados


@dataclass
class ValidationResult:
    control_id: str
    citation: str
    found: bool
    found_in_db: list[str]       # ["scopus", "ieee", ...]
    found_in_query: list[str]    # IDs das queries que capturaram
    matched_by: str              # "doi" | "title" | "not_found"
    matched_paper_id: str        # internal_id do paper encontrado
    note: str


def validate(papers: list[Paper]) -> list[ValidationResult]:
    """
    Verifica quais dos 10 papers de controle foram capturados.
    Retorna uma lista de ValidationResult.
    """
    logger.info(f"[Validator] Verificando {len(CONTROL_PAPERS)} papers de controle "
                f"contra {len(papers)} resultados...")

    results = []
    for cp in CONTROL_PAPERS:
        vr = _check_control_paper(cp, papers)
        results.append(vr)

    found_count = sum(1 for r in results if r.found)
    logger.info(
        f"[Validator] {found_count}/{len(CONTROL_PAPERS)} papers de controle capturados "
        f"(threshold: {ACCEPTANCE_THRESHOLD}/10)"
    )
    if found_count >= ACCEPTANCE_THRESHOLD:
        logger.info("[Validator] ✓ Threshold atingido — strings de busca válidas.")
    else:
        logger.warning(
            f"[Validator] ✗ Threshold NÃO atingido ({found_count} < {ACCEPTANCE_THRESHOLD}). "
            "Revisar strings de busca."
        )
    return results


def _check_control_paper(cp: dict, papers: list[Paper]) -> ValidationResult:
    cp_doi = (cp.get("doi") or "").lower().strip()
    cp_title = _normalize(cp["title"])
    cp_year = cp.get("year")

    found_in_db: list[str] = []
    found_in_query: list[str] = []
    matched_by = "not_found"
    matched_paper_id = ""

    for p in papers:
        # 1. Correspondência por DOI
        if cp_doi and p.normalized_doi and cp_doi == p.normalized_doi:
            _record_match(p, found_in_db, found_in_query)
            matched_by = "doi"
            matched_paper_id = p.internal_id
            continue

        # 2. Correspondência por título
        sim = fuzz.token_sort_ratio(cp_title, p.normalized_title)
        if sim >= TITLE_MATCH_THRESHOLD:
            # Verificação adicional de ano (tolerância ±1 ano)
            if cp_year and p.year and abs(cp_year - p.year) > 1:
                continue
            _record_match(p, found_in_db, found_in_query)
            if matched_by == "not_found":
                matched_by = f"title (sim={sim:.0f}%)"
                matched_paper_id = p.internal_id

    found = len(found_in_db) > 0
    return ValidationResult(
        control_id=cp["id"],
        citation=cp["citation"],
        found=found,
        found_in_db=list(set(found_in_db)),
        found_in_query=list(set(found_in_query)),
        matched_by=matched_by,
        matched_paper_id=matched_paper_id,
        note=cp.get("note", ""),
    )


def _normalize(title: str) -> str:
    import re
    t = (title or "").lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _record_match(p: Paper, db_list: list[str], query_list: list[str]):
    if p.source_db not in db_list:
        db_list.append(p.source_db)
    if p.source_query_id not in query_list:
        query_list.append(p.source_query_id)


def print_validation_report(results: list[ValidationResult]) -> str:
    """Gera relatório textual da validação."""
    lines = [
        "",
        "=" * 70,
        "VALIDATION REPORT — Control Papers Coverage",
        "=" * 70,
    ]

    for r in results:
        status = "✓" if r.found else "✗"
        lines.append(
            f"  {status} [{r.control_id}] {r.citation}"
        )
        if r.found:
            lines.append(f"       Databases:  {', '.join(r.found_in_db)}")
            lines.append(f"       Queries:    {', '.join(r.found_in_query)}")
            lines.append(f"       Matched by: {r.matched_by}")
        else:
            lines.append(f"       NOT FOUND — {r.note}")

    found_count = sum(1 for r in results if r.found)
    total = len(results)
    lines += [
        "",
        f"  Total: {found_count}/{total} captured",
        f"  Threshold: {ACCEPTANCE_THRESHOLD}/{total}",
        "  Status: " + ("PASS ✓" if found_count >= ACCEPTANCE_THRESHOLD else "FAIL ✗ — expand search strings"),
        "=" * 70,
        "",
    ]
    return "\n".join(lines)
