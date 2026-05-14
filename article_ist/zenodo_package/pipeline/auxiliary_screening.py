"""Full T/A screening of the deferred auxiliary corpus.

Runs the same Haiku 4.5 T/A protocol used for the working set on all 3,807
auxiliary papers and produces an aggregated decision CSV. Output is then
ready for FT priority assignment and FT screening.

Output:
  results/auxiliary/aux_ta_screened.csv
  results/auxiliary/aux_ta_summary.txt
"""
from __future__ import annotations

import argparse
import csv
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

AUX_FULL_CSV = Path("results/sensitivity/auxiliary_full.csv")
OUT_DIR = Path("results/auxiliary")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SCREENED_CSV = OUT_DIR / "aux_ta_screened.csv"
SUMMARY_TXT = OUT_DIR / "aux_ta_summary.txt"

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
    from config.screening_criteria import SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    user = PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title") or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type=_safe(paper, "doc_type") or "N/A",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "N/A",
        abstract_source=_safe(paper, "abstract_source") or "missing_or_unverified",
    )
    return SYSTEM_PROMPT, user


def _parse(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            d = str(data.get("decision", "")).lower().strip()
            if d not in ("include", "exclude", "maybe"):
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


def run() -> None:
    import anthropic

    if not AUX_FULL_CSV.exists():
        logger.error(f"{AUX_FULL_CSV} missing")
        return

    aux = pd.read_csv(AUX_FULL_CSV)
    existing = {}
    if SCREENED_CSV.exists():
        for r in pd.read_csv(SCREENED_CSV).to_dict("records"):
            d = str(r.get("ta_decision", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if d and raw != "ERROR":
                existing[r["internal_id"]] = r

    pending = [(i, row) for i, row in aux.iterrows() if row["internal_id"] not in existing]
    logger.info(f"[Aux] {len(aux)} papers, {len(existing)} done, {len(pending)} pending")
    if not pending:
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
                    "abstract": paper.get("abstract", ""),
                    "ta_decision": parsed["decision"],
                    "ta_rationale": parsed["rationale"],
                    "ta_matched_ic": parsed["matched_ic"],
                    "ta_matched_ec": parsed["matched_ec"],
                    "raw": text[:500],
                }
            except Exception as exc:
                logger.warning(f"[Aux] iid={paper.get('internal_id')} attempt {attempt} failed: {exc}")
                time.sleep(3 * attempt)
        return {
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "year": paper.get("year", ""),
            "source_db": paper.get("source_db", ""),
            "abstract": paper.get("abstract", ""),
            "ta_decision": "", "ta_rationale": "", "ta_matched_ic": "", "ta_matched_ec": "", "raw": "ERROR",
        }

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(score, ir): ir for ir in pending}
        for fut in as_completed(futs):
            results.append(fut.result())
            completed += 1
            if completed % 50 == 0 or completed == len(pending):
                el = time.time() - t0
                rate = completed / el if el else 0
                eta = (len(pending) - completed) / rate if rate else 0
                logger.info(f"[Aux] {completed}/{len(pending)} | {rate:.2f}/s | ETA {eta/60:.1f}min")
            if completed % 100 == 0:
                pd.DataFrame(results).to_csv(SCREENED_CSV, index=False)

    pd.DataFrame(results).to_csv(SCREENED_CSV, index=False)
    logger.info(f"[Aux] Saved: {SCREENED_CSV}")


def report() -> None:
    df = pd.read_csv(SCREENED_CSV)
    df["ta_decision"] = df["ta_decision"].fillna("").astype(str).str.lower().str.strip()
    n = len(df)
    inc = (df["ta_decision"] == "include").sum()
    mb = (df["ta_decision"] == "maybe").sum()
    exc = (df["ta_decision"] == "exclude").sum()
    err = ((df["ta_decision"] == "") | (df["raw"].astype(str) == "ERROR")).sum()
    lines = [
        "SLR PATHCAST — Auxiliary Corpus T/A Screening Result",
        "=" * 60,
        f"Total papers: {n}",
        f"  include: {inc} ({inc/n*100:.1f}%)",
        f"  maybe:   {mb} ({mb/n*100:.1f}%)",
        f"  exclude: {exc} ({exc/n*100:.1f}%)",
        f"  errors:  {err}",
        "",
        f"Forwarded to FT screening (include + maybe): {inc+mb}",
    ]
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.run:
        run()
    if args.report:
        report()
    if not (args.run or args.report):
        ap.print_help()


if __name__ == "__main__":
    main()
