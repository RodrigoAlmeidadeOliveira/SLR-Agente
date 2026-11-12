#!/usr/bin/env python3
"""Fase 3 · D6 — triagem dos 19 suplementares (phase3_d6_19_screen.csv)

Sob D2=B, JIT/defect prediction → em geral exclude_other.

Uso:
  python3 classify_phase3_d6_interactive.py --status
  python3 classify_phase3_d6_interactive.py --coder Rodrigo --pending-only
"""
from __future__ import annotations

import argparse
import csv
import webbrowser
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase3_d6_19_screen.csv"
VALID = {"classify", "exclude_other", "EC5a", "EC5b", "EC5c"}


def load() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(rows: list[dict[str, str]]) -> None:
    fields = list(rows[0].keys())
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def ask(p: str) -> str:
    try:
        return input(p).strip()
    except EOFError:
        return "q"


def status(rows: list[dict[str, str]]) -> None:
    done = [r for r in rows if (r.get("final_decision") or "").strip()]
    print(f"D6: {len(done)}/{len(rows)} concluídos ({len(rows) - len(done)} pendentes)")
    if done:
        print(Counter(r["final_decision"] for r in done))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder", default="Rodrigo")
    ap.add_argument("--pending-only", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    rows = load()
    if args.status:
        status(rows)
        return

    queue = [r for r in rows if not (r.get("final_decision") or "").strip()] if args.pending_only else rows
    print(f"Coder={args.coder} fila={len(queue)}")
    status(rows)
    print("1=classify  4=exclude_other  3=EC5b  2=EC5a  o=DOI  s=skip  q=quit")
    print("Sugestão default sob D2=B: 4 (defect/JIT = produto)")

    for i, r in enumerate(queue, 1):
        print("\n" + "=" * 72)
        print(f"[{i}/{len(queue)}] row={r.get('row')} year={r.get('year')}")
        print(f"Title: {r.get('title')}")
        print(f"DOI: {r.get('doi')}")
        print(f"Title-screen: {r.get('title_decision')} / {r.get('criterion')}")
        print(f"Note: {r.get('notes')}")
        print(f"Reason: {(r.get('reason') or '')[:200]}")
        raw = ask("decision [1/4/3/2/o/s/q] > ").lower()
        if raw == "q":
            break
        if raw in {"", "s"}:
            continue
        if raw == "o":
            doi = (r.get("doi") or "").strip()
            if doi:
                webbrowser.open(f"https://doi.org/{doi}")
            raw = ask("depois da leitura, decision [1/4/3/2] > ").lower()
        mapping = {"1": "classify", "4": "exclude_other", "3": "EC5b", "2": "EC5a"}
        dec = mapping.get(raw, raw)
        if dec not in VALID:
            print("inválido")
            continue
        fams = ""
        level = ""
        if dec == "classify":
            fams = ask("families (TF-PM|TF-ST|TF-FC|TF-MSR) > ")
            level = ask("level (L0/L1/L2/L3) > ")
        notes = ask("notes (Enter=manter sugestão) > ")
        r["final_decision"] = dec
        r["families"] = fams
        r["level"] = level
        if notes:
            r["notes"] = notes
        r["coder"] = args.coder
        r["date"] = date.today().isoformat()
        save(rows)
        print(f"Gravado → {dec}")

    status(rows)
    print("Quando 19/19: avise para aplicar excludes/includes e ir à iteração D1.")


if __name__ == "__main__":
    main()
