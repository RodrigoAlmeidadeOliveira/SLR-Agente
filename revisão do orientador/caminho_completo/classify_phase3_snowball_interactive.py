#!/usr/bin/env python3
"""Fase 3 · Snowballing iter1 — triagem do residual (gate-pass first).

Arquivo: phase3_snowball_iter1_screen.csv
  maybe (keyword gate pass) → triar IC/EC
  exclude_other (gate fail) → --bulk-accept-exclude

Uso:
  python3 classify_phase3_snowball_interactive.py --status
  python3 classify_phase3_snowball_interactive.py --bulk-accept-exclude
  python3 classify_phase3_snowball_interactive.py --coder Rodrigo --pending-only --only-sug maybe
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import webbrowser
from collections import Counter
from datetime import date
from pathlib import Path

csv.field_size_limit(sys.maxsize)

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase3_snowball_iter1_screen.csv"
VALID = {"classify", "exclude_other", "EC5a", "EC5b", "EC5c"}


def suggest_families(title: str) -> tuple[str, str]:
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
        r"mining software|msr|bug report|software repositor|agile|scrum)\b",
        t,
        re.I,
    ):
        fams.append("TF-MSR")
    seen: set[str] = set()
    fams = [f for f in fams if not (f in seen or seen.add(f))]
    if not fams:
        fams = ["TF-FC"]
    tech = [f for f in fams if f in {"TF-PM", "TF-ST", "TF-FC"}]
    level = {0: "L0", 1: "L0", 2: "L1", 3: "L2"}.get(len(tech), "L0")
    return "|".join(fams), level


def suggest_decision(title: str, sug: str) -> tuple[str, str]:
    """Refine maybe → classify|exclude_other with short note."""
    t = title or ""
    if sug == "exclude_other":
        return "exclude_other", "gate fail"
    # soft signals for IC
    if re.search(
        r"\b(process mining|remaining time|lead time|cycle time|bug-?fix|"
        r"pull request|effort estimation|story point|throughput|"
        r"monte carlo|markov|stochastic|forecast)\b",
        t,
        re.I,
    ) and re.search(
        r"\b(software|agile|scrum|kanban|github|jira|devops|repository|"
        r"open.?source|sdlc)\b",
        t,
        re.I,
    ):
        return "classify", "effort/flow + SE — confirmar famílias"
    return "maybe", "gate pass — revisar título"


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
    print(f"Snowball iter1: {len(done)}/{len(rows)} concluídos ({len(rows) - len(done)} pendentes)")
    if done:
        print("decisões:", dict(Counter(r["final_decision"] for r in done)))
    pend = [r for r in rows if not (r.get("final_decision") or "").strip()]
    if pend:
        print("sugestões pendentes:", dict(Counter(r.get("sug_decision") for r in pend)))
        print("gate pendentes:", dict(Counter(r.get("keyword_gate") for r in pend)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coder", default="Rodrigo")
    ap.add_argument("--pending-only", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument(
        "--bulk-accept-exclude",
        action="store_true",
        help="Aceita sug=exclude_other em todos os pendentes",
    )
    ap.add_argument(
        "--only-sug",
        choices=["maybe", "exclude_other", "classify"],
        help="Filtra fila pela sugestão",
    )
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    rows = load(CSV_PATH)

    if args.status:
        status(rows)
        return

    if args.bulk_accept_exclude:
        today = date.today().isoformat()
        n = 0
        for r in rows:
            if (r.get("final_decision") or "").strip():
                continue
            if (r.get("sug_decision") or "") != "exclude_other":
                continue
            r["final_decision"] = "exclude_other"
            r["notes"] = r.get("sug_note") or "bulk-accept gate fail"
            r["coder"] = args.coder
            r["date"] = today
            n += 1
        save(CSV_PATH, rows)
        print(f"Bulk exclude_other: {n}")
        status(rows)
        return

    today = date.today().isoformat()
    queue = []
    for r in rows:
        if args.pending_only and (r.get("final_decision") or "").strip():
            continue
        if args.only_sug and (r.get("sug_decision") or "") != args.only_sug:
            continue
        queue.append(r)
    # gate-pass first
    queue.sort(key=lambda x: (0 if x.get("keyword_gate") == "pass" else 1, x.get("title") or ""))
    if args.limit:
        queue = queue[: args.limit]

    print(f"Fila: {len(queue)}  (Enter=sugestão | 1=classify 4=exclude o=abrir q=sair)")
    for i, r in enumerate(queue, 1):
        title = r.get("title") or ""
        sug0 = r.get("sug_decision") or "maybe"
        sug, note = suggest_decision(title, sug0)
        fams, level = suggest_families(title)
        print("\n" + "=" * 72)
        print(f"[{i}/{len(queue)}]  year={r.get('year')}  gate={r.get('keyword_gate')}  n_seeds={r.get('n_seeds')}")
        print(f"Title: {title}")
        print(f"DOI: {r.get('doi') or '—'}")
        print(f"dirs: {r.get('directions')}  seeds: {r.get('seed_ids')}")
        print(f"Sugestão: {sug} — {note}")
        print(f"Famílias sug: {fams}  nível: {level}")
        ans = ask("decision [1/4/3/2/o/s/q / Enter=sugestão] > ")
        if ans == "q":
            break
        if ans == "o":
            doi = (r.get("doi") or "").strip()
            if doi:
                webbrowser.open(f"https://doi.org/{doi}")
            else:
                webbrowser.open(f"https://scholar.google.com/scholar?q={title[:120]}")
            ans = ask("decision após abrir > ")
        if ans == "s":
            continue
        if ans in ("", "enter") or ans.lower() == "enter":
            decision = sug if sug in VALID else "exclude_other"
            if sug == "maybe":
                # Enter on maybe → force human choice
                ans2 = ask("maybe: 1=classify 4=exclude > ")
                decision = {"1": "classify", "4": "exclude_other"}.get(ans2, "exclude_other")
        else:
            decision = {
                "1": "classify",
                "4": "exclude_other",
                "3": "EC5a",
                "2": "EC5b",
                "e": "exclude_other",
            }.get(ans, ans if ans in VALID else "")
            if not decision:
                print("inválido — skip")
                continue
        r["final_decision"] = decision
        if decision == "classify":
            f_in = ask(f"families (Enter={fams}) > ") or fams
            l_in = ask(f"level (Enter={level}) > ") or level
            r["families"] = f_in
            r["level"] = l_in
        else:
            r["families"] = ""
            r["level"] = ""
        r["notes"] = note if decision == sug or sug == "maybe" else (r.get("sug_note") or "")
        r["coder"] = args.coder
        r["date"] = today
        save(CSV_PATH, rows)

    status(rows)


if __name__ == "__main__":
    main()
