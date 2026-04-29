"""Run the abstract-enrichment cascade on the 880 aux FT-pending papers."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

AUX_FT_CSV = Path("results/auxiliary/aux_ft_screened.csv")
AUX_TA_CSV = Path("results/auxiliary/aux_ta_screened.csv")
ENRICHED_CSV = Path("results/auxiliary/aux_pending_enriched.csv")


def run():
    from pipeline.enrich import enrich_abstracts

    if not AUX_FT_CSV.exists() or not AUX_TA_CSV.exists():
        logger.error("Aux FT and/or T/A files missing")
        return

    ft = pd.read_csv(AUX_FT_CSV)
    ta = pd.read_csv(AUX_TA_CSV)
    ft["ft_decision"] = ft["ft_decision"].fillna("").astype(str).str.lower().str.strip()

    pending_ids = set(ft.loc[ft["ft_decision"] == "pending", "internal_id"].astype(str))
    logger.info(f"[AuxEnrich] {len(pending_ids)} pending papers")

    pending = ta[ta["internal_id"].astype(str).isin(pending_ids)].copy()
    logger.info(f"[AuxEnrich] matched in T/A: {len(pending)}")
    before = (pending["abstract"].fillna("").astype(str).str.strip() != "").sum()
    logger.info(f"[AuxEnrich] with abstract before: {before}/{len(pending)}")

    # Sanitize NaN -> "" so enrich_abstracts can handle uniformly
    pending = pending.fillna("")
    papers = pending.to_dict("records")
    enriched_papers, n_recovered = enrich_abstracts(papers, delay=0.3)
    df = pd.DataFrame(enriched_papers)
    after = (df["abstract"].fillna("").astype(str).str.strip() != "").sum()
    logger.info(f"[AuxEnrich] with abstract after: {after}/{len(df)} (+{n_recovered})")
    df.to_csv(ENRICHED_CSV, index=False, encoding="utf-8")
    logger.info(f"[AuxEnrich] Saved: {ENRICHED_CSV}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.run or True:
        run()
