"""
Extrator para Springer Nature Open Access API.

Usa o endpoint ``/openaccess/json`` e converte as queries curtas do projeto
para o formato esperado pela API, por exemplo:
    '"process mining" "software development"'
    -> 'keyword:"process mining" AND keyword:"software development"'
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

import requests
from tqdm import tqdm

from extractors.base import BaseExtractor, Paper

logger = logging.getLogger(__name__)

SPRINGER_URLS = {
    "openaccess": "https://api.springernature.com/openaccess/json",
    "metadata": "https://api.springernature.com/meta/v2/json",
}
PAGE_SIZE = 50


class SpringerExtractor(BaseExtractor):
    """Extrai referências do Springer Nature Open Access API ou Metadata API."""

    def __init__(self, api_key: str, delay: float = 1.0, max_results: int = 0):
        super().__init__(api_key, delay, max_results)
        mode = os.getenv("SPRINGER_API_MODE", "openaccess").strip().lower()
        self.api_mode = mode if mode in SPRINGER_URLS else "openaccess"
        self.base_url = SPRINGER_URLS[self.api_mode]

    def extract(self, query_id: str, query_label: str, query_str: str) -> list[Paper]:
        """Executa a query no Springer e retorna todos os papers."""
        full_query = self._build_query(query_str)
        logger.info(f"[Springer/{self.api_mode}] Iniciando query: {query_label}")
        logger.debug(f"[Springer] Query: {full_query}")

        params = {
            "q": full_query,
            "api_key": self.api_key,
            "p": PAGE_SIZE,
            "s": 1,
        }

        try:
            resp = self._get(params)
        except Exception as exc:
            logger.error(f"[Springer] Falha na primeira requisição: {exc}")
            return []

        # Total de resultados
        result_info = resp.get("result", [{}])
        total = int(result_info[0].get("total", 0)) if result_info else 0
        logger.info(f"[Springer] Total encontrado: {total:,} para '{query_label}'")

        if total == 0:
            return []

        effective_max = total
        if self.max_results > 0:
            effective_max = min(total, self.max_results)

        papers = []
        records = resp.get("records", [])
        papers.extend(self._parse_records(records, query_id, query_label))

        start = PAGE_SIZE + 1
        with tqdm(total=effective_max, initial=len(papers),
                  desc=f"Springer/{query_label[:30]}", unit="paper") as pbar:
            while start <= effective_max:
                self._sleep()
                params["s"] = start
                try:
                    resp = self._get(params)
                except Exception as exc:
                    logger.error(f"[Springer] Erro em s={start}: {exc}")
                    break

                records = resp.get("records", [])
                if not records:
                    break

                batch = self._parse_records(records, query_id, query_label)
                papers.extend(batch)
                pbar.update(len(batch))
                start += PAGE_SIZE

        logger.info(f"[Springer] Extraídos {len(papers)} papers para '{query_label}'")
        return papers

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _build_query(self, query_str: str) -> str:
        """
        Converte a sintaxe simplificada do projeto para a busca por keyword
        compatível com Open Access API e Metadata API.
        """
        terms = re.findall(r'"([^"]+)"', query_str)
        if terms:
            return " AND ".join(f'keyword:"{term}"' for term in terms)
        return query_str.strip()

    def _get(self, params: dict) -> dict:
        resp = requests.get(self.base_url, params=params, timeout=30)
        if resp.status_code == 401:
            raise PermissionError("API key Springer inválida.")
        if resp.status_code == 403:
            try:
                payload = resp.json()
                detail = payload.get("error", {}).get("error_description") or payload.get("message")
            except Exception:
                detail = ""
            raise PermissionError(
                "Acesso negado pela Springer."
                + (f" {detail}" if detail else "")
            )
        if resp.status_code == 429:
            raise RuntimeError("Rate limit Springer atingido.")
        resp.raise_for_status()
        return resp.json()

    def _parse_records(
        self, records: list[dict], query_id: str, query_label: str
    ) -> list[Paper]:
        papers = []
        for r in records:
            creators = r.get("creators", []) or r.get("authors", [])
            authors = []
            for c in creators:
                if isinstance(c, dict):
                    name = (
                        c.get("creator")
                        or c.get("name")
                        or c.get("author")
                        or ""
                    ).strip()
                else:
                    name = str(c).strip()
                if name:
                    authors.append(name)

            year: Optional[int] = None
            for date_field in ["publicationDate", "onlineDate", "coverDate", "printDate"]:
                date_str = r.get(date_field, "")
                if date_str and len(date_str) >= 4:
                    try:
                        year = int(date_str[:4])
                        break
                    except ValueError:
                        pass

            doi = (r.get("doi") or "").strip()
            identifier = (r.get("identifier") or "").strip()
            if not doi and identifier.startswith("doi:"):
                doi = identifier[4:].strip()
            elif "/" in identifier:
                doi = identifier.strip()

            url = ""
            url_obj = r.get("url", "")
            if isinstance(url_obj, list) and url_obj:
                first = url_obj[0]
                if isinstance(first, dict):
                    url = first.get("value", "") or first.get("url", "")
                else:
                    url = str(first)
            elif isinstance(url_obj, dict):
                url = url_obj.get("value", "") or url_obj.get("url", "")
            elif isinstance(url_obj, str):
                url = url_obj

            subjects = r.get("subjects", []) or r.get("keywords", [])
            keywords = []
            for s in subjects:
                if isinstance(s, dict):
                    value = (s.get("term") or s.get("value") or "").strip()
                else:
                    value = str(s).strip()
                if value:
                    keywords.append(value)

            content_type = (
                r.get("contentType")
                or r.get("genre")
                or r.get("type")
                or ""
            ).lower()
            if "article" in content_type:
                doc_type = "article"
            elif "chapter" in content_type or "book" in content_type:
                doc_type = "chapter"
            else:
                doc_type = content_type or "unknown"

            paper = Paper(
                source_db="springer",
                source_query_id=query_id,
                source_query_label=query_label,
                doi=doi,
                title=(r.get("title") or "").strip(),
                authors=authors,
                year=year,
                abstract=(r.get("abstract") or "").strip(),
                venue=((r.get("journalTitle") or r.get("publicationName") or "").strip()),
                doc_type=doc_type,
                keywords=keywords,
                url=url,
                volume=(r.get("volume") or "").strip(),
                issue=(r.get("number") or "").strip(),
                pages=(r.get("startingPage", "") + (
                    f"-{r.get('endingPage')}" if r.get("endingPage") else ""
                )).strip("-"),
                publisher=(r.get("publisher") or "").strip(),
            )
            papers.append(paper)
        return papers
