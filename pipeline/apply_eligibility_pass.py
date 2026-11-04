"""Eligibility pass on the 168 studies added after the human re-screen.

The published matrix labelled 63 added studies "none of the four" even when
the extraction already named a technique. This pass:

- removes records that fail IC1, EC1, or EC2, or that have no IC4a--d signal;
- assigns TF-PM / TF-ST / TF-FC / TF-MSR to the rest, from the extraction;
- rewrites the included-study list and the appendix matrix.

The 338 coded-set rows are not recoded. F1--F5 on the 169 and 318 cuts are
not recomputed.
"""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INC_PATH = ROOT / "results/final_review/included_studies_506.csv"
FAM_PATH = ROOT / "results/final_review/family_codes_168.csv"
EXT_PATH = ROOT / "results/auxiliary/extraction_round2_188.csv"
DECISION_PATH = ROOT / "results/final_review/corpus_eligibility_pass.csv"
MATRIX_PATHS = [
    ROOT / "article_ist/overleaf_package/results/included_506_matrix.tex",
    ROOT / "results/included_506_matrix.tex",
]
# Per-study identifier list (Supplementary Material S1), written separately so the
# main PDF carries only the classification matrix.
LIST_PATHS = [
    ROOT / "article_ist/overleaf_package/results/included_506_list.tex",
    ROOT / "results/included_506_list.tex",
]

# Records removed even if a technique token is present.
HARD = {
    "46815264": "IC1: year 1992, before 1 January 1994",
    "d327f361": "EC1: chemical separation; the software is the simulator",
    "bc9498ef": "EC1: basin stability of dynamical systems, not a software process",
    "58c1d91f": "EC2: Monte Carlo for quantum lattice models; software is the platform",
    "b9ea47c3": "EC1: abstract is a biochemical master equation, not a software process",
    "be4c9529": "EC2: time Petri nets for a robot controller, not an SDLC process",
    "5ee71dfd": "EC2: response-time module for the PIPE tool, no software-development process",
    "70af59ef": "EC2: UML model performance, not a software-development process",
    "227a76af": "EC1: clones of business-process models on GitHub, not an SDLC process",
    "780b3d58": "EC1: hospital and store workflow logs, not a software-development process",
    "b618e568": "out of scope: learner behaviour in a design tutor, not an SDLC process",
    "a6c6358f": "no IC4 technique applied: practitioner survey of challenge categories",
}

# Conformance of a development practice whose pm_technique cell was left empty.
FORCE_KEEP = {
    "b78523e4": ["TF-PM"],
}

NAMED_ST = {"markov_chain", "monte_carlo", "stochastic_petri_net", "system_dynamics"}
REPO = {"github", "gitlab", "jira", "commits", "ci_cd", "issues", "vcs", "bugzilla"}
ORDER = ["TF-PM", "TF-ST", "TF-FC", "TF-MSR"]
TO_IC = {"TF-PM": "IC1", "TF-ST": "IC2", "TF-FC": "IC3", "TF-MSR": "IC4"}
FROM_IC = {v: k for k, v in TO_IC.items()}


def tokens(value: str) -> list[str]:
    out = []
    for part in (value or "").replace("|", ",").split(","):
        part = part.strip()
        if part and part not in {"none", "não_mencionado", "nao_mencionado", "not_specified"}:
            out.append(part)
    return out


def canonical(flags: list[str]) -> str:
    return "|".join(flag for flag in ORDER if flag in flags)


def from_legacy_ic(ic: str) -> str:
    flags = []
    for part in (ic or "").split("|"):
        part = part.strip()
        if part in FROM_IC:
            flags.append(FROM_IC[part])
    return canonical(flags)


def to_legacy_ic(pattern: str) -> str:
    return "|".join(TO_IC[flag] for flag in pattern.split("|") if flag in TO_IC)


def decide(row: dict, extraction: dict) -> tuple[str, str, str]:
    """Return (decision, pattern, reason). pattern is empty when excluded."""
    ident = row["internal_id"]
    if ident in HARD:
        return "exclude", "", HARD[ident]
    if ident in FORCE_KEEP:
        pattern = canonical(FORCE_KEEP[ident])
        return "keep", pattern, "conformance of a development practice (TDD); pm cell had been left empty"
    pm = tokens(extraction["pm_technique"])
    st = tokens(extraction["stochastic_technique"])
    art = set(tokens(extraction["software_artifact"]))
    contrib = set(tokens(extraction["research_contribution"]))
    process = extraction.get("software_process") or ""
    tf_pm = bool(pm)
    tf_st = bool(set(st) & NAMED_ST) or ("other" in st)
    tf_fc = ("prediction" in contrib) and (
        tf_st or bool(art & REPO) or any(p in process for p in ("bug_fixing", "testing", "deployment"))
    )
    tf_msr = bool(art & REPO)
    flags = []
    if tf_pm:
        flags.append("TF-PM")
    if tf_st:
        flags.append("TF-ST")
    if tf_fc:
        flags.append("TF-FC")
    if tf_msr:
        flags.append("TF-MSR")
    pattern = canonical(flags)
    if not pattern:
        return "exclude", "", "no IC4a–d signal in the extraction"
    reason = (
        f"pm={extraction['pm_technique']}; st={extraction['stochastic_technique']}; "
        f"contrib={extraction['research_contribution']}; art={extraction['software_artifact']}"
    )
    return "keep", pattern, reason


def tex_pattern(pattern: str) -> str:
    if pattern == "BLANK":
        return "title only, marks blank"
    return pattern.replace("|", r"$\mid$")


def write_matrix(included: list[dict], patterns: dict[str, str]) -> None:
    coded = [r for r in included if r["corpus_role"] == "original_coded"]
    added = [r for r in included if r["corpus_role"] != "original_coded"]
    text_added = [r for r in added if patterns[r["internal_id"]] != "BLANK"]
    title_added = [r for r in added if patterns[r["internal_id"]] == "BLANK"]
    n_coded, n_text, n_title = len(coded), len(text_added), len(title_added)
    n_all = len(included)

    counts: Counter[str] = Counter()
    for row in coded:
        counts[(patterns[row["internal_id"]], "coded")] += 1
    for row in text_added:
        counts[(patterns[row["internal_id"]], "text")] += 1
    counts[("BLANK", "title")] = n_title

    keys = sorted(
        {key for key, _ in counts},
        key=lambda key: (
            -sum(counts[(key, col)] for col in ("coded", "text", "title")),
            key,
        ),
    )

    lines = [
        "% Auto-generated by pipeline/apply_eligibility_pass.py",
        "% Family labels are TF-PM, TF-ST, TF-FC, TF-MSR (IC4a--IC4d).",
        r"\begin{table}[htbp]",
        r"\centering",
        (
            r"\caption{Classification of the %d studies. "
            r"TF-PM is process mining (IC4a), TF-ST a stochastic model (IC4b), "
            r"TF-FC forecasting (IC4c), and TF-MSR repository mining (IC4d). "
            r"The %d use the codes already stored for that set. "
            r"The %d are the added studies read from an abstract or a PDF that meet at least one content criterion. "
            r"The %d title-only studies have no family mark.}"
        ) % (n_all, n_coded, n_text, n_title),
        r"\label{tab:class-matrix}",
        r"\small",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        (
            r"\textbf{Family pattern} & \textbf{%d} & \textbf{%d} & \textbf{%d} \\"
            % (n_coded, n_text, n_title)
        ),
        r"\midrule",
    ]
    for key in keys:
        c = counts[(key, "coded")] or "--"
        t = counts[(key, "text")] or "--"
        b = counts[(key, "title")] or "--"
        # title-only is not a pattern of the first two columns
        if key == "BLANK":
            c, t = "--", "--"
        lines.append(f"{tex_pattern(key)} & {c} & {t} & {b} \\\\")
    lines += [
        r"\midrule",
        rf"\textbf{{Total}} & \textbf{{{n_coded}}} & \textbf{{{n_text}}} & \textbf{{{n_title}}} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    matrix_text = "\n".join(lines)
    lines = [
        "% Auto-generated by pipeline/apply_eligibility_pass.py",
        "% Per-study identifier list (Supplementary Material S1).",
        r"\begingroup",
        r"\footnotesize",
        r"\begin{longtable}{p{1.8cm}rp{2.4cm}p{5.2cm}}",
        (
            r"\caption{Identifier list of the %d studies. "
            r"The family pattern is the one counted in the classification matrix of the main text.}"
            r"\label{tab:included-506}\\" % n_all
        ),
        r"\toprule",
        r"\textbf{Identifier} & \textbf{Year} & \textbf{Role} & \textbf{Family pattern} \\",
        r"\midrule",
        r"\endfirsthead",
        r"\multicolumn{4}{l}{\tablename\ \thetable{} -- continued}\\",
        r"\toprule",
        r"\textbf{Identifier} & \textbf{Year} & \textbf{Role} & \textbf{Family pattern} \\",
        r"\midrule",
        r"\endhead",
    ]

    def sort_key(row: dict) -> tuple:
        role_rank = 0 if row["corpus_role"] == "original_coded" else 1
        year = int(row["year"]) if str(row["year"]).isdigit() else 0
        return (role_rank, year, row["internal_id"])

    for row in sorted(included, key=sort_key):
        role = "coded set" if row["corpus_role"] == "original_coded" else "added"
        lines.append(
            rf"\texttt{{{row['internal_id']}}} & {row['year']} & {role} & {tex_pattern(patterns[row['internal_id']])} \\"
        )
    lines += [r"\bottomrule", r"\end{longtable}", r"\endgroup", ""]
    list_text = "\n".join(lines)
    for path in MATRIX_PATHS:
        path.write_text(matrix_text, encoding="utf-8")
    for path in LIST_PATHS:
        path.write_text(list_text, encoding="utf-8")


def main() -> None:
    included = list(csv.DictReader(INC_PATH.open(encoding="utf-8")))
    families = list(csv.DictReader(FAM_PATH.open(encoding="utf-8")))
    extraction = {
        row["internal_id"]: row
        for row in csv.DictReader(EXT_PATH.open(encoding="utf-8"))
    }
    fam_by_id = {row["internal_id"]: row for row in families}

    blank_ids = []
    for row in families:
        if row["evidence_basis"] == "title_only":
            continue
        if not (row.get("ic") or "").strip():
            blank_ids.append(row["internal_id"])

    decisions = []
    keep_pattern = {}
    exclude_ids = set()
    for ident in blank_ids:
        decision, pattern, reason = decide(fam_by_id[ident], extraction[ident])
        title = extraction[ident]["title"]
        year = extraction[ident]["year"]
        decisions.append({
            "internal_id": ident,
            "decision": decision,
            "tf_pattern": pattern,
            "reason": reason,
            "year": year,
            "title": title,
            "evidence_basis": fam_by_id[ident]["evidence_basis"],
        })
        if decision == "exclude":
            exclude_ids.add(ident)
        else:
            keep_pattern[ident] = pattern

    # IC1 failure that was title-only, so it never entered the blank-family list.
    if "46815264" in fam_by_id and "46815264" not in exclude_ids:
        exclude_ids.add("46815264")
        src = next(row for row in included if row["internal_id"] == "46815264")
        decisions.append({
            "internal_id": "46815264",
            "decision": "exclude",
            "tf_pattern": "",
            "reason": HARD["46815264"],
            "year": src["year"],
            "title": src["title"],
            "evidence_basis": "title_only",
        })

    with DECISION_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0].keys()))
        writer.writeheader()
        writer.writerows(decisions)

    for ident, pattern in keep_pattern.items():
        fam = fam_by_id[ident]
        flags = set(pattern.split("|"))
        fam["TF_PM"] = "sim" if "TF-PM" in flags else "não"
        fam["TF_ST"] = "sim" if "TF-ST" in flags else "não"
        fam["TF_FC"] = "sim" if "TF-FC" in flags else "não"
        fam["TF_MSR"] = "sim" if "TF-MSR" in flags else "não"
        fam["ic"] = to_legacy_ic(pattern)
        fam["evidence_sentence"] = pattern + ". " + next(
            row["reason"] for row in decisions if row["internal_id"] == ident
        )

    kept_included = []
    for row in included:
        if row["internal_id"] in exclude_ids:
            continue
        if row["internal_id"] in keep_pattern:
            row["ic"] = to_legacy_ic(keep_pattern[row["internal_id"]])
        kept_included.append(row)
    for seq, row in enumerate(kept_included, start=1):
        row["seq"] = str(seq)

    kept_families = [row for row in families if row["internal_id"] not in exclude_ids]

    inc_fields = list(included[0].keys())
    with INC_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=inc_fields)
        writer.writeheader()
        writer.writerows(kept_included)
    fam_fields = list(families[0].keys())
    with FAM_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fam_fields)
        writer.writeheader()
        writer.writerows(kept_families)

    patterns = {}
    for row in kept_included:
        ident = row["internal_id"]
        if row["corpus_role"] == "original_coded":
            patterns[ident] = from_legacy_ic(row["ic"])
        elif ident in keep_pattern:
            patterns[ident] = keep_pattern[ident]
        else:
            fam = fam_by_id.get(ident)
            if fam and fam["evidence_basis"] == "title_only":
                patterns[ident] = "BLANK"
            elif fam and (fam.get("ic") or "").strip():
                patterns[ident] = from_legacy_ic(fam["ic"])
            else:
                patterns[ident] = "BLANK"
    write_matrix(kept_included, patterns)

    added = [row for row in kept_included if row["corpus_role"] != "original_coded"]
    basis = Counter(row["evidence_basis"] for row in added)
    scored = 0
    for row in added:
        try:
            if float(row["qa_total"]) >= 4:
                scored += 1
        except ValueError:
            pass
    triples = sum(1 for pattern in patterns.values() if set(pattern.split("|")) >= {"TF-PM", "TF-ST", "TF-FC"})
    print("excluded", len(exclude_ids))
    print("corpus", len(kept_included))
    print("added", len(added), dict(basis))
    print("qa>=4 among added", scored)
    print("triples", triples)
    print("decisions", Counter(row["decision"] for row in decisions))


if __name__ == "__main__":
    main()
