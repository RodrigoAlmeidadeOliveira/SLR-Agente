"""Compare third-rater QA/extraction vs primary LLM (answer key).

Joins results/human_validation/third_rater_qa_extraction.csv with
results/human_validation/_answer_keys/ft_qa_extraction_answer_key.csv
on review_id (106 overlapping papers in the local-PDF corpus).

Usage:
    python -m pipeline.third_rater_kappa
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from pipeline.kappa import _interpret, _kappa

HUMAN_DIR = Path("results/human_validation")
THIRD_CSV = HUMAN_DIR / "third_rater_qa_extraction.csv"
ANSWER_KEY = HUMAN_DIR / "_answer_keys" / "ft_qa_extraction_answer_key.csv"
REPORT_TXT = HUMAN_DIR / "third_rater_vs_llm_report.txt"
REPORT_TEX = HUMAN_DIR / "third_rater_vs_llm_report.tex"

QA_FIELDS = [f"QA{i}" for i in range(1, 9)]
EXTRACTION_FIELDS = [
    "research_question",
    "study_type",
    "pm_technique",
    "stochastic_technique",
    "software_process",
    "dataset_source",
    "main_finding",
    "limitations",
]


def _norm_text(s) -> str:
    return re.sub(r"\s+", " ", str(s if pd.notna(s) else "").strip().lower())


def _qa_include(total: float) -> str:
    return "yes" if float(total) >= 4 else "no"


def load_merged() -> pd.DataFrame:
    third = pd.read_csv(THIRD_CSV)
    key = pd.read_csv(ANSWER_KEY)
    merged = third.merge(key, on="review_id", how="inner", suffixes=("_third", "_key"))
    if len(merged) != 106:
        raise ValueError(f"expected 106 merged rows, got {len(merged)}")
    return merged


def compute() -> None:
    merged = load_merged()
    sheet = pd.read_csv(HUMAN_DIR / "ft_qa_extraction_blind_review_sheet.csv")
    if "title" in sheet.columns:
        merged = merged.merge(sheet[["review_id", "title"]], on="review_id", how="left")
    lines = [
        "SLR PATHCAST — Third-rater vs Primary LLM Agreement Report",
        "=" * 62,
        "Primary rater (rater 1): claude-haiku-4-5-20251001 (answer key)",
        "Third rater:             independent QA/extraction pass (108-PDF corpus)",
        "",
        f"Overlap with answer key: {len(merged)} papers",
        f"  LLM ft_decision=include: {(merged['ft_decision'] == 'include').sum()}",
        f"  LLM ft_decision=exclude: {(merged['ft_decision'] == 'exclude').sum()}",
        "",
    ]

    tex_rows: list[str] = []
    qa_sub = merged[merged["llm_qa_QA1"].notna()].copy()
    lines.append(f"[QA/extraction comparison base] n={len(qa_sub)} papers with LLM QA scores")
    lines.append("(LLM-included papers in the 20% FT sample that also have local PDFs)")
    lines.append("")

    if len(qa_sub) == 0:
        lines.append("No LLM QA rows available for comparison.")
    else:
        lines.append("Per-criterion agreement (third vs LLM, binary 0/1):")
        for f in QA_FIELDS:
            llm_col = f"llm_qa_{f}"
            sub = qa_sub.dropna(subset=[f, llm_col])
            y_llm = sub[llm_col].astype(int).astype(str).tolist()
            y_third = sub[f].astype(int).astype(str).tolist()
            agree = (sub[f].astype(int) == sub[llm_col].astype(int)).mean() * 100
            k, info = _kappa(y_llm, y_third)
            k_str = f"{k:.3f} ({_interpret(k)})" if info else "n/a"
            lines.append(f"  {f}: Po={agree:.1f}%  kappa={k_str}  n={len(sub)}")
            tex_rows.append(f"{f} & {len(sub)} & {agree:.1f}\\% & {k:.3f} ({_interpret(k)}) \\\\")

        third_total = qa_sub[QA_FIELDS].astype(int).sum(axis=1)
        llm_total = pd.to_numeric(qa_sub["llm_qa_qa_total"], errors="coerce")
        mae = (third_total - llm_total).abs().mean()
        exact = (third_total == llm_total).mean() * 100
        lines.append("")
        lines.append(f"qa_total: exact match {exact:.1f}%, MAE={mae:.2f} (n={len(qa_sub)})")

        third_inc = third_total.map(_qa_include)
        llm_inc = qa_sub["llm_qa_qa_include"].fillna("").astype(str).str.strip().str.lower()
        llm_inc = llm_inc.replace({"1": "yes", "0": "no", "true": "yes", "false": "no"})
        inc_sub = qa_sub.assign(_third_inc=third_inc, _llm_inc=llm_inc)
        inc_sub = inc_sub[inc_sub["_llm_inc"].isin(["yes", "no"])]
        if len(inc_sub):
            agree_inc = (inc_sub["_third_inc"] == inc_sub["_llm_inc"]).mean() * 100
            k_inc, _ = _kappa(inc_sub["_llm_inc"].tolist(), inc_sub["_third_inc"].tolist())
            lines.append(
                f"qa_include (third: qa_total>=4 vs LLM qa_include): "
                f"Po={agree_inc:.1f}%, kappa={k_inc:.3f} ({_interpret(k_inc)}) n={len(inc_sub)}"
            )

        lines.append("")
        lines.append("[Extraction] normalized exact-match agreement:")
        for f in EXTRACTION_FIELDS:
            llm_col = f"llm_ext_{f}"
            if llm_col not in qa_sub.columns:
                continue
            sub = qa_sub[[f, llm_col]].dropna()
            sub = sub[(sub[f].astype(str).str.strip() != "") & (sub[llm_col].astype(str).str.strip() != "")]
            if len(sub) == 0:
                continue
            agree = (sub[f].map(_norm_text) == sub[llm_col].map(_norm_text)).mean() * 100
            lines.append(f"  {f}: {agree:.1f}% (n={len(sub)})")

        lines.append("")
        lines.append("[Largest qa_total disagreements] (third - LLM):")
        qa_sub = qa_sub.assign(
            qa_diff=third_total - llm_total,
            third_qa_total=third_total,
            llm_qa_total=llm_total,
        )
        top = qa_sub.reindex(qa_sub["qa_diff"].abs().sort_values(ascending=False).index).head(12)
        for _, row in top.iterrows():
            lines.append(
                f"  {row['review_id']}: third={int(row['third_qa_total'])} "
                f"LLM={int(row['llm_qa_total'])} diff={int(row['qa_diff']):+d} "
                f"| {str(row.get('title', ''))[:70]}"
            )

    lines.append("")
    lines.append("[All 106 papers] third-rater qa_total distribution:")
    for score, count in sorted(merged["qa_total"].value_counts().items()):
        lines.append(f"  qa_total={score}: {count}")

    lines.append("")
    lines.append("Interpretation thresholds (Landis & Koch 1977):")
    lines.append("  <0.00 poor | 0-0.20 slight | 0.21-0.40 fair | 0.41-0.60 moderate | 0.61-0.80 substantial | >0.80 almost perfect")

    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = [
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Agreement between the primary LLM screener (claude-haiku-4-5) and an "
        "independent third rater on QA criteria, for LLM-included papers with local PDFs "
        f"($n={len(qa_sub)}$).",
        "\\label{tab:third-rater-qa-kappa}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Criterion & $N$ & $P_o$ (\\%) & $\\kappa$ (interpretation) \\\\",
        "\\midrule",
        *tex_rows,
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ]
    REPORT_TEX.write_text("\n".join(tex), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReports saved: {REPORT_TXT}, {REPORT_TEX}")


if __name__ == "__main__":
    compute()
