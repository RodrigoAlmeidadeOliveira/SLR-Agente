from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


SCREENING_DIR = Path("results/screening")
PDF_DIR = Path("results/pdfs")
FINAL_DIR = Path("results/final_review")

FT_RESULTS_CSV = SCREENING_DIR / "ft_screening_results.csv"
MANIFEST_CSV = PDF_DIR / "download_manifest.csv"

PENDING_REVIEW_CSV = FINAL_DIR / "fulltext_pending_review.csv"
PENDING_REVIEW_PRIORITIZED_CSV = FINAL_DIR / "fulltext_pending_review_prioritized.csv"
PENDING_DOI_NO_PDF_CSV = FINAL_DIR / "fulltext_pending_doi_no_pdf.csv"
CURRENT_INCLUDED_CSV = FINAL_DIR / "included_studies_current.csv"
PRISMA_SUMMARY_TXT = FINAL_DIR / "prisma_summary_current.txt"

PENDING_COLUMNS = [
    "internal_id",
    "title",
    "doi",
    "year",
    "source_db",
    "source_query_id",
    "source_query_label",
    "ta_decision",
    "ta_matched_ic",
    "ta_matched_ec",
    "ft_priority_rank",
    "ft_priority_band",
    "ft_priority_score",
    "abstract",
    "ft_oa_url",
    "operational_priority_group",
    "operational_priority_rank",
    "pdf_status",
    "pdf_source",
    "pdf_file",
    "oa_url",
    "current_ft_decision",
    "current_ft_rationale",
    "review_final_decision",
    "review_exclusion_criterion",
    "review_notes",
]

INCLUDED_COLUMNS = [
    "internal_id",
    "title",
    "doi",
    "year",
    "source_db",
    "source_query_id",
    "source_query_label",
    "ta_decision",
    "ft_decision",
    "ft_rationale",
    "ft_matched_ic",
    "ft_matched_ec",
    "ft_screened_by",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _load_manifest_index() -> dict[str, dict[str, str]]:
    rows = _read_csv(MANIFEST_CSV)
    return {row["internal_id"]: row for row in rows if row.get("internal_id")}


def _priority_group(paper: dict, pdf: dict) -> tuple[str, int]:
    has_oa = bool((paper.get("ft_oa_url") or "").strip())
    pdf_status = (pdf.get("pdf_status") or "").strip().lower()
    has_pdf = pdf_status in {"downloaded", "oa_found"}
    has_doi = bool((paper.get("doi") or "").strip())
    band = (paper.get("ft_priority_band") or "").strip().upper()

    if has_oa or has_pdf:
        return "1_com_pdf_ou_oa", 1
    if has_doi:
        return "2_com_doi_sem_pdf", 2
    if band == "D":
        return "3_banda_d_sem_doi", 3
    if band == "E":
        return "4_banda_e_sem_doi", 4
    return "5_outros_sem_doi", 5


def export_pending_review_sheet() -> tuple[Path, int]:
    papers = _read_csv(FT_RESULTS_CSV)
    manifest = _load_manifest_index()

    pending_rows: list[dict[str, str]] = []
    for paper in papers:
        decision = (paper.get("ft_decision") or "").strip().lower()
        if decision:
            continue

        pdf = manifest.get(paper.get("internal_id", ""), {})
        priority_group, priority_rank = _priority_group(paper, pdf)
        pending_rows.append({
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "year": paper.get("year", ""),
            "source_db": paper.get("source_db", ""),
            "source_query_id": paper.get("source_query_id", ""),
            "source_query_label": paper.get("source_query_label", ""),
            "ta_decision": paper.get("ta_decision", ""),
            "ta_matched_ic": paper.get("ta_matched_ic", ""),
            "ta_matched_ec": paper.get("ta_matched_ec", ""),
            "ft_priority_rank": paper.get("ft_priority_rank", ""),
            "ft_priority_band": paper.get("ft_priority_band", ""),
            "ft_priority_score": paper.get("ft_priority_score", ""),
            "abstract": paper.get("abstract", ""),
            "ft_oa_url": paper.get("ft_oa_url", ""),
            "operational_priority_group": priority_group,
            "operational_priority_rank": priority_rank,
            "pdf_status": pdf.get("pdf_status", ""),
            "pdf_source": pdf.get("pdf_source", ""),
            "pdf_file": pdf.get("pdf_file", ""),
            "oa_url": pdf.get("oa_url", ""),
            "current_ft_decision": paper.get("ft_decision", ""),
            "current_ft_rationale": paper.get("ft_rationale", ""),
            "review_final_decision": "",
            "review_exclusion_criterion": "",
            "review_notes": "",
        })

    pending_rows.sort(
        key=lambda row: (
            int(row["operational_priority_rank"]) if str(row.get("operational_priority_rank", "")).isdigit() else 999999,
            int(row["ft_priority_rank"]) if str(row.get("ft_priority_rank", "")).isdigit() else 999999,
            row.get("title", ""),
        )
    )
    _write_csv(PENDING_REVIEW_CSV, pending_rows, PENDING_COLUMNS)
    _write_csv(PENDING_REVIEW_PRIORITIZED_CSV, pending_rows, PENDING_COLUMNS)
    doi_no_pdf_rows = [
        row for row in pending_rows
        if row.get("operational_priority_group") == "2_com_doi_sem_pdf"
    ]
    _write_csv(PENDING_DOI_NO_PDF_CSV, doi_no_pdf_rows, PENDING_COLUMNS)
    return PENDING_REVIEW_CSV, len(pending_rows)


def export_included_studies_current() -> tuple[Path, int]:
    papers = _read_csv(FT_RESULTS_CSV)
    included = []
    for paper in papers:
        if (paper.get("ft_decision") or "").strip().lower() != "include":
            continue
        included.append({col: paper.get(col, "") for col in INCLUDED_COLUMNS})

    included.sort(key=lambda row: (row.get("year", ""), row.get("title", "")), reverse=True)
    _write_csv(CURRENT_INCLUDED_CSV, included, INCLUDED_COLUMNS)
    return CURRENT_INCLUDED_CSV, len(included)


def build_prisma_summary() -> tuple[Path, str]:
    papers = _read_csv(FT_RESULTS_CSV)
    manifest = _load_manifest_index()

    total = len(papers)
    decisions = Counter((p.get("ft_decision") or "").strip().lower() or "<blank>" for p in papers)
    ta = Counter((p.get("ta_decision") or "").strip().lower() or "<blank>" for p in papers)
    bands = Counter((p.get("ft_priority_band") or "").strip().upper() or "<blank>" for p in papers)

    pending_ids = {
        p.get("internal_id", "")
        for p in papers
        if not (p.get("ft_decision") or "").strip()
    }
    pending_manifest = [row for pid, row in manifest.items() if pid in pending_ids]
    pdf_status = Counter((row.get("pdf_status") or "").strip().lower() or "<blank>" for row in pending_manifest)
    pending_papers = [p for p in papers if not (p.get("ft_decision") or "").strip()]

    operational_counts = Counter()
    for paper in pending_papers:
        pdf = manifest.get(paper.get("internal_id", ""), {})
        group, _ = _priority_group(paper, pdf)
        operational_counts[group] += 1

    ec_counts = Counter()
    for paper in papers:
        if (paper.get("ft_decision") or "").strip().lower() != "exclude":
            continue
        ecs = [item.strip() for item in (paper.get("ft_matched_ec") or "").split("|") if item.strip()]
        ec_counts[ecs[0] if ecs else "<missing>"] += 1

    lines = [
        "SLR PATHCAST — Current Full-Text / PRISMA Snapshot",
        "=" * 60,
        f"Full-text queue total: {total}",
        f"T/A include in queue: {ta.get('include', 0)}",
        f"T/A maybe in queue: {ta.get('maybe', 0)}",
        "",
        "Current FT decisions:",
        f"  include: {decisions.get('include', 0)}",
        f"  exclude: {decisions.get('exclude', 0)}",
        f"  pending: {decisions.get('pending', 0)}",
        f"  blank / unresolved: {decisions.get('<blank>', 0)}",
        "",
        "Priority bands among queue:",
        f"  A: {bands.get('A', 0)}",
        f"  B: {bands.get('B', 0)}",
        f"  C: {bands.get('C', 0)}",
        f"  D: {bands.get('D', 0)}",
        f"  E: {bands.get('E', 0)}",
        "",
        "PDF availability among pending items already attempted for download:",
        f"  downloaded: {pdf_status.get('downloaded', 0)}",
        f"  oa_found: {pdf_status.get('oa_found', 0)}",
        f"  manual: {pdf_status.get('manual', 0)}",
        f"  not_found: {pdf_status.get('not_found', 0)}",
        "",
        "Operational priority groups among unresolved items:",
        f"  1_com_pdf_ou_oa: {operational_counts.get('1_com_pdf_ou_oa', 0)}",
        f"  2_com_doi_sem_pdf: {operational_counts.get('2_com_doi_sem_pdf', 0)}",
        f"  3_banda_d_sem_doi: {operational_counts.get('3_banda_d_sem_doi', 0)}",
        f"  4_banda_e_sem_doi: {operational_counts.get('4_banda_e_sem_doi', 0)}",
        f"  5_outros_sem_doi: {operational_counts.get('5_outros_sem_doi', 0)}",
        "",
        "Dominant exclusion criterion among current FT excludes:",
    ]
    if ec_counts:
        for ec, count in ec_counts.most_common():
            lines.append(f"  {ec}: {count}")
    else:
        lines.append("  none recorded")

    lines += [
        "",
        "To finalize the SLR, the 739 unresolved items should be turned into:",
        "  include",
        "  exclude",
        "  pending only when full text remains inaccessible",
        "",
        "Artifacts generated alongside this snapshot:",
        f"  Pending review sheet: {PENDING_REVIEW_CSV}",
        f"  Pending prioritized: {PENDING_REVIEW_PRIORITIZED_CSV}",
        f"  Pending DOI no PDF: {PENDING_DOI_NO_PDF_CSV}",
        f"  Current included studies: {CURRENT_INCLUDED_CSV}",
    ]

    report = "\n".join(lines) + "\n"
    PRISMA_SUMMARY_TXT.parent.mkdir(parents=True, exist_ok=True)
    PRISMA_SUMMARY_TXT.write_text(report, encoding="utf-8")
    return PRISMA_SUMMARY_TXT, report


def export_finalization_artifacts() -> dict[str, object]:
    pending_path, pending_count = export_pending_review_sheet()
    included_path, included_count = export_included_studies_current()
    prisma_path, report = build_prisma_summary()
    return {
        "pending_review_path": pending_path,
        "pending_review_count": pending_count,
        "pending_review_prioritized_path": PENDING_REVIEW_PRIORITIZED_CSV,
        "pending_doi_no_pdf_path": PENDING_DOI_NO_PDF_CSV,
        "included_path": included_path,
        "included_count": included_count,
        "prisma_summary_path": prisma_path,
        "prisma_summary": report,
    }
