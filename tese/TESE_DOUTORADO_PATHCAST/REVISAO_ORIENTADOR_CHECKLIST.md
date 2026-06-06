# Checklist — Revisão do Orientador (Caps. 2–5)

Status: ✅ feito · 🟡 precisa de confirmação do autor · ⬜ pendente/opcional (não feito)
Branch: `claude/thesis-advisor-feedback-F0L7I` · Commits: `259ac71`, `c3b616c`

> Observação: não há LaTeX no ambiente — recomenda-se rodar `latexmk -pdf main_patched.tex`
> localmente para confirmar a compilação antes da banca.

---

## TIER 1 — Consistência numérica / factual (bloqueante)

| # | Item | Local | Status |
|---|------|-------|--------|
| 1.1 | Escopo temporal: "dez/2026" → busca em abr/2026, elegibilidade 1994–2025 | cap3 §3.2.1; External Validity | ✅ |
| 1.2 | ACM DL "3 queries" → 2 (alinhado à lista de queries) | cap3 tab:retrieval | ✅ |
| 1.3 | κ auxiliar: Po 84,8% → **54,3%** (valor real de `aux_kappa_report`) | cap3 §3.6.2 | ✅ |
| 1.4 | Aritmética falsa "3.807 = 5.783−2.340" removida; 3.441 + 366 = 3.807 consistente | cap3 §3.3.2, §3.6.3, fig. PRISMA | ✅ |
| 1.5 | **Reconciliação 3.441 → 3.807 (os 366 registros)** | cap3 | 🟡 **confirmar com dados brutos** |
| 1.6 | Power: conflito 0,72 vs 0,55 → 0,55 (medium, nível ajustado) | cap5 §5.6, conclusion validity | ✅ |
| 1.7 | Numeração de equações na tabela de métricas: "Eq. 4.15" → `\ref` | cap5 tab:metrics-rq1 | ✅ |
| 1.8 | "excluded from the synthesis" → "evidence synthesis (F1–F5), retido no PRISMA" | cap3 §3.2.4 | ✅ |
| 1.9 | Funil topo (7.740+595+12 = 8.347) | cap3 | ✅ já consistente (SpringerLink presente) |

---

## TIER 2 — Vulnerabilidades metodológicas

| # | Item | Local | Status |
|---|------|-------|--------|
| 2.1 | Corpus auxiliar reposicionado como robustez/recall-bounding (não evidência primária) | cap3 §3.4.1, §3.6.2 | ✅ |
| 2.2 | κ=0 explicado (degeneração sob desbalanceamento) + limite do peso probatório | cap3 §3.6.2 | ✅ |
| 2.3 | Salvaguarda full-text: campos ausentes = missing; explicação dos 2 PDFs não codificados | cap3 §3.4.2 | ✅ |
| 2.4 | Parâmetros do LLM de extração (temperature=0, modelo fixo, schema JSON) | cap3 §3.4.2 | ✅ |
| 2.5 | QA8 condicionado a "não aplicável" para estudos não-PM (remove viés) | cap3 §3.2.5 | ✅ |
| 2.6 | Taxa de discordância field-level no pacote de replicação (mencionada) | cap3 §3.4.2 | ✅ |

---

## TIER 3 — Rigor matemático (Cap. 4)

| # | Item | Local | Status |
|---|------|-------|--------|
| 3.1 | "quasi-stationary" → ocupação esperada (transiente); distinção da QSD clássica | cap4 §4.4 | ✅ |
| 3.2 | Teorema 4.1 → **Proposition** (correção composicional); env `proposition` no preâmbulo | cap4; main_patched | ✅ |
| 3.3 | Contradição Kmax × Propriedade de absorção resolvida (Kmax = salvaguarda defensiva) | cap4 prova | ✅ |
| 3.4 | SE de transição: Wald aproximado; Wilson para n pequeno/p extremo | cap4 §4.4 | ✅ |
| 3.5 | Algoritmo MC: não-absorvidas separadas (contador); denominador sobre absorvidas | cap4 alg:mc-full | ✅ |
| 3.6 | Estados terminais generalizados via `S_done ⊆ S_A` (GitHub/GitLab, não só Jira) | cap4 §4.5 | ✅ |
| 3.7 | Eq. deviation score na escala de probabilidade (não classe) | cap4 §4.6 | ✅ |
| 3.8 | Critério de convergência também na cauda (P85/P95) | cap4 §4.5 | ✅ |
| 3.9 | "exact replication" → "deterministic … same software environment" | cap4 §4.5 | ✅ |
| 3.10 | "Perfect Fitness by Construction" → garantia de replay (suavizado) | cap4 §4.3 | ✅ |
| 3.11 | Completion probability denominador corrigido (M_abs) | cap4 §4.5 | ✅ |

---

## TIER 4 — Hedging de novidade

| # | Item | Local | Status |
|---|------|-------|--------|
| 4.1 | "PATHCAST is proposed as the first such L3 system" → "to the best of our knowledge…" | cap3 §3.4.6 | ✅ |
| 4.2 | "first formally specified pipeline" → "no study identified in this review…" | cap3 §3.7 | ✅ |
| 4.3 | IMf "the only sound algorithm" → "among the few…" | cap2 §2.1 | ✅ |
| 4.4 | "integration has not been previously proposed" → "to the best of our knowledge…" | cap2 §2.7 | ✅ |
| 4.5 | "the first proposal, to the best of the author's knowledge" (já adequado) | cap3 §3.5 | ✅ mantido |

---

## TIER 5 — Clareza / coerência

| # | Item | Local | Status |
|---|------|-------|--------|
| 5.1 | Colisão de níveis: Analytical Depth L1–L4 → **AD1–AD4** (L0–L3 = integração) | cap3 §3.5 | ✅ |
| 5.2 | Arquitetura (figura) vs abstração funcional (contratos) explicitada | cap4 §4.1 | ✅ |
| 5.3 | Social networks marcadas como features opcionais do ML | cap4 §4.1 | ✅ |
| 5.4 | N, B consumidos pelo ML (não só análise) — explicitado | cap4 §4.1 | ✅ |
| 5.5 | "operating on temporal dimension of the past" → camada histórica pré-forecasting | cap4 §4.1 | ✅ |
| 5.6 | "Completeness" → closed-case ratio (repos vivos têm casos abertos) | cap4 §4.2 | ✅ |
| 5.7 | taphonomic bias com glosa na 1ª ocorrência | cap2 §2.2 | ✅ |
| 5.8 | ACE distinguido de ECE + citação (`gneiting2007strictly`) | cap2 §2.4 | ✅ |
| 5.9 | LSTM como baseline consolidada (justificativa) | cap2 §2.5 | ✅ |
| 5.10 | "point predictions" → "case-level predictions" | cap2 §2.7 | ✅ |
| 5.11 | Entropia → proxy (relação causal suavizada) | cap2 §2.6, §2.7 | ✅ |
| 5.12 | Correspondência 1:1 caso↔traço explicitada | cap2 §2.1 | ✅ |
| 5.13 | "candidate-generation cost" → "effort to identify/collect repositories" | cap2 §2.2 | ✅ |
| 5.14 | Mersenne Twister: "exactly reproducible" → sob seeds/ambiente fixos | cap2 §2.3 | ✅ |
| 5.15 | "PATHCAST mitigates" → "partially mitigates" (Markov) | cap2 §2.3 | ✅ |
| 5.16 | O(1/√M) "independent of dimension" → "convergence rate regardless of dimensionality" | cap2 §2.3 | ✅ |
| 5.17 | Gatilhos de retraining (calendário / limiar de degradação) | cap4 §4.7 | ✅ |

---

## TIER — Cap. 5 (avaliação): definições e ameaças

| # | Item | Local | Status |
|---|------|-------|--------|
| C5.1 | Alvo de previsão definido (total lead time) | cap5 §5.7 | ✅ |
| C5.2 | Completion Accuracy formalizada com threshold τ (Eq.) | cap5 §5.4 | ✅ |
| C5.3 | CRPS como métrica primária justificada (distribuições, não pontos) | cap5 §5.4 | ✅ |
| C5.4 | PI central 85% explicitado [Q0.075, Q0.925] | cap5 §5.4 | ✅ |
| C5.5 | MAPE: exclusão de lead time zero | cap5 §5.4 | ✅ |
| C5.6 | Ameaça: process drift (estacionariedade) | cap5 §5.7 | ✅ |
| C5.7 | Ameaça: simplificação Markov 1ª ordem | cap5 §5.7 | ✅ |
| C5.8 | Ameaça: OSS vs industrial | cap5 §5.7 | ✅ |
| C5.9 | Ameaça: subjetividade do mapeamento da taxonomia SDLC | cap5 §5.7 | ✅ |
| C5.10 | Reprodutibilidade: liberar seeds (MT19937) + configs | cap5 §5.7 | ✅ |
| C5.11 | GitHub bias reforçado (arquitetura independente, avaliação só GitHub) | cap5 §5.7 | ✅ |

---

## TIER 1.3 — Capítulos 6–8 (decisão estrutural)

| # | Item | Local | Status |
|---|------|-------|--------|
| 6.1 | `\include` dos caps. 6/7/8 comentados (build parcial) | main_patched.tex | ✅ |
| 6.2 | Arquivos stub preservados (reativar quando redigidos) | capitulos/ | ✅ |
| 6.3 | `\ref` pendentes neutralizados ("in preparation") no conjunto compilado | cap1, cap3, cap4, cap5, apêndices | ✅ |

---

## OPCIONAIS — recomendados pelo orientador, ainda NÃO aplicados

| # | Item | Motivo de ter deixado para depois | Status |
|---|------|-----------------------------------|--------|
| O.1 | Reforçar resumo §4.9 com a versão "4 níveis" sugerida pelo orientador | Resumo atual existe e é funcional; reescrita é melhoria de impacto, não correção | ⬜ |
| O.2 | Reforçar resumo §5.8 (versão expandida sugerida) | idem | ⬜ |
| O.3 | Dividir Figura 3.6 em 3.6a (níveis de integração) e 3.6b (prioridade de leitura) | Legenda já nomeia ambas as dimensões; divisão é cosmética | ⬜ |
| O.4 | Justificativa DSR + caracterização Gregor & Hevner nível 2 (§5.1) | Texto pronto fornecido pelo orientador; colar quando revisar o Cap. 5 | ⬜ |
| O.5 | Subseção 5.2.0 "Dataset Rationale" (por que 48 repositórios) | Conteúdo está na versão completa cap5_methodology.tex (não compilada) | ⬜ |
| O.6 | Definição formal da função de seleção de repositórios (Def. 5.1) | idem | ⬜ |
| O.7 | Figura de fluxo de seleção/enriquecimento de repositórios (Fig. 5.1) | Diagrama novo; requer decisão de layout | ⬜ |
| O.8 | Snapshot de coleta congelado (Def. 5.2) + datas de coleta | Datas reais necessárias do autor | 🟡 |
| O.9 | Comparação Markov Analítico × Monte Carlo (ganho do Stage 4) | Métrica/experimento adicional; pertence ao cap. de avaliação (em preparação) | ⬜ |
| O.10 | Reliability diagram como artefato visual de calibração | Pertence ao cap. de avaliação (em preparação) | ⬜ |
| O.11 | Citar Augusto et al. (2019) / Bose & van der Aalst (2013) p/ entropia–complexidade | Verificar se as chaves existem no `references.bib` | ⬜ |
| O.12 | Hipóteses estatísticas explícitas (H0/H1) para RQ3 | Melhoria de formalização da §5.6 | ⬜ |

---

## Itens que dependem do AUTOR (verificar antes da banca)

- 🟡 **1.5 / O.8** — composição exata do corpus auxiliar (3.441 vs 3.807) e datas de coleta dos snapshots: só você tem os contadores brutos das exportações.
- 🟡 Conferir que a chave `gneiting2007strictly` no `references.bib` corresponde a Gneiting & Raftery (2007), *Strictly Proper Scoring Rules*.
- 🟡 Revisar a referência Wohlin (WOHLIN; RUNESON, 2024) vs o clássico Wohlin (2014) de snowballing.
