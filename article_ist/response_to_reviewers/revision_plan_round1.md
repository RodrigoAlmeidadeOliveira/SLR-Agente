# Plano de Revisão — Round 1 (Reviewer 1)

Manuscrito: *Process Mining and Stochastic Modeling for Software Process Forecasting: A Systematic Literature Review with an LLM-Assisted Protocol* (submissão IST/Elsevier, pacote `article_ist/`, `main.tex` de 15/mai/2026).

Arquivo-fonte principal a editar: `article_ist/cap3_article_body.tex` (também replicar em `overleaf_package/cap3_article_body.tex` e, se aplicável, em `main.tex` / `cover_letter.tex`).

Ordem de execução: por criticidade × esforço (mais crítico e mais barato primeiro).

---

## 1. [CRÍTICO / TRIVIAL] W3 — Corrigir período de busca (dez/2026 → data real)

**Problema:** `cap3_article_body.tex:153` declara busca até "December 2026" com submissão em maio/2026 — anacronismo lógico. Mesmo erro em `main.tex:116` ("1995–2026") e `cover_letter.tex:44`. Tabela 2 (linhas 165-169) também usa filtro "1994–2026" nas 4 bases.

**Boa notícia:** a redação correta já existe, feita por você em `tese/TESE_DOUTORADO_PATHCAST/capitulos/cap3_slr_revised.tex:176-181` (9/jun/2026), mas nunca foi propagada de volta ao artigo submetido:

> "The eligibility window for publications spans January 1994 to December 2025 (full calendar years), and the searches were executed on 12 April 2026; publications dated 2026 that were already indexed at execution time are therefore retained."

**Ações:**
- [ ] Substituir `cap3_article_body.tex:153` pela redação acima (adaptada ao tom do artigo).
- [ ] Corrigir Tabela 2 (linhas 165-169): trocar "1994–2026" por "1994–2025 (+ 2026 indexados na data de execução)" em cada base.
- [ ] Corrigir `main.tex:116` ("1995–2026" → mesma janela revisada).
- [ ] Corrigir `cover_letter.tex:44`.
- [ ] Adicionar uma frase explícita de reprodutibilidade: data exata de execução da busca (12/abr/2026) e política para publicações de 2026 já indexadas.
- [ ] Conferir se `appendix_slr.tex` e o pacote Zenodo (`SLR_PATHCAST_Replication_v1.zip`) citam a mesma janela — se não, gerar nova versão do pacote de replicação.

**Esforço:** ~30 min. Prioridade máxima — é o tipo de erro que mina credibilidade instantaneamente se reaparecer no round 2.

---

## 2. [ESTRUTURAL / CARO] W1 — Validação humana da triagem, QA e extração

**Problema:** κ reportado (T/A=0,695; FT=0,694) é cross-model (Haiku 4.5 vs. Sonnet 4.6), não humano-LLM. QA (linhas 345-390) é 100% LLM. Único elemento manual é o autor revisando apenas as decisões "include" (linhas 324-328) — não há segundo revisor humano cego. Extração de campos (PM-technique, stochastic-technique, SDLC-phase) teve só spot-check de 73 PDFs (linha 1700-1705), com re-extração humana sistemática marcada como "recommended before camera-ready" — ou seja, ainda não feita.

**Ações (por ordem de custo crescente, escolher o mínimo que blinda contra rejeição):**
- [ ] **Mínimo defensável:** amostra estratificada de double-screening humano independente (sugestão: 10% do T/A screening = ~234 papers do working set de 2.340, ou 20% do FT screening = ~177 papers) conduzida por você (ou um segundo avaliador, se disponível) sem ver as decisões do LLM. Reportar κ humano-LLM ao lado do κ cross-model já existente.
- [ ] Amostra equivalente para QA: repontuar manualmente ~15-20% dos 381 estudos (rubrica QA1-QA8) e reportar concordância humano-LLM.
- [ ] Completar a re-extração humana sistemática já prometida no texto (linha 1704) para os campos críticos (PM-technique, stochastic-technique, SDLC-phase) — mínimo na amostra de 381, idealmente nos 404.
- [ ] Atualizar a seção "LLM-Assisted Screening Methodology" (289-342) e "Conclusion Validity" (1700-1705) para reportar os novos números de concordância humano-LLM, não apenas cross-model.
- [ ] Se o esforço total não for viável antes do prazo de resubmissão, **ao menos** reformular a seção 289-342 para deixar explícito, sem ambiguidade, que a verificação é cross-model (já é feito em parte) e adicionar um plano de validação humana como *limitation + committed future work* com escopo e cronograma concretos — reduz a crítica de "falta de transparência" mesmo sem eliminar a limitação de fundo.

**Esforço:** alto se for fazer double-screening real (dias); baixo-médio se for apenas reforçar a limitação com plano concreto. **Decisão a tomar com você antes de escrever a carta:** qual das duas rotas seguir, pois muda o texto da response letter (comprometer-se a dados novos vs. reconhecer limitação e mitigar). Assumi na carta abaixo a rota "meio-termo": amostra parcial de double-screening + plano formalizado para o restante.

---

## 3. [REENQUADRAMENTO] W4 — Reduzir dominância retórica do PATHCAST

**Problema:** volumetricamente PATHCAST/SPMF ocupa só ~3-4% do corpo (Positioning 234 palavras, linhas 1397-1435; SPMF taxonomy 107 palavras, linhas 1436-1457), mas é citado ~15 vezes como gancho antecipatório ("PATHCAST addresses...", "PATHCAST targets...") dentro de RQ1-RQ3 (901-1277) e F1-F5 (1281-1396), criando impressão de teleologia.

**Ações:**
- [ ] Fazer um grep de "PATHCAST" em `cap3_article_body.tex` e listar todas as ocorrências fora das seções 1397-1483 (Positioning/SPMF/Research Agenda).
- [ ] Para cada ocorrência em RQ1-RQ3 e F1-F5: reescrever a frase para descrever o *gap* de forma neutra (sem nomear o framework do próprio autor como solução), OU mover a menção para a seção de discussão/agenda futura.
- [ ] Regra prática: nas seções de resultados objetivos (RQ1-RQ3, F1-F5), PATHCAST só pode aparecer em frases do tipo "this gap motivates frameworks such as PATHCAST (Section X)", nunca como "PATHCAST solves/addresses this by...".
- [ ] Revisar Abstract e Introdução (linhas 1-25) — checar se já antecipam PATHCAST como conclusão predefinida da revisão; se sim, suavizar.

**Esforço:** baixo-médio (~2-3h de reescrita pontual, sem mudar estrutura).

---

## 4. [REENQUADRAMENTO] W6 — PATHCAST como agenda, não contribuição validada

**Problema:** seção "Positioning of PATHCAST" (1397-1435, ~234 palavras) tem só uma tabela de níveis L0-L3 e descrição textual curta — sem contratos de estágio, I/O formal, protocolo de avaliação ou comparação com frameworks existentes. Se é apresentado como contribuição, está subespecificado; como agenda de pesquisa, está adequado.

**Ações (ligadas ao W4 — mesma reescrita, resolver junto):**
- [ ] Renomear a seção de "Positioning of PATHCAST" para algo como "PATHCAST: An Emerging Research Agenda" (ou similar), deixando explícito no primeiro parágrafo que **não é** uma contribuição validada empiricamente neste artigo.
- [ ] Adicionar 1-2 frases reconhecendo abertamente os elementos que faltariam para maturidade de framework (contratos de estágio, avaliação empírica, comparação com frameworks existentes de process mining + forecasting) — isso preempta a crítica em vez de esperar o round 2.
- [ ] Não expandir PATHCAST tecnicamente neste artigo (isso pertenceria ao `article_method/`, que é outro artigo) — a resposta correta aqui é *conter o escopo*, não formalizar mais.
- [ ] Revisar Research Agenda (RA1-RA4, linhas 1458-1483) para garantir que estão enquadradas como "propostas para trabalho futuro da comunidade", não como "roadmap de implementação do PATHCAST pelos autores".

**Esforço:** baixo (~1-2h, complementa o item 3).

---

## 5. [CRÍTICO — ATUALIZADO 07/07] W2 + W5 — Duplicidade real nos cortes 381/404, não só apresentação

**Descoberta durante a construção do tooling de double-screening (item 2):** ao tentar juntar a amostra de FT com os registros de QA/extração por DOI/título, 12 de 34 papers "include" não bateram de forma única — investigação revelou que **63 dos 381 estudos (e 64 dos 404) são duplicatas reais**, não um problema de apresentação. A camada "auxiliary" (212 estudos) não foi deduplicada contra o "working-set" (169) antes de rodar QA/extração, e o mesmo paper foi processado duas vezes com `internal_id` diferente.

**Detalhamento (`results/auxiliary/dedup_summary.txt`, gerado por `pipeline/dedup_review.py` + `pipeline/dedup_apply.py`):**
- 64 grupos de duplicatas detectados (mesmo DOI normalizado ou mesmo título exato) = 129 linhas envolvidas.
- 61 grupos cross-tier (working_set ↔ auxiliary/aux_reft) — o bug principal.
- 3 grupos within-tier — inclusive um capítulo IGI Global republicado em 3 handbooks diferentes (G060) e um Petri net paper com workshop+conferência (G045).
- **Decisões editoriais já tomadas por você:** G045 (Stochastic Petri net CI/CD, ISSREW'22 vs RAMS'23) → contam como **2 estudos distintos** (extensão substancial). G060 (capítulo IGI Global) → conta como **1 estudo** (mesma cópia, manter a de maior QA, `internal_id=2647ea07`). As demais 62 duplicatas → resolvidas automaticamente mantendo a cópia do working-set.

**Números corrigidos (arquivos já gerados, ver `results/auxiliary/*_dedup.csv`):**

| Corte | Antes | Depois | Δ |
|---|---|---|---|
| Combined analytical subset (169+212) | 381 | **318** | −63 |
| Final confirmed set (381+23) | 404 | **340** | −64 |
| QA-passed (≥4/8), tier 318 | 315/381 (82,7%) | 259/318 (81,4%) | — |
| QA-passed (≥4/8), tier 340 | — | 279/340 (82,1%) | — |

**Ações ainda pendentes no manuscrito:**
- [ ] Substituir toda ocorrência de "381" por "318" e "404" por "340" em `cap3_article_body.tex` (Search Results, Overview, External Validity, Conclusion — linhas 428-746, 1607-1650, 1739-1799) e nos artigos/capítulos irmãos (`main.tex`, `appendix_slr.tex`, capítulo de tese).
- [ ] Recalcular TODAS as tabelas/percentuais de RQ1-RQ3, F1-F5 e da taxonomia SPMF usando os arquivos deduplicados (`qa_combined_381_dedup.csv`→renomear conceitualmente para "318", `extraction_combined_381_dedup.csv`) — os números de frequência de técnica/PM podem mudar, já que os 63 estudos duplicados podem estar super-representando certas técnicas.
- [ ] Atualizar "315 retained" (QA) para "259/318 (81,4%)" ou "279/340 (82,1%)" conforme o corte usado.
- [ ] Criar a figura/tabela única de proveniência (ação original do W2+W5, ainda válida): funil 8.347 → 5.783 → 2.340 working set → 169 confirmados → +212 aux1 (63 duplicatas removidas) → 318 (subset analítico deduplicado) → +23 aux2 (nenhuma duplicata) → 340 (total confirmado deduplicado) → QA-passed.
- [ ] Adicionar uma frase no método reconhecendo a descoberta e correção da duplicação, como evidência de rigor (isso pode virar um ponto a favor na resposta ao revisor, não só uma correção silenciosa).
- [ ] Revisar `results/spotcheck/disagreement_list_for_human.csv` e outros artefatos de replicação (pacote Zenodo) para garantir consistência com os números corrigidos.

**Esforço:** médio (~4-6h) — a detecção e correção dos dados já está feita; falta propagar os números para o texto e recalcular as tabelas de achados.

---

## Resumo executivo (ordem de execução recomendada)

| # | Item | Criticidade | Esforço | Bloqueia resubmissão? |
|---|------|------|------|------|
| 1 | W3 — datas de busca | Crítica | Trivial (30min) | Sim, se não corrigido |
| 2 | W1 — validação humana | Estrutural | Em andamento (double-screening real, 20%+20%) | Sim — em execução |
| 5 | W2+W5 — duplicidade real 381→318, 404→340 | **Crítica (escalada)** | Dados já corrigidos; falta propagar ao texto (~4-6h) | Sim — números incorretos no texto atual |
| 3 | W4 — dominância PATHCAST | Percepção | Baixo-médio | Não, mas reduz risco de rejeição por "falta de neutralidade" |
| 4 | W6 — PATHCAST como agenda | Estrutural leve | Baixo | Não, complementa #3 |

**Decisão do item 2 (W1) — CONFIRMADA:** double-screening humano real, não plano/limitação. Tooling pronto (`pipeline/human_kappa.py`), amostras de 20% construídas e embaralhadas:
- `results/human_validation/ta_blind_review_sheet.csv` (468 papers, title/abstract)
- `results/human_validation/ft_qa_extraction_blind_review_sheet.csv` (177 papers, full-text + QA + extração no mesmo passe)
- Instruções completas em `results/human_validation/README.md`
- Depois de preenchidas: `python -m pipeline.human_kappa --compute` gera `human_kappa_report.txt`/`.tex` com os κ humano-vs-LLM para preencher os placeholders da carta de resposta (W1).

**Nota sobre o item 5:** a descoberta da duplicação (63/381 e 64/404 estudos duplicados) aconteceu como efeito colateral da construção do tooling do item 2 — ao tentar juntar a amostra FT com QA/extração por DOI/título, a junção falhava de forma ambígua, o que expôs o bug. Scripts de detecção e correção já criados e executados: `pipeline/dedup_review.py` (detecção, gera `results/auxiliary/duplicate_candidates_review.csv`) e `pipeline/dedup_apply.py` (aplica as decisões editoriais e gera os arquivos `*_dedup.csv` corrigidos + `results/auxiliary/dedup_summary.txt`).
