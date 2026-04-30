"""Cohen's kappa cross-model verification on the auxiliary T/A and FT samples.

Reuses pipeline/kappa.py infrastructure but operates on the aux corpus.
Stratified random 20% sample of each stage; verifier model = Sonnet 4.6.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

AUX_TA_CSV = Path("results/auxiliary/aux_ta_screened.csv")
AUX_FT_CSV = Path("results/auxiliary/aux_ft_screened.csv")
OUT_DIR = Path("results/auxiliary/kappa")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TA_SAMPLE = OUT_DIR / "aux_ta_sample_20pct.csv"
FT_SAMPLE = OUT_DIR / "aux_ft_sample_20pct.csv"
TA_RESCREEN = OUT_DIR / "aux_ta_rescreen_sonnet.csv"
FT_RESCREEN = OUT_DIR / "aux_ft_rescreen_sonnet.csv"
REPORT_TXT = OUT_DIR / "aux_kappa_report.txt"
REPORT_TEX = OUT_DIR / "aux_kappa_report.tex"

VERIFIER_MODEL = "claude-sonnet-4-6"
PRIMARY_MODEL = "claude-haiku-4-5-20251001"
SAMPLE_RATE = 0.20
RANDOM_SEED = 20260429
N_WORKERS = 2
MAX_TOKENS = 512


def _safe(d, k):
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


def build_samples():
    import random
    random.seed(RANDOM_SEED)
    ta = pd.read_csv(AUX_TA_CSV)
    ta["ta_decision"] = ta["ta_decision"].fillna("").astype(str).str.lower().str.strip()
    ta_v = ta[ta["ta_decision"].isin(["include", "exclude", "maybe"])].copy()
    ta_s = (
        ta_v.groupby("ta_decision", group_keys=False)
        .apply(lambda g: g.sample(n=max(1, int(round(len(g) * SAMPLE_RATE))), random_state=RANDOM_SEED))
        .reset_index(drop=True)
    )
    ta_s.to_csv(TA_SAMPLE, index=False)
    logger.info(f"[AuxK] T/A sample: {len(ta_s)} of {len(ta_v)}")

    ft = pd.read_csv(AUX_FT_CSV)
    ft["ft_decision"] = ft["ft_decision"].fillna("").astype(str).str.lower().str.strip()
    ft_v = ft[ft["ft_decision"].isin(["include", "exclude", "pending"])].copy()
    ft_s = (
        ft_v.groupby("ft_decision", group_keys=False)
        .apply(lambda g: g.sample(n=max(1, int(round(len(g) * SAMPLE_RATE))), random_state=RANDOM_SEED))
        .reset_index(drop=True)
    )
    ft_s.to_csv(FT_SAMPLE, index=False)
    logger.info(f"[AuxK] FT sample: {len(ft_s)} of {len(ft_v)}")


def _build_ta(paper):
    from config.screening_criteria import SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    return SYSTEM_PROMPT, PAPER_PROMPT_TEMPLATE.format(
        title=_safe(paper, "title") or "(sem título)",
        abstract=abstract,
        venue=_safe(paper, "venue") or "N/A",
        doc_type=_safe(paper, "doc_type") or "N/A",
        year=_safe(paper, "year") or "N/A",
        source_db=_safe(paper, "source_db") or "N/A",
        abstract_source=_safe(paper, "abstract_source") or "missing_or_unverified",
    )


def _build_ft(paper):
    from config.screening_criteria import FT_SYSTEM_PROMPT, FT_PAPER_PROMPT_TEMPLATE
    abstract = _safe(paper, "abstract") or "Resumo não disponível."
    return FT_SYSTEM_PROMPT, FT_PAPER_PROMPT_TEMPLATE.format(
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


def _parse(text, valid):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            d = str(json.loads(m.group(0)).get("decision", "")).lower().strip()
            if d in valid:
                return d
        except json.JSONDecodeError:
            pass
    for v in valid:
        if v in text.lower():
            return v
    return ""


def rescreen(stage):
    import anthropic
    if stage == "ta":
        sample, out = TA_SAMPLE, TA_RESCREEN
        valid = {"include", "exclude", "maybe"}
        prim = "ta_decision"
        build = _build_ta
    else:
        sample, out = FT_SAMPLE, FT_RESCREEN
        valid = {"include", "exclude", "pending"}
        prim = "ft_decision"
        build = _build_ft

    if not sample.exists():
        logger.error("Run --sample first")
        return

    s = pd.read_csv(sample)
    existing = {}
    if out.exists():
        for r in pd.read_csv(out).to_dict("records"):
            d = str(r.get(f"{stage}_decision_verifier", "")).strip()
            raw = str(r.get("raw", "")).strip()
            if d and raw != "ERROR":
                existing[r["row_idx"]] = r

    pending = [(i, row) for i, row in s.iterrows() if i not in existing]
    logger.info(f"[AuxK-{stage}] {len(s)} sample, {len(existing)} done, {len(pending)} pending")
    if not pending:
        return

    client = anthropic.Anthropic(api_key=_load_api_key(), timeout=120.0)

    def score(idx_row):
        idx, row = idx_row
        paper = row.to_dict()
        sys_p, user_p = build(paper)
        for attempt in range(1, 4):
            try:
                msg = client.messages.create(
                    model=VERIFIER_MODEL, max_tokens=MAX_TOKENS, system=sys_p,
                    messages=[{"role": "user", "content": user_p}],
                )
                text = msg.content[0].text if msg.content else ""
                d = _parse(text, valid)
                return {
                    "row_idx": idx,
                    "internal_id": paper.get("internal_id", ""),
                    "title": paper.get("title", ""),
                    f"{stage}_decision_primary": paper.get(prim, ""),
                    f"{stage}_decision_verifier": d,
                    "verifier_model": VERIFIER_MODEL,
                    "raw": text[:600],
                }
            except Exception as exc:
                logger.warning(f"[AuxK-{stage}] idx={idx} attempt {attempt}: {exc}")
                time.sleep(3 * attempt)
        return {
            "row_idx": idx,
            "internal_id": paper.get("internal_id", ""),
            "title": paper.get("title", ""),
            f"{stage}_decision_primary": paper.get(prim, ""),
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
            results.append(fut.result())
            completed += 1
            if completed % 20 == 0 or completed == len(pending):
                el = time.time() - t0
                logger.info(f"[AuxK-{stage}] {completed}/{len(pending)} | {completed/el:.2f}/s")
            if completed % 50 == 0:
                pd.DataFrame(results).to_csv(out, index=False)

    pd.DataFrame(results).to_csv(out, index=False)
    logger.info(f"[AuxK-{stage}] Saved: {out}")


def _kappa(y1, y2):
    import numpy as np
    cats = sorted(set(y1) | set(y2))
    idx = {c: i for i, c in enumerate(cats)}
    cm = np.zeros((len(cats), len(cats)), dtype=int)
    for a, b in zip(y1, y2):
        cm[idx[a], idx[b]] += 1
    total = cm.sum()
    if total == 0:
        return float("nan"), {}
    po = np.trace(cm) / total
    pe = ((cm.sum(axis=1) / total) * (cm.sum(axis=0) / total)).sum()
    k = (po - pe) / (1 - pe) if (1 - pe) != 0 else float("nan")
    return float(k), {"po": po, "pe": pe, "n": int(total), "categories": cats, "cm": cm.tolist()}


def _interpret(k):
    if k < 0: return "poor"
    if k < 0.20: return "slight"
    if k < 0.41: return "fair"
    if k < 0.61: return "moderate"
    if k < 0.81: return "substantial"
    return "almost perfect"


def compute():
    lines = ["SLR PATHCAST — Auxiliary-Tier Inter-rater Agreement",
             "=" * 60,
             f"Primary: {PRIMARY_MODEL} | Verifier: {VERIFIER_MODEL}",
             f"Sample rate: {SAMPLE_RATE*100:.0f}% (seed={RANDOM_SEED})", ""]
    tex_rows = []
    for stage, path in (("ta", TA_RESCREEN), ("ft", FT_RESCREEN)):
        if not path.exists():
            lines.append(f"[{stage}] missing")
            continue
        df = pd.read_csv(path)
        prim = f"{stage}_decision_primary"
        ver = f"{stage}_decision_verifier"
        df[prim] = df[prim].fillna("").astype(str).str.lower().str.strip()
        df[ver] = df[ver].fillna("").astype(str).str.lower().str.strip()
        valid = df[(df[prim].isin(["include", "exclude", "maybe", "pending"])) &
                   (df[ver].isin(["include", "exclude", "maybe", "pending"]))]
        if len(valid) == 0:
            continue
        y1 = valid[prim].tolist()
        y2 = valid[ver].tolist()
        k, info = _kappa(y1, y2)
        # binary
        y1b = ["include" if d == "include" else "not_include" for d in y1]
        y2b = ["include" if d == "include" else "not_include" for d in y2]
        kb, infob = _kappa(y1b, y2b)
        lines += [
            f"[{stage.upper()}] n={len(valid)}/{len(df)}",
            f"  multi-class: kappa={k:.3f} ({_interpret(k)}), Po={info['po']*100:.1f}%, Pe={info['pe']*100:.1f}%",
            f"  binary:      kappa={kb:.3f} ({_interpret(kb)}), Po={infob['po']*100:.1f}%, Pe={infob['pe']*100:.1f}%",
            f"  CM categories: {info['categories']}",
            "",
        ]
        tex_rows.append(
            f"{stage.upper()} & {len(valid)} & {info['po']*100:.1f}\\% & {infob['po']*100:.1f}\\% & "
            f"{k:.3f} ({_interpret(k)}) & {kb:.3f} ({_interpret(kb)}) \\\\"
        )
    lines += [
        f"Target: kappa >= 0.61 (substantial; Landis \\& Koch 1977)",
    ]
    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")
    tex = [
        "\\begin{table}[htbp]", "\\centering",
        "\\caption{Auxiliary-tier inter-rater agreement (cross-model verification: Haiku 4.5 primary vs.\\ Sonnet 4.6 verifier on a stratified 20\\% sample).}",
        "\\label{tab:aux-kappa-results}",
        "\\begin{tabular}{lcccccc}", "\\toprule",
        "Stage & $N$ & $P_o^{\\text{multi}}$ & $P_o^{\\text{binary}}$ & $\\kappa_{\\text{multi}}$ & $\\kappa_{\\text{binary}}$ \\\\",
        "\\midrule",
        *tex_rows,
        "\\bottomrule", "\\end{tabular}", "\\end{table}",
    ]
    REPORT_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--rescreen-ta", action="store_true")
    ap.add_argument("--rescreen-ft", action="store_true")
    ap.add_argument("--compute", action="store_true")
    args = ap.parse_args()
    if args.sample: build_samples()
    if args.rescreen_ta: rescreen("ta")
    if args.rescreen_ft: rescreen("ft")
    if args.compute: compute()


if __name__ == "__main__":
    main()
