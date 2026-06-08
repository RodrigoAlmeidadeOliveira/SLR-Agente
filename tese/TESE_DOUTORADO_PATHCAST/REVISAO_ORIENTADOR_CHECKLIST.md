# Checklist — Revisão do Orientador (Caps. 2–5)

Status: ✅ feito · 🟡 precisa de confirmação do autor · ⬜ pendente/opcional (não feito)
Branch: `claude/thesis-advisor-feedback-F0L7I`

## Re-avaliação final (usando a skill paper-validation-review v3.0)

Itens adicionais do orientador fechados nesta rodada de re-avaliação:

| Item | Local | Status |
|------|-------|--------|
| "Full-Text Screening" → "Eligibility Screening (Full-Text/Enriched-Abstract)" | cap3 §3.3.4 | ✅ |
| Cook & Wolf: Markov como modelagem/inferência, não forecasting moderno | cap3 §3.4.6 | ✅ |
| "Design and architecture not the primary focus of any study" suavizado | cap3 §3.4.5 | ✅ |
| "no systematic disagreement" vs re-extração → reformulado como boa prática | cap3 §3.6.4 | ✅ |
| Taxonomia SDLC: nota "canônica mínima + extensões permitidas" | cap4 §4.2.3 | ✅ |
| Mapeamento PM→estado de Markov formalizado (estado ≡ atividade) + absorventes generalizados | cap4 §4.3 | ✅ |
| "on-time vs delayed" pressupõe prazo/SLA/sprint — explicitado | cap2 §2.5 | ✅ |
| "process backbone" definido formalmente | cap2 §2.7 | ✅ |

Itens RESOLVIDOS na rodada de fechamento (com dados rastreados):

- ✅ **Split EC5 → EC5/EC6/EC7**: re-classifiquei os dados. Working-set EC5 =
  **145** (todos texto-inacessível, causa única confirmada pelos rationales).
  Auxiliar: **EC6 (metadados insuficientes) = 611** (595 sem abstract + 16
  pending residual) e **EC7 (discordância irreconciliável) = 52** (10 ws_TA +
  42 aux_FT). Critérios separados na tabela; "EC5-extended" eliminado do texto.
- ✅ **Reliability diagram** adicionado às métricas (cap5 §5.4) como artefato de
  calibração visual.
- ✅ **Comparação Markov-analítico × Monte-Carlo** adicionada (cap5 §5.5,
  ablação B3 vs Stage 4 — ganho da camada de simulação).
- ✅ **Arquitetura conceitual**: já existia `fig:pipeline-architecture`
  (R→S1→S2→S3→S4→ML→Forecast); reforçada com parágrafo de visão conceitual
  end-to-end antes dos detalhes algorítmicos (cap4 §4.1).
- ✅ **Ética §5.2.5** expandida (dados públicos, unidade de análise não é o
  indivíduo, conformidade ToS/Jira, risco mínimo, replicação).
- ✅ **Augusto (2019) + Bose & van der Aalst (2013)** citados na seção de
  entropia de variantes (cap4 §4.3), com enquadramento Phase-9-compliant
  (complexidade/variabilidade comportamental, não "definem entropia"); entrada
  `bose2013trace` adicionada ao `references.bib`.

Remanescente menor:
- ⬜ Enumerar explicitamente os eventos de PR coletados (created/reviewed/
  merged/closed) em §5.2.3 — cosmético.

## Skill de revisão de artigos

- ✅ **paper-validation-review atualizada para v3.0** em
  `.claude/skills/paper-validation-review/SKILL.md`, codificando os padrões de
  revisão do orientador como novos checks:
  - Phase 8 — Aggregation & De-duplication Integrity (pega soma cega de tiers /
    aritmética de funil que não fecha — teria pego 381 inflado)
  - Phase 9 — Citation–Claim Semantic Validation (Wohlin2024 vs 2014)
  - Phase 10 — Mathematical Rigor & Terminology (theorem→proposition,
    quasi-stationary vs QSD, Wald vs Wilson, escala classe×probabilidade)
  - Phase 2.6 — Claim-Strength & Hedging (first/only/never; causal)
  - Extensões: sanidade temporal, colisão de namespace (L0–L3 vs L1–L4),
    interpretação conjunta de κ, completude de definição de métricas,
    `\input{}`-tabela ↔ narrativa, provenance de extração por LLM
  - Honesty Invariants #10–#13 + protocolo de Reconciliação de Feedback do
    Orientador + estudo de caso PATHCAST Cap. 3/4 + contrato de regressão

Commits: `259ac71`, `c3b616c`, `4e03e62`, `250f816`, `732b624`, `9ab293b`, `9dd7fea`

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
| O.9 | Comparação Markov Analítico × Monte Carlo | cap5 §5.5 (ablação B3 vs Stage 4, plano de avaliação) | ✅ (corrigido: estava marcado ⬜ por engano) |
| O.10 | Reliability diagram (calibração) | cap5 §5.4 (paragraph "Reliability diagrams") | ✅ (corrigido: estava marcado ⬜ por engano) |
| O.11 | Citar Augusto et al. (2019) / Bose & van der Aalst (2013) p/ entropia | cap4 §4.3 (`\cite{bose2013trace, augusto2019}`, enquadramento Phase-9) | ✅ (corrigido: estava marcado ⬜ por engano) |
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

## Opção A APLICADA — de-duplicação cross-tier propagada (381→319, 404→341)

De-duplicação rigorosa por título normalizado sobre os arquivos
`extraction_combined_381.csv` / `qa_combined_381.csv` (lógica validada:
reproduz exatamente IC, dataset_public=56, replication=11, QA=315/381,
ML=131, Jira=55, GitHub=51 sobre os 381 originais).

Números corrigidos e propagados em todo o Cap. 3:

| Quantidade | Bruto | De-duplicado |
|------------|-------|--------------|
| Combinado analítico (1ª passagem) | 381 | **319** (169 + 150 únicos) |
| Combinado final | 404 | **341** (169 + 150 + 22) |
| Novos auxiliares 1ª passagem | 212 | **150** (−60 cross-tier, −2 internos) |
| Novos auxiliares 2ª passagem | 23 | **22** (−1 cross-tier) |
| F1: IC1 / IC3 / IC1-só | 203(53.3%)/116(30.4%)/91(23.9%) | **162(50.8%)/100(31.3%)/78(24.5%)** |
| F2: público / replicação | 56(14.7%)/11 | **44(13.8%)/9** |
| F3: IC2 / IC2∩IC3 / IC1∩IC2 | 181(47.5%)/93(24.4%)/16(4.2%) | **158(49.5%)/81(25.4%)/13(4.1%)** |
| F4: IC1∩IC3 | 13(3.4%) | **10(3.1%)** |
| F5: ML / ML+PM | 131 / 4 | **111 / 2** |
| QA combinado retido | 315/381 | **260/319 (81.5%)** |

Tabelas auto-geradas regeneradas: `aux_qa_summary.tex` (319/260),
`aux_ft_summary.tex` (319, com linha "unique 150"). Aritmética falsa
"3.807 = 5.783 − 2.340" removida em todos os pontos.

## Itens que ainda dependem da SUA decisão

- 🟡 **Validação da de-dup**: usei correspondência por título normalizado
  (DOI não casava — exatamente a causa do problema). Recomendo confirmar
  com sua de-dup oficial; pode haver ±poucos por títulos quase-idênticos de
  versões distintas (workshop vs journal). O split estocástico (MC/Markov/SPN)
  e contagens vcs/issue usam keyword-scan que reproduz o original com desvio
  de ≤3 — recomputei consistentemente sobre o conjunto de-dup.
- 🟡 Datas de coleta por repositório no Apêndice (O.8): o snapshot global é
  2026-04-12; faltam as datas individuais por repositório, se desejar granularidade.

---

## Rodada de fechamento adicional (2026-06-07) — gaps não rastreados antes

Auditoria cruzada entre o PDF de sugestões do orientador e o estado real dos
arquivos revelou itens que NÃO constavam neste checklist (ou marcados ✅ mas
incompletos). Aplicados e compilados (`pdflatex` draftmode EXIT=0, sem
undefined refs):

| # | Item | Local | Status |
|---|------|-------|--------|
| N.1 | **`precision(L,M) ≥ 0.5`** adicionado ao critério de aceitação (antes só fitness/coverage/\|S_T\|/\|L_test\|) + justificativa flower-model | cap5 §5.3, `eq:acceptance` | ✅ |
| N.2 | **conf(c) unificado**: cap2 (eq 2.2) estava como *match-ratio* e cap4 como *cost-based* — divergência real. Padronizado na forma cost-normalizada de alinhamento (Adriansyah) nos dois: `conf(c)=1−cost(γ*_c)/cost(γ_worst,c)` | cap2 `eq:case-conformance-cap2`, cap4 `eq:case-conformance` | ✅ |
| N.3 | **ACE: citação corrigida** — checklist 5.8 citava `gneiting2007strictly` (= ref de CRPS, errada para ACE). Trocado por `kuleshov2018calibrated` (quantile calibration) + `naeini2015obtaining` (ECE). Entradas novas em `references.bib` | cap2 §2.4 | ✅ |
| N.4 | **Def. formal `Repository Snapshot R^(t)`** (`\begin{definition}`), antes só nota em prosa | cap5 §5.2, `def:repo-snapshot` | ✅ |
| N.5 | **Def. formal `LOPO Generalization`** (`\begin{definition}` com Train/Test), antes só prosa | cap5 §5.4, `def:lopo` | ✅ |
| N.6 | **process backbone**: def PRÉVIA formal na §2.1 (estava só in-loco na §2.7) | cap2 §2.1 | ✅ |
| N.7 | **Mapeamento PM→Markov com símbolo `f_M : M → S`** + absorventes estruturais `S_A={s∈S : outdeg_M(s)=0}` (antes só "estado≡atividade" em prosa) | cap4 §4.3, `def:state-space` | ✅ |
| N.8 | **Justificativa da ausência de termos ML** nas search strings (machine/deep learning, LSTM, transformer) + captura via campo ML Technique post-hoc — orientador #4/#11 | cap3 §3.2 | ✅ |
| N.9 | **Features 6/7** reescritas como `E[T\|s=μ(e_last)]` e `Pr[absorb in done\|s=μ(e_last)]` | cap4 §4.6, feature table | ✅ |
| N.10 | **Hedge em 3 spots faltantes**: caption `tab:gap` ("to the best of the author's knowledge"), F4 ("was not identified" vs "has not been proposed"), data de execução junto ao **IC1 na tabela** de critérios | cap3 | ✅ |
| N.11 | **Tabela 5.2** marcada "(preliminary; 44/48)", células "–" → "pending" (dado de harvest dos 48 repos NÃO existe no SLR-Agente; pipeline é só SLR; pertence ao cap7) | cap5 §5.2 | ✅ |
| N.12 | **PR events enumerados** em §5.2.3 (created/reviewed/approved/merged/closed) — fecha o "Remanescente menor" | cap5 §5.2.3 | ✅ |
| N.13 | **Arquitetura Conceitual** confirmada já presente (cap4 §"Architectural Overview": R→S1→S2→S3→S4→ML→Forecast + fig DAG antes dos detalhes algorítmicos) — sugestão pág.1 do PDF | cap4 §4.1 | ✅ |

### Correção de contradições internas deste checklist
O.9 / O.10 / O.11 estavam marcados ⬜ na tabela OPCIONAIS mas ✅ na seção
"Re-avaliação final". Verificação no arquivo confirmou os três FEITOS; linhas
corrigidas para ✅.

### Permanece dependendo de você
- 🟡 **Validação da de-dup** (Opção A 381→319 / 404→341; 3441→3807) — match por
  título normalizado; confirmar vs dedup oficial.
- 🟡 **Datas por-repositório** no appendix (O.8) — snapshot global 2026-04-12 ok.
- ⬜ **Dados da Tabela 5.2** — harvest dos 48 repos não está no repo (cap7, em
  preparação); rastreio confirmou ausência de fonte. "227.000 commits" sem
  proveniência rastreável no SLR-Agente.

> Compilação: `pdflatex -interaction=nonstopmode -draftmode main_patched.tex`
> → EXIT=0, sem `! errors`, sem `Undefined control sequence`. Bibliografia
> (cites novos `kuleshov2018calibrated`, `naeini2015obtaining`) entra no
> próximo build completo com bibtex/biber.
