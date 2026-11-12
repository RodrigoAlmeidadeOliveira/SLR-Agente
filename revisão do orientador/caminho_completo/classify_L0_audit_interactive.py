#!/usr/bin/env python3
"""
Auditoria interativa da amostra L0 (phase1_L0_audit_sample.csv, n=55).

1º coder (já feito — Rodrigo):
  python3 classify_L0_audit_interactive.py --coder Rodrigo --pending-only

2º coder com sugestões (LLM; cego ao 1º coder):
  python3 classify_L0_audit_interactive.py --coder Juliano --pass B --pending-only
  python3 classify_L0_audit_interactive.py --coder Juliano --pass B --pending-only --sample 11
  python3 classify_L0_audit_interactive.py --pass B --status

Enter aceita a sugestão (famílias LLM). Digite famílias para corrigir.
"""
from __future__ import annotations

import argparse
import csv
import random
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase1_L0_audit_sample.csv"
BACKUP_PATH = DIR / "phase1_L0_audit_sample.bak.csv"
VALID_FAMS = {"TF-PM", "TF-ST", "TF-FC", "TF-MSR"}
ORDER = ["TF-PM", "TF-ST", "TF-FC", "TF-MSR"]

B_COLS = [
    "human_families_b",
    "human_level_b",
    "match_llm_b",
    "notes_b",
    "coder_b",
    "date_b",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return rows
    # ensure B columns exist
    for r in rows:
        for c in B_COLS:
            r.setdefault(c, "")
    return rows


def save_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    if path.exists() and not BACKUP_PATH.exists():
        shutil.copy2(path, BACKUP_PATH)
    fields = list(rows[0].keys())
    for c in B_COLS:
        if c not in fields:
            fields.append(c)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def parse_fams(raw: str) -> list[str]:
    parts = [p.strip().upper() for p in raw.replace(",", "|").replace("+", "|").split("|") if p.strip()]
    out = []
    for p in parts:
        if not p.startswith("TF-"):
            p = "TF-" + p
        if p not in VALID_FAMS:
            raise ValueError(p)
        out.append(p)
    return sorted(set(out), key=lambda x: ORDER.index(x))


def fam_set(raw: str) -> set[str]:
    try:
        return set(parse_fams(raw))
    except ValueError:
        return set()


def level_of(fams: list[str]) -> str:
    tech = [f for f in fams if f != "TF-MSR"]
    return "L0" if len(tech) <= 1 else "L1+"


def done_a(r: dict[str, str]) -> bool:
    return bool((r.get("human_families") or "").strip()) or bool((r.get("match_llm") or "").strip())


def done_b(r: dict[str, str]) -> bool:
    return bool((r.get("human_families_b") or "").strip()) or bool((r.get("match_llm_b") or "").strip())


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "q"


def kappa_binary(pairs: list[tuple[bool, bool]]) -> float | None:
    """Cohen κ for two binary raters (match with LLM yes/no, or family-set equality)."""
    n = len(pairs)
    if n == 0:
        return None
    a_yes = sum(1 for a, _ in pairs if a)
    b_yes = sum(1 for _, b in pairs if b)
    agree = sum(1 for a, b in pairs if a == b)
    p_o = agree / n
    p_e = (a_yes / n) * (b_yes / n) + ((n - a_yes) / n) * ((n - b_yes) / n)
    if p_e >= 1.0:
        return 1.0 if p_o >= 1.0 else 0.0
    return (p_o - p_e) / (1.0 - p_e)


def status(rows: list[dict[str, str]]) -> None:
    n = len(rows)
    da = sum(1 for r in rows if done_a(r))
    db = sum(1 for r in rows if done_b(r))
    print(f"Pass A (1º coder): {da}/{n}")
    print(f"Pass B (2º coder): {db}/{n}  (pendentes B: {n - db})")
    matches = Counter((r.get("match_llm") or "").strip().lower() for r in rows if done_a(r))
    if matches:
        yes = matches.get("yes", 0) + matches.get("y", 0)
        no = matches.get("no", 0) + matches.get("n", 0)
        audited = yes + no
        if audited:
            print(f"A vs LLM: acordo {yes}/{audited} = {100 * yes / audited:.1f}%")
    both = [r for r in rows if done_a(r) and done_b(r)]
    if both:
        fam_agree = sum(
            1
            for r in both
            if fam_set(r.get("human_families") or "") == fam_set(r.get("human_families_b") or "")
        )
        print(f"A vs B (famílias): {fam_agree}/{len(both)} = {100 * fam_agree / len(both):.1f}%")
        labels_a = ["|".join(sorted(fam_set(r["human_families"]))) for r in both]
        labels_b = ["|".join(sorted(fam_set(r["human_families_b"]))) for r in both]
        cats = sorted(set(labels_a) | set(labels_b))
        n_both = len(both)
        agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
        p_o = agree / n_both
        p_e = sum((labels_a.count(c) / n_both) * (labels_b.count(c) / n_both) for c in cats)
        k_ab = (p_o - p_e) / (1 - p_e) if p_e < 1 else (1.0 if p_o == 1 else 0.0)
        print(f"Cohen κ A↔B (rótulo de famílias): {k_ab:.3f}")
        m_pairs = [
            (
                (r.get("match_llm") or "").lower() in {"yes", "y"},
                (r.get("match_llm_b") or "").lower() in {"yes", "y"},
            )
            for r in both
        ]
        k_llm = kappa_binary(m_pairs)
        if k_llm is not None:
            print(f"Cohen κ A↔B (match_llm yes/no): {k_llm:.3f}")


def run_pass_a(path: Path, rows: list[dict[str, str]], queue: list[dict[str, str]], coder: str) -> None:
    print("Famílias: TF-PM TF-ST TF-FC TF-MSR (separar por |). match: y/n. q=sair s=skip")
    print("Sugestão = families_llm. Enter aceita sugestão.\n")
    for i, r in enumerate(queue, 1):
        sug = (r.get("families_llm") or "").strip()
        print("\n" + "=" * 72)
        print(f"[A {i}/{len(queue)}]  id={r.get('internal_id')}  year={r.get('year')}  stratum={r.get('stratum_family')}")
        print(f"Title: {r.get('title')}")
        print(f"DOI: {r.get('doi')}")
        print(f"Sugestão (LLM): {sug}")
        fams_raw = ask(f"human_families [{sug}] [Enter=aceitar / s / q]: ")
        if fams_raw.lower() == "q":
            break
        if fams_raw.lower() == "s":
            print("skip")
            continue
        if fams_raw == "":
            fams_raw = sug
        try:
            fams = parse_fams(fams_raw)
        except ValueError as e:
            print(f"família inválida: {e}")
            continue
        llm = fam_set(sug)
        auto_match = set(fams) == llm
        match = ask(f"match_llm? [{'y' if auto_match else 'n'} sugerido] [y/n]: ").lower()
        if match == "":
            match = "y" if auto_match else "n"
        if match not in {"y", "n", "yes", "no"}:
            print("use y ou n")
            continue
        notes = ask("notes (opcional): ")
        r["human_families"] = "|".join(fams)
        r["human_level"] = level_of(fams)
        r["match_llm"] = "yes" if match in {"y", "yes"} else "no"
        r["notes"] = notes
        r["coder"] = coder
        r["date"] = date.today().isoformat()
        save_rows(path, rows)
        print(f"Gravado A: {r.get('internal_id')} → {r['human_families']} match={r['match_llm']}")


def run_pass_b(path: Path, rows: list[dict[str, str]], queue: list[dict[str, str]], coder: str) -> None:
    print("Pass B — cego ao 1º coder. Sugestão = families_llm.")
    print("Enter aceita sugestão | edite com PM|ST|FC|MSR | s=skip | q=sair\n")
    for i, r in enumerate(queue, 1):
        sug = (r.get("families_llm") or "").strip()
        print("\n" + "=" * 72)
        print(f"[B {i}/{len(queue)}]  id={r.get('internal_id')}  year={r.get('year')}  stratum={r.get('stratum_family')}")
        print(f"Title: {r.get('title')}")
        print(f"DOI: {r.get('doi')}")
        print(f"Sugestão (LLM): {sug}")
        fams_raw = ask(f"human_families_b [{sug}] [Enter=aceitar / s / q]: ")
        if fams_raw.lower() == "q":
            break
        if fams_raw.lower() == "s":
            print("skip")
            continue
        if fams_raw == "":
            fams_raw = sug
        try:
            fams = parse_fams(fams_raw)
        except ValueError as e:
            print(f"família inválida: {e}")
            continue
        llm = fam_set(sug)
        auto_match = set(fams) == llm
        match = ask(f"match_llm_b? [{'y' if auto_match else 'n'} sugerido] [y/n Enter]: ").lower()
        if match == "":
            match = "y" if auto_match else "n"
        if match not in {"y", "n", "yes", "no"}:
            print("use y ou n")
            continue
        notes = ask("notes_b (opcional): ")
        r["human_families_b"] = "|".join(fams)
        r["human_level_b"] = level_of(fams)
        r["match_llm_b"] = "yes" if match in {"y", "yes"} else "no"
        r["notes_b"] = notes
        r["coder_b"] = coder
        r["date_b"] = date.today().isoformat()
        save_rows(path, rows)
        print(f"Gravado B: {r.get('internal_id')} → {r['human_families_b']} match={r['match_llm_b']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoria amostra L0 (n=55) — pass A/B")
    parser.add_argument("--coder", default="Rodrigo")
    parser.add_argument("--pass", dest="pass_id", choices=["A", "B"], default="A")
    parser.add_argument("--pending-only", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--sample", type=int, default=0, help="subamostra aleatória (ex.: 11 = 20%)")
    parser.add_argument("--seed", type=int, default=20261112)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    args = parser.parse_args()

    path = args.csv
    rows = load_rows(path)
    if args.status:
        status(rows)
        return

    if args.pass_id == "B":
        queue = [r for r in rows if not done_b(r)] if args.pending_only else list(rows)
    else:
        queue = [r for r in rows if not done_a(r)] if args.pending_only else list(rows)

    if args.sample and args.sample < len(queue):
        rng = random.Random(args.seed)
        queue = rng.sample(queue, args.sample)
        queue.sort(key=lambda r: r.get("internal_id") or "")

    print(f"Coder={args.coder}  pass={args.pass_id}  fila={len(queue)}")
    status(rows)

    if args.pass_id == "B":
        run_pass_b(path, rows, queue, args.coder)
    else:
        run_pass_a(path, rows, queue, args.coder)

    status(rows)


if __name__ == "__main__":
    main()
