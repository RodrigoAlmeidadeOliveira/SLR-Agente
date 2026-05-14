# Replication Package — SLR PATHCAST

**Title.** Replication Package for *"Process Mining and Stochastic Modeling for
Software Process Forecasting: A Systematic Literature Review with an
LLM-Assisted Protocol"*

**Authors.** Rodrigo Almeida de Oliveira (corresponding); Juliano de Paulo
Ribeiro; Edson Emilio Scalabrin.
**Affiliation.** PPGIa, Pontifícia Universidade Católica do Paraná (PUC-PR),
Curitiba, Brazil.
**Contact.** rodrigo1.almeida@pucpr.edu.br
**ORCIDs.** 0009-0009-6310-4126 (Oliveira), 0009-0004-3605-485X (Ribeiro),
0000-0002-3918-1799 (Scalabrin).

**Manuscript target.** Information and Software Technology (Elsevier).

**License.** MIT (see `LICENSE`).

**Funding.** CAPES — Finance Code 001.

---

## What is in this package

This package contains the full replication artefact for the SLR. It allows
an independent reviewer to (a) re-run every screening and analysis step,
(b) re-produce the κ inter-rater agreement reports, (c) regenerate every
table referenced in the manuscript.

PDFs of primary studies are not redistributed (copyright). The package
ships DOIs/URLs so a reviewer can re-collect them; the auxiliary tier ships
abstract-only metadata as required for LLM screening.

### Top-level layout

```
.
├── README.md                         ← this file (replication guide)
├── LICENSE                           ← MIT license
├── requirements.txt                  ← Python dependencies
├── config/                           ← search queries, screening criteria, control set
├── extractors/                       ← per-database normalisers (ACM/IEEE/Scopus/Springer/WoS)
├── pipeline/                         ← all pipeline stages (dedup → screening → κ → QA → extraction)
├── scripts/                          ← ad-hoc helpers used during execution
├── docs/
│   └── prompts_llm_screening.md      ← canonical LLM prompts (T/A, FT, QA)
└── results/                          ← every output produced during the review
```

### Results subtree (highlights)

| Path                                                      | Purpose                                                                          |
| --------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `results/raw/`                                            | Per-database raw exports (JSON) — primary tier (Scopus, IEEE, ACM, Springer, WoS) |
| `results/frozen/`                                         | Snapshot of the deduplicated working corpus (`*_high_recall_2026-04-12.*`)       |
| `results/screening/`                                      | T/A and FT LLM screening outputs (batches + decisions + stats)                   |
| `results/kappa/`                                          | κ samples + cross-model rescreens + `kappa_report.{tex,txt}`                     |
| `results/working_set/`                                    | Final working-set (169 includes) — JSON + CSV                                    |
| `results/qa_assessment.{csv,xlsx}`                        | 8-criterion QA scores (Dybå & Dingsøyr 2008)                                     |
| `results/qa_assessment_llm.csv`, `qa_assessment_llm_raw.jsonl` | LLM scorer outputs                                                          |
| `results/qa_assessment_summary.{tex,txt}`                 | QA distribution summary tables                                                   |
| `results/auxiliary/`                                      | Second corpus tier — T/A, FT, re-FT, QA, κ, extraction (212 + 23 includes)       |
| `results/ec5_recovery/`                                   | EC5 PDF re-screen audit (14 mismatches)                                          |
| `results/sensitivity/`                                    | Auxiliary-tier sensitivity analysis                                              |
| `results/final_review/`                                   | PRISMA snapshot, missing-references bibliography, included-studies CSV           |
| `results/snowball_v2/`                                    | Forward/backward snowballing pass 2                                              |
| `results/spotcheck/`                                      | Disagreement list for human re-adjudication                                      |
| `results/extraction/`                                     | Structured data extraction tables for synthesis                                  |
| `results/pdf_leitura_individual_v*.{csv,xlsx}`            | Manual full-text reading sheet (Band D + EC5 audit)                              |

---

## Reproducing the review

### 1. Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Tested with Python 3.11. Anthropic SDK is required for the LLM stages
(set `ANTHROPIC_API_KEY`).

### 2. Pipeline order

Module responsibilities, in execution order:

| Stage                     | Module                                                       | Output                                                       |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 1. Collect                | `extractors/*.py`                                            | `results/raw/*.json`                                         |
| 2. Combine + dedupe       | `pipeline/dedup.py`                                          | `results/frozen/*.json,csv`                                  |
| 3. Abstract enrichment    | `pipeline/enrich.py`                                         | `results/screening/abstract_enrichment_*.csv`                |
| 4. T/A screening (LLM)    | `pipeline/screening.py`                                      | `results/screening/ta_screening_results.csv`                 |
| 5. FT screening (LLM)     | `pipeline/fulltext.py`                                       | `results/screening/ft_screening_results.csv`                 |
| 6. κ verification         | `pipeline/kappa.py`                                          | `results/kappa/kappa_report.{tex,txt}`                       |
| 7. QA scoring (LLM)       | `pipeline/qa_llm.py` + `pipeline/qa_assessment_tools.py`     | `results/qa_assessment*.{csv,jsonl,tex}`                     |
| 8. Auxiliary tier         | `pipeline/auxiliary_*.py`, `pipeline/aux_*.py`               | `results/auxiliary/**`                                       |
| 9. EC5 audit              | `pipeline/ec5_recovery.py`                                   | `results/ec5_recovery/*`                                     |
| 10. Sensitivity           | `pipeline/sensitivity.py`                                    | `results/sensitivity/*`                                      |
| 11. Snowballing v2        | `pipeline/snowball_v2.py`                                    | `results/snowball_v2/*`                                      |
| 12. Structured extraction | `pipeline/extract_prep.py` + `pipeline/extract_llm.py`       | `results/extraction/*`                                       |
| 13. Synthesis             | `pipeline/synth_llm.py`                                      | manuscript draft inputs                                      |

### 3. Search strings

All five database queries are defined in `config/queries.py`. The inclusion
and exclusion criteria (IC1–IC4, EC1–EC8) and the LLM screening prompts
live in `config/screening_criteria.py` and `docs/prompts_llm_screening.md`.

### 4. κ verification

The cross-model rescreens are produced by `pipeline/kappa.py` (T/A and FT,
20 % stratified sample, Haiku-4-5 as primary, Sonnet-4-6 as verifier). The
final report is `results/kappa/kappa_report.tex` (working-set tier) and
`results/auxiliary/kappa/aux_kappa_report.tex` (auxiliary tier).

### 5. QA rubric

The 8-criterion rubric of Dybå & Dingsøyr (2008) is implemented in
`pipeline/qa_assessment_tools.py`; LLM scoring uses `pipeline/qa_llm.py`.
Per-paper raw outputs are in `results/qa_assessment_llm_raw.jsonl`.

---

## Headline numbers (for cross-checking)

- Deduplicated corpus: 5,783 papers across two tiers (2,340 working-set +
  3,807 auxiliary; with the snowballing increment the cumulative figure
  reported in the manuscript is 6,147).
- Confirmed primary studies: 404 (169 working-set + 212 first-pass
  auxiliary + 23 second-pass auxiliary after abstract enrichment).
- κ binary (working-set, 20 % sample): T/A 0.695, FT 0.694.
- QA distribution (combined): mean 5.00 ± 1.42; 315/381 retained at ≥4/8
  threshold (82.7 %).
- IC-combination ceiling: 1 / 404 papers (0.3 %) jointly satisfies
  process-mining + stochastic-modeling + forecasting.

---

## Citation

If you use this package, please cite the underlying article:

```
Oliveira, R. A., Ribeiro, J. P., Scalabrin, E. E. (2026).
Process Mining and Stochastic Modeling for Software Process
Forecasting: A Systematic Literature Review with an
LLM-Assisted Protocol. Submitted to Information and Software
Technology.
```

And this replication package:

```
Oliveira, R. A., Ribeiro, J. P., Scalabrin, E. E. (2026).
Replication Package for "Process Mining and Stochastic
Modeling for Software Process Forecasting: A Systematic
Literature Review with an LLM-Assisted Protocol".
Zenodo. DOI: 10.5281/zenodo.20130276
```

---

## Generative-AI disclosure

`claude-haiku-4-5-20251001` (Anthropic) served as the primary LLM at the
title/abstract and full-text stages and as the LLM scorer for the QA rubric.
`claude-sonnet-4-6` (Anthropic) served as the cross-model verifier for
inter-rater agreement. All decisions were inspected by the human authors.
The LLM tools are not listed as authors and bear no responsibility for
editorial judgements. Prompts, JSON schemas, and per-paper decisions are
included in this package.

---

## Notes for reviewers

- PDFs of primary studies are not redistributed. DOIs are in
  `results/final_review/included_studies_current.csv`.
- The auxiliary tier ships abstract-only metadata; some full texts were
  retrieved later via the PDF re-extraction step described in §6 of the
  manuscript.
- All LLM calls used deterministic decoding parameters. Exact prompts are in
  `docs/prompts_llm_screening.md` and embedded in `pipeline/qa_llm.py`.
- The pipeline is idempotent at the file level: any stage can be re-run by
  invoking its module directly; outputs are versioned by filename suffix.
