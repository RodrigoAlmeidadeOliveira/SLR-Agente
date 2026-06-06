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

## OPCIONAIS — recomendados pelo orientador

| # | Item | Local / nota | Status |
|---|------|--------------|--------|
| O.1 | Reforçar resumo §4.9 com narrativa científica (4 níveis) | cap4 §4.9 | ✅ |
| O.2 | Reforçar resumo §5.8 (versão expandida) | cap5 §5.8 | ✅ |
| O.3 | Separar a figura combinada em duas (integração L0–L3 / prioridade) | cap3, fig:pdf-integration + fig:pdf-priority | ✅ |
| O.4 | Justificativa DSR + caracterização Gregor & Hevner nível 2 | cap5 §5.1 | ✅ |
| O.5 | Subseção "Dataset Rationale" (por que 48 repositórios) | cap5 §5.2 | ✅ |
| O.6 | Definição formal da função de seleção (Def.) | cap5 §5.2, def:repo-selection | ✅ |
| O.7 | Figura de fluxo de seleção/enriquecimento de repositórios | cap5 §5.2, fig:repo-selection (TikZ) | ✅ |
| O.8 | Snapshot de coleta congelado + datas | Nota de snapshot adicionada (cap5 §5.2); datas dependem do autor | 🟡 parcial |
| O.9 | Comparação Markov Analítico × Monte Carlo | Pertence ao cap. de avaliação (em preparação) | ⬜ (adiado) |
| O.10 | Reliability diagram (calibração) | Pertence ao cap. de avaliação (em preparação) | ⬜ (adiado) |
| O.11 | Citar Augusto et al. (2019) / Bose & van der Aalst (2013) p/ entropia | Orientador ambivalente ("método não cita"); `augusto2019` existe, Bose não | ⬜ (a critério) |
| O.12 | Hipóteses estatísticas explícitas (H0/H1) RQ2/RQ3 | cap5 §5.6, sec:hypotheses | ✅ |
| O.13 | Limiares de interpretação de Cliff's δ (Kampenes) | cap5 §5.6 (extra) | ✅ |
| O.14 | Justificativa estratificação + threshold 50 runs CI/CD | cap5 §5.2 (extra) | ✅ |

---

## Rastreamento dos dados da SLP no repositório (RESOLVIDO)

Fontes-verdade: `results/frozen/report_high_recall_2026-04-12.txt`,
`results/SLR_EXECUCAO_ATE_AGORA.md`, `results/auxiliary/aux_ta_summary.txt`,
`pipeline/sensitivity.py`, e contagens diretas dos CSVs.

| Item | Achado rastreado | Ação |
|------|------------------|------|
| **Data de coleta** | Snapshot congelado em **2026-04-12 15:47** (`results/frozen/`) | ✅ datas concretizadas (cap3 §3.2.1, External Validity) |
| **ACM queries** | Relatório: **3 queries** (Extra Refs 40 + Complementar MSR 32 + Principal 24 = 96). Meu ajuste anterior (3→2) estava ERRADO | ✅ revertido; `tab:retrieval`=3, `tab:db-adaptations`=3 |
| **`gneiting2007strictly`** | = Gneiting & Raftery (2007), *Strictly Proper Scoring Rules* — correto p/ CRPS | ✅ confirmado |
| **Citação snowballing** | cap3 citava `Wohlin2024` = livro *Experimentation in SE* (errado). Correto = `wohlin2014guidelines` (Wohlin 2014, snowballing) | ✅ corrigido em cap3 (compilado) |
| **3.441 vs 3.807** | `auxiliar = unique_papers.csv(5.783) − working_set ids`. Só **1.976** dos 2.340 ids da WS casam → aux = 5.783−1.976 = **3.807**. Os **364** restantes da WS divergiram de identificador na re-dedup high-recall e sobram no pool auxiliar como near-duplicates | ✅ reconciliação reescrita com a causa real (3 pontos do cap3) |
| **⚠️ 381/404 inflados** | **60 dos 212** includes auxiliares têm título idêntico a estudos da working set (0 match por DOI). Auxiliar contribui **~152 novos**, não 212 → combinado de-duplicado ≈ **321**, não 381 | 🟡 **decisão sua** — ver abaixo |

## Itens que ainda dependem da SUA decisão

- 🟡 **381/404 → ~321/~344**: o trace provou que o combinado contém ~60 duplicatas
  WS↔auxiliar. Marquei no texto como "recall upper bounds pendentes de
  de-duplicação cross-tier" e removi a afirmação (agora falsa) de que o auxiliar
  "não introduz estudos além dos confirmados". **Decisão**: (a) re-rodar a
  de-duplicação combinada e propagar 321/344 em todo o cap. 3, ou (b) manter como
  upper bounds documentados. Só você pode validar a de-dup definitiva.
- 🟡 Datas de coleta por repositório no Apêndice (O.8): o snapshot global é
  2026-04-12; faltam as datas individuais por repositório, se desejar granularidade.
