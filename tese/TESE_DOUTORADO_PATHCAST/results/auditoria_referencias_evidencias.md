# Evidências — Auditoria de Referências PATHCAST

**Data:** 2026-06-08  
**Escopo:** 98 entradas efetivamente citadas na tese (`main_patched.bbl`, compilado em 2026-06-08 09:31)  
**Fontes cruzadas:**
- `auditoria_referencias_pathcast.md` (amostra manual + leitura da bibliografia PDF)
- `references.bib` (417 entradas totais; 98 citadas)
- `REVISAO_ORIENTADOR_CHECKLIST.md` (histórico de correções, inclusive `bose2013trace` adicionada em cap4)
- `results/final_review/missing_references.bib` (registro de entradas faltantes, 2026-04-19)
- Validação automática: Crossref API + OpenAlex API (2026-06-08)

---

## Veredito executivo

**Não é possível afirmar que todas as referências da tese são válidas.**

| Categoria | Quantidade | Significado |
|-----------|------------|-------------|
| Publicação real, metadados aceitáveis | **94** | Obra existe; DOI ou busca externa confirma |
| **BLOCKER** — obra existe, metadados **incorretos** | **2** | Citação aponta para publicação errada ou veículo inexistente |
| **MAJOR** — DOI inválido / entrada placeholder | **3** | Obra existe, mas `.bib` impede verificação automática |
| Duplicatas na bibliografia citada | **3 grupos** | Mesma obra listada 2× (2 confirmadas; 1 par distinto) |
| Defeitos de formatação ABNT (sem invalidar existência) | **~15** | Veículo/páginas omitidos ou mal renderizados no `.bbl` |

**Risco de alucinação bibliográfica (LLM):** o material de auditoria não encontrou fabricação na amostra. Esta verificação ampliada encontrou **1 entrada com veículo provavelmente inexistente** (`rubin2014process`) e **1 com DOI apontando para outro artigo** (`bose2013trace`). Isso é mais grave que duplicata ou página ausente.

---

## Método e limites

1. **Inventário:** extração mecânica de `\bibitem{...}` em `main_patched.bbl` → 98 chaves únicas citadas.
2. **Parsing:** leitura de campos em `references.bib` por chave (com fallback case-insensitive, ex.: `jo2024` → `Jo2024`).
3. **Validação externa:** para cada entrada com DOI, resolução via `api.crossref.org`; sem DOI, busca por título+ano; casos críticos, OpenAlex + TOC de periódico (Dialnet).
4. **Reconciliação** com achados D1–D3 do documento de auditoria.
5. **Limite:** esta auditoria confirma **existência e metadados canônicos**, não se o corpo do texto usa cada fonte corretamente (Phase 9 da skill `paper-validation-review`).

---

## BLOCKER — correção obrigatória antes da defesa

### B1. `bose2013trace` — DOI e metadados apontam para outro artigo

| Campo | Valor no `.bib` / `.bbl` | Valor canônico (evidência) |
|-------|---------------------------|----------------------------|
| Título | Process diagnostics using trace alignment… | **Mesmo título** (obra real) |
| DOI | `10.1016/j.is.2012.12.003` | **`10.1016/j.is.2011.08.003`** |
| DOI atual resolve para | *On the privacy offered by (k, δ)-anonymity* (Elsevier) | *Process diagnostics using trace alignment…* |
| Revista / vol / págs / ano | Information Systems 38(4):596–616, **2013** | Information Systems **37(2):117–141, 2012** |

**Evidência Crossref (2026-06-08):**
```
GET https://api.crossref.org/works/10.1016/j.is.2012.12.003
→ "On the privacy offered by (k, δ)-anonymity", IS 38(4), pp. 491-494

GET https://api.crossref.org/works/10.1016/j.is.2011.08.003
→ "Process diagnostics using trace alignment: Opportunities, issues, and challenges",
  IS 37(2), pp. 117-141
```

**Citação na tese:** `cap4_method_reduced.tex` (entropia de variantes; adicionada conforme `REVISAO_ORIENTADOR_CHECKLIST.md`).

**Ação:** corrigir DOI, volume, número, páginas e ano; recompilar `main_patched.tex`.

---

### B2. `rubin2014process` — veículo declarado não contém esta obra

| Campo | Valor no `.bib` / `.bbl` |
|-------|--------------------------|
| Título | A framework for mining software development processes |
| Veículo | Information and Software Technology 56(12):1585–1597, 2014 |
| DOI | *(ausente)* |

**Evidência de inexistência no veículo declarado:**

1. **DBLP** — busca pelo título exato: *no matches* (2026-06-08).
2. **Researchr (Vladimir Rubin)** — lista de publicações 2014: apenas *Agile development with software process mining* (ICSSP 2014); **não** há artigo de revista com este título.
3. **TOC IST 56(12), 2014** ([Dialnet](https://dialnet.unirioja.es/ejemplar/493088)):
   - pp. 1578–1596: Licorish & MacDonell — *Understanding the attitudes, knowledge sharing behaviors…*
   - pp. 1597–1612: Mäntylä & Itkonen — *How are software defects found?…*
   - **Nenhum artigo de Rubin et al. neste fascículo.**

**Obra relacionada real (não substituta direta):**
- `rubin2007` — *Process Mining Framework for Software Processes*, ICSP 2007, LNCS 4470, pp. 169–181, DOI via Springer.
- Título na tese difere do título canônico de 2007; a entrada 2014 parece **versão journal inexistente** ou metadados **fabricados/confundidos**.

**Citação na tese:** `cap2_expanded_v3.tex` (múltiplas menções como “first explicit framework” / “first systematic”).

**Ação:** substituir por `rubin2007` (conferência) ou localizar artigo journal correto se existir sob outro título; **não manter** IST 56(12):1585–1597 sem fonte primária.

---

## MAJOR — obra real, `.bib` defeituoso

### M1. `montgomery2022jira` — DOI incorreto (404)

| No `.bib` | Canônico |
|-----------|----------|
| `10.1145/3524842.3528495` (404 Crossref) | **`10.1145/3524842.3528486`** |
| Título correto | *An alternative issue tracking dataset of public Jira repositories*, MSR 2022, pp. 73–77 |

**Evidência OpenAlex:** `https://doi.org/10.1145/3524842.3528486`

**Citação:** cap2, cap5, `appendix_repositories.tex` (dataset Jira).

---

### M2. `wohlin2014guidelines` — DOI no `.bib` não resolve

| No `.bib` | Observação |
|-----------|------------|
| `10.1007/s10664-013-9255-0` | HTTP 404 em Crossref (2026-06-08) |
| Artigo existe | `10.1145/2601248.2601268` — EASE 2014 (versão conferência) |
| Entrada alternativa no projeto | `missing_references.bib` chave `Wohlin2024` com DOI EASE correto |

**Citação:** `cap3_slr.tex` / `cap3_slr_revised.tex` (snowballing).

**Ação:** alinhar DOI à versão citada (journal ESE vs. EASE 2014); conferir qual versão o texto pretende.

---

### M3. `jokwon2024` — entrada placeholder no `.bib`

Entrada legada com autores `(Initials)`, venue `(Verify venue)`. Entrada correta: **`Jo2024`**, Applied Sciences 14(3):1260, DOI `10.3390/app14031260` (verificado Crossref).

O `.bbl` cita `jo2024` e resolve via alias; risco é manutenção futura se placeholder não for removido.

---

## Achados do documento de auditoria — status na tese atual

### D1. Whittaker & Thomason 1994 — **CONFIRMADO**

Ambas citadas na tese:
- `WhittakerThomason1994` — cap2 (`cap2_expanded_v3.tex`)
- `whittaker1994` — cap3 SLR, `appendix_slr.tex`

Mesmo DOI `10.1109/32.328991`, IEEE TSE 20(10):812–824. **Manter uma, remover a outra.**

### D2. Poncin et al. 2011 — **CONFIRMADO**

- `poncin2011process` — CSMR / 15th European Conference…
- `poncin2011` — CSMR 2011

Ambas citadas (cap2, cap3, appendix). **Consolidar em uma entrada.**

### D3. Bhadra 2022 vs Bhadra et al. 2023 — **OBRAS DISTINTAS (confirmado)**

| Chave | Evento | Ano | DOI verificado |
|-------|--------|-----|----------------|
| `bhadra2022` | ISSREW 2022, pp. 165–170 | 2022 | `10.1109/ISSREW55968.2022.00050` |
| `bhadra2023` | RAMS 2023 | 2023 | `10.1109/RAMS51473.2023.10088212` |

Título similar, mas autoria, veículo e DOI diferem. **Manter ambas**; completar páginas em `bhadra2023`.

---

## Entradas incompletas (auditoria) — status no `.bib` atual

| Entrada | Status auditoria | Status `.bib` 2026-06-08 | Status `.bbl` renderizado |
|---------|------------------|--------------------------|---------------------------|
| `aalst2012process` | veículo vazio | `journal={ACM TMIS}` presente; **falta DOI** `10.1145/2229156.2229157` | ainda mostra `In: .` (problema `@incollection` + ABNT) |
| `massitela2018` | sem veículo | **corrigido:** SEKE 2018, DOI `10.18293/SEKE2018-033` | ainda só ano (`.bbl` desatualizado ou tipo `@article`+`booktitle`) |
| `joshi2024` | veículo "IEEE" | **corrigido:** SANER 2024, DOI `10.1109/SANER60148.2024.00057` | `.bbl` ainda mostra só "IEEE" |
| `washizaki2015` | veículo "IEEE" | **corrigido:** Agile 2015, DOI `10.1109/Agile.2015.19` | `.bbl` ainda mostra só "IEEE" |
| `tyagi2021` | veículo "Springer" | **corrigido:** Springer chapter, DOI `10.1007/978-981-16-0404-1_26` | `.bbl` ainda mostra só "Springer" |

**Conclusão:** várias correções já estão no `.bib` mas **não se refletem** na bibliografia PDF se o `.bbl` não for regenerado após ajuste de tipo de entrada (`@inproceedings` vs `@article`).

### Páginas ausentes (prioridade baixa) — ainda pendentes no `.bib`

`buliga2025`, `guinea2025`, `gupta2017`, `jo2023`, `lopezpintado2023`, `nafreen2020`, `bhadra2023`, `magennis2015` — obras **verificadas por DOI**; faltam páginas para uniformidade ABNT.

---

## Amostra verificada externamente (reprodução + extensão)

| Entrada | Resultado | Evidência |
|---------|-----------|-----------|
| Aalst 2012 | Real | Crossref `10.1145/2229156.2229157` → ACM TMIS 3(2):1–17 |
| Massitela 2018 | Real | Crossref `10.18293/SEKE2018-033` |
| Joshi & Kahani 2024 | Real | Crossref `10.1109/SANER60148.2024.00057` |
| Buliga et al. 2025 | Real | Crossref `10.1109/ICPM66919.2025.11220730` |
| Whittaker & Thomason 1994 | Real (duplicada) | Crossref `10.1109/32.328991` |
| Poncin et al. 2011 | Real (duplicada) | CSMR 2011, pp. 5–14 |
| Bhadra 2022 / 2023 | Reais, distintas | DOIs ISSREW e RAMS acima |
| Clássicos sem DOI no `.bib` | Real | Busca Crossref por título: Hevner 2004, Peffers 2007, Metropolis 1949, Gneiting 2007, Cook 1998, Kitchenham 2007 (tech report EBSE), etc. |

**Nenhuma referência claramente fabricada** foi encontrada na amostra do documento original. **Duas entradas citadas falham** na verificação de metadados (B1, B2).

---

## Casos especiais (válidos com ressalva)

| Chave | Situação |
|-------|----------|
| `billingsley1961statistical` | DOI resolve; Crossref titula *Statistical Methods in Markov Chains* — variante de título da mesma obra (pp. 12–40, AOMS 32(1)) |
| `kitchenham2007` | Tech report EBSE-2007-01; sem DOI Crossref; obra canônica SLR |
| `github2023api`, `gharchive2023` | Recursos web; válidos como `@misc` |
| `syriani2023` | arXiv `2307.06464`; DOI DataCite 404 em Crossref, obra real |
| `kuleshov2018calibrated` | ICML 2018; sem DOI no `.bib`; arXiv `1807.00263` confirma existência |
| `little2011factory` | Capítulo Springer; DOI no `.bib` retorna 404; obra real (Little's Law) |

---

## Histórico do projeto relevante

| Registro | Implicação |
|----------|------------|
| `REVISAO_ORIENTADOR_CHECKLIST.md` | `bose2013trace` adicionada para cap4 §4.3 (Phase-9); **não validou DOI** |
| `missing_references.bib` (2026-04-19) | Documenta entradas faltantes do cap3; inclui `Wohlin2024` com DOI EASE alternativo |
| `results/raw/control_papers_bib.json` | Corpus SLR com DOIs de estudos incluídos (não substitui bib da tese) |
| `references.bib` | 417 entradas; 48 grupos de título duplicado no arquivo completo (não todos citados) |

---

## Ações recomendadas (ordem de prioridade)

1. **[BLOCKER]** Corrigir `bose2013trace` (DOI + vol/págs/ano).
2. **[BLOCKER]** Resolver `rubin2014process` — substituir por `rubin2007` ou fonte verificável; revisar claims “first framework” no cap2.
3. **[MAJOR]** Corrigir DOI `montgomery2022jira` → `10.1145/3524842.3528486`.
4. **[MAJOR]** Corrigir DOI `wohlin2014guidelines` e alinhar versão journal vs. conferência.
5. Remover duplicatas D1 (`whittaker1994` / `WhittakerThomason1994`) e D2 (`poncin2011` / `poncin2011process`).
6. Remover `jokwon2024` placeholder; padronizar chave `jo2024` → `Jo2024`.
7. Ajustar tipos BibTeX (`@inproceedings`) e recompilar para corrigir renderização ABNT de Aalst, Massitela, Joshi, Washizaki, Tyagi.
8. Completar páginas nas entradas de conferência listadas na auditoria.
9. Adicionar DOIs faltantes nas ~22 entradas clássicas sem DOI (melhora reproducibilidade, não corrige existência).

---

## Artefatos gerados nesta sessão

| Arquivo | Conteúdo |
|---------|----------|
| `results/auditoria_referencias_evidencias.md` | Este relatório |
| `/tmp/pathcast_ref_audit_evidence.json` | Resultado machine-readable por chave (98 entradas) |
| `/tmp/pathcast_unverified_batch.json` | Busca Crossref para clássicos sem DOI |

**Correções aplicadas em 2026-06-08** (`references.bib` + capítulos ativos + `latexmk -pdf main_patched.tex`):

- `bose2013trace`, `montgomery2022jira`, `wohlin2014guidelines`, `aalst2012process`, entradas `@inproceedings` (Joshi, Washizaki, Tyagi, Massitela), páginas faltantes, `jo2024`, `bhadra2023`
- Removidos: `rubin2014process`, `poncin2011`, `WhittakerThomason1994`, `jokwon2024`
- Citações atualizadas: `rubin2014process`→`rubin2007`; duplicatas Whittaker/Poncin consolidadas
- Bibliografia regenerada: **95 entradas** em `main_patched.bbl` (antes 98)

---

## Resposta direta à pergunta

> As referências da tese são todas válidas?

**Não.** A grande maioria (**~94/98**) corresponde a publicações reais, coerente com a conclusão favorável do material de auditoria sobre alucinação. Porém:

- **2 entradas citadas têm metadados invalidantes** (`bose2013trace`, `rubin2014process`).
- **3 entradas têm DOI/placeholder defeituoso** (`montgomery2022jira`, `wohlin2014guidelines`, `jokwon2024`).
- **3 pares duplicados** aparecem na bibliografia citada.
- **~15 entradas** têm defeitos de formatação que não negam existência, mas prejudicam rigor ABNT e rastreabilidade.

Para defesa com rigor de verificabilidade, tratar B1 e B2 como **bloqueantes**; o restante é correção editorial de alta prioridade.
