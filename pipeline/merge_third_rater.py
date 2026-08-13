"""Merge third-rater QA/extraction batch outputs into a single CSV.

Reads batch files from results/human_validation/third_rater_batches/:
  - batch_00.json (or batch_00.csv)
  - batch_01.csv … batch_08.csv

Writes results/human_validation/third_rater_qa_extraction.csv (108 rows).

Usage:
    python -m pipeline.merge_third_rater
    python -m pipeline.merge_third_rater --validate-only
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

HUMAN_DIR = Path("results/human_validation")
BATCH_DIR = HUMAN_DIR / "third_rater_batches"
OUT_CSV = HUMAN_DIR / "third_rater_qa_extraction.csv"

FIELDNAMES = [
    "review_id",
    "QA1", "QA2", "QA3", "QA4", "QA5", "QA6", "QA7", "QA8",
    "qa_total",
    "qa_notes",
    "research_question",
    "study_type",
    "pm_technique",
    "stochastic_technique",
    "software_process",
    "dataset_source",
    "main_finding",
    "limitations",
]


def _load_batch(path: Path) -> list[dict]:
    if path.suffix == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))
    else:
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return rows


def load_all_batches(batch_dir: Path = BATCH_DIR) -> list[dict]:
    all_rows: list[dict] = []
    for i in range(9):
        stem = f"batch_{i:02d}"
        json_path = batch_dir / f"{stem}.json"
        csv_path = batch_dir / f"{stem}.csv"
        if json_path.exists():
            path = json_path
        elif csv_path.exists():
            path = csv_path
        else:
            raise FileNotFoundError(f"Missing {stem}.json or {stem}.csv in {batch_dir}")
        rows = _load_batch(path)
        if len(rows) != 12:
            raise ValueError(f"{path.name}: expected 12 rows, got {len(rows)}")
        all_rows.extend(rows)
    return all_rows


def validate_rows(rows: list[dict]) -> list[str]:
    issues: list[str] = []
    if len(rows) != 108:
        issues.append(f"expected 108 rows, got {len(rows)}")

    ids = [r["review_id"] for r in rows]
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    if dupes:
        issues.append(f"duplicate review_id values: {dupes}")

    for r in rows:
        rid = r["review_id"]
        missing = set(FIELDNAMES) - set(r.keys())
        extra = set(r.keys()) - set(FIELDNAMES)
        if missing:
            issues.append(f"{rid}: missing columns {sorted(missing)}")
        if extra:
            issues.append(f"{rid}: unexpected columns {sorted(extra)}")
        try:
            qa_sum = sum(int(r[f"QA{i}"]) for i in range(1, 9))
        except (TypeError, ValueError) as exc:
            issues.append(f"{rid}: invalid QA values ({exc})")
            continue
        if qa_sum != int(r["qa_total"]):
            issues.append(f"{rid}: qa_total={r['qa_total']} but sum QA1-8={qa_sum}")
        for i in range(1, 9):
            v = int(r[f"QA{i}"])
            if v not in (0, 1):
                issues.append(f"{rid}: QA{i}={v} (expected 0 or 1)")

    return issues


def write_csv(rows: list[dict], out_path: Path = OUT_CSV) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in FIELDNAMES})


def main() -> None:
    ap = argparse.ArgumentParser(description="Merge third-rater batch files into one CSV")
    ap.add_argument("--validate-only", action="store_true", help="Validate without writing output")
    ap.add_argument("--batch-dir", type=Path, default=BATCH_DIR)
    ap.add_argument("--out", type=Path, default=OUT_CSV)
    args = ap.parse_args()

    rows = load_all_batches(args.batch_dir)
    issues = validate_rows(rows)
    if issues:
        print("Validation FAILED:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    qa_totals = Counter(int(r["qa_total"]) for r in rows)
    print(f"Loaded {len(rows)} rows from {args.batch_dir}")
    print(f"qa_total distribution: {dict(sorted(qa_totals.items()))}")

    if args.validate_only:
        print("Validation OK (no output written)")
        return

    write_csv(rows, args.out)
    print(f"Wrote {args.out} ({len(rows)} data rows + header)")


if __name__ == "__main__":
    main()
