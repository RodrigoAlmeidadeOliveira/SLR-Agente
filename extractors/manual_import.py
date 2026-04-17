"""
Importador de arquivos exportados manualmente das bases sem API pública.

Bases suportadas:
  - ACM Digital Library  → exportar como BibTeX (.bib)
  - Web of Science       → exportar como RIS (.ris) ou Plain Text (.txt)
  - Qualquer base        → CSV genérico com colunas padronizadas

Como usar:
  python main.py import acm --file resultados_acm.bib --query-id acm_principal
  python main.py import wos --file resultados_wos.ris --query-id wos_principal
  python main.py import csv --file minha_planilha.csv --db scopus
"""
from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Optional

from extractors.base import Paper

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  BibTeX (ACM, Scopus export, etc.)                                 #
# ------------------------------------------------------------------ #

def import_bibtex(
    filepath: str | Path,
    source_db: str = "acm",
    query_id: str = "",
    query_label: str = "",
) -> list[Paper]:
    """
    Importa papers de um arquivo BibTeX exportado do ACM DL ou similar.
    Requer o pacote bibtexparser.
    """
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.customization import convert_to_unicode

    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    logger.info(f"[Import] Lendo BibTeX: {filepath} ...")

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(filepath, encoding="utf-8", errors="replace") as fh:
        bib_db = bibtexparser.load(fh, parser=parser)

    papers = []
    for entry in bib_db.entries:
        year: Optional[int] = None
        year_raw = entry.get("year", "")
        if year_raw:
            try:
                year = int(str(year_raw).strip()[:4])
            except ValueError:
                pass

        # Autores: separados por " and " no BibTeX padrão
        authors_raw = entry.get("author", "")
        authors = [a.strip() for a in re.split(r"\s+and\s+", authors_raw) if a.strip()]

        doi = (entry.get("doi") or "").strip()
        url = (entry.get("url") or entry.get("link") or "").strip()
        keywords_raw = entry.get("keywords", "")
        keywords = [k.strip() for k in re.split(r"[,;]", keywords_raw) if k.strip()]

        entry_type = entry.get("ENTRYTYPE", "").lower()
        if "article" in entry_type:
            doc_type = "article"
        elif entry_type in ("inproceedings", "proceedings"):
            doc_type = "conference paper"
        elif "incollection" in entry_type or "book" in entry_type:
            doc_type = "chapter"
        else:
            doc_type = entry_type or "unknown"

        venue = (
            entry.get("journal")
            or entry.get("booktitle")
            or entry.get("series")
            or ""
        ).strip()

        paper = Paper(
            source_db=source_db,
            source_query_id=query_id,
            source_query_label=query_label or f"{source_db} import",
            doi=doi,
            title=(entry.get("title") or "").strip("{}").strip(),
            authors=authors,
            year=year,
            abstract=(entry.get("abstract") or "").strip(),
            venue=venue,
            doc_type=doc_type,
            keywords=keywords,
            url=url,
            volume=(entry.get("volume") or "").strip(),
            issue=(entry.get("number") or "").strip(),
            pages=(entry.get("pages") or "").strip(),
            publisher=(entry.get("publisher") or "").strip(),
        )
        papers.append(paper)

    logger.info(f"[Import] {len(papers)} papers importados de {filepath.name}")
    return papers


# ------------------------------------------------------------------ #
#  RIS (Web of Science, Scopus, IEEE export)                          #
# ------------------------------------------------------------------ #

def import_ris(
    filepath: str | Path,
    source_db: str = "wos",
    query_id: str = "",
    query_label: str = "",
) -> list[Paper]:
    """
    Importa papers de um arquivo RIS.
    Suporta exportações do Web of Science e de outras bases.
    """
    import rispy

    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    logger.info(f"[Import] Lendo RIS: {filepath} ...")

    with open(filepath, encoding="utf-8", errors="replace") as fh:
        entries = rispy.load(fh)

    papers = []
    for entry in entries:
        year: Optional[int] = None
        for year_tag in ["PY", "Y1", "DA"]:
            year_raw = entry.get(year_tag, "")
            if year_raw:
                try:
                    year = int(str(year_raw).strip()[:4])
                    break
                except ValueError:
                    pass

        # Autores: AU = lista
        authors = entry.get("AU", []) or entry.get("A1", [])
        authors = [a.strip() for a in authors if a.strip()]

        doi = (entry.get("DO") or entry.get("M3") or "").strip()
        url = (entry.get("UR") or entry.get("L2") or "").strip()

        keywords_raw = entry.get("KW", []) or []
        keywords = [k.strip() for k in keywords_raw if k.strip()]

        type_of_ref = (entry.get("TY") or "").upper()
        if type_of_ref in ("JOUR", "ABST"):
            doc_type = "article"
        elif type_of_ref in ("CONF", "CPAPER"):
            doc_type = "conference paper"
        elif type_of_ref in ("CHAP", "BOOK", "EBOOK"):
            doc_type = "chapter"
        else:
            doc_type = type_of_ref.lower() or "unknown"

        venue = (
            entry.get("JF")
            or entry.get("JO")
            or entry.get("T2")
            or entry.get("BT")
            or ""
        ).strip()

        title = (entry.get("TI") or entry.get("T1") or "").strip()
        abstract = (entry.get("AB") or entry.get("N2") or "").strip()

        paper = Paper(
            source_db=source_db,
            source_query_id=query_id,
            source_query_label=query_label or f"{source_db} import",
            doi=doi,
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            venue=venue,
            doc_type=doc_type,
            keywords=keywords,
            url=url,
            volume=(entry.get("VL") or "").strip(),
            issue=(entry.get("IS") or "").strip(),
            pages=_merge_pages(entry.get("SP"), entry.get("EP")),
            publisher=(entry.get("PB") or "").strip(),
        )
        papers.append(paper)

    logger.info(f"[Import] {len(papers)} papers importados de {filepath.name}")
    return papers


# ------------------------------------------------------------------ #
#  CSV genérico                                                       #
# ------------------------------------------------------------------ #

# Mapeamento de nomes de colunas comuns → campo do Paper
CSV_COLUMN_MAP = {
    "title": "title",
    "titulo": "title",
    "item title": "title",
    "doi": "doi",
    "item doi": "doi",
    "abstract": "abstract",
    "resumo": "abstract",
    "authors": "authors",
    "autores": "authors",
    "year": "year",
    "ano": "year",
    "publication_year": "year",
    "publication year": "year",
    "venue": "venue",
    "journal": "venue",
    "booktitle": "venue",
    "source": "venue",
    "publication title": "venue",
    "book series title": "venue_alt",
    "document_type": "doc_type",
    "type": "doc_type",
    "content type": "doc_type",
    "url": "url",
    "link": "url",
    "keywords": "keywords",
    "journal volume": "volume",
    "volume": "volume",
    "journal issue": "issue",
    "issue": "issue",
    "pages": "pages",
    "publisher": "publisher",
}


def import_csv(
    filepath: str | Path,
    source_db: str = "unknown",
    query_id: str = "",
    query_label: str = "",
    delimiter: str = ",",
) -> list[Paper]:
    """
    Importa papers de um CSV genérico.
    Detecta automaticamente as colunas usando CSV_COLUMN_MAP.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    logger.info(f"[Import] Lendo CSV: {filepath} ...")

    papers = []
    with open(filepath, encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        col_map = {
            col: CSV_COLUMN_MAP[col.lower().strip()]
            for col in (reader.fieldnames or [])
            if col.lower().strip() in CSV_COLUMN_MAP
        }

        for row in reader:
            data: dict = {}
            for csv_col, field_name in col_map.items():
                data[field_name] = (row.get(csv_col) or "").strip()

            year: Optional[int] = None
            if data.get("year"):
                try:
                    year = int(str(data["year"])[:4])
                except ValueError:
                    pass

            # Autores: separados por ";" ou "|"
            authors_raw = data.get("authors", "")
            authors = [a.strip() for a in re.split(r"[;|]", authors_raw) if a.strip()]
            if not authors and authors_raw:
                authors = [authors_raw.strip()]

            keywords_raw = data.get("keywords", "")
            keywords = [k.strip() for k in re.split(r"[;|,]", keywords_raw) if k.strip()]

            venue = data.get("venue", "") or data.get("venue_alt", "")

            paper = Paper(
                source_db=source_db,
                source_query_id=query_id,
                source_query_label=query_label or f"{source_db} csv import",
                doi=data.get("doi", ""),
                title=data.get("title", ""),
                authors=authors,
                year=year,
                abstract=data.get("abstract", ""),
                venue=venue,
                doc_type=data.get("doc_type", "unknown"),
                keywords=keywords,
                url=data.get("url", ""),
                volume=data.get("volume", ""),
                issue=data.get("issue", ""),
                pages=data.get("pages", ""),
                publisher=data.get("publisher", ""),
            )
            papers.append(paper)

    logger.info(f"[Import] {len(papers)} papers importados de {filepath.name}")
    return papers


# ------------------------------------------------------------------ #
#  Web of Science Plain Text (.txt)                                   #
# ------------------------------------------------------------------ #

def import_wos_plaintext(
    filepath: str | Path,
    query_id: str = "",
    query_label: str = "",
) -> list[Paper]:
    """
    Importa exportações do WoS no formato Plain Text (ISI/WoS format).
    Cada registro começa com 'PT ' e termina com 'ER'.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    logger.info(f"[Import] Lendo WoS Plain Text: {filepath} ...")

    with open(filepath, encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    # Divide por registros
    records_raw = re.split(r"\nER\n", content)
    papers = []

    for rec_raw in records_raw:
        rec: dict[str, list[str]] = {}
        current_tag = None
        for line in rec_raw.splitlines():
            if len(line) >= 2 and line[2] == " " and line[:2].strip():
                current_tag = line[:2].strip()
                rec.setdefault(current_tag, [])
                rec[current_tag].append(line[3:].strip())
            elif current_tag and line.startswith("   "):
                rec[current_tag].append(line.strip())

        if not rec.get("TI"):
            continue

        year: Optional[int] = None
        py = rec.get("PY", [""])[0]
        if py:
            try:
                year = int(py[:4])
            except ValueError:
                pass

        authors = [a for sublist in rec.get("AU", []) for a in [sublist] if a]
        title = " ".join(rec.get("TI", []))
        abstract = " ".join(rec.get("AB", []))
        venue = " ".join(rec.get("SO", []) or rec.get("BS", []))
        doi = " ".join(rec.get("DI", []))
        keywords = rec.get("DE", []) + rec.get("ID", [])
        doc_type_raw = " ".join(rec.get("DT", [])).lower()

        if "article" in doc_type_raw:
            doc_type = "article"
        elif "proceedings" in doc_type_raw or "conference" in doc_type_raw:
            doc_type = "conference paper"
        else:
            doc_type = doc_type_raw or "unknown"

        paper = Paper(
            source_db="wos",
            source_query_id=query_id,
            source_query_label=query_label or "wos import",
            doi=doi.strip(),
            title=title.strip(),
            authors=authors,
            year=year,
            abstract=abstract.strip(),
            venue=venue.strip(),
            doc_type=doc_type,
            keywords=[k.strip() for k in keywords if k.strip()],
            volume=" ".join(rec.get("VL", [])),
            issue=" ".join(rec.get("IS", [])),
            pages=" ".join(rec.get("BP", [])) + (
                f"-{rec.get('EP', [''])[0]}" if rec.get("EP") else ""
            ),
            publisher=" ".join(rec.get("PU", [])),
        )
        papers.append(paper)

    logger.info(f"[Import] {len(papers)} papers importados de {filepath.name}")
    return papers


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def _merge_pages(start: Optional[str], end: Optional[str]) -> str:
    if not start:
        return ""
    if not end:
        return start.strip()
    return f"{start.strip()}-{end.strip()}"
