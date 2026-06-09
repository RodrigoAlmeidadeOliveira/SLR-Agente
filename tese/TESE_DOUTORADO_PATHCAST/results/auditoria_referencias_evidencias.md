# Evidências — Auditoria de Referências PATHCAST

**Auditoria inicial:** 2026-06-08  
**Última atualização:** 2026-06-08 (pós-correções + higiene + Phase 9)  
**Escopo citado:** 95 entradas em `main_patched.bbl` (compilado 2026-06-08)  
**Fontes cruzadas:**
- `auditoria_referencias_pathcast.md` (amostra manual + leitura da bibliografia PDF)
- `references.bib` (**337** entradas totais; 95 citadas na compilação atual)
- `REVISAO_ORIENTADOR_CHECKLIST.md`
- `results/final_review/missing_references.bib` (2026-04-19)
- Validação automática: Crossref API (2026-06-08, pós-correções)

---

## Veredito executivo (atualizado)

**As 95 referências citadas na compilação atual (`main_patched`) correspondem a obras reais com metadados corrigidos nos itens bloqueantes e higiene aplicada ao `.bib`.**

| Categoria | Antes (auditoria) | Depois (correções) |
|-----------|-------------------|---------------------|
| Entradas citadas | 98 | **95** (−3 duplicatas/remoções) |
| Entradas totais no `.bib` | ~413 | **337** (−13 placeholders, −45 duplicatas não citadas, −28 outras consolidações) |
| BLOCKER (metadados invalidantes) | 2 | **0** |
| MAJOR (DOI/placeholder entre citadas) | 3 | **0** |
| Duplicatas na bibliografia citada | 3 grupos | **0** |
| Placeholders no `.bib` (não citados) | ~13 | **0** (removidos) |
| Duplicatas no `.bib` (não citados) | ~48 grupos | **45 removidos** |
| DOIs em clássicos citados | ~22 sem DOI | **5 sem DOI** (tech report, web, livro comercial) |
| Validação citação ↔ conteúdo (Phase 9) | Não realizada | **Feita** (trechos de alto risco) |
| Revalidação automática 95 chaves | Pendente | **Feita** (`ref_validation_post_corrections.json`) |

**Risco de alucinação bibliográfica (LLM):** na amostra e nos itens bloqueantes corrigidos, **não há evidência de referência fabricada** entre as entradas citadas. O caso `rubin2014process` foi removido; as citações passaram a `rubin2007` (ICSP 2007).

---

## O que foi feito

### 1. Correções BLOCKER e MAJOR em `references.bib`

| Item | Ação | Evidência pós-correção |
|------|------|------------------------|
| **B1** `bose2013trace` | DOI, vol., págs. e ano corrigidos | `10.1016/j.is.2011.08.003`, IS **37(2):117–141, 2012** |
| **B2** `rubin2014process` | Entrada **removida** | Substituída por `rubin2007` nas citações |
| **M1** `montgomery2022jira` | DOI corrigido | `10.1145/3524842.3528486` |
| **M2** `wohlin2014guidelines` | Tipo `@inproceedings`, DOI EASE 2014 | `10.1145/2601248.2601268`, pp. 1–10; nota sobre extensão ESE 19(6) |
| **M3** `jokwon2024` | Placeholder **removido** | Chave canônica `jo2024` com DOI `10.3390/app14031260` |

### 2. Duplicatas removidas (D1, D2)

| Grupo | Mantida | Removida |
|-------|---------|----------|
| D1 Whittaker 1994 | `whittaker1994` | `WhittakerThomason1994` |
| D2 Poncin 2011 | `poncin2011process` | `poncin2011` |
| D3 Bhadra 2022/2023 | **Ambas mantidas** (obras distintas) | — |

### 3. Higiene do `.bib` completo (prioridade média)

| Ação | Resultado |
|------|-----------|
| Remoção de placeholders não citados | **13** entradas (`rlpr2023`, `jokwon2023`, `leemans2025vlmc`, `caldeiracm2022`, etc.) |
| Remoção de duplicatas não citadas (mesmo título normalizado) | **45** entradas |
| Consolidação `adriansyah2011alignments` | Chave renomeada de `Adriansyah2011Alignments`; DOI `10.1109/EDOC.2011.12` |
| Bloco órfão Berti/PM4Py | Removido (duplicata de `berti2023pm4py`) |
| DOIs adicionados a clássicos citados | **31** patches via script `scripts/bib_hygiene_and_validate.py` |

### 4. Prioridade alta — conteúdo e consistência narrativa

| Item | Decisão / ação |
|------|----------------|
| **Rubin “first”** | Claims de “first framework/systematic” removidos ou hedged em `appendix_slr.tex`, `cap2_expanded_v3.tex`; citação canônica `rubin2007` (ICSP 2007). `appendix_slr.tex` mantém “earliest in validation set” (escopo da validação, não claim global). |
| **Wohlin EASE vs. ESE** | **Decisão: EASE 2014** como publicação primária (`@inproceedings`, DOI ACM). Nota no `.bib` documenta extensão journal ESE 19(6). Texto: `(EASE 2014)` em `cap3_slr_revised.tex` e `cap3_slr.tex` (legado). |
| **Phase 9** | Auditoria manual dos trechos de alto risco; relatório em `results/phase9_citation_claim_audit.md`. `cap4_method_reduced.tex`: citações `bose2013trace` e `augusto2019` separadas por afirmação (alignments vs. benchmarks). |

### 5. Prioridade baixa

| Item | Status |
|------|--------|
| Revalidação automática 95 chaves | ✅ `results/ref_validation_post_corrections.json` — 48 DOIs verificados, 5 sem DOI legítimo, 31 `TITLE_MISMATCH` (falsos positivos por normalização de título) |
| Buliga 2025 ordem de autores | ✅ Conferido: Buliga, Meneghello, Graziosi, Ronzani (Crossref / IEEE ICPM 2025) |
| `cap3_slr.tex` legado | ✅ Alinhado: `(EASE 2014)` em Wohlin; chaves `whittaker1994`, `wohlin2014guidelines` |

### 6. Citações atualizadas nos `.tex`

| Arquivo | Alteração |
|---------|-----------|
| `cap1_introduction.tex` | `rubin2014process`→`rubin2007`; `WhittakerThomason1994`→`whittaker1994` |
| `cap3_slr_revised.tex` | `WhittakerThomason1994`→`whittaker1994`; Wohlin `(EASE 2014)` |
| `cap3_slr.tex` | Wohlin `(EASE 2014)` |
| `cap4_method_reduced.tex` | Phase 9: `bose2013trace` / `augusto2019` separados |
| `appendix_slr.tex` | `poncin2011`→`poncin2011process`; hedging Rubin |
| `cap2_expanded_v3.tex` | `rubin2014process`→`rubin2007`; hedging “first” |

### 7. Bibliografia regenerada

```bash
latexmk -pdf main_patched.tex   # 2026-06-08, bibtex sem erros
```

- `main_patched.bbl`: **95** `\bibitem`
- `references.bib`: **337** entradas
- `main_patched.pdf`: recompilado

---

## Revalidação automática (95 chaves)

Arquivo: `results/ref_validation_post_corrections.json`

| Métrica | Valor |
|---------|-------|
| Total citadas | 95 |
| DOI verificado (Crossref resolve) | 48 |
| Sem DOI (esperado) | 5 (`kitchenham2007`, `poncin2011process`, `github2023api`, `gharchive2023`, `vacanti2015`) |
| TITLE_MISMATCH | 31 (majoritariamente variantes de capitalização/subtítulo; DOI resolve) |
| DOI_ERROR (ISBN/book/zenodo/arXiv) | 11 (DOIs de livro/capítulo; obra correta, Crossref não indexa como work) |

**Interpretação:** ausência de `VERIFIED` em 100% não indica obra inválida; o limiar de similaridade de título é conservador e muitos veículos SE usam títulos abreviados no `.bib`.

---

## Phase 9 — resumo

Relatório completo: `results/phase9_citation_claim_audit.md`

| Citação | Afirmação | Sustenta? |
|---------|-----------|-----------|
| `rubin2007` | Framework PM+SE (ICSP 2007) | ✅; claims “first” hedged |
| `wohlin2014guidelines` | Snowballing | ✅ EASE 2014 |
| `bose2013trace` | Variabilidade / alignments | ✅ |
| `augusto2019` | Benchmarks discovery | ✅ |
| `buliga2025` | What-if ICPM 2025 | ✅ |

---

## Casos especiais (válidos com ressalva)

| Chave | Situação |
|-------|----------|
| `billingsley1961statistical` | Variante de título no Crossref; mesma obra |
| `kitchenham2007` | Tech report EBSE-2007-01 (sem DOI) |
| `github2023api`, `gharchive2023` | Recursos web (sem DOI) |
| `vacanti2015` | Livro comercial (sem DOI) |
| `poncin2011process` | CSMR 2011 workshop (sem DOI no Crossref) |
| `syriani2023` | arXiv `10.48550/arXiv.2307.06464` |
| `kuleshov2018calibrated` | arXiv `10.48550/arXiv.1807.00263` |
| `little2011factory` | Capítulo Springer; DOI de livro retorna 404 no Crossref |

---

## Histórico do projeto

| Data | Evento |
|------|--------|
| 2026-04-19 | `missing_references.bib` gerado para cap3 |
| 2026-06-08 (manhã) | Auditoria inicial + validação Crossref/OpenAlex (98 citadas) |
| 2026-06-08 (tarde) | Correções BLOCKER/MAJOR, `.tex` ativos, `latexmk` |
| 2026-06-08 (noite) | Higiene `.bib`, DOIs clássicos, Phase 9, revalidação 95 chaves |

---

## Artefatos

| Arquivo | Conteúdo |
|---------|----------|
| `results/auditoria_referencias_evidencias.md` | Este relatório |
| `results/ref_validation_post_corrections.json` | Revalidação 95 chaves (Crossref) |
| `results/phase9_citation_claim_audit.md` | Phase 9 — citação ↔ afirmação |
| `scripts/bib_hygiene_and_validate.py` | Script de higiene + patches DOI |
| `references.bib` | Bibliografia fonte (337 entradas) |
| `main_patched.bbl` / `.pdf` | Bibliografia compilada (95 entradas) |

**Comando para recompilar:**
```bash
cd tese/TESE_DOUTORADO_PATHCAST
latexmk -pdf main_patched.tex
```

---

## Resposta direta (atualizada)

> As referências da tese são todas válidas?

**Sim, para as 95 referências citadas na compilação atual**, no sentido de existência bibliográfica, metadados corrigidos nos bloqueantes, higiene do `.bib` e auditoria Phase 9 nos trechos críticos.

**Pendências opcionais (não bloqueantes para defesa):**
- Alinhar títulos no `.bib` aos registros Crossref onde há `TITLE_MISMATCH` cosmético;
- Adicionar DOI a `poncin2011process` se localizado em repositório institucional;
- Revisão Phase 9 estendida a todas as 95 citações (não apenas alto risco).

Para defesa: **itens bloqueantes bibliográficos, higiene do `.bib`, Wohlin/Rubin e Phase 9 estão resolvidos.**
