# O que subir no Overleaf (tese íntegra)

**Documento principal:** `main_patched.tex`  
**PDF de referência local:** `main_patched.pdf` (~261 pp., com App.~J + **App.~K SEGRESS** + App.~L)

O PDF do Overleaf (~256 pp.) ficou incompleto porque o projeto remoto ainda não tinha o `appendix_slr.tex` atual + a pasta `results/final_review/` (lista 340 + SEGRESS).

## Opção A — recomendada: zip completo

Arquivo pronto:

`avaliação da banca/PATHCAST_tese_overleaf_sync.zip` (~8 MB)

1. No Overleaf: **Menu → Upload →** o zip (ou substitua a pasta do projeto).
2. Em **Settings → Main document** → `main_patched.tex`.
3. Compiler: **pdfLaTeX** (TeX Live 2024 ou 2025).
4. Recompile **2–3 vezes** (refs/TOC/LOF).
5. Confirme no PDF: existe **Appendix K — SEGRESS** e Figuras **1.1–1.4**.

## Opção B — só o delta (se o projeto Overleaf já tem a árvore)

Substitua/envie **obrigatoriamente** estes caminhos (mesma hierarquia):

### Raiz
- `main_patched.tex` (macros `\zenododoi`, TikZ, includes)
- `references.bib`
- `ppgia.cls` (se ainda não estiver)
- `pdfa.xmpi` (se usar PDF/A)

### Front matter
- `frontmatter/resumo.tex`
- `frontmatter/abstract.tex`
- `frontmatter/glossary.tex`

### Capítulos (texto DRC + figuras Cap.1)
- `capitulos/cap1_introduction.tex`
- `capitulos/fig_cap1_problem_context.tex` **(novo)**
- `capitulos/fig_cap1_throughput_blackbox.tex` **(novo)**
- `capitulos/fig_cap1_pathcast_aware.tex` **(novo)**
- `capitulos/fig_cap1_three_tools.tex` **(novo)**
- `capitulos/cap2_reduced.tex`
- `capitulos/cap3_slr_revised.tex`
- `capitulos/cap4_method_reduced.tex`
- `capitulos/cap7_evaluation.tex` (se incluir E2C)
- `capitulos/cap7_e2c_cross_paradigm.tex` (input do Cap.7)
- `capitulos/appendix_slr.tex` **(traz App. J + K)**
- demais caps já no Overleaf: `cap5_*`, `cap6_*`, `appendix_theory.tex`, `appendix_repositories.tex`

### Results (sem isto o App. K some / Cap.3 quebra)
- `results/final_review/included_studies_appendix.tex` **(novo — App. J)**
- `results/final_review/segress_checklist.tex` **(novo — App. K)**
- `results/final_review/included_studies_340.csv` (citado; opcional na compilação)
- `results/auxiliary/aux_qa_summary.tex`
- `results/auxiliary/aux_ft_summary.tex`
- `results/human_validation/human_kappa_report.tex`
- `results/human_validation/human_confusion_report.tex`
- `results/qa_assessment_summary.tex`
- `results/qa_peritem_summary.tex`
- `results/kappa/kappa_report.tex` (e/ou `results/kappa_report.tex`)
- restante de `results/auxiliary/*.tex` usados pelos caps

### Assets
- `figures/` (PNGs/JPG já usados)
- `template/PUCPR_logo.jpg`
- `template/PUCPR_watermark.png`

## Não precisa subir
- `avaliação da banca/`
- `*.pdf`, `*.aux`, `*.log`, `*.toc`, `*.out`, `*.fls`, `*.fdb_latexmk`
- `scripts/`, checklists Markdown locais

## Checklist pós-compile no Overleaf
- [ ] Páginas ≈ **261** (não ~256)
- [ ] Appendix **K SEGRESS** existe
- [ ] Appendix **J** lista dos 340 estudos
- [ ] Cap.1 tem Figuras **1.1–1.4**
- [ ] Resumo/Abstract: verbo **propõe / proposes**
- [ ] Cap.3: corpus **318 / 340** (não 319/341)
- [ ] Zero `??` no PDF

## Por que o Overleaf deu 256 páginas
Faltavam no remoto os `\input{results/final_review/...}` do fim de `appendix_slr.tex`. Sem esses ficheiros (ou com `appendix_slr.tex` antigo), o App.~K não entra — exatamente o gap vs. o PDF local.
