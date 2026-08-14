# Replication Package — SLR / Mapping Study PATHCAST

**Version.** 2.0.0 (2026-08-13) — IST round-1 revision: cross-tier dedup, human
double-screening, included-study list, SEGRESS checklist.

**Title.** Replication Package for *"Process Mining and Stochastic Modeling for
Software Process Forecasting: A Systematic Mapping Study with an
LLM-Assisted Protocol"*

**Authors.** Rodrigo Almeida de Oliveira (corresponding); Juliano de Paulo
Ribeiro; Edson Emilio Scalabrin.
**Affiliation.** PPGIa, Pontifícia Universidade Católica do Paraná (PUC-PR),
Curitiba, Brazil.
**Contact.** rodrigo1.almeida@pucpr.edu.br
**ORCIDs.** 0009-0009-6310-4126 (Oliveira), 0009-0004-3605-485X (Ribeiro),
0000-0002-3918-1799 (Scalabrin).

**Manuscript target.** Information and Software Technology (Elsevier).

**Concept DOI** (“cite all versions”). [10.5281/zenodo.20130275](https://doi.org/10.5281/zenodo.20130275)

**This version (v2).** [10.5281/zenodo.21939471](https://doi.org/10.5281/zenodo.21939471)

Version 1 of the same record was `10.5281/zenodo.20130276`.

**License.** MIT (see `LICENSE`).

**Funding.** CAPES — Finance Code 001.

---

## What is in this package

This package is the replication artefact for the mapping study. An independent
reviewer can (a) inspect every screening and analysis decision, (b) re-run
κ (LLM–LLM and human–LLM), (c) regenerate the tables referenced in the
manuscript, (d) audit the 340 distinct included studies.

PDFs of primary studies are **not** redistributed (copyright). DOIs/URLs are
in `results/final_review/included_studies_340.csv`. Human full-text review
used locally retrieved PDFs that are omitted here; links needed are in
`results/human_validation/ft_pdf_links_needed.csv`.

### Top-level layout

```
.
├── README.md                         ← this file
├── LICENSE                           ← MIT
├── CITATION.cff
├── .zenodo.json                      ← Zenodo metadata (for the deposit form)
├── requirements.txt
├── config/                           ← search queries, screening criteria, control set
├── extractors/                       ← per-database normalisers
├── pipeline/                         ← dedup → screening → κ → QA → extraction → human κ
├── scripts/                          ← helpers used during execution
├── docs/
│   └── prompts_llm_screening.md      ← canonical LLM prompts (T/A, FT, QA)
└── results/                          ← outputs of the review
```

### Results subtree (highlights)

| Path | Purpose |
| ---- | ------- |
| `results/raw/` | Per-database raw exports (JSON) |
| `results/frozen/` | Deduplicated working corpus snapshot (`*_high_recall_2026-04-12.*`) |
| `results/screening/` | T/A and FT LLM screening outputs |
| `results/kappa/` | Cross-model (LLM–LLM) κ samples and `kappa_report.{tex,txt}` |
| `results/working_set/` | Working-set includes (169) |
| `results/qa_assessment.{csv,xlsx}` | 8-criterion QA scores (Dybå & Dingsøyr 2008) |
| `results/auxiliary/` | Auxiliary tier + **cross-tier dedup** (`*_404_dedup.csv`, `dedup_summary.txt`) |
| `results/ec5_recovery/` | EC5 PDF re-screen audit |
| `results/sensitivity/` | Auxiliary-tier sensitivity analysis |
| `results/final_review/` | PRISMA snapshot, `included_studies_340.csv`, appendix TeX, SEGRESS |
| `results/snowball_v2/` | Forward/backward snowballing pass 2 |
| `results/spotcheck/` | Disagreement list for human re-adjudication |
| `results/extraction/` | Structured extraction tables (no PDFs) |
| `results/human_validation/` | Blind human double-screening sheets, gold keys, human–LLM κ and confusion reports |

---

## Headline numbers (cross-check against the manuscript)

Search executed **12 April 2026**; eligibility window January 1994–December 2025
(2026 records already indexed at execution are retained).

| Quantity | Value |
| -------- | ----- |
| Records retrieved (5 DBs + snowball + control records) | 8,347 |
| After bibliographic dedup | 5,783 |
| Operational working set screened | 2,340 |
| Working-set confirmed primary studies | 169 |
| Raw combined includes (working-set + auxiliary passes) | 404 |
| Distinct studies after cross-tier dedup | **340** |
| Combined analytical subset (de-duplicated 381-tier) | **318** (259 pass QA ≥4/8) |
| LLM–LLM κ binary (20% sample) | T/A 0.695; FT 0.694 |
| Human–LLM κ (blind) | T/A multi 0.250 / binary 0.335 (n=468); FT 0.122 (n=177) |
| Human–LLM Recall / Lost Evidence (FT, human = gold) | Recall 0.246; LE 75% (95/126) |
| Triple-family paper (PM ∩ stochastic ∩ forecasting) | 1 of 340 (PRIMAD) |

Trace claims such as “121 of 169” from `results/auxiliary/extraction_combined_404_dedup.csv`
and the 340-row list `results/final_review/included_studies_340.csv`.

---

## Reproducing the review

### 1. Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Tested with Python 3.11. Anthropic SDK is required only if you re-run LLM
stages (`ANTHROPIC_API_KEY`). Decision CSVs are already in `results/`;
re-running LLMs is **not** required to audit the published numbers.

### 2. Pipeline order (LLM stages)

| Stage | Module | Output |
| ----- | ------ | ------ |
| Collect | `extractors/*.py` | `results/raw/*.json` |
| Combine + dedupe | `pipeline/dedup.py` | `results/frozen/*` |
| Abstract enrichment | `pipeline/enrich.py` | `results/screening/abstract_enrichment_*.csv` |
| T/A screening | `pipeline/screening.py` | `results/screening/ta_screening_results.csv` |
| FT screening | `pipeline/fulltext.py` | `results/screening/ft_screening_results.csv` |
| LLM–LLM κ | `pipeline/kappa.py` | `results/kappa/kappa_report.{tex,txt}` |
| QA scoring | `pipeline/qa_llm.py` | `results/qa_assessment*.{csv,jsonl,tex}` |
| Auxiliary tier | `pipeline/auxiliary_*.py`, `pipeline/aux_*.py` | `results/auxiliary/**` |
| Cross-tier dedup | `pipeline/dedup_review.py`, `pipeline/dedup_apply.py` | `results/auxiliary/*_dedup.csv` |
| EC5 audit | `pipeline/ec5_recovery.py` | `results/ec5_recovery/*` |
| Sensitivity | `pipeline/sensitivity.py` | `results/sensitivity/*` |
| Extraction | `pipeline/extract_prep.py`, `pipeline/extract_llm.py` | `results/extraction/*` |
| Included-study appendix | `pipeline/generate_included_appendix.py` | `results/final_review/included_studies_340.csv` |

### 3. Human–LLM agreement (no API key)

```bash
python -m pipeline.human_kappa --compute
```

Inputs: filled blind sheets + `_answer_keys/` in `results/human_validation/`.
Outputs: `human_kappa_report.{tex,txt}`, `human_confusion_report.tex`.

### 4. Search strings and criteria

Queries: `config/queries.py`. Inclusion/exclusion and LLM prompts:
`config/screening_criteria.py` and `docs/prompts_llm_screening.md`.

---

## Citation

```
Oliveira, R. A., Ribeiro, J. P., Scalabrin, E. E. (2026).
Process Mining and Stochastic Modeling for Software Process
Forecasting: A Systematic Mapping Study with an LLM-Assisted
Protocol. Submitted to Information and Software Technology.
```

```
Oliveira, R. A., Ribeiro, J. P., Scalabrin, E. E. (2026).
Replication Package for "Process Mining and Stochastic Modeling
for Software Process Forecasting: A Systematic Mapping Study
with an LLM-Assisted Protocol" (v2.0.0).
Zenodo. https://doi.org/10.5281/zenodo.21939471
(concept DOI: https://doi.org/10.5281/zenodo.20130275)
```

---

## Generative-AI disclosure

`claude-haiku-4-5-20251001` (Anthropic) was the primary LLM at title/abstract
and full-text screening and the QA scorer. `claude-sonnet-4-6` (Anthropic)
was the cross-model verifier. Independent human double-screening (T/A n=468,
FT n=177) is reported in `results/human_validation/`. LLMs are not authors
and bear no responsibility for editorial judgements.

---

## Notes for reviewers

- Access must be **Open** (SEGRESS item 27 / LLM4SCREENLIT R7).
- PDFs are omitted. Use DOIs in `included_studies_340.csv`.
- The 404-row combined tables **before** dedup remain in `results/auxiliary/`
  for audit; synthesis numbers in the manuscript use the de-duplicated 340 / 318.
- Human FT sheets do not contain a `maybe` queue (unlike T/A).
- Do not open `results/human_validation/_answer_keys/` if you are replicating
  the blind protocol; it holds the LLM primary decisions used to compute κ.
