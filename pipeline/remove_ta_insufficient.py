"""Remove LLM includes whose title or abstract does not support inclusion.

Source list: results/final_review/labels_ta_insufficient_for_include.csv.
These 32 rows sit in the coded set (the 338); ee562777 was reinstated
because its include decision was PDF-based (see article §3.5). They are not part of the
168 studies added after the human re-screen.
"""
from __future__ import annotations

import csv
from pathlib import Path

from pipeline.apply_eligibility_pass import (
    FAM_PATH,
    INC_PATH,
    MATRIX_PATHS,
    from_legacy_ic,
    write_matrix,
)

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "results/final_review/labels_ta_insufficient_for_include.csv"


def main() -> None:
    labels = list(csv.DictReader(LABELS.open(encoding="utf-8")))
    drop = {row["internal_id"] for row in labels}
    included = list(csv.DictReader(INC_PATH.open(encoding="utf-8")))
    present = {row["internal_id"] for row in included}
    missing = sorted(drop - present)
    if missing:
        raise SystemExit(f"not in corpus: {missing}")

    kept = [row for row in included if row["internal_id"] not in drop]
    for seq, row in enumerate(kept, start=1):
        row["seq"] = str(seq)

    fields = list(included[0].keys())
    with INC_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)

    families = {
        row["internal_id"]: row
        for row in csv.DictReader(FAM_PATH.open(encoding="utf-8"))
    }
    patterns = {}
    for row in kept:
        ident = row["internal_id"]
        if row["corpus_role"] == "original_coded":
            patterns[ident] = from_legacy_ic(row["ic"])
        else:
            fam = families.get(ident)
            if fam and (fam.get("ic") or "").strip():
                patterns[ident] = from_legacy_ic(fam["ic"])
            else:
                patterns[ident] = "BLANK"
    write_matrix(kept, patterns)

    coded = sum(1 for row in kept if row["corpus_role"] == "original_coded")
    added = len(kept) - coded
    triples = sum(
        1 for pattern in patterns.values()
        if {"TF-PM", "TF-ST", "TF-FC"} <= set(pattern.split("|"))
    )
    print("dropped", len(drop), "corpus", len(kept), "coded", coded, "added", added, "triples", triples)

    old = "The %d use the codes already stored for that set." % coded
    new = (
        "The %d remain from the coded list of 338 after 32 studies were removed "
        "because the title or abstract does not support inclusion."
    ) % coded
    for path in MATRIX_PATHS:
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit(f"caption sentence missing in {path}")
        path.write_text(text.replace(old, new), encoding="utf-8")


if __name__ == "__main__":
    main()
