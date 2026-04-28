"""Cohen's kappa inter-rater agreement for SLR PATHCAST screening.

Methodology: cross-model verification. Re-screens a stratified random 20%
sample of T/A and FT decisions using a *different* model (Claude Sonnet 4.6)
and computes Cohen's kappa against the primary screener (Haiku 4.5).

This satisfies IST/EMSE-style methodological rigor for LLM-assisted SLRs
when a human-only second rater is impractical at scale (Khraisha 2024,
Syriani 2023). A human spot check on disagreements is still recommended
before camera-ready.

Usage:
    python -m pipeline.kappa --sample              # build 20% stratified samples
    python -m pipeline.kappa --rescreen-ta         # cross-rate T/A sample
    python -m pipeline.kappa --rescreen-ft         # cross-rate FT sample
    python -m pipeline.kappa --compute             # compute kappa stats
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TA_CSV = Path("results/screening/ta_screening_results.csv")
FT_CSV = Path("results/screening/ft_screening_results.csv")
KAPPA_DIR = Path("results/kappa")
KAPPA_DIR.mkdir(parents=True, exist_ok=True)
TA_SAMPLE = KAPPA_DIR / "ta_sample_20pct.csv"
FT_SAMPLE = KAPPA_DIR / "ft_sample_20pct.csv"
TA_RESCREEN = KAPPA_DIR / "ta_rescreen_sonnet.csv"
FT_RESCREEN = KAPPA_DIR / "ft_rescreen_sonnet.csv"
KAPPA_REPORT_TXT = KAPPA_DIR / "kappa_report.txt"
KAPPA_REPORT_TEX = KAPPA_DIR / "kappa_report.tex"

VERIFIER_MODEL = "claude-sonnet-4-6"  # Sonnet 4.6 — different (larger) model family vs Haiku primary screener
PRIMARY_MODEL = "claude-haiku-4-5-20251001"
SAMPLE_RATE = 0.20
RANDOM_SEED = 20260428
N_WORKERS = 2
MAX_TOKENS = 512


def _norm_doi(s: str) -> str:
    return (s or "").strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _load_api_key() -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        env_path = Path(".env")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not found")
    return api_key


def build_samples() -> None:
    """Build stratified 20% random samples for T/A and FT, seeded for reproducibility."""
    random.seed(RANDOM_SEED)

    ta = pd.read_csv(TA_CSV)
    ta = ta[ta["ta_decision"].isin(["include", "exclude", "maybe"])].copy()
    ta_sample = (
        ta.groupby("ta_decision", group_keys=False)
        .apply(lambda g: g.sample(n=max(1, int(round(len(g) * SAMPLE_RATE))), random_state=RANDOM_SEED))
        .reset_index(drop=True)
    )
    ta_sample.to_csv(TA_SAMPLE, index=False, encoding="utf-8")
    logger.info(f"[Kappa] T/A sample: {len(ta_sample)} of {len(ta)} ({len(ta_sample)/len(ta)*100:.1f}%)")
    logger.info(f"  by decision: {dict(ta_sample['ta_decision'].value_counts())}")

    ft = pd.read_csv(FT_CSV)
    ft = ft[ft["ft_decision"].isin(["include", "exclude"])].copy()
    ft_sample = (
        ft.groupby("ft_decision", group_keys=False)
        .apply(lambda g: g.sample(n=max(1, int(round(len(g) * SAMPLE_RATE))), random_state=RANDOM_SEED))
        .reset_index(drop=True)
    )
    ft_sample.to_csv(FT_SAMPLE, index=False, encoding="utf-8")
    logger.info(f"[Kappa] FT sample: {len(ft_sample)} of {len(ft)} ({len(ft_sample)/len(ft)*100:.1f}%)")
    logger.info(f"  by decision: {dict(ft_sample['ft_decision'].value_counts())}")


def _safe(paper: dict, key: str, default: str = "") -> str:
    v = paper.get(key, default)
    if v is None:
        return default
    try:
        import math
        if isinstance(v, float) and math.isnan(v):
            return default
    except Exception:
        pass
    return str(v)


def _build_ta_prompt(paper: dict) -> tuple[str, str]:
    from config.screening_criteria import SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract").strip() or "Resumo não disponível."
    user = PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title").strip() or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type=_safe(paper, "doc_type") or "N/A",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "N/A",
        abstract_source=_safe(paper, "abstract_source") or "missing_or_unverified",
    )
    return SYSTEM_PROMPT, user


def _build_ft_prompt(paper: dict) -> tuple[str, str]:
    from config.screening_criteria import FT_SYSTEM_PROMPT, FT_PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract").strip() or "Resumo não disponível."
    user = FT_PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title").strip() or "(sem título)",
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


def _parse_decision(text: str, valid: set) -> str:
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            d = str(data.get("decision", "")).lower().strip()
            if d in valid:
                return d
        except json.JSONDecodeError:
            pass
    for v in valid:
        if v in text.lower():
            return v
    return ""


def rescreen(stage: str) -> None:
    """Re-screen sample using verifier model (Sonnet 4.5)."""
    import anthropic

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    if stage == "ta":
        sample_path, out_path = TA_SAMPLE, TA_RESCREEN
        valid = {"include", "exclude", "maybe"}
        decision_col = "ta_decision"
        build_prompt = _build_ta_prompt
    elif stage == "ft":
        sample_path, out_path = FT_SAMPLE, FT_RESCREEN
        valid = {"include", "exclude", "pending"}
        decision_col = "ft_decision"
        build_prompt = _build_ft_prompt
    else:
        raise ValueError(stage)

    if not sample_path.exists():
        logger.error(f"Sample missing: {sample_path}. Run --sample first.")
        sys.exit(1)

    sample = pd.read_csv(sample_path)
    existing = {}
    if out_path.exists():
        for r in pd.read_csv(out_path).to_dict("records"):
            verifier_decision = str(r.get(f"{stage}_decision_verifier", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if verifier_decision and raw != "ERROR":
                existing[r["row_idx"]] = r

    pending = [(i, row) for i, row in sample.iterrows() if i not in existing]
    logger.info(f"[Kappa-{stage}] {len(sample)} sample, {len(existing)} done, {len(pending)} pending")
    if not pending:
        logger.info("[Kappa] Nothing to do.")
        return

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        sys_p, user_p = build_prompt(paper)
        for attempt in range(1, 4):
            try:
                msg = client.messages.create(
                    model=VERIFIER_MODEL,
                    max_tokens=MAX_TOKENS,
                    system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                )
                text = msg.content[0].text if msg.content else ""
                d = _parse_decision(text, valid)
                return {
                    "row_idx": idx,
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    "doi": paper.get("doi", ""),
                    f"{stage}_decision_primary": paper.get(decision_col, ""),
                    f"{stage}_decision_verifier": d,
                    "verifier_model": VERIFIER_MODEL,
                    "raw": text[:600],
                }
            except Exception as exc:
                logger.warning(f"[Kappa-{stage}] idx={idx} attempt {attempt} failed: {exc}")
                time.sleep(2 * attempt)
        return {
            "row_idx": idx,
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            f"{stage}_decision_primary": paper.get(decision_col, ""),
            f"{stage}_decision_verifier": "",
            "verifier_model": VERIFIER_MODEL,
            "raw": "ERROR",
        }

    results = list(existing.values())
    completed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(score, ir): ir for ir in pending}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            completed += 1
            if completed % 20 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[Kappa-{stage}] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(out_path, index=False)

    pd.DataFrame(results).to_csv(out_path, index=False)
    logger.info(f"[Kappa-{stage}] Saved: {out_path}")


def _kappa(y1, y2) -> tuple[float, dict]:
    """Cohen's kappa for two raters. Pure NumPy implementation (avoids sklearn dep)."""
    import numpy as np
    y1 = list(y1)
    y2 = list(y2)
    cats = sorted(set(y1) | set(y2))
    idx = {c: i for i, c in enumerate(cats)}
    n = len(cats)
    cm = np.zeros((n, n), dtype=int)
    for a, b in zip(y1, y2):
        cm[idx[a], idx[b]] += 1
    total = cm.sum()
    if total == 0:
        return float("nan"), {}
    po = np.trace(cm) / total
    row = cm.sum(axis=1) / total
    col = cm.sum(axis=0) / total
    pe = (row * col).sum()
    kappa = (po - pe) / (1 - pe) if (1 - pe) != 0 else float("nan")
    return float(kappa), {"po": po, "pe": pe, "n": int(total), "categories": cats, "cm": cm.tolist()}


def _interpret(k: float) -> str:
    if k < 0:
        return "poor (worse than chance)"
    if k < 0.20:
        return "slight"
    if k < 0.41:
        return "fair"
    if k < 0.61:
        return "moderate"
    if k < 0.81:
        return "substantial"
    return "almost perfect"


def compute() -> None:
    lines = ["SLR PATHCAST — Inter-rater Agreement Report",
             "=" * 60,
             f"Primary screener:  {PRIMARY_MODEL}",
             f"Verifier (rater 2): {VERIFIER_MODEL}",
             f"Sample rate: {SAMPLE_RATE*100:.0f}% stratified random (seed={RANDOM_SEED})",
             ""]
    tex_rows = []

    for stage, rescreen_path in (("ta", TA_RESCREEN), ("ft", FT_RESCREEN)):
        if not rescreen_path.exists():
            lines.append(f"[{stage.upper()}] no rescreen file at {rescreen_path}; skip")
            continue
        df = pd.read_csv(rescreen_path)
        primary_col = f"{stage}_decision_primary"
        verifier_col = f"{stage}_decision_verifier"
        df[primary_col] = df[primary_col].fillna("").astype(str).str.strip().str.lower()
        df[verifier_col] = df[verifier_col].fillna("").astype(str).str.strip().str.lower()
        valid = df[(df[primary_col] != "") & (df[primary_col] != "nan") &
                   (df[verifier_col] != "") & (df[verifier_col] != "nan")].copy()
        n_total = len(df)
        n_valid = len(valid)
        if n_valid == 0:
            lines.append(f"[{stage.upper()}] no valid pairs")
            continue

        y1 = valid[primary_col].astype(str).str.lower().tolist()
        y2 = valid[verifier_col].astype(str).str.lower().tolist()
        k, info = _kappa(y1, y2)
        agree_pct = info["po"] * 100
        lines.append(f"[{stage.upper()}] n={n_valid}/{n_total}")
        lines.append(f"  Cohen's kappa (multi-class): {k:.3f} ({_interpret(k)})")
        lines.append(f"  Observed agreement (Po): {agree_pct:.1f}%")
        lines.append(f"  Expected by chance (Pe): {info['pe']*100:.1f}%")
        lines.append(f"  Categories: {info['categories']}")
        lines.append(f"  Confusion matrix (rows=primary, cols=verifier):")
        cats = info["categories"]
        header = "    " + " ".join(f"{c[:6]:>7}" for c in cats)
        lines.append(header)
        for i, c in enumerate(cats):
            row_str = "    " + f"{c[:6]:>3} " + " ".join(f"{v:>7}" for v in info["cm"][i])
            lines.append(row_str)

        # Binary-collapsed κ: include vs not-include
        def _bin(d): return "include" if d == "include" else "not_include"
        y1_b = [_bin(d) for d in y1]
        y2_b = [_bin(d) for d in y2]
        k_b, info_b = _kappa(y1_b, y2_b)
        lines.append(f"  Cohen's kappa (binary include/not-include): {k_b:.3f} ({_interpret(k_b)})")
        lines.append(f"    Po (binary)={info_b['po']*100:.1f}%, Pe (binary)={info_b['pe']*100:.1f}%")
        lines.append("")

        tex_rows.append(
            f"{stage.upper()} & {n_valid} & {agree_pct:.1f}\\% & {info['pe']*100:.1f}\\% & "
            f"{k:.3f} & {k_b:.3f} & {_interpret(k_b)} \\\\"
        )

    lines.append("")
    lines.append("Interpretation thresholds (Landis & Koch 1977):")
    lines.append("  <0.00 poor | 0-0.20 slight | 0.21-0.40 fair | 0.41-0.60 moderate | 0.61-0.80 substantial | >0.80 almost perfect")
    lines.append("")
    lines.append(f"Target: kappa >= 0.61 (substantial). See cap3 Section 'LLM-Assisted Screening Methodology'.")
    KAPPA_REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = ["\\begin{table}[htbp]",
           "\\centering",
           "\\caption{Inter-rater agreement (Cohen's $\\kappa$) between primary screener (claude-haiku-4-5) and verifier (claude-sonnet-4-6) on a stratified random 20\\% sample.}",
           "\\label{tab:kappa-results}",
           "\\begin{tabular}{lcccccc}",
           "\\toprule",
           "Stage & $N$ & $P_o$ & $P_e$ & $\\kappa_{\\text{multi}}$ & $\\kappa_{\\text{binary}}$ & Interpretation (binary) \\\\",
           "\\midrule",
           *tex_rows,
           "\\bottomrule",
           "\\end{tabular}",
           "\\end{table}"]
    KAPPA_REPORT_TEX.write_text("\n".join(tex), encoding="utf-8")

    print("\n".join(lines))
    logger.info(f"Reports saved: {KAPPA_REPORT_TXT}, {KAPPA_REPORT_TEX}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="Build 20% stratified samples")
    ap.add_argument("--rescreen-ta", action="store_true", help="Cross-rate T/A sample with verifier model")
    ap.add_argument("--rescreen-ft", action="store_true", help="Cross-rate FT sample with verifier model")
    ap.add_argument("--compute", action="store_true", help="Compute kappa from rescreen files")
    args = ap.parse_args()

    if args.sample:
        build_samples()
    if args.rescreen_ta:
        rescreen("ta")
    if args.rescreen_ft:
        rescreen("ft")
    if args.compute:
        compute()
    if not (args.sample or args.rescreen_ta or args.rescreen_ft or args.compute):
        ap.print_help()


if __name__ == "__main__":
    main()
