#!/usr/bin/env python3
"""Fase 3 · D1 — triagem do residual vs pool 5783 (phase3_D1_residual_vs_pool_screen.csv)

unique_new real após dedup contra results/unique_papers.csv (n=5783).
Sob D2=B: excluir reliability/produto, domínio não-SE, PM/simulação fora de SDLC.

Uso:
  python3 classify_phase3_d1_interactive.py --status
  python3 classify_phase3_d1_interactive.py --coder Rodrigo --pending-only
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import webbrowser
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase3_D1_residual_vs_pool_screen.csv"
MIRROR_PATH = DIR / "phase3_D1_unique_new_screen.csv"
VALID = {"classify", "exclude_other", "EC5a", "EC5b", "EC5c"}

# título → sugestão (heurística; humano confirma)
SE_PROCESS = re.compile(
    r"\b(software development|software engineering|devops|devsecops|sdlc|"
    r"ci/?cd|repository|pull.?request|agile|scrum|kanban|"
    r"self-?adaptive|runtime verification|work-?stealing scheduler|"
    r"observability)\b",
    re.I,
)
OUT_OF_SCOPE = re.compile(
    r"\b(laser|optics?|ice sheet|greenland|wireless|radio|capacity market|"
    r"renewable|distribution feeder|eVTOL|ophthalmology|health system|"
    r"manufactur|production planning|digital twin|object-?centric|"
    r"mass service|information freshness|censoring|muth distribution|"
    r"grammatical|function identifier|microwave|radiometer)\b",
    re.I,
)
PRODUCT_REL = re.compile(
    r"\b(software reliability|reliability model|reliability-?testing|"
    r"semi-?markov reliability|defect|fault introduction|product reliability|"
    r"usage models?)\b",
    re.I,
)


def suggest(title: str, sources: str) -> tuple[str, str]:
    t = title or ""
    if OUT_OF_SCOPE.search(t):
        return "exclude_other", "fora de escopo (domínio ≠ processo SDLC)"
    if PRODUCT_REL.search(t):
        return "exclude_other", "D2=B reliability/produto ou usage model de teste"
    # PM/simulação genérica (V9) sem SE → exclude domínio
    if re.search(r"\b(process mining|simulation|petri|event log)\b", t, re.I) and not SE_PROCESS.search(t):
        return "exclude_other", "PM/simulação sem população SE/SDLC explícita no título"
    if SE_PROCESS.search(t):
        return "classify", "título sugere SE/processo — confirmar abstract/PDF (famílias+nível)"
    return "exclude_other", "sem sinal SE/processo no título; confirmar se dúbio"


def load() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save(rows: list[dict[str, str]]) -> None:
    fields = list(rows[0].keys())
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    # espelho para o nome usado no fluxo
    shutil.copy(CSV_PATH, MIRROR_PATH)


def ask(p: str) -> str:
    try:
        return input(p).strip()
    except EOFError:
        return "q"


def status(rows: list[dict[str, str]]) -> None:
    done = [r for r in rows if (r.get("final_decision") or "").strip()]
    print(f"D1 residual: {len(done)}/{len(rows)} concluídos ({len(rows) - len(done)} pendentes)")
    if done:
        print(Counter(r["final_decision"] for r in done))
    # preview sugestões nos pendentes
    pend = [r for r in rows if not (r.get("final_decision") or "").strip()]
    if pend:
        sug = Counter(suggest(r.get("title") or "", r.get("sources") or "")[0] for r in pend)
        print(f"Sugestões nos pendentes: {dict(sug)}")


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
    print("Enter sozinho na decision = aceitar sugestão")

    for i, r in enumerate(queue, 1):
        sug_dec, sug_note = suggest(r.get("title") or "", r.get("sources") or "")
        print("\n" + "=" * 72)
        print(f"[{i}/{len(queue)}] row={r.get('row')} year={r.get('year')} sources={r.get('sources')}")
        print(f"Title: {r.get('title')}")
        print(f"Authors: {(r.get('authors') or '')[:120]}")
        print(f"Venue: {(r.get('venue') or '')[:100]}")
        print(f"DOI: {r.get('doi')}")
        print(f"Sugestão: {sug_dec} — {sug_note}")
        raw = ask("decision [1/4/3/2/o/s/q / Enter=sugestão] > ").lower()
        if raw == "q":
            break
        if raw == "s":
            continue
        if raw == "o":
            doi = (r.get("doi") or "").strip()
            if doi:
                webbrowser.open(f"https://doi.org/{doi}")
            raw = ask("depois da leitura, decision [1/4/3/2 / Enter=sugestão] > ").lower()
        if raw == "":
            dec = sug_dec
        else:
            mapping = {"1": "classify", "4": "exclude_other", "3": "EC5b", "2": "EC5a"}
            dec = mapping.get(raw, raw)
        if dec not in VALID:
            print("inválido")
            continue
        fams = ""
        level = ""
        if dec == "classify":
            while True:
                fams = ask("families (obrigatório: TF-PM|TF-ST|TF-FC|TF-MSR) > ").strip()
                if fams:
                    break
                print("classify exige ≥1 família. Use 4 se for exclude.")
            while True:
                raw_lvl = ask("level (L0/L1/L2/L3) > ").strip().upper()
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
        r["notes"] = notes if notes else sug_note
        r["coder"] = args.coder
        r["date"] = date.today().isoformat()
        save(rows)
        print(f"Gravado → {dec}")

    status(rows)
    print("Quando 30/30: avise para atualizar ledger e seguir ao bloco ML.")


if __name__ == "__main__":
    main()
