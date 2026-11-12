#!/usr/bin/env python3
"""Fase 3 · Bloco ML — triagem prioritária com sugestão por faixa.

Arquivo default: phase3_ML_priority_screen.csv (1015 maybes ranqueados A→B→D→C)
  A = lead/cycle/remaining/merge/resolve/bug-fix
  B = pull request
  C = effort estimation
  D = outros

Uso:
  python3 classify_phase3_ml_interactive.py --status
  python3 classify_phase3_ml_interactive.py --coder Rodrigo --pending-only
  python3 classify_phase3_ml_interactive.py --coder Rodrigo --pending-only --tier A
  python3 classify_phase3_ml_interactive.py --coder Rodrigo --pending-only --tier AB
  python3 classify_phase3_ml_interactive.py --bulk-accept-exclude
"""
from __future__ import annotations

import argparse
import csv
import sys
import webbrowser
from collections import Counter
from datetime import date
from pathlib import Path

csv.field_size_limit(sys.maxsize)

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase3_ML_priority_screen.csv"
RESIDUAL_PATH = DIR / "phase3_ML_residual_vs_pool_screen.csv"
VALID = {"classify", "exclude_other", "EC5a", "EC5b", "EC5c"}
TIER_ALIASES = {
    "A": {"A_process_time"},
    "B": {"B_PR"},
    "C": {"C_effort"},
    "D": {"D_other"},
    "AB": {"A_process_time", "B_PR"},
    "ABCD": {"A_process_time", "B_PR", "C_effort", "D_other"},
}


def suggest_families(title: str, tier: str) -> tuple[str, str]:
    """Retorna (families, level) sugeridos a partir do título."""
    import re

    t = title or ""
    fams: list[str] = []
    if re.search(r"\b(process mining|event log|petri|conformance)\b", t, re.I):
        fams.append("TF-PM")
    if re.search(r"\b(markov|monte carlo|stochastic|petri)\b", t, re.I):
        fams.append("TF-ST")
    if re.search(
        r"\b(predict|prediction|forecast|estimation|remaining time|lead time|"
        r"cycle time|bug-?fix time|issue resolution|time to merge|effort)\b",
        t,
        re.I,
    ):
        fams.append("TF-FC")
    if re.search(
        r"\b(github|jira|repository|pull request|commit|issue|open.?source|"
        r"mining software|msr|bug report|software repositor)\b",
        t,
        re.I,
    ):
        fams.append("TF-MSR")
    # defaults por faixa se ainda vazio/ incompleto
    if tier == "A_process_time" and "TF-FC" not in fams:
        fams.append("TF-FC")
    if tier == "A_process_time" and "TF-MSR" not in fams and re.search(
        r"\b(bug|issue|github|repository)\b", t, re.I
    ):
        fams.append("TF-MSR")
    if tier == "B_PR":
        if "TF-FC" not in fams:
            fams.append("TF-FC")
        if "TF-MSR" not in fams:
            fams.append("TF-MSR")
    if tier == "C_effort":
        if "TF-FC" not in fams:
            fams.append("TF-FC")
        if re.search(r"\b(github|jira|repository|issue|agile|scrum|sprint)\b", t, re.I) and "TF-MSR" not in fams:
            fams.append("TF-MSR")
    # unique preserve order
    seen = set()
    fams = [f for f in fams if not (f in seen or seen.add(f))]
    if not fams:
        fams = ["TF-FC"]
    tech = [f for f in fams if f in {"TF-PM", "TF-ST", "TF-FC"}]
    n = len(tech)
    level = {0: "L0", 1: "L0", 2: "L1", 3: "L2"}.get(n, "L0")
    return "|".join(fams), level


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


def status(rows: list[dict[str, str]]) -> None:
    done = [r for r in rows if (r.get("final_decision") or "").strip()]
    print(f"ML priority: {len(done)}/{len(rows)} concluídos ({len(rows) - len(done)} pendentes)")
    if done:
        print("decisões:", dict(Counter(r["final_decision"] for r in done)))
    pend = [r for r in rows if not (r.get("final_decision") or "").strip()]
    if pend:
        print("pendentes por tier:", dict(Counter(r.get("tier") for r in pend)))
        print("sugestões pendentes:", dict(Counter(r.get("sug_decision") for r in pend)))


def mirror_many_to_residual(changed: list[dict[str, str]]) -> None:
    """Espelha decisões no residual numa única leitura/gravação."""
    if not RESIDUAL_PATH.exists() or not changed:
        return
    all_rows = load(RESIDUAL_PATH)
    by_doi = {}
    by_title = {}
    for a in all_rows:
        d = (a.get("doi") or "").strip().lower()
        if d:
            by_doi[d] = a
        by_title[(a.get("title") or "").strip().lower()] = a
    for r in changed:
        doi = (r.get("doi") or "").strip().lower()
        title = (r.get("title") or "").strip().lower()
        a = by_doi.get(doi) if doi else None
        if a is None:
            a = by_title.get(title)
        if a is None:
            continue
        for k in ("final_decision", "families", "level", "notes", "coder", "date"):
            a[k] = r.get(k, "")
    save(RESIDUAL_PATH, all_rows)


def mirror_to_residual(r: dict[str, str]) -> None:
    mirror_many_to_residual([r])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder", default="Rodrigo")
    ap.add_argument("--pending-only", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--tier", default="ABCD", help="A|B|C|D|AB|ABCD")
    ap.add_argument(
        "--bulk-accept-exclude",
        action="store_true",
        help="Aceita sug=exclude_other em todos os pendentes do CSV priority",
    )
    ap.add_argument(
        "--only-sug",
        choices=["classify", "exclude_other"],
        help="Filtra fila pela sugestão",
    )
    args = ap.parse_args()
    rows = load(CSV_PATH)

    if args.status:
        status(rows)
        return

    if args.bulk_accept_exclude:
        changed: list[dict[str, str]] = []
        today = date.today().isoformat()
        for r in rows:
            if (r.get("final_decision") or "").strip():
                continue
            if (r.get("sug_decision") or "") != "exclude_other":
                continue
            r["final_decision"] = "exclude_other"
            r["notes"] = r.get("sug_note") or "bulk-accept"
            r["coder"] = args.coder
            r["date"] = today
            changed.append(r)
        save(CSV_PATH, rows)
        mirror_many_to_residual(changed)
        print(f"Bulk exclude_other: {len(changed)}")
        status(rows)
        return

    tiers = TIER_ALIASES.get(args.tier.upper())
    if not tiers:
        print(f"tier inválido: {args.tier}")
        return

    queue = rows
    if args.pending_only:
        queue = [r for r in queue if not (r.get("final_decision") or "").strip()]
    queue = [r for r in queue if (r.get("tier") or "") in tiers]
    if args.only_sug:
        queue = [r for r in queue if (r.get("sug_decision") or "") == args.only_sug]

    print(f"Coder={args.coder} tier={args.tier.upper()} fila={len(queue)}")
    status(rows)
    print("1=classify  4=exclude_other  3=EC5b  2=EC5a  o=DOI  s=skip  q=quit")
    print("Enter = aceitar sugestão")

    for i, r in enumerate(queue, 1):
        sug = (r.get("sug_decision") or "exclude_other").strip()
        print("\n" + "=" * 72)
        print(f"[{i}/{len(queue)}] row={r.get('row')} tier={r.get('tier')} year={r.get('year')} src={r.get('sources')}")
        print(f"Title: {r.get('title')}")
        print(f"Authors: {(r.get('authors') or '')[:120]}")
        print(f"Venue: {(r.get('venue') or '')[:100]}")
        print(f"DOI: {r.get('doi')}")
        print(f"Sugestão: {sug} — {r.get('sug_note')}")
        raw = ask("decision [1/4/3/2/o/s/q / Enter=sugestão] > ").lower()
        if raw == "q":
            break
        if raw == "s":
            continue
        if raw == "o":
            doi = (r.get("doi") or "").strip()
            if doi:
                webbrowser.open(f"https://doi.org/{doi}")
            raw = ask("depois da leitura [1/4/3/2 / Enter=sugestão] > ").lower()
        if raw == "":
            dec = sug
        else:
            mapping = {"1": "classify", "4": "exclude_other", "3": "EC5b", "2": "EC5a"}
            dec = mapping.get(raw, raw)
        if dec not in VALID:
            print("inválido")
            continue
        fams = ""
        level = ""
        if dec == "classify":
            sug_fams, sug_lvl = suggest_families(r.get("title") or "", r.get("tier") or "")
            print(f"Sugestão famílias: {sug_fams}  nível: {sug_lvl}")
            while True:
                raw_f = ask(f"families (Enter={sug_fams}) > ").strip()
                fams = raw_f if raw_f else sug_fams
                if fams:
                    break
                print("classify exige ≥1 família")
            while True:
                raw_lvl = ask(f"level (Enter={sug_lvl}) > ").strip().upper()
                if raw_lvl == "":
                    level = sug_lvl
                    break
                if raw_lvl in {"0", "1", "2", "3"}:
                    raw_lvl = f"L{raw_lvl}"
                if raw_lvl in {"L0", "L1", "L2", "L3"}:
                    level = raw_lvl
                    break
                print("nível inválido")
        notes = ask("notes (Enter=manter sugestão) > ")
        r["final_decision"] = dec
        r["families"] = fams
        r["level"] = level
        r["notes"] = notes if notes else (r.get("sug_note") or "")
        r["coder"] = args.coder
        r["date"] = date.today().isoformat()
        save(CSV_PATH, rows)
        mirror_to_residual(r)
        print(f"Gravado → {dec}")

    status(rows)
    print("Dica: comece com --tier AB; depois --only-sug classify; no fim --bulk-accept-exclude.")


if __name__ == "__main__":
    main()
