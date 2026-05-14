"""
Extrator para Web of Science via Clarivate Web of Science Starter API v1.
Documentação: https://developer.clarivate.com/apis/wos-starter

Limites (plano gratuito):
  - 10 requisições/segundo
  - 50 resultados por página
  - Máximo de 10.000 resultados por query

Autenticação:
  - Header: X-ApiKey

Cadastro gratuito em: https://developer.clarivate.com/

Query format:
  Usa a sintaxe nativa do WoS (TS=, TI=, AB=, AU=, etc.).
  As queries configuradas em config/queries.py já estão neste formato.
"""
from __future__ import annotations

import logging
from typing import Optional

import requests
from tqdm import tqdm

from extractors.base import BaseExtractor, Paper

logger = logging.getLogger(__name__)

WOS_URL = "https://api.clarivate.com/apis/wos-starter/v1/documents"
PAGE_SIZE = 50   # máximo permitido pela API
MAX_OFFSET = 9950  # API limita a 10.000 resultados (página 200 com 50/pág)


class WoSExtractor(BaseExtractor):
    """
    Extrai referências do Web of Science usando a Starter API v1.

    A query deve usar a sintaxe nativa WoS:
        TS=("process mining") AND TS=("software engineering")
    """

    def extract(self, query_id: str, query_label: str, query_str: str) -> list[Paper]:
        headers = {
            "X-ApiKey": self.api_key,
            "Accept": "application/json",
        }

        params = {
            "q": query_str,
            "limit": PAGE_SIZE,
            "page": 1,
            "db": "WOS",
            "sortField": "PY+D",  # ordena por ano decrescente
        }

        logger.info(f"[WoS] Iniciando query: {query_label}")

        try:
            resp = self._get(headers, params)
        except Exception as exc:
            logger.error(f"[WoS] Falha na primeira requisição: {exc}")
            return []

        metadata = resp.get("metadata", {})
        total = int(metadata.get("total", 0))
        logger.info(f"[WoS] Total encontrado: {total:,} para '{query_label}'")

        if total == 0:
            return []

        # A API limita a 10.000 resultados; respeita também max_results do usuário
        effective_max = min(total, MAX_OFFSET + PAGE_SIZE)
        if self.max_results > 0:
            effective_max = min(effective_max, self.max_results)

        papers: list[Paper] = []
        hits = resp.get("hits", [])
        papers.extend(self._parse_hits(hits, query_id, query_label))

        page = 2
        with tqdm(
            total=effective_max,
            initial=len(papers),
            desc=f"WoS/{query_label[:30]}",
            unit="paper",
        ) as pbar:
            while len(papers) < effective_max:
                self._sleep()
                params["page"] = page
                try:
                    resp = self._get(headers, params)
                except Exception as exc:
                    logger.error(f"[WoS] Erro na página {page}: {exc}")
                    break

                hits = resp.get("hits", [])
                if not hits:
                    break

                batch = self._parse_hits(hits, query_id, query_label)
                papers.extend(batch)
                pbar.update(len(batch))
                page += 1

        logger.info(f"[WoS] Extraídos {len(papers)} papers para '{query_label}'")
        return papers

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _get(self, headers: dict, params: dict) -> dict:
        resp = requests.get(WOS_URL, headers=headers, params=params, timeout=30)
        if resp.status_code == 401:
            raise PermissionError("WOS_API_KEY inválida ou sem permissão.")
        if resp.status_code == 403:
            raise PermissionError(
                "Acesso negado. Verifique se a chave tem permissão para WoS Starter API."
            )
        if resp.status_code == 429:
            raise RuntimeError(
                "Rate limit WoS atingido (10 req/s). Aumente REQUEST_DELAY no .env."
            )
        resp.raise_for_status()
        return resp.json()

    def _parse_hits(
        self, hits: list[dict], query_id: str, query_label: str
    ) -> list[Paper]:
        papers = []
        for h in hits:
            # --- Autores ---
            names = h.get("names", {})
            authors_raw = names.get("authors", [])
            authors = [
                a.get("displayName", "").strip()
                for a in authors_raw
                if a.get("displayName")
            ]

            # --- Ano ---
            year: Optional[int] = None
            source = h.get("source", {})
            py = source.get("publishYear")
            if py:
                try:
                    year = int(py)
                except (ValueError, TypeError):
                    pass

            # --- Identificadores ---
            identifiers = h.get("identifiers", {})
            doi = (identifiers.get("doi") or "").strip()

            # URL via WoS UID
            uid = h.get("uid", "")
            links = h.get("links", {})
            url = (links.get("record") or "").strip()
            if not url and uid:
                url = f"https://www.webofscience.com/wos/woscc/full-record/{uid}"

            # --- Keywords ---
            kw_obj = h.get("keywords", {})
            author_kws = kw_obj.get("authorKeywords", []) or []
            plus_kws = kw_obj.get("keywordsPlus", []) or []
            keywords = list(dict.fromkeys(
                [k.strip() for k in author_kws + plus_kws if k.strip()]
            ))

            # --- Tipo do documento ---
            types = h.get("types", []) or []
            doc_type = _normalize_doctype(types[0] if types else "")

            # --- Venue ---
            venue = (source.get("sourceTitle") or "").strip()

            # --- Páginas ---
            pages_obj = source.get("pages", {}) or {}
            pages = (pages_obj.get("range") or "").strip()

            # --- Abstract ---
            abstract_obj = h.get("abstract", {}) or {}
            abstract = (abstract_obj.get("value") or "").strip()

            # --- Título ---
            title_obj = h.get("title", {}) or {}
            title = (title_obj.get("value") or "").strip()

            paper = Paper(
                source_db="wos",
                source_query_id=query_id,
                source_query_label=query_label,
                doi=doi,
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                venue=venue,
                doc_type=doc_type,
                keywords=keywords,
                url=url,
                volume=(source.get("volume") or "").strip(),
                issue=(source.get("issue") or "").strip(),
                pages=pages,
                publisher="",   # Starter API não retorna publisher
            )
            papers.append(paper)
        return papers


def _normalize_doctype(raw: str) -> str:
    raw = (raw or "").lower()
    if "article" in raw:
        return "article"
    if "conference" in raw or "proceeding" in raw:
        return "conference paper"
    if "review" in raw:
        return "article"  # Review articles tratados como artigos
    if "chapter" in raw or "book" in raw:
        return "chapter"
    return raw or "unknown"
