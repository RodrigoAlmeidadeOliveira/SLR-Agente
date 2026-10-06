"""Round-2 human validation of the LLM-assisted selection (IST R1 -> R2).

Implements article_ist/response_to_reviewers/round2/PREREGISTRATION_round2_validation.md.

The round-1 FT reference standard recorded PDF availability rather than
eligibility, so this round re-judges eligibility with two independent raters:

  * FT sample (working set, n=177): Rater A and Rater B judge every record.
  * Auxiliary tier: stratified samples S1 (T/A exclude), S2 (FT/re-FT exclude),
    S3 (closed under EC5-extended) plus decoy stratum S0 (LLM includes).
    Rater A judges all; Rater B judges a 30% random subset of each stratum.

Sheets never show the LLM decision or the stratum; both live in _keys/.

Usage:
    python -m pipeline.round2_validation --build-sheets
    python -m pipeline.round2_validation --build-consensus   # after both raters finish
    python -m pipeline.round2_validation --compute           # after consensus is filled
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from pipeline.human_kappa import _mcc, _wilson_ci, _wmcc
from pipeline.kappa import _interpret, _kappa

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SEED = 20261006
AUX_SAMPLE_SIZES = {"S1": 40, "S2": 40, "S3": 60, "S0": 20}
RATER_B_AUX_FRACTION = 0.30
RECALL_THRESHOLD = 0.90

FT_SAMPLE = Path("results/kappa/ft_sample_20pct.csv")
R1_FT_SHEET = Path("results/human_validation/ft_qa_extraction_blind_review_sheet.csv")
R1_FT_KEY = Path("results/human_validation/_answer_keys/ft_qa_extraction_answer_key.csv")
ALL_PAPERS = Path("results/all_papers.csv")
AUX_TA = Path("results/auxiliary/aux_ta_screened.csv")
AUX_FT = Path("results/auxiliary/aux_ft_screened.csv")
AUX_PENDING = Path("results/auxiliary/aux_pending_enriched.csv")
AUX_REFT = Path("results/auxiliary/aux_reft_enriched.csv")

OUT_DIR = Path("results/human_validation_round2")
KEY_DIR = OUT_DIR / "_keys"
FT_KEY = KEY_DIR / "ft_key.csv"
AUX_KEY = KEY_DIR / "aux_key.csv"
CONSENSUS = OUT_DIR / "consensus_sheet.xlsx"
REPORT_TXT = OUT_DIR / "round2_report.txt"
REPORT_TEX = OUT_DIR / "round2_confusion.tex"

RATER_FIELDS = ["access_basis", "decision", "ic_matched", "ec_applied", "justification", "evidence_location"]
ACCESS_VALUES = {"full_text", "abstract_only", "title_only", "not_accessible"}
DECISION_VALUES = {"include", "exclude", "not_assessable"}
BIB_COLS = ["review_id", "title", "authors", "year", "venue", "doc_type", "doi", "url", "abstract", "local_pdf_path"]


def _sheet_path(sample: str, rater: str) -> Path:
    return OUT_DIR / f"{sample}_eligibility_rater{rater}.xlsx"


def _blank_rater_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for f in RATER_FIELDS:
        df[f] = ""
    return df


def _write_sheet(df: pd.DataFrame, path: Path, seed: int) -> None:
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    df.to_excel(path, index=False)
    logger.info(f"sheet: {path} ({len(df)} rows)")


# --------------------------------------------------------------------------- build

def _build_ft() -> None:
    sample = pd.read_csv(FT_SAMPLE).reset_index(drop=True)
    sample["review_id"] = [f"ft_{i:04d}" for i in range(len(sample))]  # same ids as round 1
    r1 = pd.read_csv(R1_FT_SHEET)[["review_id", "local_pdf_path"]]
    sheet = sample.merge(r1, on="review_id", how="left")
    sheet["local_pdf_path"] = sheet["local_pdf_path"].replace("NOT_FOUND", "").fillna("")
    sheet = _blank_rater_cols(sheet.reindex(columns=BIB_COLS))
    for rater, seed in (("A", SEED), ("B", SEED + 1)):  # different order per rater
        _write_sheet(sheet, _sheet_path("ft", rater), seed)

    key = pd.read_csv(R1_FT_KEY)[["review_id", "ft_decision", "ft_matched_ic", "ft_matched_ec"]]
    key.to_csv(FT_KEY, index=False, encoding="utf-8")


def _aux_frames() -> dict[str, pd.DataFrame]:
    ta = pd.read_csv(AUX_TA)
    ft = pd.read_csv(AUX_FT)
    pend = pd.read_csv(AUX_PENDING)
    reft = pd.read_csv(AUX_REFT)
    reft_ids = set(reft["internal_id"])

    s1 = ta[ta["ta_decision"] == "exclude"]
    s2 = pd.concat([ft[ft["ft_decision"] == "exclude"], reft[reft["ft_decision"] == "exclude"]])
    s3 = pd.concat([pend[~pend["internal_id"].isin(reft_ids)], reft[reft["ft_decision"] == "pending"]])
    s0 = pd.concat([ft[ft["ft_decision"] == "include"], reft[reft["ft_decision"] == "include"]])
    frames = {"S1": s1, "S2": s2, "S3": s3, "S0": s0}
    return {k: v.drop_duplicates("internal_id")[["internal_id"]] for k, v in frames.items()}


def stratum_sizes() -> dict[str, int]:
    return {k: len(v) for k, v in _aux_frames().items()}


def _build_aux() -> None:
    papers = pd.read_csv(ALL_PAPERS, low_memory=False)
    papers = papers[papers["is_duplicate"].astype(str) != "True"].drop_duplicates("internal_id")
    # aux_pending_enriched carries abstracts recovered after the original export
    enriched = pd.concat([pd.read_csv(AUX_PENDING), pd.read_csv(AUX_REFT)])[["internal_id", "abstract"]]
    enriched = enriched.dropna(subset=["abstract"]).drop_duplicates("internal_id")

    picks = []
    for stratum, frame in _aux_frames().items():
        n = min(AUX_SAMPLE_SIZES[stratum], len(frame))
        s = frame.sample(n=n, random_state=SEED).copy()
        s["stratum"] = stratum
        s["rater_b"] = False
        s.loc[s.sample(frac=RATER_B_AUX_FRACTION, random_state=SEED).index, "rater_b"] = True
        picks.append(s)
    picks = pd.concat(picks, ignore_index=True)
    picks["review_id"] = [f"aux_{i:04d}" for i in range(len(picks))]

    sheet = picks.merge(papers, on="internal_id", how="left")
    sheet = sheet.merge(enriched.rename(columns={"abstract": "_abs2"}), on="internal_id", how="left")
    sheet["abstract"] = sheet["abstract"].where(sheet["abstract"].notna() & (sheet["abstract"].astype(str).str.strip() != ""),
                                                sheet["_abs2"])
    sheet["local_pdf_path"] = ""
    rater_b_ids = set(sheet.loc[sheet["rater_b"], "review_id"])
    sheet = _blank_rater_cols(sheet.reindex(columns=BIB_COLS))
    _write_sheet(sheet, _sheet_path("aux", "A"), SEED + 2)
    _write_sheet(sheet[sheet["review_id"].isin(rater_b_ids)], _sheet_path("aux", "B"), SEED + 3)

    picks[["review_id", "internal_id", "stratum", "rater_b"]].to_csv(AUX_KEY, index=False, encoding="utf-8")


def build_sheets() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    for p in [_sheet_path(s, r) for s in ("ft", "aux") for r in ("A", "B")]:
        if p.exists():
            raise FileExistsError(f"{p} exists — refusing to overwrite rater work")
    _build_ft()
    _build_aux()
    logger.info(f"stratum sizes: {stratum_sizes()}")


R1_OWN_FIELDS = ["human_ft_notes", "human_study_type", "human_pm_technique", "human_stochastic_technique",
                 "human_software_process", "human_dataset_source", "human_research_question",
                 "human_main_finding", "human_limitations", "human_qa_notes"]


def prefill_rater_a() -> None:
    """Append Rater A's own round-1 reading notes to his FT sheet (pre-registration deviation, 2026-10-06).

    Only fields Rater A wrote himself in round 1 are copied. The round-1 decision label
    (which encoded PDF availability) and anything produced by the LLM are not copied.
    Rater B's sheet is left untouched.
    """
    path = _sheet_path("ft", "A")
    sheet = pd.read_excel(path, dtype=str)
    if any(c.startswith("r1_") for c in sheet.columns):
        raise SystemExit(f"{path} already prefilled")
    if sheet[RATER_FIELDS].notna().any().any():
        raise SystemExit(f"{path} already has rater input — refusing to modify")
    r1 = pd.read_csv(R1_FT_SHEET, dtype=str)[["review_id"] + R1_OWN_FIELDS]
    r1 = r1.rename(columns={c: "r1_" + c.removeprefix("human_") for c in R1_OWN_FIELDS})
    out = sheet.merge(r1, on="review_id", how="left")  # left merge keeps the shuffled row order
    assert list(out["review_id"]) == list(sheet["review_id"])
    out.to_excel(path, index=False)
    filled = out["r1_study_type"].notna().sum()
    logger.info(f"prefilled {path}: R1 own notes on {filled}/{len(out)} rows")


# --------------------------------------------------------------------------- validate / consensus

def _read_rater(sample: str, rater: str) -> pd.DataFrame:
    df = pd.read_excel(_sheet_path(sample, rater), dtype=str).fillna("")
    for c in ("access_basis", "decision"):
        df[c] = df[c].str.strip().str.lower()
    return df


def _validate(df: pd.DataFrame, label: str) -> list[str]:
    errs = []
    for _, r in df.iterrows():
        rid = r["review_id"]
        if r["decision"] not in DECISION_VALUES:
            errs.append(f"{label} {rid}: decision '{r['decision']}' not in {sorted(DECISION_VALUES)}")
            continue
        if r["access_basis"] not in ACCESS_VALUES:
            errs.append(f"{label} {rid}: access_basis '{r['access_basis']}' not in {sorted(ACCESS_VALUES)}")
        if not r["justification"].strip():
            errs.append(f"{label} {rid}: justification is required")
        if r["decision"] == "include" and not r["ic_matched"].strip():
            errs.append(f"{label} {rid}: include requires ic_matched")
        if r["decision"] == "not_assessable" and r["access_basis"] != "not_accessible":
            errs.append(f"{label} {rid}: not_assessable requires access_basis=not_accessible")
        if r["decision"] != "not_assessable" and r["access_basis"] == "not_accessible":
            errs.append(f"{label} {rid}: access_basis=not_accessible requires decision=not_assessable")
    return errs


def build_consensus() -> None:
    errs = []
    sheets = {}
    for sample in ("ft", "aux"):
        for rater in ("A", "B"):
            df = _read_rater(sample, rater)
            errs += _validate(df, f"{sample}/{rater}")
            sheets[(sample, rater)] = df
    if errs:
        for e in errs:
            logger.error(e)
        raise SystemExit(f"{len(errs)} validation errors — fix the rater sheets first")

    rows = []
    for sample in ("ft", "aux"):
        a = sheets[(sample, "A")].set_index("review_id")
        b = sheets[(sample, "B")].set_index("review_id")
        for rid in a.index:
            da = a.at[rid, "decision"]
            db = b.at[rid, "decision"] if rid in b.index else ""
            agreed = db == "" or da == db
            rows.append({
                "sample": sample, "review_id": rid, "title": a.at[rid, "title"],
                "decision_A": da, "justification_A": a.at[rid, "justification"],
                "decision_B": db, "justification_B": b.at[rid, "justification"] if db else "",
                "needs_discussion": not agreed,
                "consensus_decision": da if agreed else "",
                "consensus_reason": "" if agreed else "",
            })
    out = pd.DataFrame(rows).sort_values(["needs_discussion", "sample", "review_id"], ascending=[False, True, True])
    if CONSENSUS.exists():
        raise FileExistsError(f"{CONSENSUS} exists — refusing to overwrite consensus work")
    out.to_excel(CONSENSUS, index=False)
    logger.info(f"consensus sheet: {CONSENSUS} ({int(out['needs_discussion'].sum())} disagreements to discuss)")


# --------------------------------------------------------------------------- compute

def _confusion(llm_pos: list[bool], ref_pos: list[bool]) -> dict:
    tp = sum(l and r for l, r in zip(llm_pos, ref_pos))
    fp = sum(l and not r for l, r in zip(llm_pos, ref_pos))
    fn = sum(r and not l for l, r in zip(llm_pos, ref_pos))
    tn = sum(not l and not r for l, r in zip(llm_pos, ref_pos))
    recall = tp / (tp + fn) if tp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "recall": recall,
            "ci": _wilson_ci(tp, tp + fn), "mcc": _mcc(tp, fp, fn, tn), "wmcc": _wmcc(tp, fp, fn, tn, 10)}


def _fmt(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def _cm_lines(name: str, cm: dict) -> list[str]:
    lo, hi = cm["ci"]
    verdict = "n/a" if cm["recall"] is None else ("PASS" if cm["recall"] >= RECALL_THRESHOLD else "FAIL")
    return [f"[{name}] TP={cm['tp']} FP={cm['fp']} FN={cm['fn']} TN={cm['tn']}",
            f"  Recall={_fmt(cm['recall'])}  95% Wilson CI=({_fmt(lo)}, {_fmt(hi)})  "
            f"threshold {RECALL_THRESHOLD:.2f}: {verdict}",
            f"  MCC={_fmt(cm['mcc'])}  WMCC(FN:FP=10:1)={_fmt(cm['wmcc'])}", ""]


def _kappa_line(name: str, y1, y2) -> str:
    k, info = _kappa(list(y1), list(y2))
    return f"  kappa {name}: {k:.3f} ({_interpret(k)}), Po={info['po']*100:.1f}%, n={info['n']}"


def compute() -> None:
    cons = pd.read_excel(CONSENSUS, dtype=str).fillna("")
    cons["consensus_decision"] = cons["consensus_decision"].str.strip().str.lower()
    missing = cons[~cons["consensus_decision"].isin(DECISION_VALUES)]
    if len(missing):
        raise SystemExit(f"{len(missing)} consensus rows without a valid consensus_decision")
    lines = ["Round-2 human validation report (pre-registered, see PREREGISTRATION_round2_validation.md)",
             "=" * 80, ""]

    # ---- FT working set
    ft = cons[cons["sample"] == "ft"].merge(pd.read_csv(FT_KEY, dtype=str), on="review_id")
    a, b = _read_rater("ft", "A").set_index("review_id"), _read_rater("ft", "B").set_index("review_id")
    ft["dA"], ft["dB"] = ft["review_id"].map(a["decision"]), ft["review_id"].map(b["decision"])
    lines.append(f"[FT working-set sample] n={len(ft)}")
    lines.append(_kappa_line("Rater A vs Rater B (pre-consensus)", ft["dA"], ft["dB"]))
    llm3 = ft["ft_decision"].str.lower()
    lines.append(_kappa_line("LLM vs Rater A", llm3, ft["dA"]))
    lines.append(_kappa_line("LLM vs Rater B", llm3, ft["dB"]))
    na = (ft["consensus_decision"] == "not_assessable").sum()
    lines.append(f"  not_assessable (excluded from Recall): {na}")
    lines.append("")
    assess = ft[ft["consensus_decision"] != "not_assessable"]
    cm_ft = _confusion((assess["ft_decision"].str.lower() == "include").tolist(),
                       (assess["consensus_decision"] == "include").tolist())
    lines += _cm_lines("FT — consensus reference (PRIMARY)", cm_ft)
    sens = ft[ft["dB"] != "not_assessable"]
    lines += _cm_lines("FT — Rater B only (sensitivity)",
                       _confusion((sens["ft_decision"].str.lower() == "include").tolist(),
                                  (sens["dB"] == "include").tolist()))
    fn_rows = assess[(assess["consensus_decision"] == "include") & (assess["ft_decision"].str.lower() != "include")]
    lines.append(f"  FN records (consensus include, LLM non-include): {', '.join(fn_rows['review_id']) or 'none'}")
    lines.append("")

    # ---- auxiliary tier
    aux = cons[cons["sample"] == "aux"].merge(pd.read_csv(AUX_KEY, dtype=str), on="review_id")
    sizes = stratum_sizes()
    i_aux = sizes["S0"]
    missed = 0.0
    lines.append(f"[Auxiliary tier] stratum sizes: {sizes}")
    for s in ("S1", "S2", "S3"):
        d = aux[(aux["stratum"] == s) & (aux["consensus_decision"] != "not_assessable")]
        k = int((d["consensus_decision"] == "include").sum())
        p = k / len(d) if len(d) else 0.0
        lo, hi = _wilson_ci(k, len(d)) if len(d) else (None, None)
        missed += sizes[s] * p
        lines.append(f"  {s}: {k}/{len(d)} assessable judged include  p={p:.3f} CI=({_fmt(lo)}, {_fmt(hi)})  "
                     f"est. missed={sizes[s] * p:.1f}  (not_assessable={int((aux['stratum'].eq(s) & aux['consensus_decision'].eq('not_assessable')).sum())})")
    aux_recall = i_aux / (i_aux + missed)
    lines.append(f"  Auxiliary Recall = {i_aux}/({i_aux}+{missed:.1f}) = {aux_recall:.3f}  "
                 f"threshold {RECALL_THRESHOLD:.2f}: {'PASS' if aux_recall >= RECALL_THRESHOLD else 'FAIL'}")
    s0 = aux[(aux["stratum"] == "S0") & (aux["consensus_decision"] != "not_assessable")]
    lines.append(f"  S0 decoys (LLM includes) judged include: {(s0['consensus_decision'] == 'include').sum()}/{len(s0)} (descriptive precision)")
    ab = aux[aux["rater_b"] == "True"]
    if len(ab):
        aa = _read_rater("aux", "A").set_index("review_id")["decision"]
        bb = _read_rater("aux", "B").set_index("review_id")["decision"]
        lines.append(_kappa_line("aux Rater A vs Rater B", ab["review_id"].map(aa), ab["review_id"].map(bb)))
    new_inc = aux[(aux["stratum"] != "S0") & (aux["consensus_decision"] == "include")]
    lines.append(f"  Records to ADD to the corpus (consensus include among LLM non-includes): "
                 f"{', '.join(new_inc['internal_id']) or 'none'}")
    lines.append("")
    lines.append("Escalation (pre-registered §4): "
                 f"E1 {'NOT triggered' if (cm_ft['recall'] or 0) >= RECALL_THRESHOLD else 'TRIGGERED'}; "
                 f"E2 {'NOT triggered' if aux_recall >= RECALL_THRESHOLD else 'TRIGGERED'}")

    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")
    lo, hi = cm_ft["ci"]
    REPORT_TEX.write_text(
        "FT (working set) & {tp} & {fp} & {fn} & {tn} & {r} & ({lo}, {hi}) & {le} & {mcc} & {wmcc} \\\\\n".format(
            tp=cm_ft["tp"], fp=cm_ft["fp"], fn=cm_ft["fn"], tn=cm_ft["tn"], r=_fmt(cm_ft["recall"]),
            lo=_fmt(lo), hi=_fmt(hi), le=_fmt(None if cm_ft["recall"] is None else 1 - cm_ft["recall"]),
            mcc=_fmt(cm_ft["mcc"]), wmcc=_fmt(cm_ft["wmcc"])),
        encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build-sheets", action="store_true")
    g.add_argument("--prefill-rater-a", action="store_true")
    g.add_argument("--build-consensus", action="store_true")
    g.add_argument("--compute", action="store_true")
    args = ap.parse_args()
    if args.build_sheets:
        build_sheets()
    elif args.prefill_rater_a:
        prefill_rater_a()
    elif args.build_consensus:
        build_consensus()
    else:
        compute()


if __name__ == "__main__":
    main()
