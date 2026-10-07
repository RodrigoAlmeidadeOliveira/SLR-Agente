# Conferência detalhada DRC × fonte (2026-09-05)

Auditoria contra o LaTeX atual (não contra o checklist anterior).  
Fontes: `anotacoes_DRC_TESE_20260610.md`, `prioridade_revisao_cap3_SLR_DRC.md`.

## Veredito

**Não: nem todos os itens foram atendidos plenamente.**

- **Cap. 3 (plano P0–P2 / A28–A41 + A11):** atendido de forma substantiva; residual menor (footnote de ICs nas bandas T/A).
- **Cap. 1 + resumo/abstract + Cap. 2 (A1–A27, fora Cap. 3):** quase completo; **A8 parcial**; resíduos de hedging/juízo; PDF desatualizado.
- **Elogios (E\*/A2/A10/A22/A23/A26/A42):** N/A.

---

## 1. Cap. 3 — plano `prioridade_revisao_cap3_SLR_DRC.md`

| Item plano | IDs DRC | Status verificado | Evidência |
|------------|---------|-------------------|-----------|
| P0-1 Def. única L0–L3 | A38, A39, A41 | **DONE** | `cap3_slr_revised.tex` ~95–125, `tab:il-def`; “L3 architecture” só na frase de proibição; TF-*; `tab:positioning` alinhada; PATHCAST em nota |
| P0-2 Classificação + level | A28, A29, A30 | **DONE** | Três eixos ~18–90; “level” não “degree”; RQ3.1 → `tab:il-def` |
| P0-3 Gap ↔ dor | A40 | **DONE** | Abertura Research Gap ~1550–1560 com dor operacional |
| P1-1 PICO C | A32 | **DONE** | Omitido by design + tabela PICO |
| P1-2 Control papers | A35 | **DONE** | Critério a priori + 10 papers vs 12 records |
| P1-3 Tipos de MP | A33 | **DONE** | `tab:block-i-pm-types` |
| P1-4 QA2/3/7 + reprodut. | A36, A37 | **DONE** | Rubricas + frase “designed to pass QA3/QA7” |
| P1-5 IC/EC float | A34 | **DONE** | `[H]` + `\FloatBarrier` |
| P2-1 Siglas | A11 | **DONE** | `glossary.tex`: SPMF, PPM, CRPS, L0–L3, AD1–AD4, QA, TF-* |
| P2-2 Lacuna G1–G3 | A31 | **DONE** | Tabela RQs + §RQ3.2 |
| P2-3 Tabela 3.15 | A41 | **DONE** | `tab:positioning` reeditada |

**Residual Cap. 3 (não anula DONE):** possível uso de “ICs” sem qualificativo IC4a–d em nota de bandas T/A (checar ~L684 no PDF/fonte se ainda existir após sync). “L3 architecture” aparece só como termo proibido.

**Itens “fora do Cap. 3” no mesmo arquivo** (A12, A15, A24, A1, A7, A17, A18): ver §2 — **não** todos plenos.

---

## 2. Catálogo completo `anotacoes_DRC_TESE_20260610.md`

### Elogios / N/A
E1–E7, A2, A10, A22, A23, A26, A42 — sem correção exigida.

### Front matter + Cap. 1–2

| ID | Pedido | Status | Nota |
|----|--------|--------|------|
| A1 | Padronizar pipeline | **DONE*** | Convenção tripla Cap.1 + nota Cap.4 + glossário L2. \*Não é varredura linha-a-linha de Cap.5–6/apêndices; usos legítimos de “pipeline” restam. |
| A3 | Verbo do resumo | **DONE** | “propõe” / “proposes” |
| A4 | “base mais informativa” | **DONE** | Removido; dor operacional no lugar |
| A5–A7 | Objetivo único + verbo | **DONE** | Resumo/abstract/Cap.1 alinhados (PM+Markov+MC+ML) |
| A8 | “repositórios de software” | **PARTIAL** | Corrigido no resumo/abstract e no objetivo. **Residual Cap.1:** “software repositories” / “open-source software repositories” (ex.: discovery early apps; C5; Activity 4; estrutura do doc). |
| A9 | “distribuições de resultados” | **DONE** | Definido em resumo, abstract e objetivo |
| A11 | Lista de siglas | **DONE** | Glossário completo (ver Cap.3) |
| A12 | Dor antes de PM | **DONE** | Abertura “when will this be done?” |
| A13 | Evitar juízo de valor | **DONE*** | Sem “bridges the gap”. \*Residual: “fine-grained process event data” (~L48) ainda valorativo leve. |
| A14 | Citações pré-manifesto | **DONE** | Contextualizadas + manifesto |
| A15 | Dores + trabalhos + limites | **DONE** | Triade Pain / What exists / Limitation |
| A16 | Refs. fragmentação | **DONE** | Citações por técnica |
| A17–A18 | Objetivo ≠ contribuição | **DONE** | Seções separadas; hipóteses antes dos objs. específicos |
| A19 | “proposed hypotheses” | **DONE** | Hipóteses introduzidas antes |
| A20 | Obj. empírico ↔ dor/lacuna | **DONE** | Obj.4 explícito |
| A21 | RQs × objs × método | **DONE** | `tab:rq-obj-map` |
| A24 | Relacionados dor/contrib/lim. | **DONE** | §Justification |
| A25 | Contribuições ↔ dor | **DONE** | Pain/gap em C1–C5 |
| A27 | Potencial/limitações Cap.2 | **DONE** | Incl. `conf(c)` |

### Cap. 3 (A28–A41)
Todos **DONE** na fonte — ver §1.

### Cap. 4
A42 elogio apenas; banca sem anotações após p.67.

---

## 3. Lacunas explícitas (ainda abertas)

| # | Severidade | O quê | Ação sugerida |
|---|------------|--------|----------------|
| 1 | **PARTIAL A8** | “open-source software repositories” / “software repositories” no Cap.1 onde o sentido é MSR/OSS | Trocar para “open-source development-process repositories” / “software development process repositories” onde for o objeto da previsão; manter “MSR / mining software repositories” quando for o nome do campo |
| 2 | **MINOR A13** | “fine-grained process event data” | Neutralizar: “high-resolution time-stamped event data” |
| 3 | **MINOR (Phase 2.6)** | Cap.1 ~L164: “has not been established as a named, reproducible method…” sem hedge | Acrescentar “to the best of our knowledge” / “not identified in the SLR corpus (Ch.~3)” |
| 4 | **MINOR Cap.3** | Footnote “ICs” sem IC4a–d | Qualificar “content ICs (IC4a–d)” se a frase ainda existir |
| 5 | **BLOCKER de entrega** | PDF `main_patched.pdf` de **9 jun 2026** — Phase 6 falhou | Recompilar fora do Google Drive sync |
| 6 | **A1 escopo global** | Cap.5/6/apêndices não reescritos sob a convenção | Aceitável se a convenção Cap.1+4 for a norma; opcional: grep + qualificar CI/CD |

---

## 4. Contagem

| Classe | Qtd (aprox.) |
|--------|----------------|
| N/A (elogio) | 13 |
| DONE pleno | ~35 IDs de correção |
| PARTIAL | 1 (A8) + resíduos A1/A13/novelty |
| NOT-DONE de conteúdo DRC | 0 nos Caps. 1–3 anotados |
| Entrega PDF fresca | **não** |

**Resposta direta:** o conteúdo pedido pela banca nos Caps. 1–3 e front matter está **quase todo** no fonte; **não** está “plenamente” fechado enquanto A8 residual, hedges menores e sobretudo o **PDF desatualizado** permanecerem.
