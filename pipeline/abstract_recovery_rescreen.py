"""
Abstract-recovery re-screening — working set completo (2.340 papers), SLR PATHCAST.

Fase A (não-destrutiva) de resposta ao Comentário M2 do Reviewer 2 (IST/Elsevier):
72,4% do working set (1.695/2.340, principalmente Scopus e ACM) foi triado pelo LLM
(claude-haiku-4-5-20251001) só com título, porque extractors/scopus.py usa a Scopus
Search API (dc:description), que a Elsevier deixa vazia na maioria dos registros — o
abstract real só sai pela Abstract Retrieval API, nunca chamada pelo pipeline.

Este script:
  1. Roda a cascata completa de 8 fontes (pipeline.enrich.enrich_abstracts — já validada
     numa amostra de 468 papers: 199/341 = 58% de recuperação) sobre o working set
     inteiro, indo além da cascata parcial de 2 fontes (Semantic Scholar + OpenAlex) já
     usada em results/screening/working_set_enriched.csv.
  2. Re-triagem, via o MESMO protocolo (prompt, modelo, política de decisão) do
     pipeline.screening original, só o subconjunto que ganhou abstract nesta rodada.
  3. Documenta a transição de decisão (antiga vs. nova) por paper.

Não sobrescreve nenhum arquivo oficial (ta_screening_results.csv, working_set_enriched.csv)
— tudo é gravado em arquivos novos e claramente rotulados. Adotar oficialmente estes
resultados (reconstruir fila de FT, re-FT-triar os promovidos, QA/extração, atualizar
169/381/404 no artigo) é uma decisão separada (Fase B), não feita por este script.

Usage:
    python -m pipeline.abstract_recovery_rescreen --enrich
    python -m pipeline.abstract_recovery_rescreen --count-tokens-sample [--n 10]
    python -m pipeline.abstract_recovery_rescreen --rescreen [--poll]
    python -m pipeline.abstract_recovery_rescreen --collect BATCH_ID
    python -m pipeline.abstract_recovery_rescreen --collect-all
    python -m pipeline.abstract_recovery_rescreen --report
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

SCREENING_DIR = Path("results/screening")
BASE_WS_CSV = SCREENING_DIR / "working_set_enriched.csv"                    # input, read-only
ORIGINAL_TA_RESULTS_CSV = SCREENING_DIR / "ta_screening_results.csv"        # official, read-only reference

ENRICHED_OUT_CSV = SCREENING_DIR / "working_set_enriched_full_cascade.csv"
RESCREEN_OUT_CSV = SCREENING_DIR / "ta_rescreen_full_cascade_results.csv"
BATCHES_LOG = SCREENING_DIR / "abstract_recovery_rescreen_batches.json"
SUMMARY_TXT = SCREENING_DIR / "abstract_recovery_rescreen_summary.txt"
SUMMARY_CSV = SCREENING_DIR / "abstract_recovery_rescreen_summary.csv"

BATCH_SIZE = 500

# Haiku 4.5 Batches API pricing (informational only; confirm current pricing before relying on it).
PRICE_IN_PER_MTOK = 0.50
PRICE_OUT_PER_MTOK = 2.50


def _nonempty(s) -> bool:
    return bool(str(s or "").strip())


# ------------------------------------------------------------------ #
#  Step 1: enrichment                                                  #
# ------------------------------------------------------------------ #

def cmd_enrich() -> None:
    from pipeline.enrich import enrich_abstracts

    df = pd.read_csv(BASE_WS_CSV, dtype=str, keep_default_na=False)
    before = df["abstract"].str.strip().str.len().gt(0).sum()
    logger.info(f"[Enrich] Working set completo: {len(df)} papers | com abstract antes: {before}")

    papers = df.to_dict("records")
    papers, _n = enrich_abstracts(papers, delay=0.3)

    out = pd.DataFrame(papers)
    after = out["abstract"].fillna("").astype(str).str.strip().str.len().gt(0).sum()
    logger.info(f"[Enrich] Com abstract depois: {after} | recuperados nesta rodada: {after - before}")

    out.to_csv(ENRICHED_OUT_CSV, index=False)
    logger.info(f"[Enrich] Salvo: {ENRICHED_OUT_CSV}")


def _load_recovered_subset() -> pd.DataFrame:
    """Papers sem abstract na triagem oficial original, mas com abstract após a
    cascata completa — únicos elegíveis para re-screening."""
    orig = pd.read_csv(ORIGINAL_TA_RESULTS_CSV, dtype=str, keep_default_na=False).set_index("internal_id")
    enr = pd.read_csv(ENRICHED_OUT_CSV, dtype=str, keep_default_na=False).set_index("internal_id")

    had_no_abstract = orig["abstract"].str.strip().str.len().eq(0)
    now_has_abstract = enr["abstract"].str.strip().str.len().gt(0)
    eligible_ids = set(had_no_abstract[had_no_abstract].index) & set(now_has_abstract[now_has_abstract].index)

    subset = enr.loc[sorted(eligible_ids)].reset_index()
    return subset


# ------------------------------------------------------------------ #
#  Step 2: cost sanity-check                                          #
# ------------------------------------------------------------------ #

def cmd_count_tokens_sample(n: int = 10) -> None:
    import anthropic
    from pipeline.screening import _build_user_prompt, MODEL, MAX_TOKENS
    from config.screening_criteria import SYSTEM_PROMPT

    subset = _load_recovered_subset()
    sample = subset.head(n).to_dict("records")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    total_in = 0
    for p in sample:
        msgs = [{"role": "user", "content": _build_user_prompt(p)}]
        count = client.messages.count_tokens(model=MODEL, system=SYSTEM_PROMPT, messages=msgs)
        total_in += count.input_tokens

    avg_in = total_in / len(sample)
    n_total = len(subset)
    est_in = avg_in * n_total
    est_out_max = MAX_TOKENS * n_total  # worst case, cap

    # Batches API discount: 50% off both directions
    cost_in = (est_in / 1_000_000) * PRICE_IN_PER_MTOK
    cost_out_max = (est_out_max / 1_000_000) * PRICE_OUT_PER_MTOK

    logger.info(f"[CountTokens] amostra n={len(sample)} | média input tokens/paper: {avg_in:.0f}")
    logger.info(f"[CountTokens] subconjunto elegível total: {n_total} papers")
    logger.info(f"[CountTokens] estimativa input tokens totais: {est_in:,.0f}")
    logger.info(f"[CountTokens] estimativa output tokens totais (teto max_tokens={MAX_TOKENS}): até {est_out_max:,}")
    logger.info(f"[CountTokens] custo estimado (Batches API, preço informativo): "
                f"${cost_in:.2f} (input) + até ${cost_out_max:.2f} (output no teto) "
                f"= até ~${cost_in + cost_out_max:.2f}")


# ------------------------------------------------------------------ #
#  Step 3: re-screening via Batches API                                #
# ------------------------------------------------------------------ #

def _log_batch(batch_id: str, meta: dict) -> None:
    log = []
    if BATCHES_LOG.exists():
        log = json.loads(BATCHES_LOG.read_text())
    log.append({"batch_id": batch_id, **meta})
    BATCHES_LOG.write_text(json.dumps(log, indent=2))


def cmd_rescreen(poll: bool, poll_interval: int = 60) -> None:
    from pipeline.screening import submit_batch, poll_batch, collect_batch_results

    api_key = os.getenv("ANTHROPIC_API_KEY")
    subset = _load_recovered_subset()
    if RESCREEN_OUT_CSV.exists():
        done = set(pd.read_csv(RESCREEN_OUT_CSV, dtype=str, keep_default_na=False)["internal_id"])
        before = len(subset)
        subset = subset[~subset["internal_id"].isin(done)]
        logger.info(f"[Rescreen] {len(done)} já re-triados anteriormente | {before - len(subset)} pulados | {len(subset)} restantes")
    papers = subset.to_dict("records")
    logger.info(f"[Rescreen] {len(papers)} papers elegíveis para re-screening nesta chamada")

    all_results: list[dict] = []
    for start in range(0, len(papers), BATCH_SIZE):
        chunk = papers[start:start + BATCH_SIZE]
        batch_id = submit_batch(chunk, api_key)
        _log_batch(batch_id, {"n_papers": len(chunk), "submitted_at": datetime.now(timezone.utc).isoformat()})
        if poll:
            poll_batch(batch_id, api_key, poll_interval=poll_interval)
            results = collect_batch_results(batch_id, api_key, chunk)
            all_results.extend(results)
            _merge_and_save_rescreen(results)

    if not poll:
        logger.info("[Rescreen] Batches enviados sem --poll. Use --collect <batch_id> ou --collect-all depois.")


def cmd_collect(batch_id: str | None, collect_all: bool) -> None:
    from pipeline.screening import collect_batch_results

    api_key = os.getenv("ANTHROPIC_API_KEY")
    subset = _load_recovered_subset()
    papers = subset.to_dict("records")

    batch_ids = []
    if collect_all:
        log = json.loads(BATCHES_LOG.read_text())
        batch_ids = [entry["batch_id"] for entry in log]
    elif batch_id:
        batch_ids = [batch_id]
    else:
        raise SystemExit("Forneça --collect BATCH_ID ou --collect-all")

    for bid in batch_ids:
        results = collect_batch_results(bid, api_key, papers)
        _merge_and_save_rescreen(results)


def _merge_and_save_rescreen(new_results: list[dict]) -> None:
    """Junta decisões novas com as antigas (ta_screening_results.csv oficial) e
    grava/atualiza RESCREEN_OUT_CSV com colunas antiga/nova lado a lado."""
    orig = pd.read_csv(ORIGINAL_TA_RESULTS_CSV, dtype=str, keep_default_na=False).set_index("internal_id")
    new_df = pd.DataFrame(new_results).set_index("internal_id")

    rows = []
    for iid, new_row in new_df.iterrows():
        old_row = orig.loc[iid] if iid in orig.index else None
        old_decision = old_row["ta_decision"] if old_row is not None else ""
        new_decision = new_row["ta_decision"]
        rows.append({
            "internal_id": iid,
            "title": new_row.get("title", ""),
            "doi": new_row.get("doi", ""),
            "source_db": new_row.get("source_db", ""),
            "year": new_row.get("year", ""),
            "abstract_source": new_row.get("abstract_source", ""),
            "abstract_match_type": new_row.get("abstract_match_type", ""),
            "ta_decision_original": old_decision,
            "ta_rationale_original": old_row["ta_rationale"] if old_row is not None else "",
            "ta_decision_rescreened": new_decision,
            "ta_rationale_rescreened": new_row.get("ta_rationale", ""),
            "ta_matched_ic_rescreened": new_row.get("ta_matched_ic", ""),
            "ta_matched_ec_rescreened": new_row.get("ta_matched_ec", ""),
            "ta_confidence_rescreened": new_row.get("ta_confidence", ""),
            "ta_evidence_status_rescreened": new_row.get("ta_evidence_status", ""),
            "ta_screened_at_rescreened": new_row.get("ta_screened_at", ""),
            "ta_batch_id_rescreened": new_row.get("ta_batch_id", ""),
            "changed": old_decision != new_decision,
            "transition": f"{old_decision}→{new_decision}",
        })

    new_batch_df = pd.DataFrame(rows)

    if RESCREEN_OUT_CSV.exists():
        existing = pd.read_csv(RESCREEN_OUT_CSV, dtype=str, keep_default_na=False)
        existing = existing[~existing["internal_id"].isin(new_batch_df["internal_id"])]
        combined = pd.concat([existing, new_batch_df], ignore_index=True)
    else:
        combined = new_batch_df

    combined.to_csv(RESCREEN_OUT_CSV, index=False)
    logger.info(f"[Rescreen] {len(new_batch_df)} decisões novas gravadas | total acumulado: {len(combined)}")


# ------------------------------------------------------------------ #
#  Step 4: report                                                     #
# ------------------------------------------------------------------ #

def cmd_report() -> None:
    orig = pd.read_csv(ORIGINAL_TA_RESULTS_CSV, dtype=str, keep_default_na=False)
    enr = pd.read_csv(ENRICHED_OUT_CSV, dtype=str, keep_default_na=False) if ENRICHED_OUT_CSV.exists() else None
    resc = pd.read_csv(RESCREEN_OUT_CSV, dtype=str, keep_default_na=False) if RESCREEN_OUT_CSV.exists() else None

    lines = ["SLR PATHCAST — Abstract Recovery + T/A Re-screening Summary (Fase A, Reviewer 2 M2)",
              "=" * 78, ""]

    lines.append("1. COBERTURA DE ABSTRACT POR SOURCE_DB")
    lines.append("-" * 40)
    before_by_src = orig.assign(has_ab=orig["abstract"].str.strip().str.len().gt(0)).groupby("source_db")["has_ab"].agg(["sum", "count"])
    for src, row in before_by_src.iterrows():
        lines.append(f"  {src:10s} antes: {int(row['sum'])}/{int(row['count'])} ({row['sum']/row['count']*100:.1f}%)")
    if enr is not None:
        after_by_src = enr.assign(has_ab=enr["abstract"].fillna("").astype(str).str.strip().str.len().gt(0)).groupby("source_db")["has_ab"].agg(["sum", "count"])
        lines.append("")
        for src, row in after_by_src.iterrows():
            lines.append(f"  {src:10s} depois: {int(row['sum'])}/{int(row['count'])} ({row['sum']/row['count']*100:.1f}%)")
        total_before = before_by_src["sum"].sum()
        total_after = after_by_src["sum"].sum()
        lines.append("")
        lines.append(f"  TOTAL antes: {int(total_before)}/{len(orig)} ({total_before/len(orig)*100:.1f}%)")
        lines.append(f"  TOTAL depois: {int(total_after)}/{len(enr)} ({total_after/len(enr)*100:.1f}%)")
        lines.append(f"  Recuperados nesta rodada: {int(total_after - total_before)}")

    if enr is not None:
        lines.append("")
        lines.append("2. RECUPERAÇÃO POR FONTE DA CASCATA (abstract_source, entre os recuperados)")
        lines.append("-" * 40)
        recovered = enr[(enr["abstract"].fillna("").astype(str).str.strip().str.len().gt(0))]
        orig_had = set(orig.loc[orig["abstract"].str.strip().str.len().gt(0), "internal_id"])
        recovered_only = recovered[~recovered["internal_id"].isin(orig_had)]
        if "abstract_source" in recovered_only.columns and len(recovered_only) > 0:
            src_counts = recovered_only["abstract_source"].value_counts()
            for src, cnt in src_counts.items():
                pct = cnt / len(recovered_only) * 100
                lines.append(f"  {src or '(none)':30s} {cnt:5d} ({pct:.1f}% dos recuperados)")

    if resc is not None and len(resc) > 0:
        lines.append("")
        lines.append("3. TABELA DE TRANSIÇÃO DE DECISÕES (antiga → nova, só re-triados)")
        lines.append("-" * 40)
        trans_counts = resc["transition"].value_counts()
        for trans, cnt in trans_counts.items():
            pct = cnt / len(resc) * 100
            lines.append(f"  {trans:25s} {cnt:5d} ({pct:.1f}%)")
        n_changed = resc["changed"].astype(str).isin(["True", "true"]).sum()
        lines.append("")
        lines.append(f"  Total re-triado: {len(resc)} | Decisão mudou: {n_changed} ({n_changed/len(resc)*100:.1f}%)")

        exclude_to_promoted = resc[(resc["ta_decision_original"] == "exclude") &
                                    (resc["ta_decision_rescreened"].isin(["include", "maybe"]))]
        lines.append(f"  Especificamente exclude→include/maybe (evidência potencialmente recuperada): {len(exclude_to_promoted)}")

    lines.append("")
    lines.append("FILES WRITTEN:")
    for f in [ENRICHED_OUT_CSV, RESCREEN_OUT_CSV, BATCHES_LOG]:
        if f.exists():
            lines.append(f"  {f}")

    lines.append("")
    lines.append("ACTION REQUIRED / NOTE:")
    lines.append("  Estes resultados NÃO foram propagados para ta_screening_results.csv (oficial),")
    lines.append("  nem para a fila de full-text, QA, extração, ou para os números 169/381/404 do")
    lines.append("  artigo. Adotar oficialmente exige uma Fase B separada: reconstruir a fila de FT")
    lines.append("  (pipeline/fulltext.py --export), FT-triar os papers promovidos, QA/extração dos")
    lines.append("  novos includes, e só então atualizar o texto do artigo. Decisão explícita do autor.")

    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    if resc is not None:
        resc.to_csv(SUMMARY_CSV, index=False)
    print("\n".join(lines))
    logger.info(f"Relatório salvo: {SUMMARY_TXT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enrich", action="store_true")
    ap.add_argument("--count-tokens-sample", action="store_true")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--rescreen", action="store_true")
    ap.add_argument("--poll", action="store_true")
    ap.add_argument("--poll-interval", type=int, default=60)
    ap.add_argument("--collect", type=str, default=None)
    ap.add_argument("--collect-all", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if args.enrich:
        cmd_enrich()
    if args.count_tokens_sample:
        cmd_count_tokens_sample(n=args.n)
    if args.rescreen:
        cmd_rescreen(poll=args.poll, poll_interval=args.poll_interval)
    if args.collect or args.collect_all:
        cmd_collect(args.collect, args.collect_all)
    if args.report:
        cmd_report()


if __name__ == "__main__":
    main()
