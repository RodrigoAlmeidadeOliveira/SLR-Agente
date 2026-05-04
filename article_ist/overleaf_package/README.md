# IST Submission — Overleaf Package

Standalone Elsevier (`elsarticle`) package, ready to import in Overleaf.

## Import in Overleaf

1. Overleaf → **New Project** → **Upload Project** → select the zip.
2. Set compiler: **pdfLaTeX** (Menu → Compiler).
3. Set main document: `main.tex` (Menu → Main document).
4. Click **Recompile**. Overleaf runs `pdflatex` + `bibtex` + `pdflatex` × 2 automatically.

Verified locally: `main.pdf` 38 pages, `cover_letter.pdf` 2 pages, no undefined references.

## Files

| Path | Purpose |
|------|---------|
| `main.tex` | Entry point — front matter + `\input` body + back matter |
| `cap3_article_body.tex` | Article body (sections 1–8) |
| `cover_letter.tex` | Submission cover letter (separate document) |
| `results/qa_assessment_summary.tex` | QA scores — working-set tier |
| `results/kappa/kappa_report.tex` | κ inter-rater agreement — working set |
| `results/auxiliary/aux_qa_summary.tex` | QA scores — auxiliary tier |
| `results/auxiliary/aux_ft_summary.tex` | Full-text screening — auxiliary tier |
| `results/auxiliary/aux_reft_summary.tex` | Re-screening pass — auxiliary tier |
| `results/auxiliary/kappa/aux_kappa_report.tex` | κ inter-rater agreement — auxiliary |
| `results/ec5_recovery/ec5_recovery_report.tex` | EC5 PDF re-check report |
| `results/sensitivity/sensitivity_report.tex` | Sensitivity analysis report |
| `results/final_review/missing_references.bib` | BibTeX bibliography |

## Local build (alternative to Overleaf)

```bash
pdflatex main
bibtex main
pdflatex main && pdflatex main
pdflatex cover_letter
```

## Pre-submission checklist

- [ ] Native English proofread (Editage / Elsevier Author Services)
- [ ] iThenticate plagiarism check (PUC-PR)
- [ ] Confirm 5 suggested reviewers in `cover_letter.tex`
- [ ] Verify Zenodo DOI 10.5281/zenodo.15719919 has latest replication package
- [ ] Submit at https://www.editorialmanager.com/infsof/

## Journal target

Information and Software Technology (Elsevier).
