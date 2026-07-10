"""
FT real (leitura de PDF) para os 50 papers prioritários — SLR PATHCAST.

Complementa `pipeline/pdf_band_d_review.py` (que usa um mapeamento PDF→paper hardcoded
para o lote "Band D" já processado). Este script opera sobre uma lista arbitrária de
`internal_id`s (`results/screening/ft_real_priority_50.csv`) — os 50 papers identificados
na comparação entre a re-triagem T/A com abstract real (Fase A,
`results/screening/ta_rescreen_full_cascade_results.csv`) e o `ft_decision` já registrado
(que, para 99,5% dos casos, também é baseado só em abstract, não em full-text real — ver
`article_ist/response_to_reviewers/audit_log_abstract_recovery_2026-07-09.md`).

Reaproveita, sem duplicar, de `pipeline/pdf_band_d_review.py`:
  - `extract_pdf_text` — extração via pdfplumber, primeiras 6 páginas.
  - `_build_prompt` — mesmo `FT_PAPER_PROMPT_TEMPLATE`, substitui abstract pelo pdf_text.
E de `pipeline/fulltext.py`:
  - `_parse_ft_decision`, `save_ft_csv`.

Grava direto em `ft_screening_results.csv` (upsert por `internal_id`, só as linhas alvo) —
mesmo precedente já estabelecido pelo `pdf_band_d_review.py`.

Usage:
    python -m pipeline.ft_real_priority_review --match
    python -m pipeline.ft_real_priority_review --run [--dry-run]
    python -m pipeline.ft_real_priority_review --collect BATCH_ID
    python -m pipeline.ft_real_priority_review --report
"""
from __future__ import annotations

import argparse
import glob
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

PRIORITY_CSV = Path("results/screening/ft_real_priority_50.csv")
BATCHES_LOG = Path("results/screening/ft_real_priority_batches.json")
SUMMARY_TXT = Path("results/screening/ft_real_priority_summary.txt")
NO_PDF_TXT = Path("results/screening/ft_real_priority_no_pdf.txt")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512

PDF_SEARCH_DIRS = [
    Path("results/pdfs"),
    Path("results/human_validation/ft_pdfs_local"),
    Path("results/extraction/pdfs"),
    Path("results/final_review/top30_pdfs"),
]


def _norm_doi(s) -> str:
    s = "" if pd.isna(s) else str(s)
    return s.strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _norm_title(s) -> str:
    s = "" if s is None else str(s)
    s = s.lower()
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _find_pdf(internal_id: str, doi: str, title: str) -> Path | None:
    """Localiza o PDF de um paper nas coleções locais já existentes."""
    doi_n = _norm_doi(doi)
    title_n = _norm_title(title)

    manifest_path = Path("results/pdfs/download_manifest.csv")
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
        manifest["_doi"] = manifest["doi"].map(_norm_doi)
        hit = manifest[(manifest["_doi"] == doi_n) & (doi_n != "") & (manifest["pdf_status"] == "downloaded")]
        if len(hit) == 1:
            p = Path("results/pdfs") / hit.iloc[0]["pdf_file"]
            if p.exists():
                return p

    for d in PDF_SEARCH_DIRS:
        for f in glob.glob(str(d / "*.pdf")):
            base = os.path.basename(f)
            m = re.match(r"^([0-9a-f]{8})_", base, re.IGNORECASE)
            if m and m.group(1) == internal_id:
                return Path(f)

    return None


def cmd_match() -> None:
    priority = pd.read_csv(PRIORITY_CSV, dtype=str, keep_default_na=False)
    found, missing = [], []
    for _, r in priority.iterrows():
        pdf = _find_pdf(r["internal_id"], r["doi"], r["title"])
        if pdf:
            found.append((r["internal_id"], str(pdf), r["title"]))
        else:
            missing.append((r["internal_id"], r["title"]))

    logger.info(f"[Match] {len(found)}/{len(priority)} com PDF localizado")
    for iid, path, title in found:
        print(f"  {iid}  {path}  | {title[:60]}")
    logger.info(f"[Match] {len(missing)} sem PDF")
    for iid, title in missing:
        print(f"  [SEM PDF] {iid}  | {title[:60]}")

    NO_PDF_TXT.write_text("\n".join(f"{iid}\t{title}" for iid, title in missing), encoding="utf-8")


def cmd_run(dry_run: bool = False) -> str | None:
    from pipeline.pdf_band_d_review import extract_pdf_text, _build_prompt
    from pipeline.fulltext import load_ft_queue
    from config.screening_criteria import FT_SYSTEM_PROMPT
    import anthropic

    priority = pd.read_csv(PRIORITY_CSV, dtype=str, keep_default_na=False)
    ft_by_id = {p["internal_id"]: p for p in load_ft_queue()}

    candidates = []
    for _, r in priority.iterrows():
        iid = r["internal_id"]
        p = ft_by_id.get(iid)
        if p is None:
            # 4 exclude-origin papers nunca entraram na fila FT — usa os campos da lista de prioridade
            p = {
                "internal_id": iid, "title": r["title"], "doi": r["doi"],
                "abstract": "", "venue": "", "doc_type": "", "year": "",
                "source_db": "", "abstract_source": "", "ta_decision": r["ta_decision_original"],
                "ta_rationale": "", "ta_matched_ic": "",
            }
        pdf_path = _find_pdf(iid, r["doi"], r["title"])
        if pdf_path is None:
            continue
        candidates.append((iid, p, pdf_path))

    logger.info(f"[Run] {len(candidates)}/{len(priority)} papers com PDF disponível para FT real")
    if not candidates:
        logger.info("[Run] Nenhum candidato com PDF. Rode --match para diagnosticar.")
        return None

    requests = []
    for iid, p, pdf_path in candidates:
        pdf_text = extract_pdf_text(pdf_path)
        if not pdf_text.strip():
            logger.warning(f"[Run] Texto vazio extraído de {pdf_path.name} ({iid})")
        prompt = _build_prompt(p, pdf_text)
        requests.append({
            "custom_id": iid,
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": FT_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        })

    if dry_run:
        iid, p, pdf_path = candidates[0]
        print(f"[dry-run] Exemplo ({iid}, {pdf_path.name}):")
        print(_build_prompt(p, extract_pdf_text(pdf_path))[:800])
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    batch = None
    for attempt in range(1, 6):
        try:
            batch = client.messages.batches.create(requests=requests)
            break
        except Exception as exc:
            logger.warning(f"[Run] Erro ao criar batch (tentativa {attempt}/5): {exc}")
            if attempt < 5:
                time.sleep(10 * attempt)
            else:
                raise

    log = []
    if BATCHES_LOG.exists():
        import json
        log = json.loads(BATCHES_LOG.read_text())
    log.append({"batch_id": batch.id, "n_papers": len(requests),
                "submitted_at": datetime.now(timezone.utc).isoformat()})
    import json
    BATCHES_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False))

    logger.info(f"[Run] Batch criado: {batch.id} ({len(requests)} papers)")
    return batch.id


def cmd_collect(batch_id: str) -> int:
    from pipeline.fulltext import load_ft_queue, save_ft_csv, _parse_ft_decision, FT_COLUMNS
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        c = b.request_counts
        logger.info(f"[Collect] status={b.processing_status} succeeded={c.succeeded} errored={c.errored} processing={c.processing}")
        logger.info("[Collect] Batch ainda não terminou. Tente novamente mais tarde.")
        return 0

    all_ft = load_ft_queue()
    ft_by_id = {p["internal_id"]: p for p in all_ft}
    priority = pd.read_csv(PRIORITY_CSV, dtype=str, keep_default_na=False).set_index("internal_id")

    ts = datetime.now(timezone.utc).isoformat()
    updated = 0
    new_rows = []
    for result in client.messages.batches.results(batch_id):
        pid = result.custom_id
        if result.result.type == "succeeded":
            content = result.result.message.content
            text = content[0].text if content else ""
            decision_data = _parse_ft_decision(text)
        else:
            decision_data = {
                "ft_decision": "pending", "ft_rationale": f"Erro API: {result.result.type}",
                "ft_matched_ic": "", "ft_matched_ec": "", "ft_evidence_tags": "",
                "ft_software_context": "unclear", "ft_stochastic_method": "unclear",
                "ft_forecast_target": "unclear", "ft_process_data_source": "unclear",
                "ft_confidence": "low",
            }
        decision_data["ft_evidence_status"] = "pdf_full_text"
        decision_data["ft_manual_review_required"] = "false"
        decision_data["ft_screened_at"] = ts
        decision_data["ft_screened_by"] = "llm_pdf"
        decision_data["ft_batch_id"] = batch_id

        if pid in ft_by_id:
            ft_by_id[pid].update(decision_data)
        else:
            # 4 exclude-origin papers nao estao na fila FT ainda -- criar linha nova
            r = priority.loc[pid]
            row = {c: "" for c in FT_COLUMNS}
            row.update({
                "internal_id": pid, "title": r["title"], "doi": r["doi"],
                "ta_decision": r["ta_decision_original"],
            })
            row.update(decision_data)
            new_rows.append(row)
            ft_by_id[pid] = row

        updated += 1
        logger.info(f"  {pid} -> {decision_data.get('ft_decision')} (conf={decision_data.get('ft_confidence')})")

    all_rows = list(ft_by_id.values())
    save_ft_csv(all_rows)
    logger.info(f"[Collect] {updated} decisões atualizadas ({len(new_rows)} novas linhas na fila FT)")
    return updated


def cmd_report() -> None:
    from pipeline.fulltext import load_ft_queue

    priority = pd.read_csv(PRIORITY_CSV, dtype=str, keep_default_na=False)
    ft_by_id = {p["internal_id"]: p for p in load_ft_queue()}

    lines = ["SLR PATHCAST — FT real (PDF) para os 50 papers prioritários", "=" * 60, ""]
    n_pdf_screened = 0
    n_no_pdf = 0
    transitions = []
    for _, r in priority.iterrows():
        iid = r["internal_id"]
        ft = ft_by_id.get(iid)
        screened_by = (ft or {}).get("ft_screened_by", "")
        if screened_by == "llm_pdf":
            n_pdf_screened += 1
            transitions.append((iid, r["title"], r["ta_decision_rescreened"], r.get("ft_decision_existing", ""), ft.get("ft_decision")))
        else:
            n_no_pdf += 1

    lines.append(f"Total prioritário: {len(priority)}")
    lines.append(f"Re-triados com PDF real: {n_pdf_screened}")
    lines.append(f"Sem PDF disponível (decisão anterior mantida): {n_no_pdf}")
    lines.append("")
    lines.append("Comparação: T/A+abstract (Fase A) -> FT abstract-only (existente) -> FT+PDF real")
    for iid, title, ta_resc, ft_old, ft_new in transitions:
        lines.append(f"  {iid} | {title[:60]}")
        lines.append(f"    T/A+abstract: {ta_resc} | FT abstract-only: {ft_old or '(nunca triado)'} | FT+PDF real: {ft_new}")

    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    logger.info(f"Relatório salvo: {SUMMARY_TXT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--collect", type=str, default=None)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if args.match:
        cmd_match()
    if args.run:
        cmd_run(dry_run=args.dry_run)
    if args.collect:
        cmd_collect(args.collect)
    if args.report:
        cmd_report()


if __name__ == "__main__":
    main()
