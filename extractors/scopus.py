"""
Extrator para Scopus via Elsevier Search API v2.
Documentação: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl

Limite de paginação:
  - Chave básica:  até 25 resultados/página, max 5.000 total
  - Chave institucional: até 200 resultados/página, max 100.000 total

Notas sobre sintaxe da API:
  - LIMIT-TO() é sintaxe da UI web — não é suportado na API.
    Filtros de tipo de documento usam o parâmetro `subtype`.
    Filtros de idioma devem ser convertidos para LANGUAGE(english) inline na query.
  - PUBYEAR > N e PUBYEAR < N são suportados inline na query.
  - Quebras de linha na query devem ser removidas.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import requests
from tqdm import tqdm

from extractors.base import BaseExtractor, Paper

logger = logging.getLogger(__name__)

SCOPUS_URL = "https://api.elsevier.com/content/search/scopus"

# Campos solicitados na API (reduz tamanho da resposta)
FIELDS = (
    "dc:title,dc:creator,prism:publicationName,prism:coverDate,"
    "prism:doi,dc:description,eid,subtypeDescription,"
    "prism:aggregationType,authkeywords,citedby-count,"
    "prism:volume,prism:issueIdentifier,prism:pageRange,dc:publisher"
)


def _preprocess_query(query_str: str) -> tuple[str, dict]:
    """
    Converte a query no formato da UI do Scopus para o formato aceito pela API.

    Remove os operadores LIMIT-TO (não suportados pela API) e devolve:
      - a query limpa (sem LIMIT-TO, sem quebras de linha desnecessárias)
      - parâmetros extras a serem passados na requisição (subtype)

    Filtros reconhecidos:
      LIMIT-TO(DOCTYPE, "ar")       → parâmetro subtype=ar
      LIMIT-TO(DOCTYPE, "cp")       → parâmetro subtype=cp
      LIMIT-TO(LANGUAGE, "English") → cláusula AND LANGUAGE(english) inline na query
                                      (a API não aceita `language` como parâmetro separado)
    """
    extra_params: dict = {}

    # Coletar subtypes (ar = article, cp = conference paper)
    subtype_hits = re.findall(
        r'LIMIT-TO\s*\(\s*DOCTYPE\s*,\s*"(\w+)"\s*\)', query_str, re.IGNORECASE
    )
    if subtype_hits:
        extra_params["subtype"] = ",".join(subtype_hits)

    # Coletar idiomas para converter em LANGUAGE() inline
    lang_hits = re.findall(
        r'LIMIT-TO\s*\(\s*LANGUAGE\s*,\s*"([^"]+)"\s*\)', query_str, re.IGNORECASE
    )

    # Remover todos os blocos AND (...LIMIT-TO...OR...LIMIT-TO...) da query
    clean = re.sub(
        r'AND\s+\(?(?:\s*LIMIT-TO\s*\([^)]+\)\s*(?:OR\s*)?)+\)?',
        "",
        query_str,
        flags=re.IGNORECASE,
    )
    # Remover LIMIT-TO residuais isolados
    clean = re.sub(r'LIMIT-TO\s*\([^)]+\)', "", clean, flags=re.IGNORECASE)

    # Normalizar espaços e quebras de linha
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Adicionar filtro de idioma como cláusula inline (único modo suportado pela API)
    if lang_hits:
        lang_filter = " OR ".join(f"LANGUAGE({l.lower()})" for l in lang_hits)
        clean = f"{clean} AND ({lang_filter})"

    return clean, extra_params


class ScopusExtractor(BaseExtractor):
    """Extrai referências do Scopus usando a Search API."""

    PAGE_SIZE = 25   # Aumentar para 200 se tiver chave institucional

    def extract(self, query_id: str, query_label: str, query_str: str) -> list[Paper]:
        """
        Executa a query no Scopus e retorna todos os papers.

        Pré-processa a query para remover LIMIT-TO (sintaxe da UI)
        e converte os filtros para parâmetros da API.
        """
        api_query, extra_params = _preprocess_query(query_str)
        logger.debug(f"[Scopus] Query processada: {api_query[:120]}...")

        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json",
        }

        params = {
            "query": api_query,
            "count": self.PAGE_SIZE,
            "start": 0,
            "field": FIELDS,
            "httpAccept": "application/json",
            **extra_params,
        }

        logger.info(f"[Scopus] Iniciando query: {query_label}")

        try:
            resp = self._get(SCOPUS_URL, headers=headers, params=params)
        except Exception as exc:
            logger.error(f"[Scopus] Falha na primeira requisição: {exc}")
            return []

        search_results = resp.get("search-results", {})
        total = int(search_results.get("opensearch:totalResults", 0))
        logger.info(f"[Scopus] Total encontrado: {total:,} para '{query_label}'")

        if total == 0:
            return []

        effective_max = total
        if self.max_results > 0:
            effective_max = min(total, self.max_results)

        papers = []
        entries = search_results.get("entry", [])
        papers.extend(self._parse_entries(entries, query_id, query_label))

        start = self.PAGE_SIZE
        with tqdm(total=effective_max, initial=len(papers),
                  desc=f"Scopus/{query_label[:30]}", unit="paper") as pbar:
            while start < effective_max:
                self._sleep()
                params["start"] = start
                try:
                    resp = self._get(SCOPUS_URL, headers=headers, params=params)
                except Exception as exc:
                    logger.error(f"[Scopus] Erro em start={start}: {exc}")
                    break

                entries = resp.get("search-results", {}).get("entry", [])
                if not entries:
                    break

                batch = self._parse_entries(entries, query_id, query_label)
                papers.extend(batch)
                pbar.update(len(batch))
                start += self.PAGE_SIZE

        logger.info(f"[Scopus] Extraídos {len(papers)} papers para '{query_label}'")
        return papers

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _get(self, url: str, headers: dict, params: dict) -> dict:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 401:
            raise PermissionError("API key inválida ou sem permissão para esta query.")
        if resp.status_code == 429:
            raise RuntimeError("Rate limit atingido. Aumente o delay entre requisições.")
        resp.raise_for_status()
        return resp.json()

    def _parse_entries(
        self, entries: list[dict], query_id: str, query_label: str
    ) -> list[Paper]:
        papers = []
        for e in entries:
            # Tratar "No results found" placeholder
            if e.get("error"):
                continue

            # Autores: dc:creator é uma string; authkeywords separados por " | "
            authors = []
            creator = e.get("dc:creator", "")
            if creator:
                authors = [a.strip() for a in creator.split(";") if a.strip()]

            # Palavras-chave
            kw_raw = e.get("authkeywords", "")
            keywords = [k.strip() for k in kw_raw.split("|") if k.strip()] if kw_raw else []

            # Ano a partir de prism:coverDate (YYYY-MM-DD)
            cover_date = e.get("prism:coverDate", "")
            year: Optional[int] = None
            if cover_date and len(cover_date) >= 4:
                try:
                    year = int(cover_date[:4])
                except ValueError:
                    pass

            doi = e.get("prism:doi", "") or ""
            eid = e.get("eid", "") or ""
            url = f"https://www.scopus.com/record/display.uri?eid={eid}" if eid else ""

            paper = Paper(
                source_db="scopus",
                source_query_id=query_id,
                source_query_label=query_label,
                doi=doi.strip(),
                title=(e.get("dc:title") or "").strip(),
                authors=authors,
                year=year,
                abstract=(e.get("dc:description") or "").strip(),
                venue=(e.get("prism:publicationName") or "").strip(),
                doc_type=_normalize_doctype(e.get("subtypeDescription", "")),
                keywords=keywords,
                url=url,
                volume=(e.get("prism:volume") or "").strip(),
                issue=(e.get("prism:issueIdentifier") or "").strip(),
                pages=(e.get("prism:pageRange") or "").strip(),
                publisher=(e.get("dc:publisher") or "").strip(),
            )
            papers.append(paper)
        return papers


def _normalize_doctype(raw: str) -> str:
    raw = (raw or "").lower()
    if "conference" in raw or "proceeding" in raw:
        return "conference paper"
    if "article" in raw or "journal" in raw:
        return "article"
    if "chapter" in raw or "book" in raw:
        return "chapter"
    return raw or "unknown"
