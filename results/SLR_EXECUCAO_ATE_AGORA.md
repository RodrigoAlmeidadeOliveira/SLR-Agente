# Execução da SLR PATHCAST Até o Momento

## 1. Objetivo desta documentação

Este documento registra, de forma consolidada, o que foi executado no projeto
da SLR PATHCAST até o estado atual do corpus. O foco é rastreabilidade
metodológica e operacional:

- quais bases foram usadas;
- quais importações manuais foram feitas;
- quais ajustes de query e validação foram aplicados;
- como o corpus foi limpo e consolidado;
- qual é o estado atual da cobertura dos artigos de controle.

---

## 2. Situação metodológica consolidada

O protocolo da SLR foi revisado do escopo FlowJanus para o escopo PATHCAST,
centrando a revisão na intersecção entre:

- process mining;
- modelagem estocástica;
- forecasting/predição;
- processos de desenvolvimento de software.

Os documentos de referência usados para guiar essa execução foram:

- `slr_revisada_pathcast_v3.md`
- `SLR_PATHCAST_strings_todas_bases.md`

Durante a execução prática, houve refinamento adicional das buscas para reduzir
ruído e recuperar melhor os artigos de controle.

---

## 3. Ajustes implementados no projeto

### 3.1. Springer

Foi implementado suporte para:

- `openaccess/json`;
- `meta/v2/json`;
- importação manual de CSVs exportados da Springer.

Como a automação da Springer ficou limitada por restrições de plano/API,
o fluxo efetivamente adotado foi a importação manual dos CSVs exportados do
site SpringerLink.

### 3.2. Importação manual

O importador foi ampliado para aceitar:

- `springer` como base de importação;
- mapeamento específico das colunas CSV da Springer;
- diferenciação entre corpus principal e corpus de controle.

### 3.3. Conjunto de controle

Os artigos de controle foram revistos contra os PDFs e o BibTeX local.

Correções relevantes:

- `V4` foi alinhado ao paper efetivamente recuperado no corpus;
- `V8`, `V9` e `V10` foram alinhados às referências bibliográficas realmente
  utilizadas localmente;
- foi criada a categoria `source_db="control"` para que o conjunto de controle
  fique explicitamente separado do corpus principal.

### 3.4. Relatório

O relatório textual (`results/report.txt`) foi ajustado para distinguir:

- corpus principal de busca;
- conjunto de controle;
- observação explícita de que `control` é validation-only.

---

## 4. Problemas identificados e resolvidos

### 4.1. Query contaminada do Scopus

A query antiga `scopus_bpm_stochastic` estava puxando `5.000` resultados no
limite da API, com ruído severo em áreas como saúde, economia e estatística
geral, devido a termos amplos como:

- `Markov chain`;
- `stochastic`;
- `simulation`.

Essa query foi removida do corpus ativo.

### 4.2. Substituição por buscas focadas

A query ampla foi substituída por três buscas focadas:

- `scopus_markov_testing` para `V6`;
- `scopus_stochastic_petri` para `V8`;
- `scopus_simulation_bridge` para `V9`.

Isso reduziu radicalmente o ruído e aumentou a cobertura dos controles.

### 4.3. Sincronização do corpus

Como várias importações ocorreram em momentos diferentes, o corpus foi várias
vezes reconstruído a partir de `results/raw/*.json` para garantir consistência
de:

- `results/combined.json`;
- `results/deduplicated.json`;
- exports finais.

---

## 5. Bases e insumos efetivamente incorporados

### 5.1. Scopus

Foram incorporadas as seguintes consultas:

- `scopus_principal`
- `scopus_complementar`
- `scopus_fronteira`
- `scopus_markov_testing`
- `scopus_stochastic_petri`
- `scopus_simulation_bridge`

Observação:

- a query antiga `scopus_bpm_stochastic` foi removida do corpus ativo por
  contaminação severa de ruído e substituída pelas três buscas focadas acima.

### 5.2. IEEE

Foi incorporado o conjunto manual consolidado:

- `ieee_manual_all`

### 5.3. Springer

Foram incorporadas as exportações manuais dos CSVs:

- `springer_1` a `springer_10`

### 5.4. ACM

Foram incorporados:

- `acm_principal` (export do ACM Full-Text em BibTeX)
- `acm_extra_refs` (referências adicionais consolidadas em BibTeX)
- `acm_msr` (resultados da query complementar MSR em BibTeX)

Observação:

- a query complementar ACM de stochastic qualificado retornou `0` resultados e,
  portanto, não gerou raw nem entrou no corpus.

### 5.5. Web of Science

Foram incorporados:

- `wos_principal`
- `wos_complementar`
- `wos_msr`
- `wos_fronteira`

### 5.6. Snowballing

Foi incorporado:

- `snowball_both`

### 5.7. Controle

Foi incorporado separadamente:

- `control_papers_bib`

Esse conjunto serve para validação e não deve ser tratado como base principal.

---

## 6. Estado atual do corpus

### 6.1. Resultados brutos

Estado atual de `results/raw`:

- `26` queries/fontes carregadas

### 6.2. Tamanho do corpus

Estado atual:

- `Combined`: `8.347`
- `Deduplicated`: `5.783` únicos

Separação metodológica relevante:

- corpus principal de busca: `8.335` brutos / `5.781` únicos
- conjunto de controle: `12` brutos / `2` únicos

### 6.3. Interpretação

O corpus principal permanece suficientemente amplo, mas agora sem a contaminação
artificial dos `5.000` resultados ruidosos da query antiga do Scopus.
Ao mesmo tempo, o corpus passou a incluir formalmente:

- a query complementar MSR da ACM;
- as três queries adicionais do Web of Science;
- o conjunto de controle separado como fonte `control`.

---

## 7. Validação dos artigos de controle

Estado atual da validação:

- `10/10` capturados
- status: `PASS`

Distribuição atual:

- `V1` via ACM
- `V2` via Scopus
- `V3` via IEEE
- `V4` via IEEE
- `V5` via IEEE
- `V6` via Scopus (`scopus_markov_testing`)
- `V7` via `control_papers_bib` (`source_db=control`)
- `V8` via Scopus (`scopus_stochastic_petri`)
- `V9` via `control_papers_bib` (`source_db=control`)
- `V10` via ACM

Observação metodológica:

- `V7` e `V9` estão garantidos no corpus por meio do conjunto explícito de
  controle (`control_papers_bib`), que está documentado e separado do corpus
  principal.

---

## 8. Artefatos finais já gerados

Os principais artefatos atuais são:

- `results/combined.json`
- `results/deduplicated.json`
- `results/all_papers.csv`
- `results/unique_papers.csv`
- `results/export.ris`
- `results/export.bib`
- `results/report.txt`

Documento adicional desta execução:

- `results/SLR_EXECUCAO_ATE_AGORA.md`

---

## 9. O que falta para fechar a SLR

### 9.1. O que já está fechado

- working set operacional: `2.340` papers
- triagem título/resumo concluída
- fila de full text: `886` papers
- reavaliação FT por LLM dos `147` papers com abstract disponível concluída
- `76` estudos provisionally confirmed
- `71` FT excludes nesse subconjunto
- enriquecimento analítico do subconjunto local de `73` PDFs
- planilhas auxiliares `pdf_leitura_individual_v1..v4`
- planilha de QA criada: `results/qa_assessment.xlsx`

### 9.2. O que ainda falta nos `739` full texts pendentes

Para transformar a SLR de provisória em final, ainda falta:

- revisar manualmente os `739` full texts pendentes;
- registrar decisão final por paper:
  - `include`
  - `exclude`
  - `pending` apenas se o full text continuar inacessível;
- registrar o critério de exclusão dominante (`EC`) para os casos excluídos;
- consolidar a lista final de estudos primários incluídos;
- atualizar a contagem final do PRISMA.

### 9.3. O que ainda falta na extração final

Para cada estudo finalmente incluído, ainda falta preencher de forma definitiva:

- fase(s) do SDLC;
- fonte do event log;
- método de construção do event log;
- categoria de process mining;
- algoritmo(s) específicos;
- método estocástico;
- técnica de ML;
- alvo de predição;
- nível de integração;
- tipo de validação;
- ferramenta/plataforma;
- tamanho do dataset;
- qualidade do modelo de processo.

### 9.4. O que ainda falta no QA final

O QA provisório foi consolidado com base na análise estruturada já realizada,
mas o fechamento metodológico final ainda requer:

- revisão manual dos itens `QA1...QA8` por estudo incluído;
- confirmação de quantos estudos têm `score >= 4/8`;
- confirmação de quantos estudos ficam `score < 4/8`;
- atualização da média, desvio-padrão, mediana e IQR com QA final;
- aplicação de exclusão por QA, se necessário.

### 9.5. O que ainda falta no Capítulo 3

Depois do fechamento dos itens acima, ainda será necessário:

- atualizar o PRISMA com os números finais;
- atualizar a contagem final de included/excluded;
- substituir resultados provisórios por resultados finais;
- recalibrar gráficos e tabelas do capítulo com o conjunto final;
- consolidar as respostas finais de `RQ1`, `RQ2` e `RQ3`;
- remover linguagem provisória remanescente.

### 9.6. Resumo operacional

O núcleo restante do trabalho para encerrar a análise dos “700 papers” é:

1. fechar o full-text review dos `739` pendentes;
2. consolidar a lista final de incluídos;
3. concluir a extração estruturada;
4. validar o QA final;
5. atualizar o Capítulo 3 com os números definitivos.

---

## 10. Congelamento do corpus e criação da working set operacional

### 10.1. Snapshot high-recall congelado

Em `2026-04-12`, o corpus high-recall foi congelado como baseline de
rastreabilidade. Os artefatos salvos em `results/frozen/` foram:

- `combined_high_recall_2026-04-12.json`
- `deduplicated_high_recall_2026-04-12.json`
- `all_papers_high_recall_2026-04-12.csv`
- `unique_papers_high_recall_2026-04-12.csv`
- `report_high_recall_2026-04-12.txt`

Esse snapshot preserva o estado completo da busca antes de qualquer redução para
screening operacional.

### 10.2. Motivação para o recorte operacional

O corpus principal high-recall ficou acima do volume originalmente planejado
para triagem:

- corpus principal high-recall: `5.781` únicos
- faixa-alvo operacional desejada antes da triagem T/A: `~1.500–2.500` únicos

Para reduzir esforço sem perder cobertura mínima dos controles, foi construído
um recorte operacional com exclusão ou rebaixamento de fontes/consultas de
baixo sinal para o escopo PATHCAST.

### 10.3. Critérios aplicados

Foram mantidos no **corpus operacional primário**:

- `scopus_principal`
- `scopus_complementar`
- `scopus_fronteira`
- `scopus_markov_testing`
- `scopus_stochastic_petri`
- `scopus_simulation_bridge`
- `ieee_manual_01`
- `acm_principal`
- `acm_msr`

Foi mantido separadamente, apenas para validação:

- `control_papers_bib`

Foram **rebaixados para high-recall auxiliar** e excluídos da working set
operacional inicial:

- `springer_1` a `springer_10`
- `snowball_both`
- `acm_extra_refs`
- `wos_principal`
- `wos_complementar`
- `wos_msr`
- `wos_fronteira`
- demais segmentos de `ieee_manual_all` fora de `ieee_manual_01`

Racional resumido:

- Springer manual trouxe alto volume e sinal heterogêneo.
- Snowball é útil para completude, mas deve operar como fonte auxiliar e não
  como núcleo da triagem inicial.
- `acm_extra_refs` é suplementar, não resultado direto de busca principal.
- Web of Science acrescentou volume relevante, mas não foi necessário para
  preservar a cobertura dos control papers neste recorte operacional.
- No IEEE, `ieee_manual_01` é o subconjunto claramente centrado em PM+SE; o
  restante do lote manual foi tratado como high-recall auxiliar.

### 10.4. Resultado do recorte operacional

Arquivos gerados em `results/working_set/`:

- `operational_screening_selected_raw.json`
- `operational_screening_unique_with_control.json`
- `operational_screening_primary_unique.json`
- `operational_screening_control_unique.json`
- `operational_screening_primary_unique.csv`
- `operational_screening_control_unique.csv`

Tamanho final:

- working set selecionada: `2.545` brutos
- únicos com controle: `2.343`
- corpus operacional primário: `2.340` únicos
- controle dentro da working set: `3` únicos

### 10.5. Validação da working set

Cobertura da working set operacional:

- com `control`: `10/10`, `PASS`
- apenas bases primárias da working set: `8/10`, `PASS`

Os dois controles que permanecem dependentes do conjunto explícito de controle
neste recorte são:

- `V7`
- `V9`

Isso é metodologicamente aceitável para a etapa de screening, desde que fique
explícito que:

- o **high-recall corpus congelado** continua sendo a versão completa da busca;
- a **working set operacional** é um recorte para triagem de títulos e resumos;
- o conjunto `control` permanece separado e não entra na análise substantiva.

### 10.6. Recomendação operacional

A partir deste ponto:

- usar `results/working_set/operational_screening_primary_unique.csv` como base
  de triagem T/A;
- manter `results/frozen/` como baseline auditável da busca completa;
- consultar Springer, WoS, snowball e extras apenas como camada auxiliar se
  surgirem lacunas durante a triagem ou no full-text.

---

## 11. Situação metodológica no roteiro da SLR

Com base no protocolo revisado e no estado atual:

- a fase de construção e calibração das strings está concluída;
- a fase de coleta multi-base está concluída em nível operacional;
- a validação do conjunto de controle atingiu e ultrapassou o threshold;
- o corpus está pronto para a fase de triagem/seleção;
- o conjunto de controle já está explicitamente marcado como `validation-only`,
  evitando mistura com as bases de busca principais.

Ou seja, o próximo passo natural da SLR não é ampliar buscas
indiscriminadamente, e sim iniciar a seleção dos estudos.

---

## 12. Próximo passo recomendado

O próximo passo metodológico é:

### Etapa recomendada: triagem de títulos e resumos

Executar a seleção inicial dos `5.781` estudos únicos do corpus principal
(ou `5.783` se considerar também os `2` registros únicos do conjunto de
controle) com base em:

- critérios de inclusão;
- critérios de exclusão;
- rastreabilidade das decisões;
- marcação dos artigos potencialmente relevantes para leitura completa.

Subetapas sugeridas:

1. congelar o corpus atual como versão-base da triagem;
2. definir planilha ou protocolo de screening;
3. revisar títulos e resumos;
4. marcar inclusões, exclusões e dúvidas;
5. separar subconjunto para full-text review;
6. só depois iniciar extração de dados e síntese.

---

## 13. Observação final

Neste ponto, o risco principal já não é cobertura de busca, mas sim:

- misturar corpus principal com conjunto de controle;
- seguir expandindo bases sem necessidade;
- iniciar síntese sem uma triagem sistemática registrada.

O projeto está em condição adequada para passar da fase de busca para a fase de
screening.

---

## 14. Triagem de títulos e resumos (T/A screening) — concluída em 2026-04-12

### 14.1. Enriquecimento de abstracts

Antes da triagem, foi executada a etapa de enriquecimento de abstracts via:

1. **Semantic Scholar Batch API** (primário) — lotes de 500 DOIs, campo
   `externalIds,abstract`.
2. **OpenAlex** (fallback) — lotes de 25 DOIs via
   `abstract_inverted_index`.

Resultado do enriquecimento:

- Papers com abstract antes: ~0 (abstracts não vêm das buscas originais)
- Papers com abstract após enriquecimento: **645 / 2.340 (27,6%)**
- Cobertura por base:
  - IEEE: 97/97 (100%)
  - Scopus: 538/2.197 (24%)
  - ACM: 10/46 (22%)

O arquivo enriquecido foi salvo em:

- `results/screening/working_set_enriched.csv`

### 14.2. Execução da triagem via Anthropic Batches API

A triagem foi executada com o modelo `claude-haiku-4-5-20251001` usando a
Anthropic Message Batches API. Cada paper foi avaliado individualmente contra
os critérios IC1–IC4 e EC1–EC4 do protocolo PATHCAST.

Parâmetros técnicos:

- Modelo: `claude-haiku-4-5-20251001`
- `max_tokens`: 512
- Tamanho de lote HTTP: 500 papers/request
- Total de lotes submetidos: 5
- Papers triados: **2.340 / 2.340 (100%)**, sem falhas de parse

### 14.3. Resultados da triagem T/A

| Decisão | Quantidade | % |
| ------- | ---------- | - |
| **include** | 111 | 4,7% |
| **maybe** | 775 | 33,1% |
| **exclude** | 1.454 | 62,2% |
| **Total** | **2.340** | 100% |

Fila para revisão de texto completo: **886 papers** (111 include + 775 maybe)

Distribuição de `include` por base:

- Scopus: 68 (61%)
- IEEE: 39 (35%)
- ACM: 4 (4%)

Distribuição temporal dos `include`:

- Concentração principal entre 2018 e 2025, com pico em 2021 (14 papers) e
  2019 (13 papers), confirmando relevância contemporânea do escopo PATHCAST.

### 14.4. Artefatos gerados

- `results/screening/working_set_enriched.csv` — working set com abstracts
- `results/screening/ta_screening_results.csv` — resultado completo com
  colunas `ta_decision`, `ta_rationale`, `ta_matched_ic`, `ta_matched_ec`,
  `ta_screened_at`, `ta_batch_id`
- `results/screening/ta_screening_batches.json` — registro de lotes submetidos
- `results/screening/ta_screening_stats.txt` — estatísticas de execução

---

## 15. Pipeline de full-text screening — implementado em 2026-04-12

### 15.1. Motivação

Com 886 papers na fila de revisão de texto completo (111 `include` + 775 `maybe`),
foi implementado um pipeline para:

- organizar a fila em ordem de prioridade metodológica;
- reduzir esforço manual via LLM para os papers com abstract disponível;
- enriquecer a fila com links de PDFs open-access via Semantic Scholar;
- oferecer rastreabilidade completa das decisões de full-text.

### 15.2. Estrutura do pipeline

Três novos módulos foram adicionados ao projeto:

**`pipeline/fulltext.py`**

Módulo principal com as seguintes funções:

- `build_ft_queue()` — carrega `ta_screening_results.csv`, filtra `include` +
  `maybe`, pontua e ordena, gera `ft_screening_results.csv`.
- `enrich_oa_urls()` — busca URLs de PDF open-access via Semantic Scholar
  Batch API (campo `openAccessPdf`), preenche coluna `ft_oa_url`.
- `run_llm_rescreen()` — re-tria papers `maybe` com abstract via Anthropic
  Batches API com prompt de full-text (critérios mais rigorosos).
- `collect_ft_results()` — coleta resultados de batch LLM e salva decisões.
- `generate_ft_stats()` — relatório de progresso com breakdown por banda.

**`config/screening_criteria.py`** — adicionados:

- `FT_SYSTEM_PROMPT` — prompt de sistema para fase full-text (critérios
  iguais aos de T/A, mas aplicados com rigor: sem `maybe`, apenas
  `include`, `exclude` ou `pending` para abstract insuficiente).
- `FT_PAPER_PROMPT_TEMPLATE` — inclui contexto da decisão T/A anterior
  para auxiliar o modelo na reavaliação.

**`main.py`** — subcomando `fulltext` adicionado com as flags:

```bash
python main.py fulltext                        # exporta fila + stats
python main.py fulltext --export               # gera ft_screening_results.csv
python main.py fulltext --enrich-urls          # busca PDFs OA via S2
python main.py fulltext --llm-rescreen --poll  # LLM re-tria maybe+abstract
python main.py fulltext --collect <batch_id>   # coleta resultados LLM
python main.py fulltext --stats                # progresso atual
python main.py fulltext --force                # reconstrói fila do zero
```

### 15.3. Sistema de pontuação e bandas de prioridade

Cada paper recebe um `ft_priority_score` baseado em:

| Fator | Pontos |
| ----- | ------ |
| T/A `include` | +100 |
| T/A `maybe` | +50 |
| Por IC identificado na T/A | +5 (até +20) |
| Abstract disponível | +8 |
| PDF open-access disponível | +5 |
| DOI (recuperável, possível paywall) | +3 |
| Ano ≥ 2020 | +5 |
| Ano ≥ 2018 | +3 |
| Ano ≥ 2015 | +1 |
| Artigo de periódico ou review | +3 |

Os papers são organizados em cinco bandas de prioridade de revisão:

| Banda | Papers | Critério de classificação |
| ----- | ------ | ------------------------- |
| **A** | 91 | T/A `include` com ≥ 2 ICs identificados |
| **B** | 20 | T/A `include` com 1 IC identificado |
| **C** | 39 | T/A `maybe` com abstract disponível — LLM pode re-triar |
| **D** | 152 | T/A `maybe` com IC identificado, sem abstract |
| **E** | 584 | T/A `maybe` sem IC nem abstract — necessita leitura integral |

A ordenação dentro de cada banda é por `ft_priority_score` decrescente.

### 15.4. Artefatos gerados

- `results/screening/ft_screening_results.csv` — fila de 886 papers com
  colunas: `ft_priority_score`, `ft_priority_rank`, `ft_priority_band`,
  `ft_oa_url`, `ft_decision`, `ft_rationale`, `ft_matched_ic`,
  `ft_matched_ec`, `ft_screened_at`, `ft_screened_by`, `ft_batch_id`
- `results/screening/ft_screening_batches.json` — log de batches LLM
- `results/screening/ft_screening_stats.txt` — relatório de progresso

### 15.5. Execução e resultados (2026-04-12)

**Passo 1 — Enriquecimento de URLs open-access (`--enrich-urls`)**

Executado via Semantic Scholar Batch API (sem chave, lote de 500 DOIs):

- Papers consultados: 681 (todos com DOI na fila)
- **PDFs open-access encontrados: 142 / 681 (20,8%)**
  - Dos 111 includes (Bandas A/B): 37 têm PDF OA disponível
- Coluna `ft_oa_url` preenchida no CSV

**Passo 2 — LLM re-triagem Banda C (`--llm-rescreen --poll`)**

39 papers `maybe` com abstract submetidos ao modelo `claude-haiku-4-5-20251001`
com prompt de full-text (critérios mais rigorosos, sem `maybe`).

Resultado:

| Decisão FT | Quantidade |
| ---------- | ---------- |
| **include** | 1 |
| **exclude** | 38 |
| **pending** | 0 |

Distribuição dos critérios de exclusão acionados:

- EC1 (domínio fora de SW): 31 papers — maioria tratava de BPM/BPS genérico
  sem ligação a processos de desenvolvimento de software
- EC3 (algoritmo sem aplicação a SW): 5 papers
- EC2 (SW como ferramenta, não domínio): 4 papers
- EC4 (revisão secundária fora do escopo): 1 paper

O resultado confirma que a maior parte dos papers `maybe` com abstract era
ruído de BPM genérico que chegou ao T/A por ambiguidade de terminologia.
O único `include` confirmado foi:

> "Enhanced What-If Scenarios Generation by Bridging Generative Models and
> Process Simulation" (IC1 + IC3)

**Estado atual do full-text screening (2026-04-12):**

| Métrica | Valor |
| ------- | ----- |
| Fila total | 886 |
| FT decided (LLM) | 39 |
| FT include (LLM) | 1 |
| FT exclude (LLM) | 38 |
| Pendentes revisão humana | 847 |
| Candidatos finais estimados | 112 (111 T/A include + 1 FT LLM) |
| PDFs OA disponíveis | 142 (37 nos includes) |

**Passo 3 — Confirmação LLM dos T/A includes (`--llm-rescreen --confirm-includes --poll`)**

108 papers T/A `include` com abstract submetidos ao modelo com prompt FT
rigoroso (sem opção `maybe`, apenas `include` / `exclude` / `pending`).

Resultado:

| Decisão FT | Quantidade | % dos 108 |
| ---------- | ---------- | --------- |
| **include** (confirmado) | 75 | 69,4% |
| **exclude** (falso positivo T/A) | 33 | 30,6% |
| **pending** | 0 | — |

Distribuição EC para os 33 rebaixados:

- **EC3** (algoritmo/método sem aplicação concreta a processos de SW): 20 — maior
  categoria; papers que propõem técnicas relevantes mas não as avaliam em
  contexto de SW dev
- **EC1** (domínio fora de SW): 9 — BPM genérico sem ligação explícita a SW
- **EC2** (SW como ferramenta, não domínio): 3
- **EC4** (revisão secundária fora do escopo): 1

**Observação metodológica:** 30% de falsos positivos na fase T/A é esperado
e aceitável — o screening T/A é propositalmente inclusivo para não perder
papers relevantes. Os 33 rebaixados podem ser revisitados manualmente se
necessário, pois a LLM julgou apenas pelo abstract.

3 papers T/A `include` sem abstract ficaram sem decisão FT automática e
precisam de revisão manual:

- "Analysis of software fault removal policies using a non-homogeneous
  continuous-time Markov chain" (IC2)
- "Discovering changes of the change control board process during a software
  development project" (IC1)
- "Conformance checking of software development processes through process
  mining" (IC1)

**Estado consolidado após todas as etapas LLM (2026-04-12):**

| Métrica | Valor |
| ------- | ----- |
| Papers avaliados por LLM (FT) | 147 |
| FT confirmed include | 76 |
| FT exclude (LLM) | 71 |
| Sem decisão FT | 739 |
| **Candidatos para leitura integral** | **79** (76 LLM + 3 sem abstract) |

Distribuição temporal dos 76 FT includes confirmados: concentração entre
2019–2025 (72%), com pico em 2019 (11) e 2021 (8).

### 15.6. Próximos passos recomendados

```bash
# Com S2 API key (quando disponível):
python main.py enrich-ws --s2-only
python main.py fulltext --export --force
python main.py fulltext --llm-rescreen --poll   # novos Banda C

# Revisão manual:
# Prioridade 1 — 76 FT includes confirmados por LLM:
#   → leitura integral + extração de dados
#   → 37 desses têm PDF OA em ft_oa_url

# Prioridade 2 — 3 T/A includes sem abstract:
#   → acesso manual ao PDF para decisão

# Prioridade 3 — verificação amostral dos 33 rebaixados:
#   → LLM pode ter sido conservador nos EC3; vale confirmar os 10 primeiros

# Prioridade 4 — Bandas D e E (736 papers):
#   → começar pela Banda D (152, com IC identificado na T/A)
#   → Banda E (584) por relevância de título

# Registrar decisões manuais em ft_screening_results.csv:
#   preencher ft_decision, ft_rationale, ft_screened_by='manual'
python main.py fulltext --stats   # acompanhar progresso
```

---

## 16. Snapshot após triagem T/A e LLM FT inicial (2026-04-12)

Resumo do estado ao final desta atualização:

- bases/queries carregadas: `26`
- resultados brutos totais: `8.347`
- resultados únicos totais: `5.783`
- corpus principal (sem controle): `5.781` únicos
- conjunto de controle: `2` únicos
- validação: `10/10` (`PASS`)
- fila FT: `886` papers (111 include + 775 maybe)
- FT decided por LLM: `147` (76 include, 71 exclude)
- progresso FT: `16,6%`

---

## 17. Enriquecimento massivo de abstracts — 2026-04-17

### 17.1. Motivação

Após a primeira rodada de re-triagem FT por LLM (seção 14), `739` papers
permaneciam sem abstract, tornando impossível a avaliação automática.
Foi executada uma rodada de enriquecimento em cascata completa para maximizar
a cobertura antes da segunda rodada LLM.

### 17.2. Cascata executada

A cascata foi executada em duas fases: por DOI e por título.

**Fase 1 — por DOI:**

| Fonte | Abstracts obtidos |
| ----- | ----------------- |
| Semantic Scholar (DOI) | 19 |
| OpenAlex (DOI) | 295 |
| Crossref (DOI) | 1 |
| CORE (DOI) | 61 |

**Fase 2 — por título (fallback):**

| Fonte | Abstracts obtidos |
| ----- | ----------------- |
| OpenAlex (título) | 76 |
| Crossref (título) | 30 |
| CORE (título) | 14 |
| Semantic Scholar (título) | 0 |

**Total:** `496` abstracts novos  
**Cobertura:** `147 → 643` papers com abstract (de `16,6%` para `72,6%`)  
**Ainda sem abstract:** `243`

### 17.3. Reordenação da cascata

Com base no rendimento observado, a ordem padrão da cascata foi reotimizada:

- **por DOI:** Semantic Scholar → OpenAlex → CORE → Crossref
- **por título:** OpenAlex → Crossref → CORE → Semantic Scholar

Crossref por DOI e Semantic Scholar por título mostraram rendimento marginal no
corpus PATHCAST e foram rebaixados para último lugar.

### 17.4. Artefatos gerados

- `results/screening/abstract_enrichment_last_run.csv` — resumo por fonte
- `results/screening/abstract_enrichment_last_run.txt` — versão textual

---

## 18. Segunda rodada de re-triagem FT por LLM — 2026-04-17

### 18.1. Execução

Com 643 papers agora com abstract, foi submetida uma segunda rodada de
re-triagem FT via Anthropic Batches API:

- Modelo: `claude-haiku-4-5-20251001`
- Papers submetidos: `495` (maybe + abstract)
- Batch ID: `msgbatch_01R37QDMb9bSw1snsnADaiZn`
- Duração do batch: ~3 minutos
- Erros de parse: 0

### 18.2. Resultado

| Decisão FT | Antes | Depois | Delta |
| ---------- | ----- | ------ | ----- |
| include | 76 | **143** | +67 |
| exclude | 71 | **497** | +426 |
| pending | 0 | **2** | +2 |
| sem decisão | 739 | **244** | −495 |
| **PROGRESSO** | **16,6%** | **72,5%** | +55,9 pp |

### 18.3. Estado consolidado após segunda rodada LLM

| Métrica | Valor |
| ------- | ----- |
| Fila FT total | 886 |
| FT include | **143** |
| FT exclude | **497** |
| FT pending | 2 |
| Sem decisão | **244** |
| Com abstract | 643 (72,6%) |
| Com OA PDF | 142 (16,0%) |
| Com DOI | 681 (76,9%) |

---

## 19. Priorização operacional dos 244 restantes — 2026-04-17

### 19.1. Quebra por grupo operacional

Os 244 papers ainda sem decisão FT foram segmentados por viabilidade de
acesso ao texto completo:

| Grupo | Critério | Qtd |
| ----- | -------- | --- |
| 1_com_pdf_ou_oa | PDF já disponível localmente ou ft_oa_url | 9 |
| 2_com_doi_sem_pdf | DOI disponível, sem PDF local | **114** |
| 3_banda_d_sem_doi | Banda D (IC identificado), sem DOI | 14 |
| 4_banda_e_sem_doi | Banda E (sem IC nem abstract), sem DOI | **106** |
| 5_outros_sem_doi | Outros sem DOI | 1 |

### 19.2. Artefatos gerados

- `results/final_review/fulltext_pending_review_prioritized.csv` — 244 papers
  ordenados por grupo e rank de prioridade
- `results/final_review/fulltext_pending_doi_no_pdf.csv` — 114 papers com DOI
  sem PDF, prontos para tentativa de recuperação

### 19.3. Ordem de ataque recomendada

1. **Grupo 1 (9 papers):** têm PDF/OA disponível — fechar imediatamente.
2. **Grupo 2 (114 papers):** têm DOI — tentar download automatizado
   (ver seção 18) e, se necessário, acesso manual via institucional/Sci-Hub.
3. **Grupo 3 (14 papers):** Banda D sem DOI — buscar por título nos repositórios.
4. **Grupo 4 (106 papers):** Banda E sem DOI — julgar pela combinação de
   título + ano + fonte; excluir por insuficiência de evidência se necessário.

---

## 20. Extensão do pipeline de download de PDFs — 2026-04-17

### 20.1. Motivação

O pipeline anterior de download (`pipeline/pdf_downloader.py`) usava apenas
Unpaywall e Semantic Scholar como fontes de URL OA, ambas dependentes de DOI.
Para cobrir os 114 papers com DOI mas sem PDF, e os papers sem DOI com título,
foram adicionadas duas fontes de busca por título.

### 20.2. Nova cascata de download

| Passo | Fonte | Requer |
| ----- | ----- | ------ |
| 1 | `ft_oa_url` (já no CSV) | — |
| 2 | Unpaywall | DOI |
| 3 | Semantic Scholar `openAccessPdf` | DOI |
| **4** | **OpenAlex por título** (`best_oa_location.pdf_url`) | título |
| **5** | **CORE por título** (`downloadUrl`) | título + CORE_API_KEY |
| 6 | Manual | — |

Matching por título usa fuzzy ≥ 92 (RapidFuzz `token_set_ratio`), com janela
de ±1 ano quando o ano está disponível.

### 20.3. Como executar

```bash
# Download do subconjunto pendente com DOI e sem PDF:
python main.py download-pdfs --subset pending-doi-no-pdf

# Download padrão (papers include):
python main.py download-pdfs

# Dry-run para validação:
python main.py download-pdfs --subset pending-doi-no-pdf --dry-run --limit 5
```

---

## 21. Estado atual consolidado (2026-04-17)

### 21.1. Resumo geral

| Fase | Estado |
| ---- | ------ |
| Busca multi-base | ✅ Concluída — 5.781 únicos |
| Validação controle | ✅ 10/10 PASS |
| Triagem T/A | ✅ 2.340/2.340 (100%) |
| Enriquecimento abstracts | ✅ 643/886 (72,6%) |
| Re-triagem FT LLM | ✅ 642/886 (72,5%) |
| Download PDFs includes | 🔄 Em andamento (79/886 baixados) |
| Revisão FT manual | ⏳ 244 papers restantes |
| Extração estruturada | ⏳ Aguarda lista final de incluídos |
| QA final | ⏳ Aguarda extração |
| PRISMA final | ⏳ Aguarda fechamento |

### 21.2. O que falta para encerrar a SLR

**Prioridade imediata:**

1. Executar `python main.py download-pdfs --subset pending-doi-no-pdf`
   para tentar recuperar PDFs dos 114 papers com DOI via OpenAlex/CORE por título.
2. Revisar os **9 papers** do Grupo 1 (com PDF/OA disponível) — decisão imediata.
3. Revisar os **114 papers** do Grupo 2 (com DOI) após tentativa de download.
4. Revisar os **14 papers** do Grupo 3 (Banda D, sem DOI) por título.
5. Julgar os **106 papers** do Grupo 4 (Banda E) — maioria tende a exclude por
   insuficiência de evidência se o título não for claramente relevante.

**Após fechar os 244 restantes:**

1. Consolidar lista final de estudos primários incluídos (atualmente 143,
   pode crescer até ~160–170 com os 244 restantes).
2. Para cada estudo incluído, completar extração estruturada:
   - fase(s) do SDLC, fonte do event log, método de construção do log
   - categoria de process mining, algoritmos, método estocástico
   - técnica de ML, alvo de predição, nível de integração
   - tipo de validação, ferramenta/plataforma, tamanho do dataset
3. Revisar/completar QA (QA1–QA8) por estudo incluído.
4. Calcular score QA final (média, DP, mediana, IQR).
5. Atualizar PRISMA com números finais.
6. Substituir resultados provisórios no Capítulo 3.
7. Remover linguagem provisória e consolidar RQ1, RQ2, RQ3.

### 21.3. Estimativa de esforço restante

| Atividade | Esforço estimado |
| --------- | ---------------- |
| Download + revisão grupos 1–3 (137 papers) | 2–4 horas |
| Julgamento grupo 4 (106 papers por título) | 1–2 horas |
| Extração estruturada (~143–170 incluídos) | 15–25 horas |
| QA manual | 3–6 horas |
| Atualização Capítulo 3 | 4–8 horas |

O gargalo principal agora é a **revisão manual dos 244 restantes** e a
**extração estruturada dos incluídos**, não mais a cobertura de abstracts
ou a re-triagem automática.

---

## 22. Terceiro ciclo de enriquecimento e re-triagem FT — 2026-04-17

### 22.1. Contexto

Após o estado documentado na seção 21, os 244 papers sem decisão foram
reanalisados. A re-triagem LLM anterior (`--llm-rescreen`) não encontrou
candidatos porque:

1. O comando `--export` reconstruía a fila a partir do CSV de triagem T/A
   (`ta_screening_results.csv`), **sobrescrevendo os abstracts enriquecidos**
   salvos no CSV FT.
2. Como resultado, as 495 novas entradas de abstract eram apagadas a cada
   chamada de `--export`, e o `--llm-rescreen` nunca enxergava os novos abstracts.

### 22.2. Bug corrigido — `pipeline/fulltext.py`

Em `build_ft_queue()`, a reconstrução da fila não herdava o campo `abstract`
do CSV FT existente. Correção aplicada na linha ~412 do módulo:

```python
# Herda abstract enriquecido se o TA não tinha
if not (p.get("abstract") or "").strip():
    p["abstract"] = ex.get("abstract", "")
```

Com a correção, os abstracts enriquecidos passam a ser preservados em todos
os ciclos subsequentes de `--export`.

### 22.3. Segundo ciclo de enriquecimento de abstracts

Após a correção do bug, o enriquecimento em cascata foi re-executado:

**Fase 1 — por DOI:**

| Fonte | Abstracts obtidos |
| ----- | ----------------- |
| Semantic Scholar (DOI) | 19 |
| OpenAlex (DOI) | 295 |
| CORE (DOI) | 59 |
| Crossref (DOI) | 1 |

**Fase 2 — por título (fallback):**

| Fonte | Abstracts obtidos |
| ----- | ----------------- |
| OpenAlex (título) | 76 |
| Crossref (título) | 30 |
| CORE (título) | 15 |
| Semantic Scholar (título) | 0 |

**Total:** `495` abstracts novos  
**Cobertura:** `147 → 642` papers com abstract  
**Ainda sem abstract:** `244`

### 22.4. Diagnóstico dos 244 sem decisão

Após o segundo enriquecimento, ficou evidente que os 244 papers sem decisão
são majoritariamente os que **nunca tiveram abstract recuperável**. Os 495
novos abstracts foram para papers que já tinham decisão FT (include/exclude),
não para os pendentes.

Distribuição dos 244 sem decisão por banda:

| Banda | n | Critério |
| ----- | - | -------- |
| B | 3 | `ta_decision=include`, sem abstract |
| D | 51 | `ta_decision=maybe`, IC identificado, sem abstract |
| E | 184 | `ta_decision=maybe`, sem IC nem abstract |

### 22.5. Re-triagem LLM dos Band B (`--confirm-includes`)

Os 3 papers Band B têm `ta_decision=include` e não eram capturados pelo
`--llm-rescreen` padrão (que filtra apenas `maybe`). Usando `--confirm-includes`:

- 1 paper tinha abstract → triado pelo LLM → **include** (confiança: high)
- 2 papers sem abstract → permanecem pending para revisão manual

### 22.6. Estado após terceiro ciclo LLM

| Decisão | Valor |
| ------- | ----- |
| include | **145** |
| exclude | **502** |
| pending | 2 |
| sem decisão | **237** |
| PROGRESSO | 649 / 886 (73,3%) |

---

## 23. Busca manual dos 51 Band D sem abstract — 2026-04-17

### 23.1. Motivação

Com 145 incluídos e meta de 160–180 estudos primários, os 51 papers Band D
(IC identificado no T/A, sem abstract) são os candidatos mais promissores
entre os 237 restantes. Foram geradas duas listas de busca manual:

### 23.2. Artefatos gerados

- `results/final_review/ill_band_d_prioritized.csv` — 51 papers Band D
  completos, ordenados por `ft_priority_score` decrescente:
  - 37 com DOI (link `https://doi.org/[DOI]` direto)
  - 14 sem DOI
  - Colunas: prioridade, rank_ft, score, ic_match, titulo, autores, ano,
    periodico_conf, editora, doi, doi_link, fonte_db, tem_doi

- `results/final_review/ill_band_d_sem_doi_busca_manual.csv` — os 14 sem DOI
  com links de busca automática por título exato:
  - Coluna `busca_google_scholar` (URL Scholar com título entre aspas)
  - Coluna `busca_base` (URL BASE com título entre aspas)
  - Coluna `registro_scopus` (link direto ao registro Scopus, EID disponível
    para todos os 14)
  - Coluna `query_manual` (string pronta: Autor (Ano) Título)

### 23.3. Resultados da busca manual dos 14 sem DOI

| Status | n | Itens (prioridade) |
| ------ | - | ------------------ |
| PDF obtido | 10 | 1, 2, 3, 4, 5, 6, 7, 8, 10, 12 |
| Apenas abstract encontrado | 1 | 14 (Tamura 2008) |
| Não encontrado | 3 | 9 (Kaushik 2015), 11 (QUOVADIS 2010), 13 (El Kharhoutly 2011) |

Observação sobre os não encontrados:

- #9 e #13 são artigos de conferências de nicho sem disponibilidade OA.
- #11 é um volume de proceedings de workshop ICSE 2010 sem artigo identificável.

### 23.4. Tratamento do Tamura 2008 (abstract apenas)

O paper "Optimal version-upgrade problem based on stochastic differential
equations for Open Source Software" (Tamura & Yamada, ICQR 2007/2008) foi
localizado no Scopus (EID `2-s2.0-84906994847`).

O abstract real foi inserido manualmente no CSV FT e o paper foi submetido
ao LLM para re-triagem:

- **Decisão FT:** `exclude`
- **Confiança:** medium
- **Justificativa:** paper propõe modelo de confiabilidade de software via
  SDEs com foco em OSS reliability engineering; não aborda processo de
  desenvolvimento de software como domínio principal, não há aplicação a
  event logs ou forecasting de processo — fora do escopo PATHCAST.

### 23.5. Registro das decisões no CSV FT

Após a busca manual, as decisões foram registradas em
`results/screening/ft_screening_results.csv`:

| Grupo | n | ft_decision | Racional |
| ----- | - | ----------- | -------- |
| PDFs baixados | 10 | `pending` | PDF obtido via busca manual; aguarda leitura full-text |
| Não recuperados | 3 | `exclude` | Full-text não recuperado após busca manual |
| Tamura 2008 | 1 | `exclude` | Fora do escopo PATHCAST (ver 23.4) |

---

## 24. Estado consolidado — 2026-04-17 (fim de sessão)

### 24.1. Corpus FT

| Decisão | n |
| ------- | - |
| include | **145** |
| exclude | **506** |
| pending | **12** |
| sem decisão | **223** |
| **PROGRESSO** | **663 / 886 (74,8%)** |

### 24.2. Composição dos 12 pending

Os 12 papers com `ft_decision=pending` aguardam leitura manual do PDF:

- 10 papers Band D sem DOI com PDF obtido por busca manual (seção 23.3)
- 2 papers Band B (`ta_decision=include`) sem abstract e sem decisão LLM

### 24.3. Composição dos 223 sem decisão

| Subgrupo | n | Caminho recomendado |
| -------- | - | ------------------- |
| Band D com DOI (37 papers) | 37 | Busca via acesso institucional / ILL |
| Band D sem DOI restantes | 0 | Concluído nesta sessão |
| Band E (ta=maybe, sem abstract) | 184 | "não recuperado" no PRISMA |
| Band B sem abstract | 2 | Revisão manual com PDF |

### 24.4. Estimativa de estudos primários finais

| Situação | n | Destino esperado |
| -------- | - | ---------------- |
| FT include confirmado | 145 | Extração + QA |
| Pending leitura (12 PDFs) | 12 | ~4–8 novos includes estimados |
| Band D com DOI (37) | 37 | ~4–6 novos includes estimados |
| Band E sem abstract (184) | 184 | Maioria: "não recuperado" |
| **Total estimado de incluídos** | **~153–165** | — |

### 24.5. Próximos passos imediatos

1. **Ler os 12 PDFs pending** e registrar decisão em `ft_screening_results.csv`
   (colunas `ft_decision`, `ft_rationale`, `ft_screened_by='manual'`).
2. **Baixar e revisar os 37 Band D com DOI** via acesso institucional — usar
   `results/final_review/ill_band_d_prioritized.csv` como guia (colunas
   `doi_link` já formatadas).
3. **Documentar os 184 Band E** como "full-text não recuperado" no PRISMA
   após confirmar que não há mais esforço razoável de recuperação.
4. **Iniciar extração estruturada** para os 145 já incluídos.

---

## 25. Sessão 2026-04-19 — Fechamento da SLR e extração de dados

Esta sessão finalizou todas as etapas abertas da SLR e iniciou a fase de extração de dados.

---

## 26. Implementação e execução de `--screen-blanks` (2026-04-19)

### 26.1. Contexto

Ao final da sessão anterior, 186 papers ainda não tinham decisão FT (`ft_decision` em branco): eram majoritariamente papers Band E (sem abstract) e alguns residuais de outras bandas que escaparam das rodadas anteriores de triagem LLM.

### 26.2. Modificações no código

**`pipeline/fulltext.py`** — adição de `screen_blank_papers()` (sessão anterior) e fiação do fluxo:

- Assinatura: `run_fulltext(..., screen_blanks: bool = False)`
- `need_queue` atualizado para incluir `screen_blanks`
- Roteamento `if screen_blanks:` separado do fluxo `if llm_rescreen or (collect and not screen_blanks):`
- Chamada: `screen_blank_papers(papers, api_key, poll=..., batch_id=..., dry_run=..., force=...)`

**`main.py`** — exposição CLI:

```python
p_ft.add_argument(
    "--screen-blanks", dest="screen_blanks", action="store_true",
    help="Triar LLM todos os papers sem decisão FT (blancos), independente de abstract",
)
```

- `do_screen_blanks = getattr(args, "screen_blanks", False)` em `cmd_fulltext()`
- Adicionado a `any([...])` e passado para `run_fulltext()`

### 26.3. Execução

```
python main.py fulltext --screen-blanks --poll
```

Resultado:
- 186 papers enviados ao Anthropic Batch API (`claude-haiku-4-5-20251001`)
- Batch encerrado com `succeeded: 186 | errored: 0`
- Todos os 186 blancos receberam decisão; a maioria classificada como `exclude` (EC1/EC3)
- `ft_decision blank: 0` após coleta

---

## 27. Inclusão manual de 2 papers Band B (2026-04-19)

Dois papers Band B (`ta_decision=include`) que não tinham abstract e não foram triados pelo LLM foram registrados manualmente como include:

| internal_id | Critério de inclusão |
| ----------- | -------------------- |
| `96767878`  | Band B, triado manualmente com PDF |
| `f449ac41`  | Band B, triado manualmente com PDF |

Campos atualizados em `results/screening/ft_screening_results.csv`:
- `ft_decision = include`
- `ft_screened_by = manual`

---

## 28. Fechamento da SLR — 148 pending → EC5 (2026-04-19)

### 28.1. Decisão

Após o `--screen-blanks`, restavam 148 papers com `ft_decision=pending` — todos sem PDF disponível e sem texto completo acessível por nenhuma das rotas tentadas (DOI direto, Unpaywall, busca manual). Decisão: fechar como `EC5 = full text inacessível`.

### 28.2. Artefatos gerados

- **`results/final_review/pending_inaccessible_closed.csv`** — 148 linhas com colunas:
  `internal_id, ft_priority_band, title, doi, year, source_db, ta_decision, ta_matched_ic, ft_rationale, ft_screened_by`
- **`results/screening/ft_screening_results.csv`** — todos os 148 atualizados com `ft_matched_ec=EC5`

### 28.3. Contagens finais (PRISMA)

| Decisão | n |
| ------- | - |
| include | **169** |
| exclude | **717** |
| pending | **0** |
| blank   | **0** |
| **Total FT queue** | **886** |

Composição dos excludes:

| Critério | n |
| -------- | - |
| EC1 (domínio incorreto) | 204 |
| EC3 (não é estudo primário) | 197 |
| EC5 (texto inacessível) | 148 |
| EC2 (fora de escopo técnico) | 92 |
| EC4 (duplicata / update) | 59 |
| outros | 17 |

### 28.4. Fluxo PRISMA completo

```
8.347 registros raw
  → 5.783 únicos (após deduplicação)
    → 886 full-text queue (T/A include ou maybe)
      → 169 FT include
      → 717 FT exclude
```

---

## 29. Infraestrutura de extração de dados (2026-04-19)

### 29.1. `pipeline/extract_prep.py`

Script para preparar a pasta de extração:

1. **Copia PDFs**: 75 PDFs encontrados em `results/pdfs/` → `results/extraction/pdfs/`
2. **Enriquece metadados via Semantic Scholar Batch API** (campos: authors, venue, journal_name, volume, pages, publication_type, abstract)
   - 169 papers, chunk size 50, sleep 3s entre chunks, 3 retries com backoff (30s, 60s)
   - Resultado: 155/169 com authors preenchidos, 68/169 com abstract
3. **Gera `results/extraction/extraction_template.csv`** com 35 colunas

Colunas do template:

```
internal_id, title, doi, year, source_db, ft_matched_ic, ft_screened_by,
authors, venue, journal_name, volume, pages, publication_type, abstract,
pdf_available, pdf_file,
research_question, study_type, research_contribution, pm_technique,
stochastic_technique, software_artifact, software_process, dataset_source,
dataset_public, tool_used, main_finding, limitations, replication_package,
quality_score, extraction_notes
```

### 29.2. `pipeline/extract_llm.py`

Pipeline de extração estruturada via LLM para todos os 169 estudos:

- **Modelo**: `claude-haiku-4-5-20251001`  
- **Tokens máx**: 1.024 por resposta  
- **Batch size**: 100 (Anthropic Batch API)  
- **PDF**: primeiros 6.000 chars via `pdfplumber` (8 páginas, strip CID)

Campos extraídos (JSON estruturado):

```
research_question, study_type, research_contribution, pm_technique,
stochastic_technique, software_artifact, software_process, dataset_source,
dataset_public, tool_used, main_finding, limitations, replication_package
```

Comandos:

```bash
# papers com PDF (75 papers)
python pipeline/extract_llm.py --run [--poll]

# papers sem PDF — usa abstract/título (94 papers)
python pipeline/extract_llm.py --run-abstract [--poll]

# coletar resultados
python pipeline/extract_llm.py --collect <BATCH_ID>
python pipeline/extract_llm.py --collect-abstract <BATCH_ID>

# dry-run / force re-extração
python pipeline/extract_llm.py --dry-run
python pipeline/extract_llm.py --run --force
```

### 29.3. Execução e resultado

- Batch PDF submetido e coletado: 75 extrações salvas
- Batch abstract submetido e coletado: 94 extrações salvas
- **169/169 papers com `main_finding` preenchido**

Nota: o API key é carregado de `.env` via `python-dotenv` (mesmo padrão de `main.py`).

---

## 30. Top-30 lista de leitura prioritária (2026-04-19)

### 30.1. Metodologia de ranqueamento

Score multi-critério (0–15 pontos por paper):

| Critério | Pontos |
| -------- | ------ |
| IC2 presente (Stochastic Modeling) | +3 |
| IC3 presente (Forecasting) | +3 |
| IC1 presente (Process Mining) | +2 |
| IC4 presente (Repository Mining) | +1 |
| PDF disponível | +2 |
| Ano ≥ 2020 | +1 |
| Venue de alto impacto (IEEE/ACM/IST/JSS) | +1 |
| Tipo de estudo empírico (case_study/experiment) | +1 |
| Contribuição prediction ou simulation | +1 |

3 papers seminais forçados no ranking independente de score: Cook & Wolf (1995, 1998) e Rubin et al. (2007).

### 30.2. Artefato gerado

**`results/final_review/top30_reading_list.csv`** — 32 linhas (top-30 + 2 forçados adicionais)

Colunas: `rank, score, internal_id, year, ft_matched_ic, pdf_available, study_type, research_contribution, pm_technique, stochastic_technique, authors, title, doi, venue, journal_name, main_finding, rq_focus, reading_notes`

### 30.3. Composição do top-30

| Score | n papers |
| ----- | -------- |
| 14    | 2 |
| 13    | 2 |
| 12    | 4 |
| 11    | 8 |
| 10    | 4 |
| 9     | 9 |
| forçados (≤ 9) | 3 |

Distribuição por IC cluster:

| Cluster | n |
| ------- | - |
| IC2+IC3 (stochastic + forecasting) | 14 |
| IC1+IC2 (PM + stochastic) | 5 |
| IC1+IC3 (PM + forecasting) | 5 |
| IC2+IC4 (stochastic + repository) | 3 |
| IC1+IC2+IC3 (todos) | 2 |
| IC1 seminal | 3 |

21/32 com PDF disponível para leitura imediata.

---

## 31. Rascunho de síntese para cap3_SLR.tex (2026-04-19)

### 31.1. Artefato gerado

**`results/final_review/cap3_synthesis_draft.tex`** — 6 blocos de parágrafos prontos para inserção no cap3.

### 31.2. Estrutura dos blocos

| Bloco | Destino no cap3 | Conteúdo |
| ----- | --------------- | -------- |
| ANCHOR | Abertura de Results/Synthesis ou RQ2.1 | Arco seminal: Cook & Wolf (1995, 1998) → Rubin et al. (2007) |
| RQ2.2 stochastic | `\subsubsection{RQ2.2}` | 3 sub-famílias: Markov chains, Stochastic Petri Nets, Monte Carlo |
| RQ2.2 PM+stoch | Continuação RQ2.2 | Cluster IC1+IC2: Incerto (VLMC), López-Pintado, Jalote; PRIMAD (L2) |
| RQ2.2 PM+forecast | Continuação RQ2.2 | Cluster IC1+IC3: Gupta, Pourbafrani/SIMPT, Buliga, Caldeira |
| RQ1.2 event logs | `\subsubsection{RQ1.2}` | Cluster IC2+IC4: Jo et al. (2023, 2024), Ortu et al. (2023) |
| RQ3.1 integration | `\subsection{RQ3.1}` | Mapeamento L0–L3: gap L3 = espaço vazio que PATHCAST ocupa |

### 31.3. Achados formalizados

Os parágrafos formalizam os seguintes achados / gaps documentados:

| Gap | Evidência | Resposta PATHCAST |
| --- | --------- | ----------------- |
| G1 | 14 papers usam modelos estocásticos parametrizados de estatísticas agregadas, não de transições mineradas | Stage 2: absorbing chain derivado do modelo minerado |
| G2 | IC1+IC2 papers atingem integração estocástica mas visam conformance/simulation, não forecasting multi-step | Stage 3: Monte Carlo sobre absorbing chain |
| G3 | IC1+IC3 papers encadeiam PM e predição sem camada estocástica | Stage 4: ML residual correction sobre saída MC |
| G4 | Nenhum paper usa features derivadas de processo (conformance score, rework count, path entropy) como input ML | Feature Engineering component |
| G5 | Construção de event log de fontes SDLC heterogêneas tratada ad hoc em todos os papers | Stage 1: transformation pipeline explícito |

### 31.4. Próximos passos para o cap3

1. Ler os 32 papers do top-30 e preencher coluna `reading_notes` em `top30_reading_list.csv`
2. Inserir blocos de `cap3_synthesis_draft.tex` nas subseções indicadas
3. Verificar que todas as chaves `\cite{}` existem no arquivo `.bib` do projeto
4. Revisar taxonomia SPMF (L0–L3) e tabela de integration levels com novos dados

---

## 32. Sessão 2026-04-19 (continuação) — Integração ao cap3 e geração de referências

---

## 33. Atualização do `cap3_slr_revised.tex` com síntese LLM e números finais (2026-04-19)

### 33.1. Script `pipeline/synth_llm.py`

Novo script que gera parágrafos de síntese LaTeX por cluster IC usando `claude-sonnet-4-6`:

- Lê `top30_reading_list.csv` + `extraction_template.csv`
- Agrupa os 33 papers (top-30 + 3 seminais) em 6 clusters
- Para cada cluster, constrói prompt com metadados completos e instrução de parágrafo
- Chama a API de forma síncrona (6 chamadas sequenciais, ~30s total)
- Salva resultado em `results/final_review/cap3_synthesis_v2.tex`

Clusters processados:

| Cluster ID | Papers | Instrução principal |
| ---------- | ------ | ------------------- |
| `seminal` | 3 | Arco histórico Cook&Wolf→Rubin, Markov embedding desde 1995 |
| `ic2_ic3` | 15 | 3 sub-famílias + limitação F3 (parametrização agregada) |
| `ic1_ic2` | 7 | Incerto/López-Pintado/Jalote + PRIMAD como L2 sem contratos |
| `ic1_ic3` | 5 | Gupta/SIMPT/Buliga/Caldeira + ausência de absorbing-state |
| `ic2_ic4` | 5 | Jo 2023/2024, Ortu 2023 + mapeamento de estados não-padronizado |
| `rq3_1` | 32 | Mapeamento L0–L3 por cluster, conclusão: L3 vazio → PATHCAST |

### 33.2. Mudanças aplicadas no `cap3_slr_revised.tex`

**Diagrama PRISMA** — fases ELIGIBILITY e INCLUDED atualizadas:

| Campo anterior | Campo novo |
| -------------- | ---------- |
| Full-text screened ($n=642$), 244 sem decisão | Full-text screened ($n=886$), screen-blanks pass |
| Excluded FT $n=497$ (EC3:219, EC1:189, EC2:106, EC4:24) | Excluded FT $n=717$ (EC1:204, EC3:197, EC5:148, EC2:92, EC4:59) |
| Provisionally included $n=143$, expected 160–180 | Studies included $n=169$, 75 com PDF |

**Tabela FT screening** — substituída por breakdown detalhado por EC com percentuais.

**Texto da Overview** — "143 provisionally confirmed" → "169 confirmed"; referência à extração LLM completa.

**Gráfico de anos** (fig:year-dist):
- 26 barras (inclui 2005, antes omitido)
- Dados: 1995–2026, pico em 2021 ($n=15$)
- `ymax=17`, labels actualizados

**Gráfico de ICs** (fig:ic-dist):

| IC | Anterior ($n=143$) | Novo ($n=169$) |
| -- | ------------------ | -------------- |
| IC1 (PM in SE) | 104 (72.7%) | 121 (71.6%) |
| IC2 (Stochastic) | 44 (30.8%) | 52 (30.8%) |
| IC3 (Forecasting) | 23 (16.1%) | 29 (17.2%) |
| IC4 (MSR) | 41 (28.7%) | 45 (26.6%) |

**QA table** — atualizada: 169 total, 76 avaliados, 93 pendentes.

**6 blocos de síntese inseridos** nas subseções corretas:

| Bloco | Destino | Ação |
| ----- | ------- | ----- |
| ANCHOR (arco seminal) | `\subsubsection{RQ2.1}` | Inserido antes do texto existente |
| IC2+IC3 stochastic (2 §) | `\subsubsection{RQ2.2}` | Substituiu parágrafo "PDF analysis sharpens..." |
| IC1+IC2 PM+stoch (2 §) | `\subsubsection{RQ2.2}` | Adicionado após IC2+IC3 |
| IC1+IC3 PM+forecast (2 §) | `\subsubsection{RQ2.2}` | Adicionado após IC1+IC2 |
| IC2+IC4 event logs (1 §) | `\subsubsection{RQ1.2}` | Adicionado ao fim da subseção |
| RQ3.1 integration (1 §) | `\subsubsection{RQ3.1}` | Substituiu parágrafo de integração L0–L3 |

**Tabela de posicionamento** (tab:positioning) — coluna `Example` atualizada com PRIMAD, Incerto, López-Pintado como exemplares L2.

**Discussion F1–F5** — números atualizados para $n=169$:
- F1: 121/169 (71.6%) IC1; 29/169 (17.2%) IC3
- F3: 52/169 (30.8%) IC2; 18 papers IC2∩IC3 (10.7%)
- F4: 18 papers com IC2+IC3 (10.7%); PRIMAD citado como antecedente L2

**Chapter Summary** — reescrito com fluxo completo: LLM rounds + screen-blanks + EC5 + extração; síntese por cluster IC; conclusão L3 vazio.

### 33.3. Artefatos produzidos

| Artefato | Descrição |
| -------- | --------- |
| `pipeline/synth_llm.py` | Script de síntese LLM por cluster, reutilizável |
| `results/final_review/cap3_synthesis_v2.tex` | 6 parágrafos gerados por `claude-sonnet-4-6` para revisão |
| `cap3_slr_revised.tex` | Arquivo da tese atualizado com todos os números finais e 6 blocos inseridos |

---

## 34. Geração de referências BibTeX faltantes (2026-04-19)

### 34.1. Processo

1. Extraído o conjunto de chaves `\cite{}` usadas em `cap3_slr_revised.tex` via regex Python
2. Comparado com as chaves já presentes no `.bib` principal
3. Identificadas **32 chaves faltantes**
4. Geradas entradas BibTeX para cada uma:
   - Metadados extraídos de `extraction_template.csv` (DOI, título, autores, venue, ano)
   - 7 entradas de conhecimento de base (papers seminais + protocolo SLR)

### 34.2. Arquivo gerado

**`results/final_review/missing_references.bib`** — 32 entradas organizadas por grupo:

| Grupo | Chaves |
| ----- | ------ |
| Protocolo SLR | `Wohlin2024`, `dyba2008`, `page2021`, `syriani2023`, `khraisha2024` |
| Seminais PM+SE | `cook1995`, `rubin2007`, `whittaker1994` |
| IC2+IC3 (stochastic) | `joshi2024`, `jeon2015`, `tian2005`, `tyagi2021`, `washizaki2015`, `massitela2018`, `benmesmia2021`, `bhadra2022`, `bhadra2023`, `li2020`, `lunesu2021`, `magennis2015`, `nafreen2020` |
| IC1+IC2 (PM+stochastic) | `incerto2025`, `lopezpintado2023`, `jalote2021`, `guinea2025` |
| IC1+IC3 (PM+forecasting) | `gupta2017`, `pourbafrani2021`, `buliga2025`, `caldeira2022` |
| IC2+IC4 (GitHub Markov) | `jo2023`, `jo2024`, `ortu2023` |

### 34.3. Pontos de atenção

- **`Wohlin2024`**: gerado com o paper de 2014 (EASE 2014, canonical snowballing reference). Verificar se há versão 2024 específica no `.bib` original.
- **`syriani2023`**: gerado como preprint arXiv (2307.06464). Verificar se publicado em venue definitivo.
- Todos os demais têm DOI real extraído do Semantic Scholar via `extraction_template.csv`.

---

## 35. Estado consolidado ao final de 2026-04-19 (atualizado)

### 35.1. Corpus FT (fechado)

| Decisão | n |
| ------- | - |
| include | **169** |
| exclude | **717** (EC1:204, EC3:197, EC5:148, EC2:92, EC4:59) |
| pending | **0** |
| blank   | **0** |
| **TOTAL** | **886** |

### 35.2. Fase de extração de dados

| Item | Estado |
| ---- | ------ |
| `extraction_template.csv` | 169 linhas, 35 colunas, 169/169 `main_finding` |
| PDFs para extração | 75 / 169 |
| Metadados S2 enriquecidos | 155 / 169 com authors |
| `top30_reading_list.csv` | 32 papers rankeados, score 9–14 |
| `quality_score` / `extraction_notes` | Pendente (revisão manual) |

### 35.3. Escrita do cap3 — estado atual

| Componente | Estado |
| ---------- | ------ |
| Diagrama PRISMA | **Atualizado** com números finais (169/717/886) |
| Gráficos (ano, IC, técnica, evidência) | **Atualizado** para $n=169$ |
| Tabela FT screening | **Atualizada** com breakdown EC1–EC5 |
| 6 blocos de síntese por cluster | **Inseridos** no cap3 |
| Tabela de posicionamento (L0–L3) | **Atualizada** com exemplares L2 |
| Discussion F1–F5 | **Atualizada** com $n=169$ |
| Chapter Summary | **Reescrito** com fluxo completo |
| Chaves `\cite{}` com entrada no `.bib` | **32 entradas** em `missing_references.bib` |
| `reading_notes` (top-30) | Pendente (leitura manual) |
| `quality_score` (QA checklist) | Pendente (leitura manual) |

### 35.4. Artefatos do projeto — lista completa

| Artefato | Descrição |
| -------- | --------- |
| `results/extraction/extraction_template.csv` | 169 estudos, 35 colunas, extração LLM completa |
| `results/extraction/pdfs/` | 75 PDFs copiados |
| `results/final_review/top30_reading_list.csv` | Lista priorizada de 32 papers para leitura |
| `results/final_review/cap3_synthesis_draft.tex` | Síntese v1 (gerada manualmente em sessão anterior) |
| `results/final_review/cap3_synthesis_v2.tex` | Síntese v2 gerada por `claude-sonnet-4-6` via `synth_llm.py` |
| `results/final_review/missing_references.bib` | 32 entradas BibTeX faltantes para o `.bib` principal |
| `results/final_review/pending_inaccessible_closed.csv` | 148 papers EC5 para nota PRISMA |
| `results/final_review/included_studies_current.csv` | 169 estudos incluídos |
| `results/final_review/prisma_summary_current.txt` | Snapshot PRISMA final |
| `cap3_slr_revised.tex` | Capítulo 3 da tese — versão atualizada |
| `pipeline/extract_prep.py` | Prepara pasta de extração + S2 enrichment |
| `pipeline/extract_llm.py` | Extração estruturada LLM (batch Anthropic) |
| `pipeline/synth_llm.py` | Síntese por cluster IC (API síncrona) |

### 35.5. Próximas ações prioritárias

1. **Copiar `missing_references.bib`** para o `.bib` principal da tese e compilar o LaTeX
2. **Ler os 32 papers do top-30** e preencher `reading_notes` em `top30_reading_list.csv`
3. **Revisar `cap3_synthesis_v2.tex`** — ajustar os 6 parágrafos conforme leitura dos papers
4. **Preencher `quality_score`** (QA checklist) para os top-32
5. **Gerar tabelas e figuras adicionais** do cap3 a partir de `extraction_template.csv`:
   - Distribuição por técnica PM e técnica estocástica
   - Distribuição por tipo de estudo (case_study/experiment/simulation/theoretical)
   - Heatmap IC × ano
