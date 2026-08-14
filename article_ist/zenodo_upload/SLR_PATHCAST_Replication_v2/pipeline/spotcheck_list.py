"""Build a prioritized disagreement list for human spot-check.

Picks papers from the working-set and auxiliary κ samples where the LLM
screener and LLM verifier disagreed on the final binary outcome
(include vs not-include). Outputs a single CSV with rationale columns
prepared for a senior researcher to fill in.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

OUT_CSV = Path("results/spotcheck/disagreement_list_for_human.csv")
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)


def _bin(d: str) -> str:
    return "include" if str(d).strip().lower() == "include" else "not_include"


def collect():
    rows = []

    # Working-set T/A
    p = Path("results/kappa/ta_rescreen_sonnet.csv")
    if p.exists():
        df = pd.read_csv(p)
        df["primary_b"] = df["ta_decision_primary"].fillna("").apply(_bin)
        df["verifier_b"] = df["ta_decision_verifier"].fillna("").apply(_bin)
        dis = df[df["primary_b"] != df["verifier_b"]].copy()
        dis["stage"] = "ws_TA"
        for _, r in dis.iterrows():
            rows.append({
                "stage": "ws_TA",
                "internal_id": r.get("internal_id", ""),
                "title": str(r.get("title", ""))[:200],
                "doi": r.get("doi", ""),
                "primary_decision": r.get("ta_decision_primary", ""),
                "verifier_decision": r.get("ta_decision_verifier", ""),
                "binary_disagreement": f"{r['primary_b']} vs {r['verifier_b']}",
            })

    # Working-set FT
    p = Path("results/kappa/ft_rescreen_sonnet.csv")
    if p.exists():
        df = pd.read_csv(p)
        df["primary_b"] = df["ft_decision_primary"].fillna("").apply(_bin)
        df["verifier_b"] = df["ft_decision_verifier"].fillna("").apply(_bin)
        dis = df[df["primary_b"] != df["verifier_b"]].copy()
        for _, r in dis.iterrows():
            rows.append({
                "stage": "ws_FT",
                "internal_id": r.get("internal_id", ""),
                "title": str(r.get("title", ""))[:200],
                "doi": r.get("doi", ""),
                "primary_decision": r.get("ft_decision_primary", ""),
                "verifier_decision": r.get("ft_decision_verifier", ""),
                "binary_disagreement": f"{r['primary_b']} vs {r['verifier_b']}",
            })

    # Aux FT
    p = Path("results/auxiliary/kappa/aux_ft_rescreen_sonnet.csv")
    if p.exists():
        df = pd.read_csv(p)
        df["primary_b"] = df["ft_decision_primary"].fillna("").apply(_bin)
        df["verifier_b"] = df["ft_decision_verifier"].fillna("").apply(_bin)
        dis = df[df["primary_b"] != df["verifier_b"]].copy()
        for _, r in dis.iterrows():
            rows.append({
                "stage": "aux_FT",
                "internal_id": r.get("internal_id", ""),
                "title": str(r.get("title", ""))[:200],
                "doi": r.get("doi", ""),
                "primary_decision": r.get("ft_decision_primary", ""),
                "verifier_decision": r.get("ft_decision_verifier", ""),
                "binary_disagreement": f"{r['primary_b']} vs {r['verifier_b']}",
            })

    df = pd.DataFrame(rows)
    df["human_decision"] = ""           # to fill
    df["root_cause"] = ""               # to fill (criteria_ambiguity | abstract_insufficiency | scope_drift | other)
    df["human_notes"] = ""              # to fill

    # Prioritize: ws_FT (highest stakes) > aux_FT (preliminary) > ws_TA
    priority = {"ws_FT": 0, "aux_FT": 1, "ws_TA": 2}
    df["_p"] = df["stage"].map(priority)
    df = df.sort_values(["_p", "stage", "binary_disagreement"]).drop(columns="_p").reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    by = df["stage"].value_counts().to_dict()
    print(f"Total disagreements: {len(df)}")
    for s, c in sorted(by.items()):
        print(f"  {s}: {c}")
    print(f"\nSaved: {OUT_CSV}")
    print("\nReviewer instructions:")
    print("  1. Open the CSV in Excel / Google Sheets.")
    print("  2. For each row, read the title (and DOI if needed) and decide:")
    print("     human_decision: include | exclude | maybe")
    print("     root_cause: criteria_ambiguity | abstract_insufficiency | scope_drift | other")
    print("     human_notes: 1-2 sentence justification")
    print("  3. Save and commit. The numbers will feed the camera-ready validity section.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    if args.build or True:
        collect()


if __name__ == "__main__":
    main()
