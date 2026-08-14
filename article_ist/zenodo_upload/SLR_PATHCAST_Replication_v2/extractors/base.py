"""
Modelo de dados central e classe base para todos os extratores.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Paper:
    """Representação normalizada de um paper extraído de qualquer base."""

    # Identificação interna
    internal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Fonte
    source_db: str = ""          # "scopus" | "ieee" | "springer" | "acm" | "wos"
    source_query_id: str = ""    # ID da query que capturou este paper
    source_query_label: str = "" # Label legível da query

    # Metadados bibliográficos
    doi: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: str = ""
    venue: str = ""              # Nome do periódico ou conferência
    doc_type: str = ""           # "article" | "conference paper" | "chapter"
    language: str = "English"
    keywords: list[str] = field(default_factory=list)
    url: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    publisher: str = ""
    abstract_source: str = ""       # semanticscholar | openalex | crossref | core
    abstract_match_type: str = ""   # doi_exact | title_exact | title_fuzzy

    # Flags de pipeline
    is_duplicate: bool = False
    duplicate_of: str = ""       # internal_id do paper original
    qа_score: Optional[float] = None
    selected: Optional[bool] = None  # None = não avaliado

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def normalized_doi(self) -> str:
        if not self.doi:
            return ""
        return self.doi.lower().strip().lstrip("https://doi.org/").lstrip("http://dx.doi.org/")

    @property
    def normalized_title(self) -> str:
        import re
        if not self.title:
            return ""
        t = self.title.lower()
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @property
    def first_author_lastname(self) -> str:
        if not self.authors:
            return ""
        name = self.authors[0]
        # "Last, First" ou "First Last"
        if "," in name:
            return name.split(",")[0].strip().lower()
        parts = name.strip().split()
        return parts[-1].lower() if parts else ""


class BaseExtractor:
    """
    Classe base para todos os extratores de bases de dados.
    Subclasses devem implementar `extract(query_id, query_str) -> list[Paper]`.
    """

    def __init__(self, api_key: str, delay: float = 1.0, max_results: int = 0):
        """
        Args:
            api_key:     Chave de API da base.
            delay:       Segundos entre requisições.
            max_results: Limite global de resultados (0 = sem limite).
        """
        self.api_key = api_key
        self.delay = delay
        self.max_results = max_results

    def _sleep(self):
        if self.delay > 0:
            time.sleep(self.delay)

    def extract(self, query_id: str, query_label: str, query_str: str) -> list[Paper]:
        raise NotImplementedError
