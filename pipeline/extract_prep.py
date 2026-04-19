"""
Prepara pasta de extração de dados para os 169 estudos incluídos.

Ações:
  1. Copia PDFs disponíveis para results/extraction/pdfs/
  2. Enriquece metadados via Semantic Scholar batch API (authors, venue, abstract)
  3. Gera results/extraction/extraction_template.csv com metadados + colunas vazias

Uso:
  python pipeline/extract_prep.py
  python pipeline/extract_prep.py --dry-run
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
import time
from pathlib import Path

import requests

INCLUDED_CSV = Path("results/final_review/included_studies_current.csv")
MANIFEST_CSV = Path("results/pdfs/download_manifest.csv")
PDF_SRC_DIR  = Path("results/pdfs")
EXTRACT_DIR  = Path("results/extraction")
EXTRACT_PDF_DIR = EXTRACT_DIR / "pdfs"
TEMPLATE_CSV = EXTRACT_DIR / "extraction_template.csv"

S2_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
S2_FIELDS    = "title,authors,year,venue,publicationVenue,externalIds,abstract,openAccessPdf,publicationTypes,journal"
S2_CHUNK     = 100  # max per batch request


TEMPLATE_COLUMNS = [
    # --- identificação ---
    "internal_id",
    "title",
    "doi",
    "year",
    "source_db",
    "ft_matched_ic",
    "ft_screened_by",
    # --- metadados enriquecidos ---
    "authors",
    "venue",
    "journal_name",
    "volume",
    "pages",
    "publication_type",
    "abstract",
    # --- PDF ---
    "pdf_available",
    "pdf_file",
    # --- extração (a preencher) ---
    "research_question",
    "study_type",
    "research_contribution",
    "pm_technique",
    "stochastic_technique",
    "software_artifact",
    "software_process",
    "dataset_source",
    "dataset_public",
    "tool_used",
    "main_finding",
    "limitations",
    "replication_package",
    "quality_score",
    "extraction_notes",
]


def _read_csv(p: Path) -> list[dict]:
    if not p.exists():
        return []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _build_manifest_index(rows: list[dict]) -> dict[str, dict]:
    return {r["internal_id"]: r for r in rows if r.get("internal_id")}


def _find_pdf(iid: str, manifest: dict, pdf_dir: Path) -> Path | None:
    m = manifest.get(iid, {})
    fname = (m.get("pdf_file") or "").strip()
    if fname:
        p = pdf_dir / fname
        if p.exists():
            return p
    # fallback: glob by prefix
    hits = list(pdf_dir.glob(f"{iid}*.pdf"))
    return hits[0] if hits else None


def _copy_pdfs(included: list[dict], manifest: dict, dry_run: bool) -> dict[str, str]:
    """Returns mapping internal_id → destination filename (or '' if no PDF)."""
    EXTRACT_PDF_DIR.mkdir(parents=True, exist_ok=True)
    result: dict[str, str] = {}
    copied = skipped = missing = 0

    for row in included:
        iid = row["internal_id"]
        src = _find_pdf(iid, manifest, PDF_SRC_DIR)
        if src is None:
            result[iid] = ""
            missing += 1
            continue
        dst = EXTRACT_PDF_DIR / src.name
        if not dry_run:
            if not dst.exists():
                shutil.copy2(src, dst)
                copied += 1
            else:
                skipped += 1
        else:
            copied += 1  # count as would-copy
        result[iid] = src.name

    print(f"  PDFs copiados : {copied}")
    print(f"  Já existentes : {skipped}")
    print(f"  Sem PDF       : {missing}")
    return result


def _s2_enrich(included: list[dict]) -> dict[str, dict]:
    """Query Semantic Scholar batch API. Returns internal_id → enriched fields."""
    dois = [(r["internal_id"], r.get("doi", "").strip()) for r in included if r.get("doi", "").strip()]
    no_doi = [r["internal_id"] for r in included if not r.get("doi", "").strip()]

    print(f"  {len(dois)} papers com DOI → batch S2")
    print(f"  {len(no_doi)} papers sem DOI → metadados não disponíveis via S2")

    enriched: dict[str, dict] = {}

    for start in range(0, len(dois), S2_CHUNK):
        chunk = dois[start : start + S2_CHUNK]
        ids = [f"DOI:{doi}" for _, doi in chunk]
        try:
            resp = requests.post(
                S2_BATCH_URL,
                params={"fields": S2_FIELDS},
                json={"ids": ids},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                for (iid, _), paper in zip(chunk, data):
                    if paper is None:
                        enriched[iid] = {}
                        continue
                    authors = "; ".join(a.get("name", "") for a in (paper.get("authors") or []))
                    venue = (paper.get("publicationVenue") or {}).get("name", "") or paper.get("venue", "")
                    journal = (paper.get("journal") or {}).get("name", "")
                    volume = (paper.get("journal") or {}).get("volume", "")
                    pages = (paper.get("journal") or {}).get("pages", "")
                    pub_types = "; ".join(paper.get("publicationTypes") or [])
                    abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
                    enriched[iid] = {
                        "authors": authors,
                        "venue": venue,
                        "journal_name": journal,
                        "volume": volume,
                        "pages": pages,
                        "publication_type": pub_types,
                        "abstract": abstract,
                    }
            else:
                print(f"  [WARN] S2 retornou {resp.status_code} no chunk {start//S2_CHUNK + 1}", file=sys.stderr)
        except Exception as exc:
            print(f"  [WARN] Erro S2 no chunk {start//S2_CHUNK + 1}: {exc}", file=sys.stderr)

        if start + S2_CHUNK < len(dois):
            time.sleep(1.0)

    found = sum(1 for v in enriched.values() if v.get("authors"))
    print(f"  Enriquecidos com sucesso: {found}/{len(dois)}")
    return enriched


def _write_template(included: list[dict], pdf_map: dict[str, str], enriched: dict[str, dict], dry_run: bool) -> int:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for paper in included:
        iid = paper["internal_id"]
        e = enriched.get(iid, {})
        pdf_file = pdf_map.get(iid, "")
        row = {col: "" for col in TEMPLATE_COLUMNS}
        # identificação
        row["internal_id"] = iid
        row["title"]        = paper.get("title", "")
        row["doi"]          = paper.get("doi", "")
        row["year"]         = paper.get("year", "")
        row["source_db"]    = paper.get("source_db", "")
        row["ft_matched_ic"]  = paper.get("ft_matched_ic", "")
        row["ft_screened_by"] = paper.get("ft_screened_by", "")
        # enriquecidos
        row["authors"]          = e.get("authors", "")
        row["venue"]            = e.get("venue", "")
        row["journal_name"]     = e.get("journal_name", "")
        row["volume"]           = e.get("volume", "")
        row["pages"]            = e.get("pages", "")
        row["publication_type"] = e.get("publication_type", "")
        row["abstract"]         = e.get("abstract", "") or paper.get("abstract", "")
        # pdf
        row["pdf_available"] = "sim" if pdf_file else "não"
        row["pdf_file"]      = pdf_file
        rows.append(row)

    # sort: sem PDF por último, depois por IC e ano
    rows.sort(key=lambda r: (r["pdf_available"] == "não", r.get("ft_matched_ic", ""), r.get("year", "")))

    if not dry_run:
        with open(TEMPLATE_CSV, "w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=TEMPLATE_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    return len(rows)


def main(dry_run: bool = False) -> None:
    from colorama import Fore, Style, init
    init(autoreset=True)

    print(f"\n{Fore.CYAN}── Carregando dados...{Style.RESET_ALL}")
    included = _read_csv(INCLUDED_CSV)
    manifest = _build_manifest_index(_read_csv(MANIFEST_CSV))
    print(f"  {len(included)} papers incluídos")

    print(f"\n{Fore.CYAN}── Copiando PDFs → {EXTRACT_PDF_DIR}{Style.RESET_ALL}")
    if dry_run:
        print(f"  {Fore.YELLOW}(dry-run — nenhum arquivo será copiado){Style.RESET_ALL}")
    pdf_map = _copy_pdfs(included, manifest, dry_run=dry_run)

    print(f"\n{Fore.CYAN}── Enriquecendo metadados via Semantic Scholar...{Style.RESET_ALL}")
    enriched = _s2_enrich(included)

    print(f"\n{Fore.CYAN}── Gerando template de extração...{Style.RESET_ALL}")
    n = _write_template(included, pdf_map, enriched, dry_run=dry_run)

    with_pdf = sum(1 for v in pdf_map.values() if v)
    without_pdf = sum(1 for v in pdf_map.values() if not v)

    print(f"\n{Fore.GREEN}✓ Concluído{Style.RESET_ALL}")
    print(f"  Template     : {TEMPLATE_CSV}  ({n} linhas)")
    print(f"  PDFs copiados: {with_pdf}  |  Sem PDF: {without_pdf}")
    print(f"\n{Fore.YELLOW}Próximo passo:{Style.RESET_ALL}")
    print(f"  Abra {TEMPLATE_CSV} e defina os campos de extração")
    print(f"  que deseja usar antes de iniciar o preenchimento.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
