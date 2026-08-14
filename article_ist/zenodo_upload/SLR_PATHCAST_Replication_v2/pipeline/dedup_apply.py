"""Apply author-adjudicated duplicate decisions to the 404-study confirmed set.

Reads results/auxiliary/duplicate_candidates_review.csv (produced by
pipeline.dedup_review and adjudicated by the author — see decisions for
G045 and G060 in the commit/PR that introduced this script) and writes
deduplicated versions of qa_combined_381.csv and extraction_combined_381.csv,
plus a recomputed headline-numbers summary for the manuscript.

Editorial decisions applied (2026-07-07, author-confirmed):
  - G045 ("A Stochastic Petri net Model of CI/CD", ISSREW'22 workshop vs
    RAMS'23 conference): kept as TWO distinct primary studies (conference
    version judged to contain substantial extensions beyond the workshop
    paper) — decision='keep' for both internal_ids.
  - G060 ("An integrated infrastructure using process mining techniques for
    software process verification", 3 IGI Global book-chapter reprints):
    same underlying study republished editorially — decision='keep' only
    for the highest-QA copy (internal_id=2647ea07, qa_total=7), 'drop' for
    the other two.
  - All other 62 groups (exact normalized-DOI or exact-title cross-tier
    matches between working_set and auxiliary/aux_reft): unambiguous
    duplicates — keep the working_set-tier copy (or, if no working_set row
    is in the group, the row with the highest qa_total), drop the rest.

Usage:
    python -m pipeline.dedup_apply
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

REVIEW_SHEET = Path("results/auxiliary/duplicate_candidates_review.csv")
QA_COMBINED = Path("results/auxiliary/qa_combined_381.csv")
EXTRACTION_COMBINED = Path("results/auxiliary/extraction_combined_381.csv")
AUX_REFT_QA = Path("results/auxiliary/aux_reft_qa.csv")
AUX_REFT_EXTRACTION = Path("results/auxiliary/aux_reft_extraction.csv")

QA_DEDUP_OUT = Path("results/auxiliary/qa_combined_381_dedup.csv")
EXTRACTION_DEDUP_OUT = Path("results/auxiliary/extraction_combined_381_dedup.csv")
QA_404_DEDUP_OUT = Path("results/auxiliary/qa_combined_404_dedup.csv")
EXTRACTION_404_DEDUP_OUT = Path("results/auxiliary/extraction_combined_404_dedup.csv")
SUMMARY_OUT = Path("results/auxiliary/dedup_summary.txt")

# Explicit editorial adjudication (see module docstring).
KEEP_BOTH_GROUPS = {"G045"}
MANUAL_KEEP_IDS = {"2647ea07"}  # G060: keep this one only
MANUAL_GROUPS = {"G045", "G060"}


def resolve_decisions(review: pd.DataFrame) -> pd.DataFrame:
    review = review.copy()
    for gid, g in review.groupby("dup_group_id"):
        idx = g.index
        if gid in KEEP_BOTH_GROUPS:
            review.loc[idx, "decision"] = "keep"
            review.loc[idx, "decision_notes"] = "author: distinct contributions (workshop vs extended conference version)"
            continue
        if gid == "G060":
            for i in idx:
                iid = review.loc[i, "internal_id"]
                if iid in MANUAL_KEEP_IDS:
                    review.loc[i, "decision"] = "keep"
                    review.loc[i, "decision_notes"] = "author: same study, editorial reprint — canonical (highest QA) copy"
                else:
                    review.loc[i, "decision"] = "drop"
                    review.loc[i, "decision_notes"] = "author: same study, editorial reprint — duplicate of G060 keeper"
            continue
        # unambiguous groups: prefer working_set tier; else highest qa_total
        ws_rows = g[g["origin"] == "working_set"]
        if len(ws_rows) == 1:
            keep_id = ws_rows["internal_id"].iloc[0]
        else:
            keep_id = g.sort_values("qa_total", ascending=False)["internal_id"].iloc[0]
        for i in idx:
            iid = review.loc[i, "internal_id"]
            if iid == keep_id:
                review.loc[i, "decision"] = "keep"
                review.loc[i, "decision_notes"] = "auto: unambiguous cross/within-tier duplicate — canonical copy"
            else:
                review.loc[i, "decision"] = "drop"
                review.loc[i, "decision_notes"] = "auto: unambiguous cross/within-tier duplicate — same study as keeper"
    return review


def main() -> None:
    if not REVIEW_SHEET.exists():
        raise FileNotFoundError(f"{REVIEW_SHEET} missing — run `python -m pipeline.dedup_review` first")

    review = pd.read_csv(REVIEW_SHEET)
    review["decision"] = review["decision"].astype("object")
    review["decision_notes"] = review["decision_notes"].astype("object")
    review = resolve_decisions(review)
    review.to_csv(REVIEW_SHEET, index=False, encoding="utf-8")

    drop_ids = set(review[review["decision"] == "drop"]["internal_id"])
    logger.info(f"Resolved {review['dup_group_id'].nunique()} groups; dropping {len(drop_ids)} duplicate rows")

    qa_381 = pd.read_csv(QA_COMBINED)
    ext_381 = pd.read_csv(EXTRACTION_COMBINED)
    ext_381 = ext_381.loc[:, ~ext_381.columns.duplicated()]

    qa_381_dedup = qa_381[~qa_381["internal_id"].isin(drop_ids)].reset_index(drop=True)
    ext_381_dedup = ext_381[~ext_381["internal_id"].isin(drop_ids)].reset_index(drop=True)
    qa_381_dedup.to_csv(QA_DEDUP_OUT, index=False, encoding="utf-8")
    ext_381_dedup.to_csv(EXTRACTION_DEDUP_OUT, index=False, encoding="utf-8")

    aux_reft_qa = pd.read_csv(AUX_REFT_QA)
    aux_reft_ext = pd.read_csv(AUX_REFT_EXTRACTION)
    aux_reft_qa_dedup = aux_reft_qa[~aux_reft_qa["internal_id"].isin(drop_ids)].reset_index(drop=True)
    aux_reft_ext_dedup = aux_reft_ext[~aux_reft_ext["internal_id"].isin(drop_ids)].reset_index(drop=True)

    qa_404_dedup = pd.concat([qa_381_dedup, aux_reft_qa_dedup], ignore_index=True)
    ext_404_dedup = pd.concat([ext_381_dedup, aux_reft_ext_dedup], ignore_index=True)
    qa_404_dedup.to_csv(QA_404_DEDUP_OUT, index=False, encoding="utf-8")
    ext_404_dedup.to_csv(EXTRACTION_404_DEDUP_OUT, index=False, encoding="utf-8")

    qa_pass_before = int((qa_381["qa_total"] >= 4).sum())
    qa_pass_after_381 = int((qa_381_dedup["qa_total"] >= 4).sum())
    qa_pass_after_404 = int((qa_404_dedup["qa_total"] >= 4).sum())

    lines = [
        "SLR PATHCAST — Deduplication Summary (post Reviewer-1 W1 tooling discovery)",
        "=" * 70,
        f"381-tier (working_set + auxiliary): {len(qa_381)} -> {len(qa_381_dedup)} distinct studies "
        f"({len(qa_381) - len(qa_381_dedup)} duplicates removed)",
        f"404-tier (381 + second auxiliary pass): {len(qa_381) + len(aux_reft_qa)} -> {len(qa_404_dedup)} distinct studies "
        f"({(len(qa_381) + len(aux_reft_qa)) - len(qa_404_dedup)} duplicates removed)",
        "",
        f"QA-passed (>=4/8) before dedup, 381-tier: {qa_pass_before}/{len(qa_381)} ({qa_pass_before/len(qa_381)*100:.1f}%)",
        f"QA-passed (>=4/8) after dedup, 381-tier:  {qa_pass_after_381}/{len(qa_381_dedup)} ({qa_pass_after_381/len(qa_381_dedup)*100:.1f}%)",
        f"QA-passed (>=4/8) after dedup, 404-tier:  {qa_pass_after_404}/{len(qa_404_dedup)} ({qa_pass_after_404/len(qa_404_dedup)*100:.1f}%)",
        "",
        "Editorial adjudications:",
        "  G045 (Petri net CI/CD, ISSREW'22 vs RAMS'23): kept as 2 distinct studies (author decision)",
        "  G060 (IGI Global chapter reprinted 3x): kept as 1 study, canonical copy internal_id=2647ea07 (author decision)",
        "  Remaining 62 groups: auto-resolved as unambiguous cross/within-tier duplicates (working_set copy kept)",
        "",
        "Files written:",
        f"  {QA_DEDUP_OUT}",
        f"  {EXTRACTION_DEDUP_OUT}",
        f"  {QA_404_DEDUP_OUT}",
        f"  {EXTRACTION_404_DEDUP_OUT}",
        "",
        "ACTION REQUIRED: update cap3_article_body.tex — every occurrence of '381' and '404' "
        "(text, tables, figures, RQ1-RQ3/F1-F5 percentages, SPMF taxonomy counts) must be "
        "reviewed against the corrected counts above before resubmission.",
    ]
    SUMMARY_OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    logger.info(f"Summary: {SUMMARY_OUT}")


if __name__ == "__main__":
    main()
