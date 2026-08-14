"""
Deduplicação de papers com duas estratégias em cascata:
  1. DOI exato (normalizado)
  2. Título fuzzy + ano (para papers sem DOI ou com DOIs divergentes)

Ao encontrar duplicatas, mantém o paper com mais informações preenchidas
e marca os demais com is_duplicate=True.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from rapidfuzz import fuzz

from extractors.base import Paper

logger = logging.getLogger(__name__)

# Threshold de similaridade de título para considerar duplicata (0–100)
TITLE_SIMILARITY_THRESHOLD = 92


def deduplicate(papers: list[Paper]) -> list[Paper]:
    """
    Remove duplicatas da lista.
    Retorna nova lista com duplicatas marcadas (is_duplicate=True)
    e papers únicos primeiro.

    Estratégia:
      Passo 1: Agrupa por DOI normalizado (ignora papers sem DOI).
      Passo 2: Nos papers restantes sem DOI (ou com DOI único),
               agrupa por título fuzzy dentro do mesmo ano ± 1.
    """
    if not papers:
        return []

    logger.info(f"[Dedup] Iniciando deduplicação de {len(papers)} papers...")

    # Indexa por posição para marcar duplicatas
    result = list(papers)
    duplicate_flags: dict[str, str] = {}  # internal_id → duplicate_of

    # ------------------------------------------------------------------ #
    # Passo 1: DOI exato                                                  #
    # ------------------------------------------------------------------ #
    doi_index: dict[str, int] = {}  # doi_norm → índice do "sobrevivente"

    for i, p in enumerate(result):
        doi = p.normalized_doi
        if not doi:
            continue
        if doi in doi_index:
            # Já existe: comparar riqueza de metadados, manter o melhor
            existing_idx = doi_index[doi]
            existing = result[existing_idx]
            if _richness(p) > _richness(existing):
                # O novo é mais rico: marca o existente como duplicata
                duplicate_flags[existing.internal_id] = p.internal_id
                doi_index[doi] = i
            else:
                duplicate_flags[p.internal_id] = existing.internal_id
        else:
            doi_index[doi] = i

    # ------------------------------------------------------------------ #
    # Passo 2: Título fuzzy (somente em papers ainda não marcados)         #
    # ------------------------------------------------------------------ #
    # Agrupa por (year, first_word_of_title) para reduzir comparações O(n²)
    buckets: dict[tuple, list[int]] = defaultdict(list)
    for i, p in enumerate(result):
        if p.internal_id in duplicate_flags:
            continue
        first_word = (p.normalized_title.split() or [""])[0]
        year_key = p.year if p.year else 0
        buckets[(year_key, first_word)].append(i)

    for bucket_key, indices in buckets.items():
        if len(indices) < 2:
            continue
        for a_pos in range(len(indices)):
            i = indices[a_pos]
            if result[i].internal_id in duplicate_flags:
                continue
            for b_pos in range(a_pos + 1, len(indices)):
                j = indices[b_pos]
                if result[j].internal_id in duplicate_flags:
                    continue
                pi, pj = result[i], result[j]
                sim = fuzz.token_sort_ratio(pi.normalized_title, pj.normalized_title)
                if sim >= TITLE_SIMILARITY_THRESHOLD:
                    if _richness(pj) > _richness(pi):
                        duplicate_flags[pi.internal_id] = pj.internal_id
                        break  # pi marcado; próximo i
                    else:
                        duplicate_flags[pj.internal_id] = pi.internal_id

    # Aplica os flags
    for p in result:
        if p.internal_id in duplicate_flags:
            p.is_duplicate = True
            p.duplicate_of = duplicate_flags[p.internal_id]

    unique = sum(1 for p in result if not p.is_duplicate)
    dupes = len(result) - unique
    logger.info(
        f"[Dedup] Concluído: {unique} únicos, {dupes} duplicatas "
        f"({dupes / len(result) * 100:.1f}% taxa)"
    )
    return result


def unique_papers(papers: list[Paper]) -> list[Paper]:
    """Retorna apenas papers não marcados como duplicata."""
    return [p for p in papers if not p.is_duplicate]


def _richness(p: Paper) -> int:
    """
    Score de riqueza de metadados.
    Usado para decidir qual versão de um paper manter ao deduplicar.
    """
    score = 0
    if p.doi:
        score += 10
    if p.abstract and len(p.abstract) > 50:
        score += 5
    if p.authors:
        score += 3
    if p.keywords:
        score += 2
    if p.venue:
        score += 2
    if p.year:
        score += 1
    if p.pages:
        score += 1
    return score
