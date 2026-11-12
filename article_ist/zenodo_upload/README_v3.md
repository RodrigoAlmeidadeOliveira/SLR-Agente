# Replication Package — SMS PATHCAST (v3, corpus n=1710)

**Version.** 3.0.0 (2026-11-12) — Full caminho-completo corpus after ML block,
Wohlin snowballing to saturation, IC1 filter, and F2.3 flips.

**Title.** Replication Package for *"Process Mining and Stochastic Modeling for
Software Process Forecasting: A Systematic Mapping Study with an
LLM-Assisted Protocol"*

**Authors.** Rodrigo Almeida de Oliveira (corresponding); Juliano de Paulo
Ribeiro; Edson Emilio Scalabrin.
**Affiliation.** PPGIa, Pontifícia Universidade Católica do Paraná (PUC-PR),
Curitiba, Brazil.
**Contact.** rodrigo1.almeida@pucpr.edu.br

**Manuscript target.** Information and Software Technology (Elsevier).

**Concept / cite-all DOI.** [10.5281/zenodo.21939599](https://doi.org/10.5281/zenodo.21939599)
(always resolves to the latest version; version DOIs such as `21939600` are immutable snapshots).

**License.** MIT (see `LICENSE`).

**Funding.** CAPES — Finance Code 001.

---

## Headline numbers (cross-check against the manuscript)

| Quantity | Value |
| -------- | ----- |
| Search executed | 12 April 2026 |
| Unique records after bibliographic dedup | 5,783 |
| Final included corpus | **1,710** |
| RQ3 priority (human core extraction) | **293** |
| RQ3 suggestion-assisted core coding | **1,417** |
| Phase-2 blind re-screen κ (n=117) | **1.00** |
| L0 second-coder sample | 11/55 (20%); κ A↔B = 1.00 (with LLM suggestion) |
| Step-2 recall pre-registration | [10.5281/zenodo.24148068](https://doi.org/10.5281/zenodo.24148068) |

PDFs of primary studies are **not** redistributed (copyright). Identifiers and
DOIs are in `corpus_n1710/included_studies_1710.csv` and
`caminho_completo/phase4_rq3_extraction_template.csv`.

---

## Top-level layout

```
.
├── README.md
├── LICENSE / CITATION.cff / .zenodo.json
├── config/  extractors/  pipeline/  scripts/  docs/
├── results/                 ← historical screening / κ / SEGRESS stack
├── corpus_n1710/            ← canonical included set for the manuscript
│   ├── studies.json
│   ├── included_studies_1710.csv
│   ├── figs.py / figs_pt.py
│   └── appendix_studies*.tex
└── caminho_completo/        ← protocols, sheets, interactive classifiers
    ├── 00_DECISOES.md … 06_PROTOCOLO_*.md
    ├── phase1_* / phase2_* / phase3_* / phase4_*
    └── classify_*.py / enrich_phase4_venues.py / …
```

### What changed vs v2 (340-study deposit)

- Canonical included list is now **`studies.json` / `included_studies_1710.csv` (n=1710)**.
- Added `caminho_completo/` with Phase 0–5 protocols, blind re-screen, ML/snowball
  decisions, RQ3 sheets, SPMF/venue summaries, and L0 audit sample.
- Retained the screening pipeline and `results/` tree so Step-1/2 artefacts remain auditable.
- Supersedes the 340-row `included_studies_340.csv` as the manuscript corpus
  (that file remains under `results/final_review/` for historical audit only).

---

## How to verify quickly

```bash
python3 -c "import json; print(len(json.load(open('corpus_n1710/studies.json'))))"  # 1710
wc -l caminho_completo/phase4_rq3_extraction_template.csv   # 1711 = header + 1710
wc -l caminho_completo/phase4_rq3_priority_sheet.csv         # 294 = header + 293
```

Regenerate manuscript figures from `corpus_n1710/figs.py` (matplotlib).

---

## Citation

Almeida de Oliveira, R., Ribeiro, J. de P., & Scalabrin, E. E. (2026).
Replication Package for "Process Mining and Stochastic Modeling for Software
Process Forecasting: A Systematic Mapping Study with an LLM-Assisted Protocol"
(Version 3.0.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.21939599
