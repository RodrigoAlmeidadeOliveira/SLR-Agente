"""
Extrator para IEEE Xplore via REST API v1.
Documentação: https://developer.ieee.org/docs/read/IEEE_Xplore_API_Overview

Limites:
  - Chave gratuita: 200 req/dia, max 200 resultados/req
  - Máximo teórico: ~10.000 resultados por query (paginado)

Query format:
  A API usa parâmetro `querytext` com operadores booleanos.
  As queries do plano usam formato web UI "All Metadata":"term";
  esta classe converte automaticamente para formato da API.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import requests
from tqdm import tqdm

from extractors.base import BaseExtractor, Paper

logger = logging.getLogger(__name__)

IEEE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
MAX_PER_PAGE = 200


class IEEEExtractor(BaseExtractor):
    """Extrai referências do IEEE Xplore usando a REST API v1."""

    def extract(self, query_id: str, query_label: str, query_str: str) -> list[Paper]:
        """
        Executa a query no IEEE Xplore.
        Converte automaticamente o formato web UI para formato da API.
        """
        api_query = _convert_ieee_query(query_str)
        logger.info(f"[IEEE] Iniciando query: {query_label}")
        logger.debug(f"[IEEE] Query convertida: {api_query[:120]}...")

        params = {
            "apikey": self.api_key,
            "querytext": api_query,
            "max_records": MAX_PER_PAGE,
            "start_record": 1,
            "sort_order": "asc",
            "sort_field": "publication_year",
        }

        try:
            resp = self._get(params)
        except Exception as exc:
            logger.error(f"[IEEE] Falha na primeira requisição: {exc}")
            return []

        total = int(resp.get("total_records", 0))
        logger.info(f"[IEEE] Total encontrado: {total:,} para '{query_label}'")

        if total == 0:
            return []

        effective_max = total
        if self.max_results > 0:
            effective_max = min(total, self.max_results)

        papers = []
        articles = resp.get("articles", [])
        papers.extend(self._parse_articles(articles, query_id, query_label))

        start = MAX_PER_PAGE + 1
        with tqdm(total=effective_max, initial=len(papers),
                  desc=f"IEEE/{query_label[:30]}", unit="paper") as pbar:
            while start <= effective_max:
                self._sleep()
                params["start_record"] = start
                try:
                    resp = self._get(params)
                except Exception as exc:
                    logger.error(f"[IEEE] Erro em start_record={start}: {exc}")
                    break

                articles = resp.get("articles", [])
                if not articles:
                    break

                batch = self._parse_articles(articles, query_id, query_label)
                papers.extend(batch)
                pbar.update(len(batch))
                start += MAX_PER_PAGE

        logger.info(f"[IEEE] Extraídos {len(papers)} papers para '{query_label}'")
        return papers

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _get(self, params: dict) -> dict:
        resp = requests.get(IEEE_URL, params=params, timeout=30)
        if resp.status_code == 401:
            raise PermissionError("API key IEEE inválida.")
        if resp.status_code == 429:
            raise RuntimeError("Rate limit IEEE atingido.")
        resp.raise_for_status()
        return resp.json()

    def _parse_articles(
        self, articles: list[dict], query_id: str, query_label: str
    ) -> list[Paper]:
        papers = []
        for a in articles:
            # Autores
            authors_raw = a.get("authors", {}).get("authors", [])
            authors = [
                auth.get("full_name", "").strip()
                for auth in authors_raw
                if auth.get("full_name")
            ]

            # Ano
            year: Optional[int] = None
            py = a.get("publication_year")
            if py:
                try:
                    year = int(py)
                except (ValueError, TypeError):
                    pass

            # DOI
            doi = (a.get("doi") or "").strip()
            article_number = a.get("article_number", "")
            url = f"https://ieeexplore.ieee.org/document/{article_number}" if article_number else ""

            # Keywords
            keywords = []
            for kw_section in ["index_terms", "author_terms", "controlled_terms"]:
                terms = a.get(kw_section, {}).get("terms", [])
                keywords.extend([t.strip() for t in terms if t.strip()])
            keywords = list(dict.fromkeys(keywords))  # dedup mantendo ordem

            # Doc type
            content_type = (a.get("content_type") or "").lower()
            if "journal" in content_type:
                doc_type = "article"
            elif "conference" in content_type:
                doc_type = "conference paper"
            else:
                doc_type = content_type or "unknown"

            paper = Paper(
                source_db="ieee",
                source_query_id=query_id,
                source_query_label=query_label,
                doi=doi,
                title=(a.get("title") or "").strip(),
                authors=authors,
                year=year,
                abstract=(a.get("abstract") or "").strip(),
                venue=(a.get("publication_title") or "").strip(),
                doc_type=doc_type,
                keywords=keywords,
                url=url,
                volume=(a.get("volume") or "").strip(),
                issue=(a.get("issue") or "").strip(),
                pages=(a.get("start_page", "") + (
                    f"-{a.get('end_page')}" if a.get("end_page") else ""
                )).strip("-"),
                publisher=(a.get("publisher") or "").strip(),
            )
            papers.append(paper)
        return papers


def _convert_ieee_query(query_str: str) -> str:
    """
    Converte o formato web UI do IEEE ("All Metadata":"term")
    para o formato da API (plain boolean query).

    Exemplos:
      '"All Metadata":"process mining"' → '"process mining"'
      '"All Metadata":"software"'       → '"software"'
    """
    # Remove o prefixo "All Metadata": mantendo o termo entre aspas
    converted = re.sub(r'"All Metadata"\s*:\s*', "", query_str)
    return converted.strip()
