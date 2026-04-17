"""
Re-triagem dos 79 papers Banda E (maybe sem IC nem abstract) usando apenas
título + venue + ano + rationale da fase T/A.

Objetivo: excluir com alta confiança os que são claramente fora do escopo
a partir do título/venue, sem precisar do full text.

Uso:
    python scripts/band_e_title_rescreen.py --dry-run        # preview do prompt
    python scripts/band_e_title_rescreen.py --submit         # envia batch
    python scripts/band_e_title_rescreen.py --collect BATCH_ID
    python scripts/band_e_title_rescreen.py --stats          # resultado atual
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

FT_CSV       = Path("results/screening/ft_screening_results.csv")
MANUAL_CSV   = Path("results/pdfs/manual_download_prioritized.csv")
RESULTS_CSV  = Path("results/screening/band_e_rescreen_results.csv")
BATCH_LOG    = Path("results/screening/band_e_rescreen_batches.json")

MODEL      = "claude-haiku-4-5-20251001"
MAX_TOKENS = 256

SYSTEM_PROMPT = """\
Você é um especialista em SLR na área de process mining e engenharia de software.
Você recebe SOMENTE o título, venue, ano, query de origem e o raciocínio da
triagem anterior (que concluiu 'maybe' por falta de abstract).

Sua tarefa: decidir se é possível EXCLUIR com confiança a partir dessas informações.

Critérios de exclusão (aplicar a partir do título/venue):
EC1 – Domínio claramente fora de SW: saúde, manufatura, finanças, logística, etc.
EC2 – Software é apenas ferramenta de implementação, não o processo estudado.
EC3 – Trabalho puramente teórico/algorítmico sem avaliação em processos de SW.
EC4 – Revisão sistemática ou survey fora do escopo PM+SE.

Regras estritas:
- Use "exclude" SOMENTE quando o título/venue tornam inequívoca a aplicação de um EC.
- Use "pending" quando há ambiguidade genuína — o full text ainda pode revelar relevância.
- NUNCA use "include" — sem abstract não há base para inclusão nesta fase.
- Seja conservador: na dúvida entre exclude e pending, prefira pending.

Responda SOMENTE com JSON válido:
{"decision": "exclude"|"pending", "matched_ec": ["EC1"], "rationale": "<1 frase objetiva>"}"""


def _load_band_e_ids() -> set[str]:
    ids = set()
    with open(MANUAL_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["band"] == "E":
                ids.add(row["internal_id"])
    return ids


def _load_ft_papers(ids: set[str]) -> list[dict]:
    papers = []
    with open(FT_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["internal_id"] in ids:
                papers.append(row)
    return papers


def _load_existing_results() -> dict[str, dict]:
    if not RESULTS_CSV.exists():
        return {}
    with open(RESULTS_CSV, encoding="utf-8", newline="") as f:
        return {row["internal_id"]: row for row in csv.DictReader(f)}


def _build_prompt(p: dict) -> str:
    return (
        f"Título: {p['title']}\n"
        f"Venue: {p.get('venue', 'N/A')}\n"
        f"Ano: {p.get('year', 'N/A')} | Base: {p.get('source_db', 'N/A')} "
        f"| Query: {p.get('source_query_label', 'N/A')}\n\n"
        f"Raciocínio da triagem T/A (fase 1, sem abstract):\n"
        f"{p.get('ta_rationale', 'N/A')}\n\n"
        "Decida: é possível excluir com confiança apenas com esses dados?"
    )


def _parse_response(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        data = json.loads(text)
        decision = data.get("decision", "pending").lower()
        if decision not in ("exclude", "pending"):
            decision = "pending"
        matched_ec = "|".join(data.get("matched_ec") or [])
        rationale = str(data.get("rationale", ""))[:300]
        return {"decision": decision, "matched_ec": matched_ec, "rationale": rationale}
    except (json.JSONDecodeError, TypeError):
        return {"decision": "pending", "matched_ec": "", "rationale": f"parse_error: {text[:100]}"}


def _save_results(results: list[dict]) -> None:
    existing = _load_existing_results()
    for r in results:
        existing[r["internal_id"]] = r
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["internal_id", "title", "doi", "year", "source_db",
            "venue", "ft_priority_band", "ft_priority_score",
            "be_decision", "be_matched_ec", "be_rationale", "be_screened_at", "be_batch_id"]
    with open(RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing.values())


def _log_batch(batch_id: str, n: int) -> None:
    existing = []
    if BATCH_LOG.exists():
        try:
            existing = json.loads(BATCH_LOG.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append({"batch_id": batch_id, "n_papers": n,
                     "created_at": datetime.now(timezone.utc).isoformat()})
    BATCH_LOG.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_dry_run(papers: list[dict]) -> None:
    print(f"\n{'='*60}")
    print(f"DRY RUN — {len(papers)} papers Banda E")
    print("=" * 60)
    for i, p in enumerate(papers[:3], 1):
        print(f"\n--- Paper {i}: {p['title'][:70]} ---")
        print(_build_prompt(p)[:500])
        print("...")
    print(f"\nTotal que seriam enviados: {len(papers)}")


def cmd_submit(papers: list[dict], api_key: str) -> None:
    """Processa os papers via API síncrona (mais rápido para volumes pequenos)."""
    import anthropic
    from tqdm import tqdm

    existing = _load_existing_results()
    pending = [p for p in papers if p["internal_id"] not in existing]
    print(f"\n{len(existing)} já processados → {len(pending)} pendentes")

    if not pending:
        print("Nenhum paper pendente.")
        cmd_stats()
        return

    client = anthropic.Anthropic(api_key=api_key, timeout=60.0)
    ts = datetime.now(timezone.utc).isoformat()
    results = []

    with tqdm(total=len(pending), desc="re-screening Banda E", unit="paper") as pbar:
        for p in pending:
            for attempt in range(1, 4):
                try:
                    resp = client.messages.create(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": _build_prompt(p)}],
                    )
                    text = resp.content[0].text
                    parsed = _parse_response(text)
                    break
                except Exception as exc:
                    if attempt == 3:
                        parsed = {"decision": "pending", "matched_ec": "",
                                  "rationale": f"api_error: {exc}"}
                    else:
                        time.sleep(5 * attempt)

            results.append({
                "internal_id": p["internal_id"],
                "title": p.get("title", ""),
                "doi": p.get("doi", ""),
                "year": p.get("year", ""),
                "source_db": p.get("source_db", ""),
                "venue": p.get("venue", ""),
                "ft_priority_band": p.get("ft_priority_band", "E"),
                "ft_priority_score": p.get("ft_priority_score", ""),
                "be_decision": parsed["decision"],
                "be_matched_ec": parsed["matched_ec"],
                "be_rationale": parsed["rationale"],
                "be_screened_at": ts,
                "be_batch_id": "sync",
            })
            pbar.update(1)

    _save_results(results)
    print(f"\n✓ {len(results)} decisões salvas em {RESULTS_CSV}")
    cmd_stats()


def cmd_collect(batch_id: str, api_key: str, papers: list[dict]) -> None:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    b = client.messages.batches.retrieve(batch_id)
    c = b.request_counts
    print(f"Status: {b.processing_status} — succeeded: {c.succeeded} | errored: {c.errored} | processing: {c.processing}")
    if b.processing_status != "ended":
        print("Batch ainda não terminou. Tente novamente em alguns minutos.")
        return

    paper_index = {p["internal_id"]: p for p in papers}
    ts = datetime.now(timezone.utc).isoformat()

    results = []
    for result in client.messages.batches.results(batch_id):
        pid = result.custom_id
        p = paper_index.get(pid, {})
        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            parsed = _parse_response(text)
        else:
            parsed = {"decision": "pending", "matched_ec": "", "rationale": f"api_error: {result.result.type}"}

        results.append({
            "internal_id": pid,
            "title": p.get("title", ""),
            "doi": p.get("doi", ""),
            "year": p.get("year", ""),
            "source_db": p.get("source_db", ""),
            "venue": p.get("venue", ""),
            "ft_priority_band": p.get("ft_priority_band", "E"),
            "ft_priority_score": p.get("ft_priority_score", ""),
            "be_decision": parsed["decision"],
            "be_matched_ec": parsed["matched_ec"],
            "be_rationale": parsed["rationale"],
            "be_screened_at": ts,
            "be_batch_id": batch_id,
        })

    _save_results(results)
    print(f"\n✓ {len(results)} decisões salvas em {RESULTS_CSV}")
    cmd_stats()


def cmd_stats() -> None:
    if not RESULTS_CSV.exists():
        print("Nenhum resultado ainda.")
        return

    rows = list(_load_existing_results().values())
    total = len(rows)
    excludes = [r for r in rows if r.get("be_decision") == "exclude"]
    pending = [r for r in rows if r.get("be_decision") == "pending"]

    print(f"\n{'='*60}")
    print("BANDA E — RE-SCREENING POR TÍTULO")
    print("=" * 60)
    print(f"  Total processado: {total}")
    print(f"  exclude:  {len(excludes)}  ({len(excludes)/total*100:.1f}%)" if total else "")
    print(f"  pending:  {len(pending)}  ({len(pending)/total*100:.1f}%)" if total else "")

    from collections import Counter
    ec_c: Counter = Counter()
    for r in excludes:
        for ec in (r.get("be_matched_ec") or "").split("|"):
            if ec.strip():
                ec_c[ec.strip()] += 1
    if ec_c:
        print("\n  ECs nos excludes:")
        for ec, n in ec_c.most_common():
            print(f"    {ec}: {n}")

    if excludes:
        print(f"\n  Exemplos de excludes:")
        for r in excludes[:5]:
            print(f"    [{r.get('be_matched_ec','')}] {r['title'][:70]}")
            print(f"           {r.get('be_rationale','')[:100]}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-triagem Banda E por título")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--submit", action="store_true")
    group.add_argument("--collect", metavar="BATCH_ID")
    group.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    band_e_ids = _load_band_e_ids()
    papers = _load_ft_papers(band_e_ids)
    print(f"Banda E carregada: {len(papers)} papers")

    if args.dry_run:
        cmd_dry_run(papers)
    elif args.submit:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("ANTHROPIC_API_KEY não definida.")
            return
        cmd_submit(papers, api_key)
    elif args.collect:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        cmd_collect(args.collect, api_key, papers)
    elif args.stats:
        cmd_stats()


if __name__ == "__main__":
    main()
