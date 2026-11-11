#!/usr/bin/env python3
"""
Auditoria interativa da amostra L0 (phase1_L0_audit_sample.csv, n=55).

Para cada estudo, o auditor informa as famílias humanas e se batem com o LLM.
No fim, imprime taxa de erro e κ aproximado (match_llm).

Uso:
  python3 classify_L0_audit_interactive.py --coder Rodrigo --pending-only
  python3 classify_L0_audit_interactive.py --status
"""
from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase1_L0_audit_sample.csv"
BACKUP_PATH = DIR / "phase1_L0_audit_sample.bak.csv"
VALID_FAMS = {"TF-PM", "TF-ST", "TF-FC", "TF-MSR"}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    if path.exists() and not BACKUP_PATH.exists():
        shutil.copy2(path, BACKUP_PATH)
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def done(r: dict[str, str]) -> bool:
    return bool((r.get("human_families") or "").strip()) or bool((r.get("match_llm") or "").strip())


def status(rows: list[dict[str, str]]) -> None:
    n = len(rows)
    d = sum(1 for r in rows if done(r))
    print(f"Progresso L0 audit: {d}/{n} concluídos ({n - d} pendentes)")
    matches = Counter((r.get("match_llm") or "").strip().lower() for r in rows if done(r))
    if matches:
        print("match_llm:", dict(matches))
        yes = matches.get("yes", 0) + matches.get("y", 0) + matches.get("1", 0)
        no = matches.get("no", 0) + matches.get("n", 0) + matches.get("0", 0)
        audited = yes + no
        if audited:
            print(f"Taxa de acordo com LLM: {yes}/{audited} = {100 * yes / audited:.1f}%")
            print(f"Taxa de erro (vs LLM): {no}/{audited} = {100 * no / audited:.1f}%")


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "q"


def parse_fams(raw: str) -> list[str]:
    parts = [p.strip().upper() for p in raw.replace(",", "|").replace("+", "|").split("|") if p.strip()]
    out = []
    for p in parts:
        if not p.startswith("TF-"):
            p = "TF-" + p
        if p not in VALID_FAMS:
            raise ValueError(p)
        out.append(p)
    return sorted(set(out), key=lambda x: ["TF-PM", "TF-ST", "TF-FC", "TF-MSR"].index(x))


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoria amostra L0 (n=55)")
    parser.add_argument("--coder", default="Rodrigo")
    parser.add_argument("--pending-only", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    args = parser.parse_args()

    rows = load_rows(args.csv)
    if args.status:
        status(rows)
        return

    queue = [r for r in rows if not done(r)] if args.pending_only else rows
    print(f"Coder={args.coder} fila={len(queue)}")
    status(rows)
    print("Famílias: TF-PM TF-ST TF-FC TF-MSR (separar por |). match: y/n. q=sair s=skip")

    for i, r in enumerate(queue, 1):
        print("\n" + "=" * 72)
        print(f"[{i}/{len(queue)}]  id={r.get('internal_id')}  year={r.get('year')}  stratum={r.get('stratum_family')}")
        print(f"Title: {r.get('title')}")
        print(f"DOI: {r.get('doi')}")
        print(f"LLM families: {r.get('families_llm')}")
        fams_raw = ask("human_families (ex: TF-ST|TF-FC) [s/q]: ")
        if fams_raw.lower() == "q":
            break
        if fams_raw.lower() in {"", "s"}:
            print("skip")
            continue
        try:
            fams = parse_fams(fams_raw)
        except ValueError as e:
            print(f"família inválida: {e}")
            continue
        match = ask("match_llm? [y/n]: ").lower()
        if match not in {"y", "n", "yes", "no"}:
            print("use y ou n")
            continue
        notes = ask("notes (opcional): ")
        r["human_families"] = "|".join(fams)
        r["human_level"] = "L0" if len([f for f in fams if f != "TF-MSR"]) <= 1 else "L1+"
        r["match_llm"] = "yes" if match in {"y", "yes"} else "no"
        r["notes"] = notes
        r["coder"] = args.coder
        r["date"] = date.today().isoformat()
        save_rows(args.csv, rows)
        print(f"Gravado: {r.get('internal_id')} → {r['human_families']} match={r['match_llm']}")

    status(rows)


if __name__ == "__main__":
    main()
