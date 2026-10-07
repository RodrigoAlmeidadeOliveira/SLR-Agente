# Checklist de reconciliação — anotações DRC × tese

Fonte: `anotacoes_DRC_TESE_20260610.md`  
Protocolo: Advisor-Feedback Reconciliation (skill `paper-validation-review` v3)  
Atualizado: 2026-09-05

Legenda: **DONE** | **PARTIAL** | **NOT-DONE** | **DEFERRED** | **N/A (elogio)**

| ID | Tema | Severidade | Status | Onde / nota |
|----|------|------------|--------|-------------|
| E1–E7 | Elogios | — | N/A | Sem ação |
| A1 | Padronizar *pipeline* | MINOR | DONE | Convenção tripla em Cap.~1; Cap.~4 `def:pipeline`; L2 no glossário; CI/CD qualificado |
| A2 | Declaração IA | — | N/A | Elogio |
| A3 | Verbo do resumo | MAJOR | DONE | `frontmatter/resumo.tex` + `abstract.tex` |
| A4 | “base mais informativa” | PRIORIDADE | DONE | Substituído por formulação operacional |
| A5–A7 | Objetivo único / verbo de dizer | PRIORIDADE | DONE | Resumo + Cap.~1 §Objectives alinhados a 1.2.1 |
| A8 | “repositórios de software” | PRIORIDADE | DONE | Cap.~1: process repositories; MSR nomeado só como campo; residual C5/Act.~4 fechado 2026-09-05 |
| A9 | “distribuições de resultados” | PRIORIDADE | DONE | Definido: distribuições de tempo/trajetória/desfecho |
| A10 | Contribuição no resumo | — | N/A | Elogio |
| A11 | Siglas (SPMF…) | PRIORIDADE | DONE | Cap.~3 plan: `glossary.tex` (2026-08-13) |
| A12 | Dor antes de PM | PRIORIDADE | DONE | Abertura Cap.~1 (slides 4–5) |
| A13 | Evitar juízo de valor | MINOR | DONE | Sem “bridges the gap”; “fine-grained” → “high-resolution time-stamped” (2026-09-05) |
| A14 | Citações PM pré-manifesto | PRIORIDADE | DONE | Contextualizadas + manifesto 2011 |
| A15 | Dores + trabalhos + limitações | PRIORIDADE | DONE | §Research Problem + slides 3/5 |
| A16 | Refs. para fragmentação | PRIORIDADE | DONE | Citações por técnica isolada |
| A17–A18 | Objetivo ≠ contribuição | MAJOR | DONE | §Objectives reescrito |
| A19 | “proposed hypotheses” | MINOR | DONE | Hipóteses introduzidas antes dos objetivos específicos |
| A20 | Obj. empírico ↔ motivação/lacuna | MAJOR | DONE | Ligação explícita no item 4 |
| A21 | RQs × objetivos × método | MAJOR | DONE | Tabela de mapeamento |
| A22–A23 | Elogios | — | N/A | — |
| A24 | Relacionados: dor/contrib./lim. | PRIORIDADE | DONE | §Justification reestruturada |
| A25 | Contribuições ↔ dor/lacuna | PRIORIDADE | DONE | Cada C1–C5 ligada à dor |
| A26 | Metodologia | — | N/A | Elogio |
| A27 | Potencial/limitações Cap.~2 | PRIORIDADE | DONE | `cap2_reduced.tex`: parágrafos Potential/Limitations por seção + `conf(c)` |
| A28–A41 | Protocolo SLR Cap.~3 | PRIORIDADE | DONE* | DRC done; *2026-09-05 sync números 318/340 + human validation from IST paper — see `sync_cap3_tese_vs_paper_IST.md` |
| A42 | Fig. 4.2 | — | N/A | Elogio |

## Slides da qualificação (3–7) → Cap.~1

| Slide | Conteúdo | Destino na tese |
|-------|----------|-----------------|
| 3 | Teto descritivo / cegueira estrutural / fragmentação | §Research Problem |
| 4 | “Quando isto vai ficar pronto?” + fluxo + event logs | Abertura do capítulo |
| 5 | Limitações do MC de throughput | §Research Problem (2º problema) |
| 6 | PATHCAST process-aware | Fecho da abertura + ponte para Cap.~4 |
| 7 | Markov + MC + ML (por quê) | §Research Problem (3º) + H3 / contribuições |

## Próximo ciclo (fora deste passe)

1. ~~Recompilar PDF~~ — `main_patched.pdf` regenerado 2026-09-05 (~259 pp.; App.~J lista 340 + App.~K SEGRESS)
2. ~~Portar apêndice SEGRESS / lista 340~~ — DONE
3. ~~Citation `\cite{...}` Cap.~7~~ — DONE (`oliveira2026mcsml`)
4. Revisar Cap.~4+ se a banca estender anotações além da p.~67

## Resíduos Cap.~1 fechados em 2026-09-05

- A8: C5 / Activity 4 / discovery early apps / figura DSR → *software development process repositories* / *OSS process repos*
- A13: *fine-grained* → *high-resolution time-stamped*
- Phase 2.6: novidade hedged com *to the best of our knowledge* + escopo Cap.~3
- Cap.~2: MSR nomeado como campo (não “software repositories” genérico)
