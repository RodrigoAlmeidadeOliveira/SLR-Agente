"""
Snowballing automático via OpenAlex API.

Estratégias:
  - Backward (referências): para cada paper com DOI, busca no OpenAlex seus
    `referenced_works` e traz metadados dos que ainda não estão no corpus.
  - Forward (citações): para cada paper com DOI, busca no OpenAlex os trabalhos
    que o citam (filter=cites:<openalex_id>) e traz os relevantes.

Filtro de relevância:
  Um paper descoberto pelo snowball só é incluído se seu título + abstract
  contiver ao menos um termo de cada dimensão da SLR:
    D1 (PM/stochastic): process mining | markov chain | monte carlo |
                        stochastic | predictive process | event log | ...
    D2 (SE): software engineering | software development | software process |
             sdlc | devops | agile | issue tracking | ...

Uso via CLI:
  python main.py snowball --direction backward
  python main.py snowball --direction forward
  python main.py snowball --direction both --limit 5
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import requests
from tqdm import tqdm

from extractors.base import Paper

logger = logging.getLogger(__name__)

OPENALEX_URL = "https://api.openalex.org"
BATCH_SIZE = 50          # papers por requisição OpenAlex
REQUEST_DELAY = 0.5      # segundos entre chamadas
USER_AGENT = "SLR-PATHCAST/1.0 (mailto:slr@research.example)"

# ------------------------------------------------------------------ #
#  Termos de relevância (case-insensitive, substring match)           #
# ------------------------------------------------------------------ #

_D1_TERMS = [
    "process mining", "process discovery", "conformance checking",
    "workflow mining", "predictive process monitoring",
    "event log", "markov chain", "monte carlo", "stochastic",
    "transition matrix", "absorbing markov", "petri net",
    "remaining time prediction", "cycle time prediction",
    "lead time prediction", "process simulation", "process model",
    "business process",
]

_D2_TERMS = [
    "software engineering", "software development", "software process",
    "software testing",
    "sdlc", "devops", "continuous integration", "agile",
    "issue tracking", "version control", "code review", "pull request",
    "software repository", "software project", "software maintenance",
    "software evolution", "mining software repositories",
    "jira", "github", "commit", "build pipeline",
]


def _is_relevant(title: str, abstract: str) -> bool:
    """Retorna True se o paper parece relevante para a SLR."""
    text = (title + " " + abstract).lower()
    has_d1 = any(t in text for t in _D1_TERMS)
    has_d2 = any(t in text for t in _D2_TERMS)
    return has_d1 and has_d2


# ------------------------------------------------------------------ #
#  OpenAlex helpers                                                   #
# ------------------------------------------------------------------ #

def _headers() -> dict:
    return {"User-Agent": USER_AGENT}


def _normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/",
                   "https://dx.doi.org/", "http://dx.doi.org/"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def _get_openalex_work(doi: str) -> Optional[dict]:
    """Busca um trabalho no OpenAlex por DOI. Retorna o dict ou None."""
    url = f"{OPENALEX_URL}/works/https://doi.org/{doi}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.debug(f"[Snowball] Erro ao buscar DOI {doi}: {exc}")
        return None


def _fetch_works_by_ids(openalex_ids: list[str]) -> list[dict]:
    """Busca metadados de uma lista de OpenAlex IDs (ex: W12345678)."""
    results = []
    for i in range(0, len(openalex_ids), BATCH_SIZE):
        batch = openalex_ids[i:i + BATCH_SIZE]
        filter_str = "|".join(batch)
        params = {
            "filter": f"openalex_id:{filter_str}",
            "select": "id,doi,title,authorships,publication_year,primary_location,"
                      "abstract_inverted_index,keywords,type",
            "per-page": BATCH_SIZE,
        }
        try:
            resp = requests.get(
                f"{OPENALEX_URL}/works",
                params=params,
                headers=_headers(),
                timeout=30,
            )
            resp.raise_for_status()
            results.extend(resp.json().get("results", []))
        except Exception as exc:
            logger.warning(f"[Snowball] Erro ao buscar lote de IDs: {exc}")
        time.sleep(REQUEST_DELAY)
    return results


def _fetch_citations_page(openalex_id: str, page: int = 1, per_page: int = 50) -> dict:
    """Busca uma página de trabalhos que citam openalex_id."""
    params = {
        "filter": f"cites:{openalex_id}",
        "select": "id,doi,title,authorships,publication_year,primary_location,"
                  "abstract_inverted_index,keywords,type",
        "per-page": per_page,
        "page": page,
    }
    try:
        resp = requests.get(
            f"{OPENALEX_URL}/works",
            params=params,
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning(f"[Snowball] Erro ao buscar citações de {openalex_id}: {exc}")
        return {"results": [], "meta": {"count": 0}}


def _reconstruct_abstract(inverted_index: Optional[dict]) -> str:
    """Reconstrói texto do abstract a partir do abstract_inverted_index do OpenAlex."""
    if not inverted_index:
        return ""
    try:
        max_pos = max(pos for positions in inverted_index.values() for pos in positions)
        tokens = [""] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                tokens[pos] = word
        return " ".join(t for t in tokens if t)
    except Exception:
        return ""


def _work_to_paper(work: dict, direction: str, parent_doi: str) -> Optional[Paper]:
    """Converte um dict OpenAlex Work em Paper, ou retorna None se irrelevante."""
    title = work.get("title") or ""
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

    if not title:
        return None

    if not _is_relevant(title, abstract):
        return None

    doi = _normalize_doi(work.get("doi") or "")
    year_raw = work.get("publication_year")
    year = int(year_raw) if year_raw else None

    # Filtra por intervalo de anos (alinhado com as queries: 1994–2026)
    if year and (year < 1994 or year > 2026):
        return None

    # Autores
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name", "")
        if name:
            authors.append(name)

    # Venue
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    venue = source.get("display_name", "")

    # Keywords
    keywords = [kw.get("display_name", "") for kw in work.get("keywords", [])]
    keywords = [k for k in keywords if k]

    # doc_type
    work_type = work.get("type", "")
    if work_type == "journal-article":
        doc_type = "article"
    elif work_type in ("proceedings-article", "conference-paper"):
        doc_type = "conference paper"
    else:
        doc_type = work_type

    query_label = f"snowball:{direction} from {parent_doi}"

    return Paper(
        source_db="snowball",
        source_query_id=f"snowball_{direction}",
        source_query_label=query_label,
        doi=doi,
        title=title,
        authors=authors,
        year=year,
        abstract=abstract,
        venue=venue,
        doc_type=doc_type,
        keywords=keywords,
        url=work.get("id", ""),  # OpenAlex URL do trabalho
    )


# ------------------------------------------------------------------ #
#  Snowballing principal                                              #
# ------------------------------------------------------------------ #

def snowball(
    papers: list[Paper],
    direction: str = "both",
    limit: int = 0,
    delay: float = REQUEST_DELAY,
) -> tuple[list[Paper], dict]:
    """
    Executa snowballing automático sobre a lista de papers do corpus.

    Args:
        papers:    Lista de Papers já no corpus (usados como semente).
        direction: "backward" | "forward" | "both"
        limit:     Máx de papers semente a processar (0 = todos).
        delay:     Delay entre requisições à API.

    Returns:
        (new_papers, stats)
        - new_papers: papers novos encontrados (relevantes e não duplicados)
        - stats: dicionário com contagens de diagnóstico
    """
    from pipeline.dedup import deduplicate, unique_papers

    do_backward = direction in ("backward", "both")
    do_forward = direction in ("forward", "both")

    # Conjunto de DOIs já no corpus (para dedup rápida)
    existing_dois: set[str] = set()
    for p in papers:
        d = _normalize_doi(p.doi)
        if d:
            existing_dois.add(d)

    # Seeds: papers com DOI (os que conseguimos buscar no OpenAlex)
    seeds = [p for p in papers if _normalize_doi(p.doi)]
    if limit > 0:
        seeds = seeds[:limit]

    logger.info(
        f"[Snowball] Iniciando snowball {direction.upper()} | "
        f"{len(seeds)} seeds | delay={delay}s"
    )

    stats = {
        "seeds": len(seeds),
        "direction": direction,
        "backward_candidates": 0,
        "forward_candidates": 0,
        "relevant_found": 0,
        "new_after_dedup": 0,
    }

    candidate_works: list[dict] = []   # works OpenAlex brutos
    parent_map: dict[str, str] = {}    # openalex_id → parent_doi (para label)

    # ---------------------------------------------------------------- #
    # Backward: busca referenced_works de cada paper seed              #
    # ---------------------------------------------------------------- #
    if do_backward:
        logger.info("[Snowball] ← Backward: buscando referências...")
        ref_ids_to_fetch: list[str] = []

        with tqdm(total=len(seeds), desc="Backward/seeds", unit="paper") as pbar:
            for seed in seeds:
                doi = _normalize_doi(seed.doi)
                work = _get_openalex_work(doi)
                if work:
                    ref_ids = work.get("referenced_works") or []
                    for rid in ref_ids:
                        # rid é URL: https://openalex.org/W12345
                        oa_id = rid.split("/")[-1]
                        ref_ids_to_fetch.append(oa_id)
                        parent_map[oa_id] = doi
                pbar.update(1)
                time.sleep(delay)

        logger.info(f"[Snowball] ← {len(ref_ids_to_fetch)} referências encontradas, buscando metadados...")
        stats["backward_candidates"] = len(ref_ids_to_fetch)

        # Remove duplicatas de IDs
        unique_ref_ids = list(dict.fromkeys(ref_ids_to_fetch))
        batch_works = _fetch_works_by_ids(unique_ref_ids)
        candidate_works.extend(
            (w, parent_map.get(w.get("id", "").split("/")[-1], "backward"))
            for w in batch_works
        )

    # ---------------------------------------------------------------- #
    # Forward: busca papers que citam cada seed                        #
    # ---------------------------------------------------------------- #
    if do_forward:
        logger.info("[Snowball] → Forward: buscando citantes...")

        with tqdm(total=len(seeds), desc="Forward/seeds", unit="paper") as pbar:
            for seed in seeds:
                doi = _normalize_doi(seed.doi)
                work = _get_openalex_work(doi)
                if not work:
                    pbar.update(1)
                    time.sleep(delay)
                    continue

                oa_id = work.get("id", "").split("/")[-1]
                if not oa_id:
                    pbar.update(1)
                    time.sleep(delay)
                    continue

                # Pagina resultados de citações
                page = 1
                while True:
                    data = _fetch_citations_page(oa_id, page=page)
                    results = data.get("results", [])
                    for w in results:
                        w_id = w.get("id", "").split("/")[-1]
                        candidate_works.append((w, doi))
                        if w_id:
                            parent_map[w_id] = doi
                        stats["forward_candidates"] += 1
                    meta = data.get("meta", {})
                    total = meta.get("count", 0)
                    fetched_so_far = page * 50
                    if fetched_so_far >= total or not results:
                        break
                    page += 1
                    time.sleep(delay)

                pbar.update(1)
                time.sleep(delay)

    # ---------------------------------------------------------------- #
    # Filtra relevância e dedup                                        #
    # ---------------------------------------------------------------- #
    new_papers_raw: list[Paper] = []
    seen_dois: set[str] = set(existing_dois)
    seen_titles: set[str] = set()

    logger.info(f"[Snowball] Filtrando {len(candidate_works)} candidatos por relevância...")

    for item in candidate_works:
        work, parent_doi = item
        doi = _normalize_doi(work.get("doi") or "")
        if doi and doi in seen_dois:
            continue  # já no corpus ou já visto nesta rodada

        title = (work.get("title") or "").strip()
        norm_title = title.lower()
        if norm_title and norm_title in seen_titles:
            continue

        paper = _work_to_paper(work, direction, parent_doi)
        if paper is None:
            continue

        stats["relevant_found"] += 1
        new_papers_raw.append(paper)
        if doi:
            seen_dois.add(doi)
        if norm_title:
            seen_titles.add(norm_title)

    # Dedup interno entre si (título fuzzy)
    if new_papers_raw:
        deduped = deduplicate(new_papers_raw)
        new_unique = unique_papers(deduped)
    else:
        new_unique = []

    stats["new_after_dedup"] = len(new_unique)

    logger.info(
        f"[Snowball] Concluído: {stats['relevant_found']} relevantes → "
        f"{stats['new_after_dedup']} novos únicos"
    )
    return new_unique, stats


def print_snowball_report(stats: dict, new_papers: list[Paper]) -> str:
    lines = [
        "",
        "═" * 60,
        "  SNOWBALL REPORT",
        "═" * 60,
        f"  Direção       : {stats.get('direction', '-').upper()}",
        f"  Seeds usados  : {stats.get('seeds', 0):,}",
        f"  Candidatos (←): {stats.get('backward_candidates', 0):,}",
        f"  Candidatos (→): {stats.get('forward_candidates', 0):,}",
        f"  Relevantes    : {stats.get('relevant_found', 0):,}",
        f"  Novos únicos  : {stats.get('new_after_dedup', 0):,}",
        "─" * 60,
    ]
    if new_papers:
        lines.append("  Amostra de novos papers encontrados:")
        for p in new_papers[:10]:
            year = p.year or "?"
            authors = p.authors[0] if p.authors else "?"
            lines.append(f"    [{year}] {authors} — {p.title[:70]}")
        if len(new_papers) > 10:
            lines.append(f"    ... e mais {len(new_papers) - 10} papers")
    else:
        lines.append("  Nenhum paper novo encontrado.")
    lines.append("═" * 60)
    return "\n".join(lines)
