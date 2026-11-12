#!/usr/bin/env python3
"""Extração humana RQ3 + SPMF (Fase 4) — phase4_rq3_*.csv

Uso:
  python3 classify_phase4_rq3_interactive.py --sheet priority --pending-only
  python3 classify_phase4_rq3_interactive.py --sheet priority --pending-only --compact
  python3 classify_phase4_rq3_interactive.py --sheet full --mode venue --pending-only
  python3 classify_phase4_rq3_interactive.py --sheet priority --status

No modo normal, Enter em branco NÃO grava a linha.
No modo --compact, uma linha com 9 campos separados por ';' (use - para manter sugestão).
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
SHEETS = {
    "full": DIR / "phase4_rq3_extraction_template.csv",
    "priority": DIR / "phase4_rq3_priority_sheet.csv",
}

CORE_FIELDS = [
    "sdlc_phase",
    "event_log_source",
    "log_construction",
    "pm_algorithm",
    "stochastic_method",
    "ml_technique",
    "forecast_target",
    "validation_type",
    "research_type",
]
VENUE_FIELDS = ["venue", "pub_type"]
SPMF_FIELDS = [
    "spmf_analytical_depth",
    "spmf_sdlc_coverage",
    "spmf_technique_integration",
]

HINTS = {
    "sdlc_phase": "requirements | development | quality | delivery | operations (multi com |)",
    "event_log_source": "Jira | GitHub | GitLab | Jenkins | IDE | other | NA",
    "log_construction": "manual | semi | automatic | NA",
    "pm_algorithm": "Alpha | Heuristics | Inductive | Fuzzy | other | NA",
    "stochastic_method": "DTMC | CTMC | SPN | Monte Carlo | System Dynamics | other | NA",
    "ml_technique": "texto curto | NA",
    "forecast_target": "lead_time | cycle_time | remaining_time | throughput | issue_resolution | outcome | other | NA",
    "validation_type": "texto curto | NA",
    "research_type": "evaluation | validation | solution | philosophical | opinion | experience",
    "venue": "nome do veículo",
    "pub_type": "journal | conference | workshop | other",
    "spmf_analytical_depth": "taxonomia SPMF",
    "spmf_sdlc_coverage": "taxonomia SPMF",
    "spmf_technique_integration": "taxonomia SPMF",
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


def ask(p: str) -> str:
    try:
        return input(p).strip()
    except EOFError:
        return "q"


def mode_fields(mode: str) -> list[str]:
    if mode == "venue":
        return VENUE_FIELDS
    if mode == "spmf":
        return SPMF_FIELDS
    if mode == "core":
        return CORE_FIELDS
    return CORE_FIELDS + VENUE_FIELDS + SPMF_FIELDS


def fams(row: dict[str, str]) -> set[str]:
    return {x.strip() for x in (row.get("families") or "").split("|") if x.strip()}


def suggest(row: dict[str, str], field: str) -> str:
    """Sugestão mecânica por família/título — revisão humana obrigatória."""
    cur = (row.get(field) or "").strip()
    if cur:
        return cur
    f = fams(row)
    title = (row.get("title") or "").lower()
    if field == "pm_algorithm":
        return "NA" if "TF-PM" not in f else "other"
    if field == "stochastic_method":
        if "TF-ST" not in f:
            return "NA"
        if "petri" in title:
            return "SPN"
        if "system dynamics" in title or "project dynamics" in title:
            return "System Dynamics"
        if "monte carlo" in title:
            return "Monte Carlo"
        if "markov" in title or "dtmc" in title:
            return "DTMC"
        if "discrete event" in title or "discrete simulation" in title:
            return "Monte Carlo"
        return "other"
    if field == "ml_technique":
        return "NA" if "TF-FC" not in f else "NA"
    if field == "forecast_target":
        if "TF-FC" not in f:
            return "NA"
        if "schedul" in title:
            return "other"
        if "reliab" in title or "fault" in title or "defect" in title:
            return "outcome"
        if "effort" in title:
            return "other"
        return "other"
    if field in ("event_log_source", "log_construction"):
        if "TF-MSR" in f:
            return "other" if field == "event_log_source" else "semi"
        if "event" in title or "log" in title or "discover" in title:
            return "other" if field == "event_log_source" else "semi"
        return "NA"
    if field == "sdlc_phase":
        bits = []
        if "requirement" in title:
            bits.append("requirements")
        if any(k in title for k in ("test", "quality", "reliab", "fault", "defect", "validation")):
            bits.append("quality")
        if any(k in title for k in ("schedul", "project", "develop", "process simulation", "process discovery")):
            bits.append("development")
        if "deliver" in title or "devops" in title or "ci/cd" in title:
            bits.append("delivery")
        return "|".join(bits) if bits else "development"
    if field == "validation_type":
        if "case study" in title:
            return "case study"
        if "simulation" in title:
            return "simulation"
        return "NA"
    if field == "research_type":
        if any(k in title for k in ("survey", "why?", "what?", "how?", "review", "roadmap")):
            return "philosophical"
        if "case study" in title or "industrial" in title:
            return "evaluation"
        if any(k in title for k in ("model", "simulator", "approach", "method", "framework")):
            return "solution"
        return "solution"
    if field == "venue":
        return (row.get("venue") or "").strip()
    if field == "pub_type":
        cur_v = (row.get("venue") or "").strip()
        if not cur_v:
            return ""
        vl = cur_v.lower()
        if "workshop" in vl:
            return "workshop"
        if any(
            k in vl
            for k in (
                "journal",
                "transactions",
                "empir",
                "information and software",
                "software: practice",
                "acm comput",
            )
        ):
            return "journal"
        if any(
            k in vl
            for k in (
                "proceedings",
                "conference",
                "symposium",
                "icse",
                "icsme",
                "lecture notes",
            )
        ):
            return "conference"
        return "journal"  # named venue without proceedings → likely journal
    return ""


def is_done(row: dict[str, str], fields: list[str]) -> bool:
    return all((row.get(f) or "").strip() for f in fields)


def status(rows: list[dict[str, str]], fields: list[str]) -> None:
    done = sum(1 for r in rows if is_done(r, fields))
    print(f"Preenchidos: {done}/{len(rows)}")
    print("por nível:", dict(Counter(r.get("level_technique") for r in rows)))
    pending_l2 = [r for r in rows if r.get("level_technique") == "L2" and not is_done(r, fields)]
    if pending_l2:
        print(f"L2 ainda abertos: {len(pending_l2)}")


def sync_full(priority_rows: list[dict[str, str]]) -> None:
    """Espelha alterações do priority no full sheet."""
    full_path = SHEETS["full"]
    full = load(full_path)
    by = {r["internal_id"]: r for r in priority_rows}
    fields = list(full[0].keys())
    n = 0
    for r in full:
        src = by.get(r["internal_id"])
        if not src:
            continue
        for f in fields:
            if f in src and src[f] != r.get(f):
                r[f] = src[f]
                n += 1
    save(full_path, full)
    if n:
        print(f"  (sync full: {n} células)")


def apply_stamp(row: dict[str, str], extractor: str) -> None:
    row["extractor"] = extractor
    stamp = f"extracted:{date.today().isoformat()}"
    notes = (row.get("notes") or "").strip()
    notes = re.sub(r";?\s*extracted:\d{4}-\d{2}-\d{2}", "", notes).strip(" ;")
    row["notes"] = f"{notes}; {stamp}".strip("; ") if notes else stamp


def edit_field_by_field(row: dict[str, str], fields: list[str], use_suggest: bool) -> tuple[bool, bool]:
    """Returns (changed, abort)."""
    changed = False
    for f in fields:
        sug = suggest(row, f) if use_suggest else (row.get(f) or "").strip()
        hint = HINTS.get(f, "")
        while True:
            raw = ask(f"  {f} [{sug or 'vazio'}] ({hint}): ")
            if raw == "q":
                return changed, True
            if raw == "s":
                break
            if raw == "?":
                print(f"    → {hint}")
                continue
            if raw == "":
                # Enter = aceitar sugestão se houver; senão manter vazio (não grava linha depois)
                if sug and sug != (row.get(f) or "").strip():
                    row[f] = sug
                    changed = True
                break
            row[f] = raw
            changed = True
            break
    return changed, False


def edit_compact(row: dict[str, str], fields: list[str]) -> tuple[bool, bool]:
    """Uma linha: v1;v2;...  |  - = manter sugestão  |  Enter = aceitar todas as sugestões."""
    sug = [suggest(row, f) for f in fields]
    print("  sugestão:")
    print("   " + " | ".join(f"{f}={s or '∅'}" for f, s in zip(fields, sug)))
    print(f"  cole {len(fields)} valores com ';'  (ou Enter=aceitar sugestões, s=skip, q=sair)")
    raw = ask("  > ")
    if raw == "q":
        return False, True
    if raw == "s":
        return False, False
    if raw == "":
        for f, s in zip(fields, sug):
            if s:
                row[f] = s
        return True, False
    parts = [p.strip() for p in raw.split(";")]
    if len(parts) != len(fields):
        print(f"  ! esperado {len(fields)} campos, veio {len(parts)}. Não salvei.")
        return False, False
    for f, p, s in zip(fields, parts, sug):
        if p in {"", "-"}:
            row[f] = s
        else:
            row[f] = p
    return True, False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", choices=sorted(SHEETS), default="priority")
    ap.add_argument("--mode", choices=["all", "core", "venue", "spmf"], default="core")
    ap.add_argument("--extractor", default="Rodrigo")
    ap.add_argument("--pending-only", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--id", help="começar num internal_id específico")
    ap.add_argument("--compact", action="store_true", help="entrada em uma linha com ';'")
    ap.add_argument("--no-suggest", action="store_true", help="não pré-preencher por família/título")
    args = ap.parse_args()

    path = SHEETS[args.sheet]
    rows = load(path)
    fields = mode_fields(args.mode)
    use_suggest = not args.no_suggest

    if args.status:
        status(rows, fields)
        return

    work = rows
    if args.pending_only:
        work = [r for r in rows if not is_done(r, fields)]
    if args.id:
        idx = next((i for i, r in enumerate(work) if r["internal_id"] == args.id), None)
        if idx is None:
            raise SystemExit(f"id não encontrado na fila: {args.id}")
        work = work[idx:] + work[:idx]

    print(f"Arquivo: {path.name}  |  modo={args.mode}  |  fila={len(work)}  |  campos={len(fields)}")
    if args.compact:
        print("Compact: Enter=aceitar sugestões | s=skip | q=sair | vals com ';'")
    else:
        print("Enter=aceitar sugestão do campo | s=skip campo | q=sair")
        print("Linha só é gravada se algum campo mudar (Enter em branco sem sugestão NÃO grava).\n")

    by_id = {r["internal_id"]: r for r in rows}
    for i, r in enumerate(work, 1):
        print("=" * 72)
        print(f"[{i}/{len(work)}] {r['internal_id']}  {r['year']}  {r['families']}  {r['level_technique']}")
        print(f"  {r.get('title', '')[:160]}")
        if r.get("doi"):
            print(f"  DOI: {r['doi']}")
        if r.get("notes"):
            print(f"  notes: {r['notes']}")
        print()

        if args.compact and args.mode in {"core", "all"}:
            # compact applies to core fields only when mode=all for clarity
            edit_fields = CORE_FIELDS if args.mode == "all" else fields
            changed, abort = edit_compact(r, edit_fields)
            if args.mode == "all" and changed and not abort:
                # still walk venue/spmf field-by-field
                c2, abort = edit_field_by_field(r, VENUE_FIELDS + SPMF_FIELDS, use_suggest)
                changed = changed or c2
        else:
            changed, abort = edit_field_by_field(r, fields, use_suggest)

        if abort:
            print("Saindo.")
            break

        if not changed:
            print("  (não salvo — nada preenchido; use valores ou Enter nas sugestões)")
            continue

        if not is_done(r, fields if args.mode != "all" else CORE_FIELDS):
            missing = [f for f in (fields if args.mode != "all" else CORE_FIELDS) if not (r.get(f) or "").strip()]
            print(f"  ! incompleto ({', '.join(missing)}). Salvei parcial.")

        apply_stamp(r, args.extractor)
        by_id[r["internal_id"]].update(r)
        save(path, rows)
        if args.sheet == "priority":
            sync_full(rows)
        print("  ✓ salvo")

    status(rows, fields)


if __name__ == "__main__":
    main()
