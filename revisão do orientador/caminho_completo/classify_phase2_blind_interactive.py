#!/usr/bin/env python3
"""Re-triagem cega Fase 2 — phase2_blind_rescreen_sheet.csv / master.csv

Uso:
  python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --pending-only
  python3 classify_phase2_blind_interactive.py --coder Juliano --rater B --pending-only
  python3 classify_phase2_blind_interactive.py --score
  python3 classify_phase2_blind_interactive.py --includes-only --rater A --pending-only
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
SHEET = DIR / "phase2_blind_rescreen_sheet.csv"
MASTER = DIR / "phase2_blind_rescreen_master.csv"
VALID = {"include", "exclude", "not_assessable"}


def load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def ask(p: str) -> str:
    try:
        return input(p).strip()
    except EOFError:
        return "q"


def rater_key(rater: str) -> tuple[str, str, str]:
    r = rater.upper()
    if r == "A":
        return "rater_A_decision", "rater_A_notes", "coder_A"
    if r == "B":
        return "rater_B_decision", "rater_B_notes", "coder_B"
    raise SystemExit("--rater deve ser A ou B")


def pending(rows: list[dict[str, str]], dec_col: str, includes_only: bool, master: list[dict[str, str]]) -> list[dict[str, str]]:
    master_by = {r["audit_id"]: r for r in master}
    out = []
    for r in rows:
        if includes_only and master_by.get(r["audit_id"], {}).get("original_decision") != "include":
            continue
        if not (r.get(dec_col) or "").strip():
            out.append(r)
    return out


def score(master: list[dict[str, str]]) -> None:
    both = [r for r in master if (r.get("rater_A_decision") or "").strip() and (r.get("rater_B_decision") or "").strip()]
    print(f"Pares A+B preenchidos: {len(both)}/{len(master)}")
    if not both:
        return
    agree = sum(1 for r in both if r["rater_A_decision"] == r["rater_B_decision"])
    print(f"Concordância bruta A vs B: {agree}/{len(both)} = {100 * agree / len(both):.1f}%")
    # simple kappa multiclass
    labels = sorted(VALID)
    n = len(both)
    po = agree / n
    pe = 0.0
    for lab in labels:
        pa = sum(1 for r in both if r["rater_A_decision"] == lab) / n
        pb = sum(1 for r in both if r["rater_B_decision"] == lab) / n
        pe += pa * pb
    kappa = (po - pe) / (1 - pe) if pe < 1 else 0.0
    print(f"Cohen κ (aproximado): {kappa:.3f}")

    # vs original when consensus or A-only
    for who, col in [("A", "rater_A_decision"), ("B", "rater_B_decision"), ("consensus", "consensus_decision")]:
        rows = [r for r in master if (r.get(col) or "").strip() and r.get("original_decision") in {"include", "exclude"}]
        if not rows:
            continue
        ok = sum(1 for r in rows if r[col] == r["original_decision"])
        print(f"Concordância {who} vs original (assessable): {ok}/{len(rows)} = {100 * ok / len(rows):.1f}%")
        flips = [r for r in rows if r[col] in {"include", "exclude"} and r[col] != r["original_decision"]]
        print(f"  flips: {len(flips)}  {Counter((r['original_decision'], r[col]) for r in flips)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder", default="Rodrigo")
    ap.add_argument("--rater", choices=["A", "B", "a", "b"])
    ap.add_argument("--pending-only", action="store_true")
    ap.add_argument("--includes-only", action="store_true")
    ap.add_argument("--score", action="store_true")
    args = ap.parse_args()

    sheet = load(SHEET)
    master = load(MASTER)
    if args.score:
        # sync decisions from sheet into master for scoring
        by = {r["audit_id"]: r for r in sheet}
        for m in master:
            s = by.get(m["audit_id"], {})
            for k in ("rater_A_decision", "rater_A_notes", "rater_B_decision", "rater_B_notes",
                      "consensus_decision", "coder_A", "coder_B", "date"):
                if s.get(k):
                    m[k] = s[k]
            if m.get("consensus_decision") and m.get("original_decision"):
                m["agree_original"] = "yes" if m["consensus_decision"] == m["original_decision"] else "no"
        save(MASTER, master)
        score(master)
        return

    if not args.rater:
        raise SystemExit("informe --rater A|B")
    dec_col, notes_col, coder_col = rater_key(args.rater)
    queue = pending(sheet, dec_col, args.includes_only, master) if args.pending_only else sheet
    print(f"Coder={args.coder} rater={args.rater.upper()} fila={len(queue)} (includes-only={args.includes_only})")
    print("Labels: include | exclude | not_assessable | s=skip | q=quit")

    by_m = {r["audit_id"]: r for r in master}
    for i, r in enumerate(queue, 1):
        print("\n" + "=" * 72)
        print(f"[{i}/{len(queue)}] {r['audit_id']}  stratum={r['stratum']}  year={r.get('year')}")
        print(f"Title: {r.get('title')}")
        print(f"DOI: {r.get('doi')}  URL: {r.get('url')}")
        abs_ = (r.get("abstract") or "").strip()
        print(f"Abstract: {abs_[:500] if abs_ else '(vazio)'}")
        d = ask("decision > ").lower().replace(" ", "_")
        if d == "q":
            break
        if d in {"", "s"}:
            continue
        if d in {"na", "n/a"}:
            d = "not_assessable"
        if d not in VALID:
            print("inválido")
            continue
        notes = ask("notes > ")
        r[dec_col] = d
        r[notes_col] = notes
        r[coder_col] = args.coder
        r["date"] = date.today().isoformat()
        # mirror to master
        m = by_m[r["audit_id"]]
        m[dec_col] = d
        m[notes_col] = notes
        m[coder_col] = args.coder
        m["date"] = r["date"]
        save(SHEET, sheet)
        save(MASTER, master)
        print(f"Gravado {r['audit_id']} → {d}")

    left = pending(sheet, dec_col, args.includes_only, master)
    print(f"Pendentes rater {args.rater.upper()}: {len(left)}")


if __name__ == "__main__":
    main()
