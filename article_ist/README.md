# IST Submission Package

Standalone Elsevier article derived from `cap3_slr_revised.tex`.

## Files

- `main.tex` — Elsevier `elsarticle` entry point (front matter + `\input` body + back matter)
- `cap3_article_body.tex` — body cloned from `cap3_slr_revised.tex` with thesis cross-refs replaced for standalone use
- `cover_letter.tex` — submission cover letter
- `main.pdf` — compiled article (36 pages)
- `cover_letter.pdf` — compiled cover letter

## Build

From this directory:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
pdflatex cover_letter
```

## Bibliography

`main.tex` references `../results/final_review/missing_references.bib`.

## External `\input` files (preserve relative paths under project root)

- `../results/qa_assessment_summary.tex`
- `../results/kappa/kappa_report.tex`
- `../results/auxiliary/aux_qa_summary.tex`
- `../results/auxiliary/aux_ft_summary.tex`
- `../results/auxiliary/aux_reft_summary.tex`
- `../results/auxiliary/kappa/aux_kappa_report.tex`
- `../results/ec5_recovery/ec5_recovery_report.tex`
- `../results/sensitivity/sensitivity_report.tex`

## Pre-submission checklist

- [ ] Confirm specific funding grants and update `\section*{Funding}` in `main.tex`
- [ ] Add second author (advisor) in `main.tex` if applicable
- [ ] Add ORCID iDs once available
- [ ] Native English proofread (Editage / Elsevier Author Services)
- [ ] Plagiarism check (iThenticate via PUC-PR)
- [ ] Finalize 5 suggested reviewers in `cover_letter.tex`
- [ ] Verify Zenodo DOI 10.5281/zenodo.15719919 contains the latest replication package
- [ ] Submit at https://www.editorialmanager.com/infsof/

## Pending camera-ready items (post-acceptance)

- Human spot-check on 69 disagreements (`results/spotcheck/disagreement_list_for_human.csv`)
- Aux T/A κ rescreen completion (39 of 761 done before API exhaustion)
- Aux PDF re-extraction (PDF text vs abstract-only) — 49 PDFs ready
- Snowball v2 T/A LLM screening of 357 candidates
- Manual full-text retrieval for 595 enrichment-failed + 121 EC5 + 16 reft pending papers
