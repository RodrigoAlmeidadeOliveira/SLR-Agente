"""
Exportação dos resultados em múltiplos formatos:
  - JSON  (formato interno, para reprocessamento)
  - CSV   (planilha para triagem manual)
  - RIS   (importação no Zotero, Mendeley, Parsifal)
  - BibTeX (importação em ferramentas LaTeX / Parsifal)
  - TXT   (relatório legível de sumário)
"""
from __future__ import annotations

import csv
import json
import logging
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

from extractors.base import Paper
from pipeline.validator import ValidationResult

logger = logging.getLogger(__name__)

CONTROL_SOURCE_DB = "control"


# ------------------------------------------------------------------ #
#  JSON                                                               #
# ------------------------------------------------------------------ #

def save_json(papers: list[Paper], filepath: str | Path) -> Path:
    """Salva lista de papers como JSON (formato interno)."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump([p.to_dict() for p in papers], fh, ensure_ascii=False, indent=2)
    logger.info(f"[Export] JSON salvo: {filepath} ({len(papers)} papers)")
    return filepath


def load_json(filepath: str | Path) -> list[Paper]:
    """Carrega lista de papers a partir de JSON interno."""
    filepath = Path(filepath)
    with open(filepath, encoding="utf-8") as fh:
        data = json.load(fh)
    papers = []
    for d in data:
        p = Paper(**{k: v for k, v in d.items() if k in Paper.__dataclass_fields__})
        papers.append(p)
    logger.info(f"[Export] JSON carregado: {filepath} ({len(papers)} papers)")
    return papers


# ------------------------------------------------------------------ #
#  CSV                                                                #
# ------------------------------------------------------------------ #

CSV_COLUMNS = [
    "internal_id", "source_db", "source_query_id", "source_query_label",
    "doi", "title", "authors", "year", "abstract", "venue",
    "doc_type", "keywords", "url", "volume", "issue", "pages", "publisher",
    "is_duplicate", "duplicate_of", "selected",
]


def save_csv(papers: list[Paper], filepath: str | Path) -> Path:
    """Exporta para CSV com todas as colunas. Ideal para triagem no Excel/Google Sheets."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for p in papers:
            row = p.to_dict()
            row["authors"] = "; ".join(p.authors)
            row["keywords"] = "; ".join(p.keywords)
            writer.writerow(row)
    logger.info(f"[Export] CSV salvo: {filepath} ({len(papers)} papers)")
    return filepath


# ------------------------------------------------------------------ #
#  RIS                                                                #
# ------------------------------------------------------------------ #

def save_ris(papers: list[Paper], filepath: str | Path) -> Path:
    """
    Exporta para formato RIS (importável no Zotero, Mendeley, Parsifal).
    Inclui apenas papers não marcados como duplicata.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    ris_lines = []
    for p in papers:
        if p.is_duplicate:
            continue
        ris_lines.extend(_paper_to_ris(p))
        ris_lines.append("")

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(ris_lines))

    count = sum(1 for p in papers if not p.is_duplicate)
    logger.info(f"[Export] RIS salvo: {filepath} ({count} papers)")
    return filepath


def _paper_to_ris(p: Paper) -> list[str]:
    """Converte um Paper para linhas RIS."""
    lines = []

    # Tipo
    if "conference" in (p.doc_type or "").lower():
        ty = "CPAPER"
    elif "chapter" in (p.doc_type or "").lower():
        ty = "CHAP"
    else:
        ty = "JOUR"

    lines.append(f"TY  - {ty}")
    lines.append(f"TI  - {p.title}")

    for author in p.authors:
        lines.append(f"AU  - {author}")

    if p.year:
        lines.append(f"PY  - {p.year}")

    if p.abstract:
        lines.append(f"AB  - {p.abstract}")

    if p.venue:
        if ty == "JOUR":
            lines.append(f"JF  - {p.venue}")
        else:
            lines.append(f"T2  - {p.venue}")

    if p.doi:
        lines.append(f"DO  - {p.doi}")

    if p.url:
        lines.append(f"UR  - {p.url}")

    if p.volume:
        lines.append(f"VL  - {p.volume}")

    if p.issue:
        lines.append(f"IS  - {p.issue}")

    if p.pages:
        parts = p.pages.split("-")
        lines.append(f"SP  - {parts[0].strip()}")
        if len(parts) > 1:
            lines.append(f"EP  - {parts[1].strip()}")

    if p.publisher:
        lines.append(f"PB  - {p.publisher}")

    for kw in p.keywords:
        lines.append(f"KW  - {kw}")

    lines.append(f"N1  - Source: {p.source_db} | Query: {p.source_query_label}")
    lines.append("ER  - ")
    return lines


# ------------------------------------------------------------------ #
#  BibTeX                                                             #
# ------------------------------------------------------------------ #

def save_bibtex(papers: list[Paper], filepath: str | Path) -> Path:
    """Exporta para BibTeX. Inclui apenas papers não duplicados."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for p in papers:
        if p.is_duplicate:
            continue
        entries.append(_paper_to_bibtex(p))

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(entries))

    count = len(entries)
    logger.info(f"[Export] BibTeX salvo: {filepath} ({count} papers)")
    return filepath


def _paper_to_bibtex(p: Paper) -> str:
    """Converte um Paper para entrada BibTeX."""
    # Chave citekey: firstauthorYYYYfirstword
    first_author = p.first_author_lastname or "unknown"
    year_str = str(p.year) if p.year else "0000"
    first_word = (p.normalized_title.split() or ["x"])[0][:8]
    citekey = f"{first_author}{year_str}{first_word}"

    if "conference" in (p.doc_type or "").lower():
        entry_type = "inproceedings"
    elif "chapter" in (p.doc_type or "").lower():
        entry_type = "incollection"
    else:
        entry_type = "article"

    fields = []
    fields.append(f"  title     = {{{p.title}}}")
    if p.authors:
        fields.append(f"  author    = {{{' and '.join(p.authors)}}}")
    if p.year:
        fields.append(f"  year      = {{{p.year}}}")
    if p.venue:
        key = "journal" if entry_type == "article" else "booktitle"
        fields.append(f"  {key:<9} = {{{p.venue}}}")
    if p.doi:
        fields.append(f"  doi       = {{{p.doi}}}")
    if p.volume:
        fields.append(f"  volume    = {{{p.volume}}}")
    if p.issue:
        fields.append(f"  number    = {{{p.issue}}}")
    if p.pages:
        fields.append(f"  pages     = {{{p.pages}}}")
    if p.publisher:
        fields.append(f"  publisher = {{{p.publisher}}}")
    if p.abstract:
        fields.append(f"  abstract  = {{{p.abstract[:500]}{'...' if len(p.abstract) > 500 else ''}}}")

    body = ",\n".join(fields)
    return f"@{entry_type}{{{citekey},\n{body}\n}}"


# ------------------------------------------------------------------ #
#  Relatório de Sumário                                               #
# ------------------------------------------------------------------ #

def save_report(
    all_papers: list[Paper],
    unique_papers: list[Paper],
    validation_results: Optional[list[ValidationResult]],
    filepath: str | Path,
) -> Path:
    """Gera relatório textual com estatísticas completas da busca."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    primary_all = [p for p in all_papers if p.source_db != CONTROL_SOURCE_DB]
    primary_unique = [p for p in unique_papers if p.source_db != CONTROL_SOURCE_DB]
    control_all = [p for p in all_papers if p.source_db == CONTROL_SOURCE_DB]
    control_unique = [p for p in unique_papers if p.source_db == CONTROL_SOURCE_DB]

    lines = [
        "=" * 70,
        "SLR PATHCAST — SEARCH RESULTS REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        "1. OVERVIEW",
        "-" * 40,
        f"   Total raw results:       {len(all_papers):,}",
        f"   After deduplication:     {len(unique_papers):,}",
        f"   Duplicates removed:      {len(all_papers) - len(unique_papers):,}",
        f"   Duplication rate:        {(len(all_papers) - len(unique_papers)) / max(len(all_papers), 1) * 100:.1f}%",
        "",
        "   Primary search corpus only (excludes control set):",
        f"     Raw:                   {len(primary_all):,}",
        f"     Unique:                {len(primary_unique):,}",
        "",
        "   Control set only:",
        f"     Raw:                   {len(control_all):,}",
        f"     Unique:                {len(control_unique):,}",
        "",
        "2. RESULTS BY DATABASE",
        "-" * 40,
    ]

    db_counter = Counter(p.source_db for p in all_papers)
    db_unique = Counter(p.source_db for p in unique_papers)
    for db in sorted(db_counter):
        lines.append(f"   {db:<15} raw={db_counter[db]:>5,}   unique={db_unique.get(db, 0):>5,}")

    if control_all:
        lines += [
            "",
            "   Note: source_db='control' is validation-only and should not be counted as a search database.",
        ]

    lines += [
        "",
        "3. RESULTS BY QUERY",
        "-" * 40,
    ]
    query_counter = Counter((p.source_db, p.source_query_id) for p in all_papers)
    for (db, qid), count in sorted(query_counter.items()):
        query_label = next(
            (p.source_query_label for p in all_papers if p.source_query_id == qid),
            qid
        )
        lines.append(f"   [{db}] {query_label[:45]:<45}  {count:>5,}")

    lines += [
        "",
        "4. PUBLICATION YEAR DISTRIBUTION (unique papers)",
        "-" * 40,
    ]
    year_counter = Counter(p.year for p in unique_papers if p.year)
    for year in sorted(year_counter):
        bar = "#" * min(year_counter[year] // 2, 40)
        lines.append(f"   {year}  {year_counter[year]:>4}  {bar}")

    lines += [
        "",
        "5. DOCUMENT TYPES (unique papers)",
        "-" * 40,
    ]
    dtype_counter = Counter(p.doc_type for p in unique_papers)
    for dtype, count in dtype_counter.most_common():
        lines.append(f"   {dtype:<25}  {count:>5,}")

    if validation_results:
        lines += [
            "",
            "6. CONTROL PAPERS VALIDATION",
            "-" * 40,
        ]
        from pipeline.validator import ACCEPTANCE_THRESHOLD
        for r in validation_results:
            status = "✓" if r.found else "✗"
            dbs = ", ".join(r.found_in_db) if r.found else "NOT FOUND"
            lines.append(f"   {status} [{r.control_id}] {r.citation:<35}  {dbs}")

        found = sum(1 for r in validation_results if r.found)
        total = len(validation_results)
        lines.append("")
        lines.append(f"   Coverage: {found}/{total}  "
                     f"Status: {'PASS ✓' if found >= ACCEPTANCE_THRESHOLD else 'FAIL ✗'}")

    lines += ["", "=" * 70, ""]

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    logger.info(f"[Export] Relatório salvo: {filepath}")
    return filepath
