"""FT screening for the auxiliary-corpus papers that survived T/A.

Takes the include (and optionally maybe) decisions from aux_ta_screened.csv
and applies the same FT LLM protocol used for the working set.
"""
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

AUX_TA_CSV = Path("results/auxiliary/aux_ta_screened.csv")
OUT_DIR = Path("results/auxiliary")
FT_CSV = OUT_DIR / "aux_ft_screened.csv"
SUMMARY_TXT = OUT_DIR / "aux_ft_summary.txt"
SUMMARY_TEX = OUT_DIR / "aux_ft_summary.tex"

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512
N_WORKERS = 2


def _safe(d: dict, k: str) -> str:
    v = d.get(k, "")
    if v is None:
        return ""
    try:
        import math
        if isinstance(v, float) and math.isnan(v):
            return ""
    except Exception:
        pass
    return str(v).strip()


def _load_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        for line in Path(".env").read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")
    return api_key


def _build_prompt(paper: dict) -> tuple[str, str]:
    from config.screening_criteria import FT_SYSTEM_PROMPT, FT_PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    user = FT_PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title") or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type=_safe(paper, "doc_type") or "N/A",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "N/A",
        abstract_source=_safe(paper, "abstract_source") or "missing_or_unverified",
        ta_decision=_safe(paper, "ta_decision") or "N/A",
        ta_rationale=_safe(paper, "ta_rationale"),
        ta_matched_ic=_safe(paper, "ta_matched_ic"),
        ta_matched_ec=_safe(paper, "ta_matched_ec"),
    )
    return FT_SYSTEM_PROMPT, user


def _parse(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            d = str(data.get("decision", "")).lower().strip()
            if d not in ("include", "exclude", "pending"):
                d = ""
            return {
                "decision": d,
                "rationale": str(data.get("rationale", ""))[:400],
                "matched_ic": "|".join(data.get("matched_ic") or []),
                "matched_ec": "|".join(data.get("matched_ec") or []),
            }
        except json.JSONDecodeError:
            pass
    return {"decision": "", "rationale": f"PARSE_ERROR: {text[:200]}", "matched_ic": "", "matched_ec": ""}


def run(include_maybe: bool = False) -> None:
    import anthropic

    if not AUX_TA_CSV.exists():
        logger.error(f"{AUX_TA_CSV} missing")
        return

    aux_ta = pd.read_csv(AUX_TA_CSV)
    aux_ta["ta_decision"] = aux_ta["ta_decision"].fillna("").astype(str).str.lower().str.strip()
    if include_maybe:
        forward = aux_ta[aux_ta["ta_decision"].isin(["include", "maybe"])].copy()
    else:
        forward = aux_ta[aux_ta["ta_decision"] == "include"].copy()
    logger.info(f"[AuxFT] forwarded to FT: {len(forward)}")

    existing = {}
    if FT_CSV.exists():
        for r in pd.read_csv(FT_CSV).to_dict("records"):
            d = str(r.get("ft_decision", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if d and raw != "ERROR":
                existing[r["internal_id"]] = r

    pending = [(i, row) for i, row in forward.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[AuxFT] {len(forward)} target, {len(existing)} done, {len(pending)} pending")
    if not pending:
        report()
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        sys_p, user_p = _build_prompt(paper)
        for attempt in range(1, 5):
            try:
                msg = client.messages.create(
                    model=MODEL, max_tokens=MAX_TOKENS, system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                )
                text = msg.content[0].text if msg.content else ""
                parsed = _parse(text)
                return {
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    "year": paper.get("year", ""),
                    "source_db": paper.get("source_db", ""),
                    "ta_decision": paper.get("ta_decision", ""),
                    "ft_decision": parsed["decision"],
                    "ft_rationale": parsed["rationale"],
                    "ft_matched_ic": parsed["matched_ic"],
                    "ft_matched_ec": parsed["matched_ec"],
                    "raw": text[:500],
                }
            except Exception as exc:
                logger.warning(f"[AuxFT] iid={paper.get('internal_id')} attempt {attempt} failed: {exc}")
                time.sleep(3 * attempt)
        return {
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "year": paper.get("year", ""),
            "source_db": paper.get("source_db", ""),
            "ta_decision": paper.get("ta_decision", ""),
            "ft_decision": "", "ft_rationale": "", "ft_matched_ic": "", "ft_matched_ec": "", "raw": "ERROR",
        }

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
                rate = completed / el if el else 0
                eta = (len(pending) - completed) / rate if rate else 0
                logger.info(f"[AuxFT] {completed}/{len(pending)} | {rate:.2f}/s | ETA {eta/60:.1f}min")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(FT_CSV, index=False)

    pd.DataFrame(results).to_csv(FT_CSV, index=False)
    logger.info(f"[AuxFT] Saved: {FT_CSV}")
    report()


def report() -> None:
    if not FT_CSV.exists():
        logger.error("Run --run first")
        return
    df = pd.read_csv(FT_CSV)
    df["ft_decision"] = df["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    n = len(df)
    inc = (df["ft_decision"] == "include").sum()
    exc = (df["ft_decision"] == "exclude").sum()
    pend = (df["ft_decision"] == "pending").sum()
    err = ((df["ft_decision"] == "") | (df["raw"].astype(str) == "ERROR")).sum()
    lines = [
        "SLR PATHCAST — Auxiliary FT Screening Result",
        "=" * 60,
        f"Forwarded to FT: {n}",
        f"  include: {inc} ({inc/n*100:.1f}%)",
        f"  exclude: {exc} ({exc/n*100:.1f}%)",
        f"  pending: {pend} ({pend/n*100:.1f}%)",
        f"  errors:  {err}",
        "",
        f"NEW confirmed includes from auxiliary corpus: {inc}",
        f"Combined working-set + auxiliary confirmed: {169 + inc}",
    ]
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Auxiliary-corpus FT-screening outcome (papers that passed T/A on the 3{,}807-paper deferred corpus).}",
        "\\label{tab:aux-ft-screening}",
        "\\begin{tabular}{lrr}",
        "\\toprule",
        "\\textbf{Outcome} & \\textbf{Count} & \\textbf{\\%} \\\\",
        "\\midrule",
        f"Forwarded from T/A & {n} & 100.0 \\\\",
        f"Included (new)     & {inc} & {inc/n*100:.1f} \\\\",
        f"Excluded            & {exc} & {exc/n*100:.1f} \\\\",
        f"Pending / unparsed  & {pend + err} & {(pend+err)/n*100:.1f} \\\\",
        "\\midrule",
        f"\\textbf{{Combined SLR set (working-set + auxiliary)}} & \\textbf{{{169 + inc}}} & --- \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]
    SUMMARY_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--include-maybe", action="store_true",
                    help="Also FT-screen the 'maybe' papers from T/A")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.run:
        run(include_maybe=args.include_maybe)
    if args.report:
        report()
    if not (args.run or args.report):
        ap.print_help()


if __name__ == "__main__":
    main()
