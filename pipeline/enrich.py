"""
Enriquecimento de abstracts em cascata.

Ordem de tentativas:
  1. Semantic Scholar por DOI
  2. OpenAlex por DOI
  3. CORE por DOI
  4. Crossref por DOI
  5. OpenAlex por título
  6. Crossref por título
  7. CORE por título
  8. Semantic Scholar por título

Notas:
  - A ordem foi reotimizada com base no rendimento observado no corpus FT.
  - DOI continua sendo a melhor chave. As buscas por título usam match
    exato normalizado e fallback fuzzy com RapidFuzz.
  - CORE é opcional e só roda quando CORE_API_KEY estiver configurada.
"""
from __future__ import annotations

import logging
import os
import re
import time
from html import unescape
from typing import Optional

import requests
from rapidfuzz import fuzz
from tqdm import tqdm

logger = logging.getLogger(__name__)

# ── Semantic Scholar ────────────────────────────────────────────────
S2_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
S2_BATCH_SIZE = 500
S2_MAX_RETRIES = 5

# ── OpenAlex ────────────────────────────────────────────────────────
OA_URL = "https://api.openalex.org/works"
OA_BATCH_SIZE = 25
OA_MAX_RETRIES = 6
OA_BACKOFF_START = 30.0
OA_BACKOFF_MAX = 300.0
COOLDOWN_AFTER_FAIL = 120

# ── Crossref ────────────────────────────────────────────────────────
CR_WORKS_URL = "https://api.crossref.org/works"
CR_MAX_RETRIES = 4

# ── CORE ────────────────────────────────────────────────────────────
CORE_SEARCH_URL = "https://api.core.ac.uk/v3/search/works/"
CORE_MAX_RETRIES = 4

# ── Configuração geral ──────────────────────────────────────────────
REQUEST_DELAY = 3.0
BATCH_SIZE = S2_BATCH_SIZE
TITLE_MATCH_MIN_SCORE = 92


def enrich_abstracts(papers: list, delay: float = REQUEST_DELAY) -> tuple[list, int]:
    """
    Busca abstracts para papers sem abstract, primeiro por DOI e depois por título.
    """
    need = [p for p in papers if not (_get(p, "abstract") or "").strip()]
    if not need:
        logger.info("[Enrich] Todos os papers já têm abstract.")
        return papers, 0

    need_with_doi = [p for p in need if _normalize_doi(_get(p, "doi"))]
    need_with_title = [p for p in need if _normalize_title(_get(p, "title"))]

    logger.info(
        "[Enrich] %s sem abstract | %s com DOI | %s com título buscável",
        f"{len(need):,}",
        f"{len(need_with_doi):,}",
        f"{len(need_with_title):,}",
    )

    enriched = 0

    doi_index: dict[str, object] = {}
    for paper in need_with_doi:
        doi = _normalize_doi(_get(paper, "doi"))
        if doi and doi not in doi_index:
            doi_index[doi] = paper

    if doi_index:
        enriched += _enrich_s2(doi_index, delay=delay)

        remaining = {doi: p for doi, p in doi_index.items() if not (_get(p, "abstract") or "").strip()}
        if remaining:
            logger.info("[Enrich] %s restantes após S2 DOI — tentando OpenAlex...", f"{len(remaining):,}")
            enriched += _enrich_openalex(remaining, delay=delay)

        remaining = {doi: p for doi, p in doi_index.items() if not (_get(p, "abstract") or "").strip()}
        if remaining:
            logger.info("[Enrich] %s restantes após OpenAlex DOI — tentando CORE...", f"{len(remaining):,}")
            enriched += _enrich_core_by_doi(remaining, delay=delay)

        remaining = {doi: p for doi, p in doi_index.items() if not (_get(p, "abstract") or "").strip()}
        if remaining:
            logger.info("[Enrich] %s restantes após CORE DOI — tentando Crossref...", f"{len(remaining):,}")
            enriched += _enrich_crossref_by_doi(remaining, delay=delay)

    title_candidates = [
        p for p in papers
        if not (_get(p, "abstract") or "").strip() and _normalize_title(_get(p, "title"))
    ]
    if title_candidates:
        logger.info("[Enrich] %s ainda sem abstract — iniciando fallback por título...", f"{len(title_candidates):,}")
        enriched += _enrich_by_title_cascade(title_candidates, delay=delay)

    still_missing = sum(1 for p in papers if not (_get(p, "abstract") or "").strip())
    logger.info(
        "[Enrich] Total enriquecidos: %s | ainda sem abstract: %s",
        f"{enriched:,}",
        f"{still_missing:,}",
    )
    return papers, enriched


def enrich_abstracts_with_checkpoints(
    papers: list,
    *,
    delay: float = REQUEST_DELAY,
    after_source=None,
) -> tuple[list, int]:
    """
    Variante com checkpoint por fonte.

    O callback `after_source(papers, source_name, source_enriched, total_enriched)`
    é chamado ao final de cada fonte da cascata.
    """
    need = [p for p in papers if not (_get(p, "abstract") or "").strip()]
    if not need:
        logger.info("[Enrich] Todos os papers já têm abstract.")
        return papers, 0

    need_with_doi = [p for p in need if _normalize_doi(_get(p, "doi"))]
    need_with_title = [p for p in need if _normalize_title(_get(p, "title"))]

    logger.info(
        "[Enrich] %s sem abstract | %s com DOI | %s com título buscável",
        f"{len(need):,}",
        f"{len(need_with_doi):,}",
        f"{len(need_with_title):,}",
    )

    total_enriched = 0

    def _checkpoint(source_name: str, source_enriched: int) -> None:
        if after_source:
            after_source(papers, source_name, source_enriched, total_enriched)

    doi_index: dict[str, object] = {}
    for paper in need_with_doi:
        doi = _normalize_doi(_get(paper, "doi"))
        if doi and doi not in doi_index:
            doi_index[doi] = paper

    if doi_index:
        source_enriched = _enrich_s2(doi_index, delay=delay)
        total_enriched += source_enriched
        _checkpoint("semanticscholar_doi", source_enriched)

        remaining = {doi: p for doi, p in doi_index.items() if not (_get(p, "abstract") or "").strip()}
        if remaining:
            logger.info("[Enrich] %s restantes após S2 DOI — tentando OpenAlex...", f"{len(remaining):,}")
            source_enriched = _enrich_openalex(remaining, delay=delay)
            total_enriched += source_enriched
            _checkpoint("openalex_doi", source_enriched)

        remaining = {doi: p for doi, p in doi_index.items() if not (_get(p, "abstract") or "").strip()}
        if remaining:
            logger.info("[Enrich] %s restantes após OpenAlex DOI — tentando CORE...", f"{len(remaining):,}")
            source_enriched = _enrich_core_by_doi(remaining, delay=delay)
            total_enriched += source_enriched
            _checkpoint("core_doi", source_enriched)

        remaining = {doi: p for doi, p in doi_index.items() if not (_get(p, "abstract") or "").strip()}
        if remaining:
            logger.info("[Enrich] %s restantes após CORE DOI — tentando Crossref...", f"{len(remaining):,}")
            source_enriched = _enrich_crossref_by_doi(remaining, delay=delay)
            total_enriched += source_enriched
            _checkpoint("crossref_doi", source_enriched)

    title_candidates = [
        p for p in papers
        if not (_get(p, "abstract") or "").strip() and _normalize_title(_get(p, "title"))
    ]
    if title_candidates:
        logger.info("[Enrich] %s ainda sem abstract — iniciando fallback por título...", f"{len(title_candidates):,}")
        title_total = _enrich_by_title_cascade(title_candidates, delay=delay, after_source=_checkpoint)
        total_enriched += title_total

    still_missing = sum(1 for p in papers if not (_get(p, "abstract") or "").strip())
    logger.info(
        "[Enrich] Total enriquecidos: %s | ainda sem abstract: %s",
        f"{total_enriched:,}",
        f"{still_missing:,}",
    )
    return papers, total_enriched


def _enrich_s2(doi_index: dict, delay: float) -> int:
    """Preenche abstracts via Semantic Scholar Batch API."""
    api_key = os.getenv("S2_API_KEY") or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key

    doi_list = list(doi_index.keys())
    enriched = 0

    with tqdm(total=len(doi_list), desc="SemanticScholar/abstracts", unit="paper") as pbar:
        for batch in _chunks(doi_list, S2_BATCH_SIZE):
            ids = [f"DOI:{doi}" for doi in batch]
            results = _s2_fetch(ids, headers)
            for work in results:
                if not work:
                    continue
                ext_ids = work.get("externalIds") or {}
                doi = _normalize_doi(ext_ids.get("DOI") or "")
                if not doi or doi not in doi_index:
                    continue
                abstract = (work.get("abstract") or "").strip()
                if abstract:
                    _set_abstract(doi_index[doi], abstract, source="semanticscholar", match_type="doi_exact")
                    enriched += 1
            pbar.update(len(batch))
            time.sleep(delay)

    logger.info("[Enrich/S2] %s abstracts obtidos", f"{enriched:,}")
    return enriched


def _s2_fetch(ids: list[str], headers: dict, *, max_retries: int = S2_MAX_RETRIES) -> list[dict]:
    wait = 10.0
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                S2_BATCH_URL,
                json={"ids": ids},
                params={"fields": "externalIds,abstract"},
                headers=headers,
                timeout=60,
            )
            if resp.status_code == 429:
                logger.warning("[Enrich/S2] 429 — aguardando %.0fs (tentativa %s)", wait, attempt + 1)
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            if resp.status_code == 400:
                logger.warning("[Enrich/S2] 400 Bad Request — pulando lote")
                return []
            resp.raise_for_status()
            return resp.json() or []
        except requests.HTTPError as exc:
            logger.warning("[Enrich/S2] HTTP %s — pulando lote", exc.response.status_code)
            return []
        except Exception as exc:
            logger.warning("[Enrich/S2] Erro: %s", exc)
            if attempt < max_retries - 1:
                time.sleep(wait)
                wait = min(wait * 2, 120)
    logger.warning("[Enrich/S2] Máximo de tentativas atingido.")
    return []


def _enrich_openalex(doi_index: dict, delay: float) -> int:
    email = os.getenv("OPENALEX_EMAIL", "slr@research.example")
    headers = {"User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})"}

    doi_list = list(doi_index.keys())
    enriched = 0

    with tqdm(total=len(doi_list), desc="OpenAlex/abstracts", unit="paper") as pbar:
        for batch in _chunks(doi_list, OA_BATCH_SIZE):
            results, rate_limited = _oa_fetch(batch, headers)
            for work in results:
                doi = _normalize_doi(work.get("doi") or "")
                if not doi or doi not in doi_index:
                    continue
                abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
                if abstract:
                    _set_abstract(doi_index[doi], abstract, source="openalex", match_type="doi_exact")
                    enriched += 1
            pbar.update(len(batch))
            if rate_limited:
                logger.warning("[Enrich/OA] Cooldown %ss", COOLDOWN_AFTER_FAIL)
                time.sleep(COOLDOWN_AFTER_FAIL)
            else:
                time.sleep(delay)

    logger.info("[Enrich/OA] %s abstracts obtidos", f"{enriched:,}")
    return enriched


def _oa_fetch(dois: list[str], headers: dict, *, max_retries: int = OA_MAX_RETRIES) -> tuple[list[dict], bool]:
    filter_str = "|".join(f"https://doi.org/{doi}" for doi in dois)
    params = {
        "filter": f"doi:{filter_str}",
        "select": "doi,abstract_inverted_index",
        "per-page": len(dois),
    }
    wait = OA_BACKOFF_START
    for attempt in range(max_retries):
        try:
            resp = requests.get(OA_URL, params=params, headers=headers, timeout=30)
            if resp.status_code == 429:
                logger.warning(
                    "[Enrich/OA] 429 — aguardando %.0fs (tentativa %s/%s)",
                    wait, attempt + 1, max_retries,
                )
                time.sleep(wait)
                wait = min(wait * 2, OA_BACKOFF_MAX)
                continue
            resp.raise_for_status()
            return resp.json().get("results", []), False
        except requests.HTTPError as exc:
            logger.warning("[Enrich/OA] HTTP %s — pulando lote", exc.response.status_code)
            return [], False
        except Exception as exc:
            logger.warning("[Enrich/OA] Erro de rede: %s", exc)
            if attempt < max_retries - 1:
                time.sleep(wait)
                wait = min(wait * 2, OA_BACKOFF_MAX)
    logger.warning("[Enrich/OA] Lote esgotou tentativas — cooldown %ss", COOLDOWN_AFTER_FAIL)
    return [], True


def _enrich_crossref_by_doi(doi_index: dict, delay: float) -> int:
    email = os.getenv("OPENALEX_EMAIL", "slr@research.example")
    headers = {
        "User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})",
        "Accept": "application/json",
    }
    enriched = 0

    with tqdm(total=len(doi_index), desc="Crossref/abstracts", unit="paper") as pbar:
        for doi, paper in doi_index.items():
            abstract = _crossref_fetch_by_doi(doi, headers)
            if abstract and not (_get(paper, "abstract") or "").strip():
                _set_abstract(paper, abstract, source="crossref", match_type="doi_exact")
                enriched += 1
            pbar.update(1)
            time.sleep(delay)

    logger.info("[Enrich/Crossref] %s abstracts obtidos por DOI", f"{enriched:,}")
    return enriched


def _crossref_fetch_by_doi(doi: str, headers: dict, *, max_retries: int = CR_MAX_RETRIES) -> str:
    url = f"{CR_WORKS_URL}/{doi}"
    wait = 5.0
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 404:
                return ""
            if resp.status_code == 429:
                time.sleep(wait)
                wait = min(wait * 2, 60)
                continue
            resp.raise_for_status()
            message = resp.json().get("message") or {}
            return _clean_abstract(message.get("abstract") or "")
        except requests.HTTPError as exc:
            logger.debug("[Enrich/Crossref] HTTP %s for DOI %s", exc.response.status_code, doi)
            return ""
        except Exception as exc:
            logger.debug("[Enrich/Crossref] Erro DOI %s: %s", doi, exc)
            if attempt < max_retries - 1:
                time.sleep(wait)
                wait = min(wait * 2, 60)
    return ""


def _core_escape_doi(doi: str) -> str:
    """Escapa barras no DOI para query Lucene do CORE (ex: 10.1007/s... vira 10.1007\\/s...)."""
    return doi.replace("/", "\\/")


def _enrich_core_by_doi(doi_index: dict, delay: float) -> int:
    api_key = os.getenv("CORE_API_KEY", "").strip()
    if not api_key:
        logger.info("[Enrich/CORE] CORE_API_KEY ausente — pulando etapa por DOI")
        return 0

    headers = {"Authorization": f"Bearer {api_key}"}
    enriched = 0

    with tqdm(total=len(doi_index), desc="CORE/abstracts", unit="paper") as pbar:
        for doi, paper in doi_index.items():
            escaped = _core_escape_doi(doi)
            abstract = _core_fetch_by_query(f"doi:{escaped}", headers, doi=doi)
            if abstract and not (_get(paper, "abstract") or "").strip():
                _set_abstract(paper, abstract, source="core", match_type="doi_exact")
                enriched += 1
            pbar.update(1)
            time.sleep(delay)

    logger.info("[Enrich/CORE] %s abstracts obtidos por DOI", f"{enriched:,}")
    return enriched


def _enrich_by_title_cascade(papers: list, delay: float, after_source=None) -> int:
    enriched = 0
    title_sources = (
        ("openalex", _openalex_fetch_by_title),
        ("crossref", _crossref_fetch_by_title),
        ("core", _core_fetch_by_title),
        ("semanticscholar", _s2_fetch_by_title),
    )

    remaining = [paper for paper in papers if not (_get(paper, "abstract") or "").strip()]
    for source_name, fetcher in title_sources:
        if not remaining:
            break
        logger.info("[Enrich/%s] Tentando fallback por título para %s papers", source_name, f"{len(remaining):,}")
        source_enriched = 0
        with tqdm(total=len(remaining), desc=f"{source_name}/title", unit="paper") as pbar:
            next_remaining = []
            for paper in remaining:
                title = _get(paper, "title")
                year = _safe_int(_get(paper, "year"))
                abstract, match_type = fetcher(title, year)
                if abstract:
                    _set_abstract(paper, abstract, source=source_name, match_type=match_type)
                    enriched += 1
                    source_enriched += 1
                else:
                    next_remaining.append(paper)
                pbar.update(1)
                time.sleep(delay)
        logger.info("[Enrich/%s] %s abstracts obtidos por título", source_name, f"{source_enriched:,}")
        if after_source:
            after_source(f"{source_name}_title", source_enriched)
        remaining = next_remaining

    return enriched


def _s2_fetch_by_title(title: str, year: Optional[int]) -> tuple[str, str]:
    api_key = os.getenv("S2_API_KEY") or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
    params = {
        "query": f'"{title}"',
        "limit": 5,
        "fields": "title,year,abstract,externalIds",
    }
    try:
        resp = requests.get(S2_SEARCH_URL, params=params, headers=headers, timeout=30)
        if resp.status_code in (400, 404):
            return "", ""
        resp.raise_for_status()
        candidates = resp.json().get("data") or []
        return _pick_best_title_match(
            title=title,
            target_year=year,
            candidates=candidates,
            title_getter=lambda item: item.get("title", ""),
            abstract_getter=lambda item: item.get("abstract", ""),
            year_getter=lambda item: item.get("year"),
        )
    except Exception as exc:
        logger.debug("[Enrich/S2] Título falhou: %s", exc)
        return "", ""


def _openalex_fetch_by_title(title: str, year: Optional[int]) -> tuple[str, str]:
    email = os.getenv("OPENALEX_EMAIL", "slr@research.example")
    headers = {"User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})"}
    params = {
        "filter": f'title.search:{title}',
        "select": "display_name,publication_year,abstract_inverted_index",
        "per-page": 5,
    }
    try:
        resp = requests.get(OA_URL, params=params, headers=headers, timeout=30)
        if resp.status_code in (400, 404):
            return "", ""
        resp.raise_for_status()
        candidates = resp.json().get("results") or []
        return _pick_best_title_match(
            title=title,
            target_year=year,
            candidates=candidates,
            title_getter=lambda item: item.get("display_name", ""),
            abstract_getter=lambda item: _reconstruct_abstract(item.get("abstract_inverted_index")),
            year_getter=lambda item: item.get("publication_year"),
        )
    except Exception as exc:
        logger.debug("[Enrich/OA] Título falhou: %s", exc)
        return "", ""


def _crossref_fetch_by_title(title: str, year: Optional[int]) -> tuple[str, str]:
    email = os.getenv("OPENALEX_EMAIL", "slr@research.example")
    headers = {
        "User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})",
        "Accept": "application/json",
    }
    params = {"query.title": title, "rows": 5}
    try:
        resp = requests.get(CR_WORKS_URL, params=params, headers=headers, timeout=30)
        if resp.status_code in (400, 404):
            return "", ""
        resp.raise_for_status()
        candidates = (resp.json().get("message") or {}).get("items") or []
        return _pick_best_title_match(
            title=title,
            target_year=year,
            candidates=candidates,
            title_getter=lambda item: (item.get("title") or [""])[0],
            abstract_getter=lambda item: _clean_abstract(item.get("abstract") or ""),
            year_getter=_crossref_year,
        )
    except Exception as exc:
        logger.debug("[Enrich/Crossref] Título falhou: %s", exc)
        return "", ""


def _core_fetch_by_title(title: str, year: Optional[int]) -> tuple[str, str]:
    api_key = os.getenv("CORE_API_KEY", "").strip()
    if not api_key:
        return "", ""
    headers = {"Authorization": f"Bearer {api_key}"}
    return _core_fetch_title_query(title, year, headers)


def _core_fetch_title_query(title: str, year: Optional[int], headers: dict) -> tuple[str, str]:
    query = f'title:"{title}"'
    params = {"q": query, "limit": 5}
    try:
        resp = requests.get(CORE_SEARCH_URL, params=params, headers=headers, timeout=30)
        if resp.status_code in (400, 401, 403, 404):
            return "", ""
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("results") or data.get("data") or []
        return _pick_best_title_match(
            title=title,
            target_year=year,
            candidates=candidates,
            title_getter=lambda item: item.get("title", ""),
            abstract_getter=lambda item: _clean_abstract(item.get("abstract") or ""),
            year_getter=lambda item: item.get("yearPublished") or item.get("year"),
        )
    except Exception as exc:
        logger.debug("[Enrich/CORE] Título falhou: %s", exc)
        return "", ""


def _core_extract_abstract_from_fulltext(fulltext: str) -> str:
    """
    Tenta extrair um trecho de abstract do campo fullText do CORE.
    Usa apenas como último recurso quando abstract está vazio.
    Retorna string vazia se o texto não parecer um abstract válido.
    """
    if not fulltext:
        return ""
    # Normaliza espaços e quebras de linha
    text = " ".join(fulltext.split())
    # Descarta se começa com padrões típicos de página de rosto (não é abstract)
    lower = text[:120].lower()
    skip_patterns = ("university", "universit", "institute", "faculty", "chapter ",
                     "table of contents", "copyright", "issn", "isbn", "vol.", "proceedings")
    if any(lower.startswith(p) for p in skip_patterns):
        return ""
    # Pega os primeiros 500 caracteres como proxy de abstract
    snippet = text[:500].strip()
    if len(snippet) < 80:
        return ""
    return snippet


def _core_fetch_by_query(query: str, headers: dict, doi: str = "") -> str:
    params = {"q": query, "limit": 5}
    wait = 5.0
    for attempt in range(CORE_MAX_RETRIES):
        try:
            resp = requests.get(CORE_SEARCH_URL, params=params, headers=headers, timeout=30)
            if resp.status_code in (401, 403, 404):
                return ""
            if resp.status_code == 429:
                time.sleep(wait)
                wait = min(wait * 2, 60)
                continue
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results") or data.get("data") or []
            doi_norm = _normalize_doi(doi)
            for item in results:
                item_doi = _normalize_doi(item.get("doi") or "")
                if doi_norm and item_doi != doi_norm:
                    continue
                abstract = _clean_abstract(item.get("abstract") or "")
                if abstract:
                    return abstract
                # Fallback: tenta extrair do fullText quando abstract está ausente
                ft_abstract = _core_extract_abstract_from_fulltext(item.get("fullText") or "")
                if ft_abstract:
                    return ft_abstract
            return ""
        except Exception as exc:
            logger.debug("[Enrich/CORE] Query falhou: %s", exc)
            if attempt < CORE_MAX_RETRIES - 1:
                time.sleep(wait)
                wait = min(wait * 2, 60)
    return ""


def _fetch_batch(dois: list[str], *, max_retries: int = OA_MAX_RETRIES) -> tuple[list[dict], bool]:
    """Mantido para compatibilidade com screening.py."""
    email = os.getenv("OPENALEX_EMAIL", "slr@research.example")
    headers = {"User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})"}
    return _oa_fetch(dois, headers, max_retries=max_retries)


def _pick_best_title_match(
    *,
    title: str,
    target_year: Optional[int],
    candidates: list[dict],
    title_getter,
    abstract_getter,
    year_getter,
) -> tuple[str, str]:
    target_norm = _normalize_title(title)
    if not target_norm:
        return "", ""

    best_score = -1
    best_abstract = ""
    best_match_type = ""

    for item in candidates:
        candidate_title = title_getter(item) or ""
        candidate_abstract = (abstract_getter(item) or "").strip()
        if not candidate_title or not candidate_abstract:
            continue

        cand_norm = _normalize_title(candidate_title)
        if not cand_norm:
            continue

        candidate_year = _safe_int(year_getter(item))
        if cand_norm == target_norm:
            return candidate_abstract, "title_exact"

        score = fuzz.token_set_ratio(target_norm, cand_norm)
        if target_year and candidate_year and abs(target_year - candidate_year) <= 1:
            score += 3

        if score > best_score:
            best_score = score
            best_abstract = candidate_abstract
            best_match_type = "title_fuzzy"

    if best_score >= TITLE_MATCH_MIN_SCORE:
        return best_abstract, best_match_type
    return "", ""


def _reconstruct_abstract(inverted_index: Optional[dict]) -> str:
    if not inverted_index:
        return ""
    try:
        max_pos = max(pos for positions in inverted_index.values() for pos in positions)
        tokens = [""] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                tokens[pos] = word
        return " ".join(token for token in tokens if token)
    except Exception:
        return ""


def _clean_abstract(value: str) -> str:
    if not value:
        return ""
    text = unescape(value)
    text = re.sub(r"</?(jats:)?[^>]+>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _crossref_year(item: dict) -> Optional[int]:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = (((item.get(key) or {}).get("date-parts")) or [])
        if parts and parts[0]:
            return _safe_int(parts[0][0])
    return None


def _normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi.strip()


def _normalize_title(title: str) -> str:
    if not title:
        return ""
    title = title.lower()
    title = unescape(title)
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _chunks(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def _get(obj, field: str):
    if isinstance(obj, dict):
        return obj.get(field, "")
    return getattr(obj, field, "")


def _set(obj, field: str, value):
    if isinstance(obj, dict):
        obj[field] = value
    else:
        setattr(obj, field, value)


def _set_abstract(obj, abstract: str, *, source: str, match_type: str) -> None:
    _set(obj, "abstract", abstract)
    _set(obj, "abstract_source", source)
    _set(obj, "abstract_match_type", match_type)


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
