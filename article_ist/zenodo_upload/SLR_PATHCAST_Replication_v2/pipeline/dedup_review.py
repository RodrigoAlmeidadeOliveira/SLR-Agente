"""Duplicate-candidate detection across the 404-study confirmed set (SLR PATHCAST).

Discovered while building the human double-screening tooling (Reviewer 1, W1):
qa_combined_381.csv mixes a "working_set" tier (169 studies) with an
"auxiliary" tier (212 studies) that was not deduplicated against the
working set before QA/extraction — at least 55 studies are scored twice
under two different internal_id values. This script generalizes the check
to the full 404-study corpus (381 combined + 23 second auxiliary pass) and
groups rows into duplicate-candidate clusters by exact normalized DOI or
exact normalized title (connected components — a row can join a cluster
via either signal).

This does NOT auto-resolve anything. It writes a review sheet with one row
per flagged study; a human (author) must fill the `decision` column
(`keep` / `drop`) per row before pipeline.dedup_apply can produce corrected,
deduplicated files.

Usage:
    python -m pipeline.dedup_review
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

QA_COMBINED = Path("results/auxiliary/qa_combined_381.csv")
AUX_REFT_QA = Path("results/auxiliary/aux_reft_qa.csv")
OUT_DIR = Path("results/auxiliary")
REVIEW_SHEET = OUT_DIR / "duplicate_candidates_review.csv"


def _norm_doi(s) -> str:
    s = "" if pd.isna(s) else str(s)
    return s.strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _norm_title(s) -> str:
    s = "" if pd.isna(s) else str(s)
    return re.sub(r"\s+", " ", s.strip().lower())


class _UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def load_404() -> pd.DataFrame:
    qa = pd.read_csv(QA_COMBINED)
    aux_reft = pd.read_csv(AUX_REFT_QA)
    aux_reft = aux_reft.copy()
    aux_reft["origin"] = "aux_reft"
    full = pd.concat([qa, aux_reft], ignore_index=True)
    full["_doi"] = full["doi"].map(_norm_doi)
    full["_title"] = full["title"].map(_norm_title)
    return full


def find_duplicate_groups(full: pd.DataFrame) -> pd.DataFrame:
    uf = _UnionFind(full["internal_id"].tolist())

    for _, g in full[full["_doi"] != ""].groupby("_doi"):
        ids = g["internal_id"].tolist()
        for other in ids[1:]:
            uf.union(ids[0], other)

    for _, g in full.groupby("_title"):
        ids = g["internal_id"].tolist()
        if len(ids) > 1:
            for other in ids[1:]:
                uf.union(ids[0], other)

    full = full.copy()
    full["_root"] = full["internal_id"].map(uf.find)
    group_sizes = full.groupby("_root")["internal_id"].transform("count")
    dup = full[group_sizes > 1].copy()

    roots = sorted(dup["_root"].unique())
    root_to_gid = {r: f"G{i+1:03d}" for i, r in enumerate(roots)}
    dup["dup_group_id"] = dup["_root"].map(root_to_gid)

    dup["match_signal"] = dup.apply(
        lambda r: "exact_doi" if r["_doi"] != "" and (full["_doi"] == r["_doi"]).sum() > 1 else "exact_title_only",
        axis=1,
    )

    dup["decision"] = ""  # to be filled by the author: "keep" or "drop"
    dup["decision_notes"] = ""

    cols = ["dup_group_id", "match_signal", "internal_id", "origin", "title", "doi", "year",
            "qa_total", "qa_include", "decision", "decision_notes"]
    dup = dup[cols].sort_values(["dup_group_id", "origin"]).reset_index(drop=True)
    return dup


def main() -> None:
    full = load_404()
    logger.info(f"Loaded {len(full)} studies (381 combined + 23 second auxiliary pass)")
    dup = find_duplicate_groups(full)
    n_groups = dup["dup_group_id"].nunique()
    logger.info(f"Flagged {len(dup)} rows in {n_groups} duplicate-candidate groups")
    logger.info(f"  by match_signal: {dict(dup.groupby('dup_group_id')['match_signal'].first().value_counts())}")
    cross_tier = 0
    within_tier = 0
    for _, g in dup.groupby("dup_group_id"):
        if g["origin"].nunique() > 1:
            cross_tier += 1
        else:
            within_tier += 1
    logger.info(f"  cross-tier groups (working_set <-> auxiliary/aux_reft): {cross_tier}")
    logger.info(f"  within-tier groups (same origin repeated): {within_tier}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dup.to_csv(REVIEW_SHEET, index=False, encoding="utf-8")
    logger.info(f"Review sheet: {REVIEW_SHEET}")
    logger.info("Fill the 'decision' column ('keep'/'drop') per row, one row per group must be "
                "'keep' at minimum (or all 'drop' if the whole group is invalid), then run "
                "`python -m pipeline.dedup_apply`.")


if __name__ == "__main__":
    main()
