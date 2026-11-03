"""Option B — risk-directed human re-read of the family codes (L1 -> L2/L3 audit).

Scope. Every study in the coded set (the 306 that remain from the 338) whose
model-assigned family codes carry at least two of the three *technique*
families (TF-PM, TF-ST, TF-FC) is one family away from L2 or, for the single
L2 study, from L3. These are the studies where a single under-coded family
would change the central claim of the article ("no study identified in this
review reaches L3"). The 74 studies added in this revision were coded by the
authors and are out of scope.

Usage
-----
    python -m pipeline.family_code_audit build
        -> results/family_code_audit/l1_audit_sheet.csv (+ .xlsx if openpyxl)
           results/family_code_audit/l1_audit_sheet_META.json

    python -m pipeline.family_code_audit recompute
        -> reads the filled sheet, applies the consensus verdicts, recomputes
           L0-L3 and the pairwise/triple intersections on WS-151, the 293 joint
           cut and the 380, and writes
           results/family_code_audit/audit_report.txt
           results/family_code_audit/audit_report.tex

The verdict columns are filled by humans. Nothing in this module calls an LLM.

Decision rule (fixed before the reading starts, see README.md):
  * third_family_present in {yes, no, not_assessable}; 'yes' requires a
    quoted evidence span from the abstract or the PDF.
  * For the L2 study, l3_end_to_end in {yes, no, not_assessable}; 'yes'
    requires that the three families are coupled through explicit interfaces
    AND evaluated end-to-end as one pipeline on SDLC event data.
  * Rater B reads a fixed 30% random subset (seed 20261101). Disagreements go
    to consensus; the consensus column is what recompute uses. Where Rater B
    did not read, Rater A's verdict is the consensus.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "results/final_review/included_studies_506.csv"
EXTRACTION = ROOT / "results/auxiliary/extraction_combined_381_dedup.csv"
ABSTRACT_SOURCES = [
    ROOT / "results/auxiliary/extraction_combined_381_dedup.csv",
    ROOT / "results/screening/ft_screening_results.csv",
    ROOT / "results/auxiliary/aux_ta_screened.csv",
    ROOT / "results/auxiliary/aux_reft_enriched.csv",
    ROOT / "results/unique_papers.csv",
]
PDF_DIRS = [
    ROOT / "results/pdfs",
    ROOT / "results/auxiliary/pdfs",
    ROOT / "results/final_review/top30_pdfs",
]
OUT_DIR = ROOT / "results/family_code_audit"
SHEET = OUT_DIR / "l1_audit_sheet.csv"
META = OUT_DIR / "l1_audit_sheet_META.json"
REPORT_TXT = OUT_DIR / "audit_report.txt"
REPORT_TEX = OUT_DIR / "audit_report.tex"

RATER_B_SEED = 20261101
RATER_B_SHARE = 0.30

FAMILY_OF_IC = {"IC1": "PM", "IC2": "ST", "IC3": "FC", "IC4": "MSR"}
TECH = ("PM", "ST", "FC")
TEX_NAME = {"PM": "TF-PM", "ST": "TF-ST", "FC": "TF-FC"}

VERDICTS = {"yes", "no", "not_assessable", ""}


def _read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def families(ic: str) -> set[str]:
    out = set()
    for tok in (ic or "").split("|"):
        tok = tok.strip()
        for prefix, fam in FAMILY_OF_IC.items():
            if tok.startswith(prefix):
                out.add(fam)
    return out


def tech_families(ic: str) -> set[str]:
    return families(ic) & set(TECH)


def level(fams: set[str], l3: bool = False) -> str:
    n = len(fams & set(TECH))
    if n == 3:
        return "L3" if l3 else "L2"
    if n == 2:
        return "L1"
    return "L0"


def _abstract_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for src in ABSTRACT_SOURCES:
        if not src.exists():
            continue
        for r in _read(src):
            iid = (r.get("internal_id") or "").strip()
            ab = (r.get("abstract") or "").strip()
            if iid and ab and iid not in idx:
                idx[iid] = ab
    return idx


def _pdf_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for d in PDF_DIRS:
        if not d.exists():
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".pdf"):
                m = re.match(r"([0-9a-f]{8})", f)
                if m and m.group(1) not in idx:
                    idx[m.group(1)] = str((d / f).relative_to(ROOT))
    # manifest of the working-set download pass (maps id -> file)
    man = ROOT / "results/pdfs/download_manifest.csv"
    if man.exists():
        for r in _read(man):
            iid = (r.get("internal_id") or "").strip()
            f = (r.get("pdf_file") or "").strip()
            if iid and f and iid not in idx and (ROOT / "results/pdfs" / Path(f).name).exists():
                idx[iid] = str(Path("results/pdfs") / Path(f).name)
    return idx


def build() -> None:
    corpus = _read(CORPUS)
    ext = {r["internal_id"]: r for r in _read(EXTRACTION)}
    abstracts = _abstract_index()
    pdfs = _pdf_index()

    coded = [r for r in corpus if r.get("corpus_role") == "original_coded"]
    cands = [r for r in coded if len(tech_families(r["ic"])) >= 2]
    cands.sort(key=lambda r: (r.get("origin") != "WS", int(r["year"] or 0), r["title"].lower()))

    rng = random.Random(RATER_B_SEED)
    n_b = round(RATER_B_SHARE * len(cands))
    b_ids = set(rng.sample([r["internal_id"] for r in cands], n_b))

    rows = []
    for i, r in enumerate(cands, 1):
        fams = tech_families(r["ic"])
        missing = sorted(set(TECH) - fams)
        e = ext.get(r["internal_id"], {})
        rows.append({
            "seq": i,
            "internal_id": r["internal_id"],
            "tier": "WS-151" if r.get("origin") == "WS" else "Aux (293)",
            "in_extraction_318": "yes" if r["internal_id"] in ext else "no",
            "year": r["year"],
            "authors": r.get("authors", ""),
            "title": r["title"],
            "doi": r.get("doi", ""),
            "source_db": r.get("source_db", ""),
            "current_ic": r["ic"],
            "current_families": "|".join(TEX_NAME[f] for f in sorted(fams, key=TECH.index)),
            "current_level": level(fams),
            "family_to_check": TEX_NAME[missing[0]] if missing else "L3 (end-to-end coupling)",
            "question": (
                f"Does the study ALSO apply {TEX_NAME[missing[0]]}? "
                + {
                    "PM": "(process discovery / conformance / enhancement from event logs)",
                    "ST": "(Markov chain, stochastic Petri net, Monte Carlo, queueing or other explicitly stochastic model)",
                    "FC": "(prediction/forecast of a process metric: duration, remaining time, lead/cycle time, delay, throughput, outcome)",
                }[missing[0]]
                if missing else
                "Are TF-PM, TF-ST and TF-FC coupled through explicit interfaces AND evaluated end-to-end as ONE pipeline on SDLC event data?"
            ),
            "pdf_available": "yes" if r["internal_id"] in pdfs else "no",
            "pdf_path": pdfs.get(r["internal_id"], ""),
            "abstract": abstracts.get(r["internal_id"], ""),
            "hint_pm_technique": e.get("pm_technique", ""),
            "hint_stochastic_technique": e.get("stochastic_technique", ""),
            "hint_research_contribution": e.get("research_contribution", ""),
            "rater_B_required": "yes" if r["internal_id"] in b_ids else "no",
            # ---- to be filled by humans ----
            "A_evidence_basis": "",          # abstract | pdf
            "A_third_family_present": "",    # yes | no | not_assessable
            "A_l3_end_to_end": "",           # only for the L2 row: yes | no | not_assessable
            "A_evidence_quote": "",
            "A_notes": "",
            "B_evidence_basis": "",
            "B_third_family_present": "",
            "B_l3_end_to_end": "",
            "B_evidence_quote": "",
            "B_notes": "",
            "consensus_third_family_present": "",
            "consensus_l3_end_to_end": "",
            "consensus_notes": "",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SHEET, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    meta = {
        "built_from": {"corpus": str(CORPUS.relative_to(ROOT)), "extraction": str(EXTRACTION.relative_to(ROOT))},
        "coded_set_n": len(coded),
        "candidates_n": len(rows),
        "by_tier": dict(Counter(r["tier"] for r in rows)),
        "by_current_level": dict(Counter(r["current_level"] for r in rows)),
        "by_family_to_check": dict(Counter(r["family_to_check"] for r in rows)),
        "with_pdf": sum(1 for r in rows if r["pdf_available"] == "yes"),
        "with_abstract": sum(1 for r in rows if r["abstract"]),
        "rater_B_seed": RATER_B_SEED,
        "rater_B_share": RATER_B_SHARE,
        "rater_B_n": n_b,
    }
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    try:
        import pandas as pd  # optional
        pd.DataFrame(rows).to_excel(SHEET.with_suffix(".xlsx"), index=False)
    except Exception as exc:  # pragma: no cover
        print(f"[audit] xlsx not written ({exc.__class__.__name__}); CSV is the canonical sheet", file=sys.stderr)

    print(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"[audit] sheet -> {SHEET.relative_to(ROOT)}")


# --------------------------------------------------------------------------- #
def _consensus(row: dict, col: str) -> str:
    c = (row.get(f"consensus_{col}") or "").strip().lower()
    if c:
        return c
    a = (row.get(f"A_{col}") or "").strip().lower()
    b = (row.get(f"B_{col}") or "").strip().lower()
    if row.get("rater_B_required") == "yes" and b and a and a != b:
        return "CONFLICT"
    return a


def recompute() -> None:
    if not SHEET.exists():
        sys.exit("sheet not found; run `build` first")
    sheet = _read(SHEET)
    corpus = _read(CORPUS)
    ext_ids = {r["internal_id"] for r in _read(EXTRACTION)}

    # --- completeness and agreement -------------------------------------
    problems, conflicts = [], []
    kappa_pairs = []
    for r in sheet:
        for col in ("A_third_family_present", "B_third_family_present", "A_l3_end_to_end", "B_l3_end_to_end",
                    "consensus_third_family_present", "consensus_l3_end_to_end"):
            if (r.get(col) or "").strip().lower() not in VERDICTS:
                problems.append(f"{r['internal_id']}: invalid value in {col}: {r[col]!r}")
        is_l2 = r["current_level"] == "L2"
        col = "l3_end_to_end" if is_l2 else "third_family_present"
        if not (r.get(f"A_{col}") or "").strip():
            problems.append(f"{r['internal_id']}: Rater A verdict missing ({col})")
        if r.get("rater_B_required") == "yes":
            if not (r.get(f"B_{col}") or "").strip():
                problems.append(f"{r['internal_id']}: Rater B verdict missing ({col})")
            else:
                kappa_pairs.append(((r.get(f"A_{col}") or "").lower(), (r.get(f"B_{col}") or "").lower()))
        v = _consensus(r, col)
        if v == "CONFLICT":
            conflicts.append(r["internal_id"])
        if v == "yes" and not (r.get("consensus_notes") or r.get("A_evidence_quote") or "").strip():
            problems.append(f"{r['internal_id']}: 'yes' without an evidence quote")

    kappa = None
    if kappa_pairs:
        po = sum(1 for a, b in kappa_pairs if a == b) / len(kappa_pairs)
        try:
            from pipeline.kappa import _kappa  # type: ignore
            kappa = _kappa([a for a, _ in kappa_pairs], [b for _, b in kappa_pairs])
            if isinstance(kappa, tuple):
                kappa = kappa[0]
            import math
            if isinstance(kappa, float) and (math.isnan(kappa) or math.isinf(kappa)):
                # Pe=1 when both raters use a single category → κ undefined
                kappa = f"undef (Po={po:.3f})"
        except Exception:
            kappa = f"Po={po:.3f} (kappa helper unavailable)"

    # --- apply verdicts --------------------------------------------------
    verdict = {r["internal_id"]: r for r in sheet}
    fam_of: dict[str, set[str]] = {}
    l3_of: dict[str, bool] = {}
    changes = []
    for r in corpus:
        fams = tech_families(r["ic"])
        l3 = False
        v = verdict.get(r["internal_id"])
        if v:
            is_l2 = v["current_level"] == "L2"
            if is_l2:
                l3 = _consensus(v, "l3_end_to_end") == "yes"
                if l3:
                    changes.append((r["internal_id"], "L2 -> L3"))
            else:
                if _consensus(v, "third_family_present") == "yes":
                    missing = {"TF-PM": "PM", "TF-ST": "ST", "TF-FC": "FC"}[v["family_to_check"]]
                    fams = fams | {missing}
                    changes.append((r["internal_id"], f"L1 -> L2 (+{v['family_to_check']})"))
        fam_of[r["internal_id"]] = fams
        l3_of[r["internal_id"]] = l3

    def stats(ids: list[str]) -> dict:
        f = [fam_of[i] for i in ids]
        n = len(ids)
        d = {
            "n": n,
            "PM": sum("PM" in x for x in f), "ST": sum("ST" in x for x in f), "FC": sum("FC" in x for x in f),
            "PM&ST": sum({"PM", "ST"} <= x for x in f), "PM&FC": sum({"PM", "FC"} <= x for x in f),
            "ST&FC": sum({"ST", "FC"} <= x for x in f), "triple": sum({"PM", "ST", "FC"} <= x for x in f),
        }
        lv = Counter(level(x, l3_of[i]) for i, x in zip(ids, f))
        d.update({k: lv.get(k, 0) for k in ("L0", "L1", "L2", "L3")})
        return d

    coded = [r for r in corpus if r["corpus_role"] == "original_coded"]
    ws = [r["internal_id"] for r in coded if r["origin"] == "WS"]
    joint = [r["internal_id"] for r in coded if r["internal_id"] in ext_ids]
    marked = [r["internal_id"] for r in corpus if families(r["ic"])]  # the 380

    res = {"WS-151": stats(ws), "joint-293": stats(joint), "marked-380": stats(marked)}

    lines = ["Family-code audit (Option B) — recompute", "=" * 60,
             f"sheet rows: {len(sheet)} | Rater B pairs: {len(kappa_pairs)} | kappa A vs B: {kappa}",
             f"conflicts awaiting consensus: {len(conflicts)} {conflicts[:10]}",
             f"problems: {len(problems)}"]
    lines += [f"  - {p}" for p in problems[:40]]
    lines += ["", "changes applied:"] + ([f"  {i}: {c}" for i, c in changes] or ["  none"])
    lines += [""]
    for cut, d in res.items():
        lines.append(f"[{cut}] n={d['n']} PM={d['PM']} ST={d['ST']} FC={d['FC']} | PM&ST={d['PM&ST']} PM&FC={d['PM&FC']} "
                     f"ST&FC={d['ST&FC']} triple={d['triple']} | L0/L1/L2/L3={d['L0']}/{d['L1']}/{d['L2']}/{d['L3']}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    n_read = sum(1 for r in sheet if (r.get("A_third_family_present") or r.get("A_l3_end_to_end") or "").strip())
    n_pdf = sum(1 for r in sheet if (r.get("A_evidence_basis") or "").strip().lower() == "pdf")
    n_yes = sum(1 for i, c in changes if c.startswith("L1"))
    tex = (
        "% auto-generated by pipeline/family_code_audit.py recompute\n"
        f"\\newcommand{{\\auditN}}{{{len(sheet)}}}\n"
        f"\\newcommand{{\\auditRead}}{{{n_read}}}\n"
        f"\\newcommand{{\\auditPdf}}{{{n_pdf}}}\n"
        f"\\newcommand{{\\auditMovedToLtwo}}{{{n_yes}}}\n"
        f"\\newcommand{{\\auditLthree}}{{{res['marked-380']['L3']}}}\n"
        f"\\newcommand{{\\auditKappa}}{{{kappa if isinstance(kappa, str) else (f'{kappa:.3f}' if kappa is not None else 'n/a')}}}\n"
    )
    REPORT_TEX.write_text(tex, encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[audit] report -> {REPORT_TXT.relative_to(ROOT)} ; macros -> {REPORT_TEX.relative_to(ROOT)}")
    if problems or conflicts:
        sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["build", "recompute"])
    args = ap.parse_args()
    {"build": build, "recompute": recompute}[args.cmd]()


if __name__ == "__main__":
    main()
