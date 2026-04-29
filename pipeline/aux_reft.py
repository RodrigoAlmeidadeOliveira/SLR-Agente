"""Re-FT screening on the aux pending papers that gained an abstract via enrichment."""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ENRICHED_CSV = Path("results/auxiliary/aux_pending_enriched.csv")
AUX_FT_CSV = Path("results/auxiliary/aux_ft_screened.csv")
OUT_CSV = Path("results/auxiliary/aux_reft_enriched.csv")
SUMMARY_TXT = Path("results/auxiliary/aux_reft_summary.txt")
SUMMARY_TEX = Path("results/auxiliary/aux_reft_summary.tex")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512
N_WORKERS = 2


def _safe(d, k):
    import math
    v = d.get(k, "")
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def _load_api_key():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        for line in Path(".env").read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")
    return api_key


def _build(paper):
    from config.screening_criteria import FT_SYSTEM_PROMPT, FT_PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    return FT_SYSTEM_PROMPT, FT_PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title") or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type=_safe(paper, "doc_type") or "N/A",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "N/A",
        abstract_source=_safe(paper, "abstract_source") or "enriched",
        ta_decision=_safe(paper, "ta_decision") or "N/A",
        ta_rationale=_safe(paper, "ta_rationale"),
        ta_matched_ic=_safe(paper, "ta_matched_ic"),
        ta_matched_ec=_safe(paper, "ta_matched_ec"),
    )


def _parse(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            d = str(data.get("decision", "")).lower().strip()
            if d in ("include", "exclude", "pending"):
                return {
                    "decision": d,
                    "rationale": str(data.get("rationale", ""))[:400],
                    "matched_ic": "|".join(data.get("matched_ic") or []),
                    "matched_ec": "|".join(data.get("matched_ec") or []),
                }
        except json.JSONDecodeError:
            pass
    for v in ("include", "exclude", "pending"):
        if v in text.lower():
            return {"decision": v, "rationale": text[:400], "matched_ic": "", "matched_ec": ""}
    return {"decision": "", "rationale": f"PARSE_ERROR: {text[:200]}", "matched_ic": "", "matched_ec": ""}


def run():
    import anthropic
    if not ENRICHED_CSV.exists():
        logger.error("Enrichment CSV missing")
        return
    enriched = pd.read_csv(ENRICHED_CSV)
    has_abs = enriched[enriched["abstract"].fillna("").astype(str).str.strip() != ""].copy()
    logger.info(f"[ReFT] enriched with abstract: {len(has_abs)} of {len(enriched)}")

    existing = {}
    if OUT_CSV.exists():
        for r in pd.read_csv(OUT_CSV).to_dict("records"):
            d = str(r.get("ft_decision", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if d and raw != "ERROR":
                existing[r["internal_id"]] = r

    pending = [(i, row) for i, row in has_abs.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[ReFT] {len(has_abs)} target, {len(existing)} done, {len(pending)} pending")
    if not pending:
        report()
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        sys_p, user_p = _build(paper)
        for attempt in range(1, 5):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS, system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                )
                text = msg.content[0].text if msg.content else ""
                p = _parse(text)
                return {
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    "year": paper.get("year", ""),
                    "abstract": paper.get("abstract", ""),
                    "ft_decision": p["decision"],
                    "ft_rationale": p["rationale"],
                    "ft_matched_ic": p["matched_ic"],
                    "ft_matched_ec": p["matched_ec"],
                    "raw": text[:500],
                }
            except Exception as exc:
                logger.warning(f"[ReFT] {paper.get('internal_id')} attempt {attempt}: {exc}")
                time.sleep(3 * attempt)
        return {"internal_id": paper.get("internal_id", ""), "ft_decision": "", "raw": "ERROR"}

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(score, ir): ir for ir in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 25 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[ReFT] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(OUT_CSV, index=False)

    pd.DataFrame(results).to_csv(OUT_CSV, index=False)
    logger.info(f"[ReFT] Saved: {OUT_CSV}")
    report()


def report():
    if not OUT_CSV.exists():
        return
    df = pd.read_csv(OUT_CSV)
    df["ft_decision"] = df["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    n = len(df)
    inc = (df["ft_decision"] == "include").sum()
    exc = (df["ft_decision"] == "exclude").sum()
    pen = (df["ft_decision"] == "pending").sum()
    err = ((df["ft_decision"] == "") | (df["raw"].astype(str) == "ERROR")).sum()
    lines = [
        "SLR PATHCAST — Aux Re-FT after Enrichment",
        "=" * 60,
        f"Re-FT papers: {n} (those that gained an abstract via enrichment)",
        f"  include: {inc} ({inc/n*100:.1f}%)",
        f"  exclude: {exc} ({exc/n*100:.1f}%)",
        f"  pending: {pen} ({pen/n*100:.1f}%)",
        f"  errors:  {err}",
        "",
        f"NEW includes from re-FT: {inc}",
    ]
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    tex = [
        "\\begin{table}[htbp]", "\\centering",
        "\\caption{Re-FT screening of aux-pending papers that gained an abstract through the post-hoc enrichment cascade.}",
        "\\label{tab:aux-reft}",
        "\\begin{tabular}{lrr}", "\\toprule",
        "\\textbf{Outcome} & \\textbf{Count} & \\textbf{\\%} \\\\",
        "\\midrule",
        f"Re-FT include & {inc} & {inc/n*100:.1f} \\\\",
        f"Re-FT exclude & {exc} & {exc/n*100:.1f} \\\\",
        f"Re-FT pending & {pen} & {pen/n*100:.1f} \\\\",
        "\\midrule",
        f"\\textbf{{Total re-FT}} & \\textbf{{{n}}} & 100.0 \\\\",
        "\\bottomrule", "\\end{tabular}", "\\end{table}",
    ]
    SUMMARY_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.run: run()
    if args.report: report()
    if not (args.run or args.report): ap.print_help()


if __name__ == "__main__":
    main()
