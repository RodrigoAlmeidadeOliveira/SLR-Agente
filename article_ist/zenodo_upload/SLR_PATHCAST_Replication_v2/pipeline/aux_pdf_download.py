"""Download PDFs for the 27 EC5 OA-recovered papers and the 212 aux includes.

Reuses pipeline.pdf_downloader cascade (Unpaywall, Semantic Scholar, OpenAlex,
CORE). Downloads to results/auxiliary/pdfs/.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

EC5_REC = Path("results/ec5_recovery/ec5_recovery_results.csv")
AUX_FT = Path("results/auxiliary/aux_ft_screened.csv")
AUX_TA = Path("results/auxiliary/aux_ta_screened.csv")
DOWN_DIR = Path("results/auxiliary/pdfs")
DOWN_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = DOWN_DIR / "download_manifest.csv"
SUMMARY_TXT = Path("results/auxiliary/aux_pdf_summary.txt")


def collect_targets(scope: str) -> list[dict]:
    targets = []
    if scope in ("all", "ec5"):
        if EC5_REC.exists():
            df = pd.read_csv(EC5_REC)
            df = df[df["recovered"].fillna(False).astype(bool)]
            for _, r in df.iterrows():
                targets.append({
                    "internal_id": str(r.get("internal_id", "")),
                    "doi": str(r.get("doi", "")),
                    "title": str(r.get("title", "")),
                    "ft_oa_url": str(r.get("best_url", "")),
                    "source_db": "ec5_recovered",
                })
    if scope in ("all", "aux"):
        if AUX_FT.exists() and AUX_TA.exists():
            ft = pd.read_csv(AUX_FT)
            ft["ft_decision"] = ft["ft_decision"].fillna("").astype(str).str.lower().str.strip()
            inc = ft[ft["ft_decision"] == "include"]
            ta = pd.read_csv(AUX_TA).set_index("internal_id")
            for _, r in inc.iterrows():
                iid = str(r.get("internal_id", ""))
                row = ta.loc[iid] if iid in ta.index else None
                targets.append({
                    "internal_id": iid,
                    "doi": str(r.get("doi", "")),
                    "title": str(r.get("title", "")),
                    "ft_oa_url": "",
                    "source_db": "aux_include",
                    "abstract": (row.get("abstract", "") if row is not None else ""),
                })
    logger.info(f"[AuxPDF] targets: {len(targets)} (scope={scope})")
    return targets


def run(scope: str, limit: int = 0):
    from pipeline.pdf_downloader import download_pdfs

    # Override DOWNLOAD_DIR & MANIFEST_CSV at module level
    import pipeline.pdf_downloader as pd_mod
    pd_mod.DOWNLOAD_DIR = DOWN_DIR
    pd_mod.MANIFEST_CSV = MANIFEST
    pd_mod.MANUAL_LIST = DOWN_DIR / "manual_required.txt"

    targets = collect_targets(scope)
    if not targets:
        logger.error("No targets collected")
        return

    email = "rodrigoalmeidadeoliveira@gmail.com"
    download_pdfs(targets, email=email, delay=1.0, force=False, limit=limit)
    summarize()


def summarize():
    if not MANIFEST.exists():
        logger.error("Manifest missing")
        return
    df = pd.read_csv(MANIFEST)
    total = len(df)
    ok = (df.get("pdf_status", "") == "downloaded").sum() if "pdf_status" in df.columns else 0
    fail = total - ok
    lines = [
        "SLR PATHCAST — Auxiliary PDF Download Summary",
        "=" * 60,
        f"Targets attempted: {total}",
        f"Downloaded: {ok} ({ok/total*100:.1f}%)" if total else "Downloaded: 0",
        f"Failed:    {fail} ({fail/total*100:.1f}%)" if total else "Failed: 0",
        "",
        f"Files in: {DOWN_DIR}",
    ]
    SUMMARY_TXT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["ec5", "aux", "all"], default="all")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--summarize", action="store_true")
    args = ap.parse_args()
    if args.summarize:
        summarize()
    else:
        run(args.scope, args.limit)


if __name__ == "__main__":
    main()
