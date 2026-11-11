#!/usr/bin/env python3
"""
Classificador interativo — phase1_title_only_needs_human.csv (23 restantes)

Fila sem abstract útil. Fluxo típico:
  o  → abrir DOI
  1  → classify (se leu abstract/PDF)
  2  → EC5a (full text irrecuperável)
  3  → EC5b (sem abstract e sem full text)  ← padrão desta fila
  4  → exclude_other
  p  → colar abstract no card (depois classificar)

Uso:
  python3 classify_needs_human_interactive.py --status
  python3 classify_needs_human_interactive.py --coder Rodrigo --pending-only
  python3 classify_needs_human_interactive.py --coder Rodrigo --lot A --pending-only
  python3 classify_needs_human_interactive.py --coder Juliano --lot B --pending-only
  python3 classify_needs_human_interactive.py --apply   # só reaplica CSV → studies.json

Lotes (por internal_id): A = 12 primeiros | B = 11 restantes
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import textwrap
import webbrowser
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase1_title_only_needs_human.csv"
BACKUP_PATH = DIR / "phase1_title_only_needs_human.bak.csv"
STUDIES_PATH = DIR.parent / "MSL___Rodrigo_e_Juliano" / "studies.json"
EXCLUSIONS_PATH = DIR / "phase1_needs_human_exclusions.csv"

FAMILIES = ["TF-PM", "TF-ST", "TF-FC", "TF-MSR"]
TECH = {"TF-PM", "TF-ST", "TF-FC"}
DECISIONS = {
    "1": "classify",
    "2": "EC5a",
    "3": "EC5b",
    "4": "exclude_other",
}
DECISION_HELP = (
    "1 classify          — incluir e classificar (precisa abstract/PDF)\n"
    "2 EC5a              — full text não recuperável\n"
    "3 EC5b              — sem abstract e sem full text (comum nesta fila)\n"
    "4 exclude_other     — excluir por outro critério (explique em notes)"
)


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = [{k: (v or "") for k, v in r.items()} for r in reader]
    for col in [
        "decision",
        "families",
        "level",
        "coder",
        "date",
        "abstract",
        "suggest_families",
        "suggest_level",
        "suggest_flags",
    ]:
        if col not in fieldnames:
            fieldnames.append(col)
    rows.sort(key=lambda r: r.get("internal_id", ""))
    return fieldnames, rows


def save_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    if path.exists() and not BACKUP_PATH.exists():
        shutil.copy2(path, BACKUP_PATH)
    tmp = path.with_suffix(".tmp.csv")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def is_done(row: dict[str, str]) -> bool:
    d = (row.get("decision") or "").strip()
    if not d:
        return False
    if d == "classify":
        return bool((row.get("families") or "").strip()) and bool((row.get("level") or "").strip())
    return True


def level_from_families(families: list[str]) -> str:
    n = len([f for f in families if f in TECH])
    if n <= 1:
        return "L0"
    if n == 2:
        return "L1"
    return "L2_candidate"


def parse_families(raw: str) -> list[str]:
    parts = [p.strip() for p in (raw or "").replace(",", "|").split("|") if p.strip()]
    out: list[str] = []
    for p in parts:
        if p in FAMILIES and p not in out:
            out.append(p)
    return out


def wrap(text: str, width: int = 88) -> str:
    text = " ".join((text or "").split())
    if not text:
        return "(vazio — use o para DOI, ou p para colar abstract)"
    return textwrap.fill(text, width=width)


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSaindo.")
        raise SystemExit(0)


def select_lot(rows: list[dict[str, str]], lot: str | None) -> list[dict[str, str]]:
    if not lot:
        return rows
    lot = lot.upper()
    if lot == "A":
        return rows[:12]
    if lot == "B":
        return rows[12:]
    raise SystemExit("--lot deve ser A ou B")


def status(rows: list[dict[str, str]], lot: str | None = None) -> None:
    subset = select_lot(rows, lot) if lot else rows
    n = len(subset)
    done = sum(1 for r in subset if is_done(r))
    print(f"Progresso{' lot '+lot if lot else ''}: {done}/{n} concluídos ({n-done} pendentes)")
    by: dict[str, int] = {}
    for r in subset:
        d = (r.get("decision") or "").strip() or "(vazio)"
        by[d] = by.get(d, 0) + 1
    print("Por decision:", ", ".join(f"{k}={v}" for k, v in sorted(by.items())))


def show_card(row: dict[str, str], idx: int, total: int) -> None:
    print("\n" + "=" * 88 + "\n")
    print(f"[{idx}/{total}]  id={row['internal_id']}  year={row.get('year','')}  pdf={row.get('pdf_available','')}")
    print(f"Title: {wrap(row.get('title',''), 80)}")
    print(f"Authors: {row.get('authors') or '(não preenchidos)'}")
    doi = (row.get("doi") or "").strip()
    print(f"DOI: {doi or '(sem DOI)'}")
    if doi:
        print(f"Link: https://doi.org/{doi}")
    print(f"Ação sugerida: {row.get('suggested_action') or '(n/a)'}")
    print(f"source_db: {row.get('source_db') or '(n/a)'}")
    print("\nAbstract:")
    print(wrap(row.get("abstract", ""), 88))
    if row.get("decision"):
        print("\nJá preenchido:")
        print(f"  decision={row.get('decision')}  families={row.get('families')}  level={row.get('level')}")
        print(f"  notes={row.get('notes')}")


def paste_abstract(row: dict[str, str]) -> None:
    print("Cole o abstract. Linha vazia ou END encerra:")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() in {"", "END", "end"}:
            if line.strip() in {"END", "end"} or lines:
                break
            continue
        lines.append(line)
    text = " ".join(" ".join(lines).split())
    if text:
        row["abstract"] = text
        print(f"Abstract salvo ({len(text)} chars).")
    else:
        print("Nada colado.")


def choose_decision(row: dict[str, str]) -> str | None:
    print("\nDecision:")
    print(DECISION_HELP)
    print("Atalhos: q = sair | k = skip | p = colar abstract")
    print("         (Enter só mantém se já houver decision)")
    has_abs = bool((row.get("abstract") or "").strip())
    has_pdf = (row.get("pdf_available") or "").startswith("yes")
    if not has_abs and not has_pdf:
        print("Obs: sem abstract/PDF → prefira 3 (EC5b) ou 2 (EC5a), salvo se for classificar pelo título+DOI.")
    cur = (row.get("decision") or "").strip()
    if cur:
        print(f"Atual: {cur} → Enter mantém")
    ans = ask("> ").lower()
    if ans == "q":
        return None
    if ans == "k":
        return "__skip__"
    if ans == "p":
        paste_abstract(row)
        return choose_decision(row)
    if ans == "":
        if cur:
            return cur
        print("Decision vazia. Digite 1–4, k ou q.")
        return choose_decision(row)
    if ans in DECISIONS:
        return DECISIONS[ans]
    if ans in DECISIONS.values():
        return ans
    print("Opção inválida.")
    return choose_decision(row)


def choose_families(row: dict[str, str]) -> list[str] | None:
    selected = parse_families(row.get("families", ""))
    while True:
        print("\nFamílias (toggle):")
        for i, f in enumerate(FAMILIES, 1):
            mark = "X" if f in selected else " "
            print(f"  {i}. [{mark}] {f}")
        print("  c = limpar   done/Enter = confirmar   q = sair")
        print(f"Selecionadas: {'|'.join(selected) or '(nenhuma)'}  → level {level_from_families(selected)}")
        ans = ask("fam> ").lower()
        if ans == "q":
            return None
        if ans in ("", "done", "d"):
            return selected
        if ans == "c":
            selected = []
            continue
        if ans.isdigit() and 1 <= int(ans) <= len(FAMILIES):
            f = FAMILIES[int(ans) - 1]
            if f in selected:
                selected.remove(f)
            else:
                selected.append(f)
            continue
        typed = parse_families(ans.replace(" ", "|"))
        if typed:
            for f in typed:
                if f in selected:
                    selected.remove(f)
                else:
                    selected.append(f)
            continue
        print("Use 1–4, c, done.")


def choose_notes(row: dict[str, str], decision: str) -> str:
    cur = (row.get("notes") or "").strip()
    hint = ""
    if decision == "exclude_other":
        hint = " (obrigatório)"
    elif decision in {"EC5a", "EC5b"}:
        hint = " (opcional: onde tentou buscar)"
    print(f"\nNotes{hint}. Enter = manter.")
    if cur:
        print(f"Atual: {cur}")
    ans = ask("notes> ")
    return cur if ans == "" else ans


def apply_to_studies(rows: list[dict[str, str]]) -> None:
    if not STUDIES_PATH.exists():
        print(f"studies.json não encontrado: {STUDIES_PATH}")
        return
    S = json.loads(STUDIES_PATH.read_text(encoding="utf-8"))
    by = {r["id"]: r for r in S}
    bak = DIR / f"studies.json.bak_needs_human_{date.today().isoformat()}"
    if not bak.exists():
        shutil.copy2(STUDIES_PATH, bak)
        print(f"Backup studies: {bak.name}")

    classified = removed = 0
    exclusions: list[dict[str, str]] = []
    if EXCLUSIONS_PATH.exists():
        exclusions = list(csv.DictReader(EXCLUSIONS_PATH.open(encoding="utf-8")))
    excl_ids = {e["internal_id"] for e in exclusions}

    for d in rows:
        if not is_done(d):
            continue
        rid = d["internal_id"]
        decision = d["decision"]
        if decision == "classify":
            if rid not in by:
                # re-add if previously removed? skip
                print(f"  WARN {rid} classify mas não está em studies.json")
                continue
            fams = parse_families(d.get("families", ""))
            by[rid]["fam"] = fams
            by[rid]["pat"] = "|".join(fams)
            classified += 1
        elif decision in {"EC5a", "EC5b", "exclude_other"}:
            if rid in by:
                del by[rid]
                removed += 1
            if rid not in excl_ids:
                exclusions.append(
                    {
                        "internal_id": rid,
                        "year": d.get("year", ""),
                        "title": d.get("title", ""),
                        "decision": decision,
                        "notes": d.get("notes", ""),
                        "coder": d.get("coder", ""),
                        "date": d.get("date", ""),
                    }
                )
                excl_ids.add(rid)

    S2 = sorted(by.values(), key=lambda r: (r.get("year", 0), r.get("id", "")))
    STUDIES_PATH.write_text(json.dumps(S2, ensure_ascii=False), encoding="utf-8")
    with EXCLUSIONS_PATH.open("w", encoding="utf-8", newline="") as f:
        fields = ["internal_id", "year", "title", "decision", "notes", "coder", "date"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(exclusions)
    print(
        f"Aplicado a studies.json: classify={classified} removed={removed} "
        f"→ n={len(S2)} classified={sum(1 for r in S2 if r.get('fam'))} "
        f"title_only={sum(1 for r in S2 if not r.get('fam'))}"
    )


def classify_one(row: dict[str, str], coder: str, idx: int, total: int) -> str:
    show_card(row, idx, total)
    print("\nComandos: Enter=classificar | o=DOI | p=colar abstract | k=skip | q=sair")
    pre = ask("> ").lower()
    if pre == "q":
        return "quit"
    if pre == "k":
        return "skip"
    if pre == "o":
        doi = (row.get("doi") or "").strip()
        if doi:
            webbrowser.open(f"https://doi.org/{doi}")
        else:
            print("Sem DOI.")
    if pre == "p":
        paste_abstract(row)

    decision = choose_decision(row)
    if decision is None:
        return "quit"
    if decision == "__skip__":
        return "skip"

    families: list[str] = []
    level = ""
    if decision == "classify":
        if not (row.get("abstract") or "").strip() and not (row.get("pdf_available") or "").startswith("yes"):
            yn = ask("Sem abstract/PDF local. Classificar mesmo assim? [y/N] > ").lower()
            if yn not in {"y", "yes", "s", "sim"}:
                print("Use 3 (EC5b) ou recupere o PDF.")
                return classify_one(row, coder, idx, total)
        fam = choose_families(row)
        if fam is None:
            return "quit"
        while not fam:
            print("Classify exige família. Marque 1–4.")
            fam = choose_families(row)
            if fam is None:
                return "quit"
        families = fam
        level = level_from_families(families)
        print(f"Level: {level}")

    notes = choose_notes(row, decision)
    if decision == "exclude_other" and not notes.strip():
        print("exclude_other exige notes.")
        notes = choose_notes(row, decision)

    row["decision"] = decision
    row["families"] = "|".join(families) if decision == "classify" else ""
    row["level"] = level if decision == "classify" else ""
    row["notes"] = notes
    row["coder"] = coder
    row["date"] = date.today().isoformat()
    print(f"\nGravado: {row['internal_id']} → {decision} {row['families']} {row['level']}")
    return "saved"


def main() -> None:
    parser = argparse.ArgumentParser(description="Classificador da fila needs_human (23)")
    parser.add_argument("--coder", default="")
    parser.add_argument("--lot", choices=["A", "B", "a", "b"])
    parser.add_argument("--pending-only", action="store_true")
    parser.add_argument("--redo", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Reaplica CSV concluído → studies.json e saia")
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--no-auto-apply", action="store_true", help="Não aplica studies.json a cada save")
    args = parser.parse_args()

    path: Path = args.csv
    if not path.exists():
        raise SystemExit(f"CSV não encontrado: {path}")

    fieldnames, rows = load_rows(path)
    lot = args.lot.upper() if args.lot else None

    if args.status:
        status(rows)
        status(rows, "A")
        status(rows, "B")
        return

    if args.apply:
        apply_to_studies(rows)
        return

    coder = args.coder.strip() or ask("Coder [Rodrigo/Juliano]: ")
    if not coder:
        raise SystemExit("coder obrigatório")

    if lot is None:
        print("Lotes: A = 12 primeiros | B = 11 restantes | Enter = todos")
        ans = ask("Lot [A/B/Enter]: ").upper()
        lot = ans if ans in {"A", "B"} else None

    subset = select_lot(rows, lot)
    queue = [r for r in subset if not is_done(r)] if (args.pending_only or not args.redo) else list(subset)

    print(f"\nCoder={coder} lot={lot or 'ALL'} fila={len(queue)}")
    status(rows, lot)
    if not queue:
        print("Nada pendente. Use --redo ou --apply.")
        return
    ask("Enter para começar...")

    by_id = {r["internal_id"]: r for r in rows}
    saved = skipped = 0
    for i, item in enumerate(queue, 1):
        row = by_id[item["internal_id"]]
        result = classify_one(row, coder, i, len(queue))
        if result == "quit":
            break
        if result == "skip":
            skipped += 1
            continue
        save_rows(path, fieldnames, rows)
        saved += 1
        if not args.no_auto_apply:
            apply_to_studies(rows)
        status(rows, lot)

    print(f"\nSessão: salvos={saved} skips={skipped}")
    status(rows, lot)
    print(f"CSV: {path}")
    if not args.no_auto_apply:
        print("studies.json atualizado a cada item salvo.")
        print("Regenere figuras: cd ../MSL___Rodrigo_e_Juliano && python3 figs.py && python3 figs_pt.py")


if __name__ == "__main__":
    main()
