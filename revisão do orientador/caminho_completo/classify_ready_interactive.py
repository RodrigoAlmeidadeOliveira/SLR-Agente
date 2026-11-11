#!/usr/bin/env python3
"""
Classificador interativo — phase1_title_only_ready_to_classify.csv

Uso:
  python3 classify_ready_interactive.py
  python3 classify_ready_interactive.py --coder Rodrigo --lot A
  python3 classify_ready_interactive.py --coder Juliano --lot B
  python3 classify_ready_interactive.py --coder Rodrigo --pending-only
  python3 classify_ready_interactive.py --status

Lotes (índice 0-based, ordenado por internal_id):
  A = primeiros 27  |  B = últimos 26
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import textwrap
import webbrowser
from datetime import date
from pathlib import Path

DIR = Path(__file__).resolve().parent
CSV_PATH = DIR / "phase1_title_only_ready_to_classify.csv"
BACKUP_PATH = DIR / "phase1_title_only_ready_to_classify.bak.csv"

FAMILIES = ["TF-PM", "TF-ST", "TF-FC", "TF-MSR"]
TECH = {"TF-PM", "TF-ST", "TF-FC"}
DECISIONS = {
    "1": "classify",
    "2": "EC5a",
    "3": "EC5b",
    "4": "exclude_other",
}
DECISION_HELP = (
    "1 classify          — incluir e classificar famílias\n"
    "2 EC5a              — full text não recuperável\n"
    "3 EC5b              — sem abstract e sem full text\n"
    "4 exclude_other     — excluir por outro critério (explique em notes)"
)


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = [{k: (v or "") for k, v in r.items()} for r in reader]
    required = [
        "internal_id",
        "decision",
        "families",
        "level",
        "notes",
        "coder",
        "date",
        "suggest_families",
        "suggest_level",
        "suggest_flags",
    ]
    for col in required:
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
        return "(vazio)"
    return textwrap.fill(text, width=width)


def clear() -> None:
    print("\n" + "=" * 88 + "\n")


def status(rows: list[dict[str, str]], lot: str | None = None) -> None:
    subset = select_lot(rows, lot) if lot else rows
    n = len(subset)
    done = sum(1 for r in subset if is_done(r))
    print(f"Progresso{' lot '+lot if lot else ''}: {done}/{n} concluídos ({n-done} pendentes)")
    by_dec: dict[str, int] = {}
    for r in subset:
        d = (r.get("decision") or "").strip() or "(vazio)"
        by_dec[d] = by_dec.get(d, 0) + 1
    print("Por decision:", ", ".join(f"{k}={v}" for k, v in sorted(by_dec.items())))


def select_lot(rows: list[dict[str, str]], lot: str | None) -> list[dict[str, str]]:
    if not lot:
        return rows
    lot = lot.upper()
    if lot == "A":
        return rows[:27]
    if lot == "B":
        return rows[27:]
    raise SystemExit("--lot deve ser A ou B")


def show_card(row: dict[str, str], idx: int, total: int) -> None:
    clear()
    print(f"[{idx}/{total}]  id={row['internal_id']}  year={row.get('year','')}  pdf={row.get('pdf_available','')}")
    print(f"Title: {wrap(row.get('title',''), 80)}")
    authors = row.get("authors") or "(autores não preenchidos)"
    print(f"Authors: {authors}")
    doi = (row.get("doi") or "").strip()
    print(f"DOI: {doi or '(sem DOI)'}")
    if doi:
        print(f"Link: https://doi.org/{doi}")
    flags = (row.get("suggest_flags") or "").strip()
    if flags:
        print(f"\n*** FLAG: {flags}  (D2=B → revisar confiabilidade de produto) ***")
    print("\nAbstract:")
    print(wrap(row.get("abstract", ""), 88))
    print(f"\nFonte abstract: {row.get('abstract_source') or '(n/a)'}")
    print("\nSugestão (atalho — NÃO aceitar no automático sem ler):")
    print(f"  families = {row.get('suggest_families') or '(vazia)'}")
    print(f"  level    = {row.get('suggest_level') or '(vazio)'}")
    if row.get("decision"):
        print("\nJá preenchido:")
        print(f"  decision={row.get('decision')}  families={row.get('families')}  level={row.get('level')}")
        print(f"  notes={row.get('notes')}")
        print(f"  coder={row.get('coder')}  date={row.get('date')}")


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSaindo sem gravar este item.")
        raise SystemExit(0)


def choose_decision(row: dict[str, str]) -> str | None:
    print("\nDecision:")
    print(DECISION_HELP)
    print("Atalhos: s = aceitar sugestão+classify | q = sair | k = skip")
    print("         (Enter só mantém se já houver decision; senão pede de novo)")
    cur = (row.get("decision") or "").strip()
    if cur:
        print(f"Atual: {cur}  → Enter mantém")
    has_suggest = bool((row.get("suggest_families") or "").strip())
    if not has_suggest:
        print("Obs: suggest_families vazia → NÃO use s; digite 1 e marque 1–4 manualmente,")
        print("     ou 4 exclude_other (ex.: D2 reliability/product).")
    ans = ask("> ").lower()
    if ans == "q":
        return None
    if ans == "k":
        return "__skip__"
    if ans == "":
        if cur:
            return cur
        print("Decision vazia. Digite 1, 2, 3, 4, s, k ou q — Enter sozinho não pula.")
        return choose_decision(row)
    if ans == "s":
        if not has_suggest:
            print("Sem sugestão de famílias. Use 1 e escolha TF-* manualmente, ou 4 para excluir.")
            return choose_decision(row)
        return "classify+suggest"
    if ans in DECISIONS:
        return DECISIONS[ans]
    if ans in DECISIONS.values():
        return ans
    print("Opção inválida.")
    return choose_decision(row)


def choose_families(row: dict[str, str], accept_suggest: bool = False) -> list[str] | None:
    selected = parse_families(row.get("suggest_families", "") if accept_suggest else row.get("families", ""))
    if accept_suggest and not selected:
        selected = parse_families(row.get("suggest_families", ""))
    while True:
        print("\nFamílias (toggle):")
        for i, f in enumerate(FAMILIES, 1):
            mark = "X" if f in selected else " "
            print(f"  {i}. [{mark}] {f}")
        print("  a = aceitar sugestão   c = limpar   done/Enter = confirmar   q = sair")
        print(f"Selecionadas: {'|'.join(selected) or '(nenhuma)'}  → level {level_from_families(selected)}")
        ans = ask("fam> ").lower()
        if ans == "q":
            return None
        if ans in ("", "done", "d"):
            return selected
        if ans == "c":
            selected = []
            continue
        if ans == "a":
            selected = parse_families(row.get("suggest_families", ""))
            continue
        if ans.isdigit() and 1 <= int(ans) <= len(FAMILIES):
            f = FAMILIES[int(ans) - 1]
            if f in selected:
                selected.remove(f)
            else:
                selected.append(f)
            continue
        # allow typing codes
        typed = parse_families(ans.replace(" ", "|"))
        if typed:
            for f in typed:
                if f in selected:
                    selected.remove(f)
                else:
                    selected.append(f)
            continue
        print("Entrada inválida. Use 1-4, a, c, done ou códigos TF-PM|TF-ST...")


def choose_notes(row: dict[str, str], decision: str) -> str:
    cur = (row.get("notes") or "").strip()
    hint = ""
    if decision == "exclude_other":
        hint = " (obrigatório explicar o critério)"
    elif (row.get("suggest_flags") or "").strip():
        hint = " (se D2: anote se excluiu por reliability/product)"
    print(f"\nNotes{hint}. Enter = manter.")
    if cur:
        print(f"Atual: {cur}")
    ans = ask("notes> ")
    if ans == "":
        return cur
    return ans


def open_doi(row: dict[str, str]) -> None:
    doi = (row.get("doi") or "").strip()
    if not doi:
        print("Sem DOI.")
        return
    webbrowser.open(f"https://doi.org/{doi}")


def classify_one(row: dict[str, str], coder: str, idx: int, total: int) -> str:
    """Returns: saved | skip | quit"""
    show_card(row, idx, total)
    print("\nComandos gerais neste card: o = abrir DOI no browser")
    pre = ask("Enter para classificar, o = DOI, k = skip, q = sair > ").lower()
    if pre == "q":
        return "quit"
    if pre == "k":
        return "skip"
    if pre == "o":
        open_doi(row)

    accept_suggest = False
    decision = choose_decision(row)
    if decision is None:
        return "quit"
    if decision == "__skip__":
        return "skip"
    if decision == "classify+suggest":
        decision = "classify"
        accept_suggest = True
    elif decision == "classify" and (row.get("suggest_families") or "").strip():
        yn = ask("Aceitar suggest_families agora? [Y/n] > ").lower()
        accept_suggest = yn in ("", "y", "yes", "s", "sim")

    families: list[str] = []
    level = ""
    if decision == "classify":
        fam = choose_families(row, accept_suggest=accept_suggest)
        if fam is None:
            return "quit"
        if not fam:
            print("Classify exige ao menos uma família. Marque 1–4, ou volte e use 4/EC.")
            # stay on families instead of restarting whole card
            while not fam:
                fam = choose_families(row, accept_suggest=False)
                if fam is None:
                    return "quit"
                if not fam:
                    print("Ainda vazio. Ex.: digite 2 para TF-ST, depois Enter.")
        families = fam
        level = level_from_families(families)
        print(f"Level calculado: {level}")
        if level == "L2_candidate":
            print("Atenção: 3 famílias de técnica → confirme depois no PDF se L2 ou L3.")

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

    print("\nGravado:")
    print(f"  {row['internal_id']}: decision={row['decision']} families={row['families']} level={row['level']}")
    return "saved"


def main() -> None:
    parser = argparse.ArgumentParser(description="Classificador interativo dos 53 ready")
    parser.add_argument("--coder", default="", help="Nome do classificador (Rodrigo ou Juliano)")
    parser.add_argument("--lot", choices=["A", "B", "a", "b"], help="A=27 primeiros, B=26 últimos")
    parser.add_argument("--pending-only", action="store_true", help="Só itens sem decision completa")
    parser.add_argument("--redo", action="store_true", help="Inclui já preenchidos (permite corrigir)")
    parser.add_argument("--status", action="store_true", help="Só mostra progresso e sai")
    parser.add_argument("--csv", type=Path, default=CSV_PATH, help="Caminho do CSV")
    args = parser.parse_args()

    path: Path = args.csv
    if not path.exists():
        raise SystemExit(f"CSV não encontrado: {path}")

    fieldnames, rows = load_rows(path)
    lot = args.lot.upper() if args.lot else None

    if args.status:
        status(rows, None)
        status(rows, "A")
        status(rows, "B")
        return

    coder = args.coder.strip()
    if not coder:
        coder = ask("Seu nome (coder) [Rodrigo/Juliano]: ")
        if not coder:
            raise SystemExit("coder obrigatório")

    if not lot:
        print("Lotes: A = ids 1–27 | B = ids 28–53 | Enter = todos")
        ans = ask("Lot [A/B/Enter]: ").upper()
        lot = ans if ans in {"A", "B"} else None

    subset = select_lot(rows, lot)
    if args.pending_only or not args.redo:
        queue = [r for r in subset if not is_done(r)]
    else:
        queue = list(subset)

    print(f"\nCoder={coder}  lot={lot or 'ALL'}  fila={len(queue)}  arquivo={path.name}")
    status(rows, lot)
    if not queue:
        print("Nada pendente neste lote. Use --redo para revisar.")
        return

    ask("Enter para começar...")

    # map id -> row in full list for in-place edit
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
        status(rows, lot)

    print(f"\nSessão: salvos={saved}  skips={skipped}")
    status(rows, lot)
    print(f"CSV atualizado: {path}")
    if BACKUP_PATH.exists():
        print(f"Backup inicial: {BACKUP_PATH}")


if __name__ == "__main__":
    main()
