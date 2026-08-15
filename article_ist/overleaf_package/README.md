# IST Submission — Overleaf Package

Standalone Elsevier (`elsarticle`) package. Round-1 revision: mapping study,
human validation, Zenodo `10.5281/zenodo.21939600`.

## Import / update in Overleaf

**New project:** Overleaf → **New Project** → **Upload Project** → this zip.

**Existing project:** do not re-import the May 2026 zip. Upload/overwrite:

- `main.tex`, `cap3_article_body.tex`, `cover_letter.tex`
- `protocol_refs.bib`
- `results/segress_checklist.tex` (new)
- `results/human_validation/human_kappa_report.tex` (new)
- `results/human_validation/human_confusion_report.tex` (new)
- remaining `results/**` reports and `results/final_review/missing_references.bib`

Compiler: **pdfLaTeX**. Main document: `main.tex`. Then **Recompile**.

## Files

| Path | Purpose |
|------|---------|
| `main.tex` | Entry point — `\zenododoi` = `10.5281/zenodo.21939600` |
| `protocol_refs.bib` | SEGRESS + LLM4SCREENLIT (`kitchenham2023segress`, `llm4screenlit2025`) |
| `cap3_article_body.tex` | Article body |
| `cover_letter.tex` | Cover letter (compile as a separate Overleaf job) |
| `results/qa_assessment_summary.tex` | QA — working-set |
| `results/kappa/kappa_report.tex` | LLM–LLM κ |
| `results/human_validation/` | Human–LLM κ and confusion |
| `results/auxiliary/` | Auxiliary-tier summaries |
| `results/ec5_recovery/ec5_recovery_report.tex` | EC5 audit |
| `results/sensitivity/sensitivity_report.tex` | Sensitivity |
| `results/segress_checklist.tex` | Appendix B SEGRESS |
| `results/final_review/missing_references.bib` | Bibliography |

## Local build

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
pdflatex cover_letter
```

## Journal

Information and Software Technology (Elsevier).
Replication: https://doi.org/10.5281/zenodo.21939600
