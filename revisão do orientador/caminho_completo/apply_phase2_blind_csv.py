#!/usr/bin/env python3
"""Aplica decisões de uma planilha CSV ao sheet/master da Fase 2.3.

CSV deve ter: audit_id, decision_A (ou decision_B), opcional notes_A/notes_B.

  python3 apply_phase2_blind_csv.py --rater A --file phase2_blind_raterA_includes.csv --coder Rodrigo
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
SHEET = DIR / "phase2_blind_rescreen_sheet.csv"
MASTER = DIR / "phase2_blind_rescreen_master.csv"
VALID = {"include", "exclude", "not_assessable"}
ALIAS = {
    "i": "include",
    "inc": "include",
    "e": "exclude",
    "exc": "exclude",
    "n": "not_assessable",
    "na": "not_assessable",
}


def load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rater", required=True, choices=["A", "B", "a", "b"])
    ap.add_argument("--file", required=True)
    ap.add_argument("--coder", default="Rodrigo")
    args = ap.parse_args()
    r = args.rater.upper()
    dec_in = f"decision_{r}"
    notes_in = f"notes_{r}"
    dec_col = f"rater_{r}_decision"
    notes_col = f"rater_{r}_notes"
    coder_col = f"coder_{r}"

    incoming = load(Path(args.file))
    sheet = load(SHEET)
    master = load(MASTER)
    by_s = {x["audit_id"]: x for x in sheet}
    by_m = {x["audit_id"]: x for x in master}

    n = 0
    for row in incoming:
        aid = (row.get("audit_id") or "").strip()
        raw = (row.get(dec_in) or row.get("decision") or "").strip().lower().replace(" ", "_")
        if not aid or not raw:
            continue
        d = ALIAS.get(raw, raw)
        if d not in VALID:
            print(f"skip {aid}: inválido {raw!r}")
            continue
        if aid not in by_s:
            print(f"skip {aid}: não está no sheet")
            continue
        notes = (row.get(notes_in) or row.get("notes") or "").strip()
        for store in (by_s[aid], by_m[aid]):
            store[dec_col] = d
            store[notes_col] = notes
            store[coder_col] = args.coder
            store["date"] = date.today().isoformat()
        n += 1
        print(f"{aid} → {d}")

    save(SHEET, sheet)
    save(MASTER, master)
    left = sum(1 for x in sheet if not (x.get(dec_col) or "").strip())
    print(f"Aplicados: {n}. Ainda vazios no sheet (qualquer estrato): {left}")


if __name__ == "__main__":
    main()
