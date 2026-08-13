# Anotações da banca — DRC

Fonte: `TESE_DOUTORADO_PATHCAST_20260610_DRC.pdf`  
Revisor: **drdrc**  
Extração: 13 ago 2026  
Anotações: **42** (40 destaques + 2 notas de texto), todas com comentário  
Período das anotações: 24 jun 2026 – 1 jul 2026  
Cobertura: capa, resumo, lista de siglas, Cap. 1, Cap. 2 (parcial), Cap. 3, início do Cap. 4 (p. 67). Sem anotações nos capítulos posteriores.

Convenção do revisor: itens iniciados com `******` (ou variação) foram marcados como prioridade.  
Páginas abaixo: **página impressa da tese** (PDF entre parênteses).

---

## 1. Elogios (não exigem correção)

| # | Página | Trecho marcado | Comentário |
|---|--------|----------------|------------|
| E1 | Capa (PDF 1) | Título PATHCAST | Declaração do uso de IA Generativa — **Parabéns**. LLM Screening Prompts. |
| E2 | ii (PDF 8) | Parágrafo final do resumo (incorporação da estrutura do processo…) | **OK** — contribuição apresentada de forma clara e objetiva. |
| E3 | 4 (PDF 30) | Pergunta central de pesquisa | **Boa pergunta. Parabéns.** |
| E4 | 5 (PDF 31) | *Justification and Research Gap* | Elaboração desta seção é muito interessante. **Parabéns.** |
| E5 | 7 (PDF 33) | *Research Methodology* | Síntese e apresentação do percurso metodológico é muito interessante. |
| E6 | 11 (PDF 37) | Reuso de `conf(c)` no Cap. 4 | Interessante a associação com o que será adotado nos próximos capítulos. *(segue pedido de análise de potencial/limitações — ver A20)* |
| E7 | 67 (PDF 93) | Figura 4.2 — PATHCAST component overview | **Boa apresentação.** |

---

## 2. Catálogo completo por localização

### Capa e front matter

#### A1 — Capa (PDF 1) — Highlight
**Trecho:** nome do autor (área do título).  
**Comentário:**
> Vale rever o texto como um todo buscando padronizar os termos.  
> Apenas como exemplo PIPELINE está apresentado de diversas formas.

#### A2 — Capa (PDF 1) — Highlight
**Trecho:** `PATHCAST: A`  
**Comentário:**
> Declaração do uso de IA Generativa  
> Parabéns  
> LLM Screening Prompts

#### A3 — Resumo, p. ii (PDF 8) — Highlight
**Trecho:** `Esta tese investiga se modelos`  
**Comentário:**
> O que se espera como resultado deste verbo de dizer?

#### A4 — Resumo, p. ii (PDF 8) — Highlight  **[prioridade]**
**Trecho:** `uma base mais informativa`  
**Comentário:**
> ****** o que seria uma base mais informativa?

#### A5 — Resumo, p. ii (PDF 8) — Highlight
**Trecho:** parágrafo que introduz o PATHCAST (`Para abordar esse problema, a tese propõe o PATHCAST…`)  
**Comentário:**
> este seria o objetivo?  
> Em caso afirmativo seria interessante adotar um VERBO DE DIZER

#### A6 — Resumo, p. ii (PDF 8) — Nota (Text)
**Comentário:**
> OBJETIVO APRESENTADO NA SEÇÃO 1.  
> "Esta tese propõe um método que preenche a lacuna entre os ricos dados de eventos gerados por ferramentas de desenvolvimento de software e as capacidades de previsão probabilística que esses dados poderiam viabilizar."

#### A7 — Resumo, p. ii (PDF 8) — Nota (Text)  **[prioridade]**
**Comentário:**
> ***** REVER o objetivo apresentado em diversos pontos do texto  
>  
> OBJETIVO APRESENTADO NA SEÇÃO 1.2.1  
> *To develop a computational method for the probabilistic forecasting of software development processes, based on the integration of process mining, stochastic modeling through Markov chains, Monte Carlo simulation, and machine learning, capable of transforming data from software repositories into analytical models that enable the prediction of the behavior and outcomes of these processes.*

#### A8 — Resumo, p. ii (PDF 8) — Highlight  **[prioridade]**
**Trecho:** `repositórios de software`  
**Comentário:**
> ****** seriam repositorios de processos de desenvolvimento de software?

#### A9 — Resumo, p. ii (PDF 8) — Highlight  **[prioridade]**
**Trecho:** `suas distribuições de resultados`  
**Comentário:**
> ****** o que seriam distribuições de resultados

#### A10 — Resumo, p. ii (PDF 8) — Highlight
**Trecho:** parágrafo final do resumo  
**Comentário:**
> OK — contribuição apresentada de forma clara e objetiva

#### A11 — List of Acronyms, p. xx (PDF 26) — Highlight  **[prioridade]**
**Trecho:** `List of Acronyms`  
**Comentário:**
> ****** O que significa SPMF?  
> 3.5.3 Proposed Taxonomy: SPMF (página 50)  
> Completar esta lista, pois o texto apresenta SIMPLIFICAÇÕES DE DEFINIÇÕES QUE NÃO FACILITAM A COMPREENSÃO E QUANDO BUSCAMOS AQUI A SUA RESPECTIVA DEFINIÇÃO NÃO LOCALIZAMOS

---

### Capítulo 1 — Introduction

#### A12 — p. 1 (PDF 27) — Highlight  **[prioridade]**
**Trecho:** parágrafo de abertura sobre process mining (van der Aalst).  
**Comentário:**
> ******* me parece prematuro entrar com Mineração de processos sem claramente apresentar A DOR QUE motiva o processo.  
> QUAL É A DOR?

#### A13 — p. 2 (PDF 28) — Highlight
**Trecho:** `This thesis proposes a method that bridges the gap…`  
**Comentário:**
> Evitar a adoção de termos que envolvam juízo de valor

#### A14 — p. 2 (PDF 28) — Highlight  **[prioridade]**
**Trecho:** `existing literature on process mining applied to software development (COOK; WOLF, 1998; PONCIN; SEREBRENIK; BRAND, 2011; RUBIN et al., 2007)`  
**Comentário:**
> ****** Parece curioso que estas referências sustentem esta afirmação tendo em vista que o MANIFESTO MINERAÇÃO DE PROCESSOS é datado de <<? Original version appeared in the BPM 2011 Workshops proceedings, Lecture Notes in Business Information Processing, Springer-Verlag, 2011>>>

#### A15 — p. 2 (PDF 28) — Highlight  **[prioridade]**
**Trecho:** título *Research Problem*  
**Comentário:**
> ******** esta seção é interessante, mas não deixa claro:  
> Quais são as dores geradas por estas situações?  
> O que existe (referências) — trabalhos relacionados que tentam minimizar estas dores e as suas limitações.

#### A16 — p. 3 (PDF 29) — Highlight  **[prioridade]**
**Trecho:** parágrafo sobre técnicas independentes (Markov, Monte Carlo, ML) e ausência de pipeline formalizado.  
**Comentário:**
> ****** Não temos referências que sustentam estes problemas apresentados  
> É desejável que nesta seção as referências sejam claramente apresentadas.

#### A17 — p. 3 (PDF 29) — Highlight
**Trecho:** `In this context, this research investigates the potential of process mining…`  
**Comentário:**
> É importante alinhar os objetivos apresentados

#### A18 — p. 3 (PDF 29) — Highlight
**Trecho:** objetivo geral (*To develop a computational method…*)  
**Comentário:**
> IDEM… sobre o alinhamento do objetivo… Talvez esteja sendo confundido um pouco com contribuição

#### A19 — p. 4 (PDF 30) — Highlight
**Trecho:** `proposed hypotheses`  
**Comentário:**
> A hipótese já foi proposta?

#### A20 — p. 4 (PDF 30) — Highlight
**Trecho:** objetivo específico de avaliação empírica (ML vs métricas tradicionais).  
**Comentário:**
> *Avaliar empiricamente o método proposto…*  
> Como você dialoga este objetivo / necessidade frente:  
> A motivação?  
> A Lacuna?

#### A21 — p. 4 (PDF 30) — Highlight
**Trecho:** título *Research Questions*  
**Comentário:**
> Como estas perguntas dialogam com os objetivos específicos?  
> De que forma o percurso metodológico esclarece como os objetivos específicos serão atendidos e como as perguntas estabelecidas serão respondidas?

#### A22 — p. 4 (PDF 30) — Highlight
**Trecho:** pergunta central de pesquisa  
**Comentário:**
> Boa pergunta. Parabéns

#### A23 — p. 5 (PDF 31) — Highlight
**Trecho:** título *Justification and Research Gap*  
**Comentário:**
> a elaboração desta seção é muito interessante. PARABÉNS

#### A24 — p. 5 (PDF 31) — Highlight  **[prioridade]**
**Trecho:** `Several systematic reviews and surveys have been published in areas adjacent…`  
**Comentário:**
> ******* Qual é a principal dor?  
> Qual é a principal contribuição de cada trabalho relacionado para minimizar a principal dor?  
> Qual é a limitação de cada trabalho referente à minimização da dor?

#### A25 — p. 6 (PDF 32) — Highlight  **[prioridade]**
**Trecho:** título *Expected Contributions*  
**Comentário:**
> ******* De que forma cada contribuição apontada contribui para a minimização da dor?  
> Contribui para a redução da lacuna?

#### A26 — p. 7 (PDF 33) — Highlight  **[prioridade]**
**Trecho:** título *Research Methodology*  
**Comentário:**
> ****** Legal esta síntese e apresentação do percurso metodológico é muito interessante.

---

### Capítulo 2 — Theoretical Foundation

#### A27 — p. 11 (PDF 37) — Highlight  **[prioridade]**
**Trecho:** definição de `conf(c)` e reuso no Cap. 4 (Eq. 4.24).  
**Comentário:**
> ******* Interessante esta associação sobre o que está apresentado neste capítulo com o que estará sendo adotado nos próximos capítulos.  
> Mas não seria importante apresentar alguma análise sobre potencial e limitações que permita justificar esta opção metodológica?  
> Esta observação vale para a seção como um todo

---

### Capítulo 3 — Systematic Literature Review

#### A28 — p. 18 (PDF 44) — Highlight  **[prioridade]**
**Trecho:** `The primary objective is to identify, classify, and synthesize…`  
**Comentário:**
> ***** Verificar se ficou claro qual o critério adotado para esta classificação.

#### A29 — p. 18 (PDF 44) — Highlight
**Trecho:** decomposição em sub-perguntas (PM no SDLC, técnicas de previsão, grau de integração).  
**Comentário:**
> Verificar se estes critérios — perguntas estão bem definidos  
> - aplicação de *process mining* em contextos de SDLC,  
> - as técnicas e os métodos de previsão empregados e  
> - o grau de integração entre *process mining* e métodos de previsão estocástica.

#### A30 — p. 19 (PDF 45) — Highlight  **[prioridade]**
**Trecho:** `What is the level of integration between PM and stochastic methods?`  
**Comentário:**
> ******** process mining and stochastic forecasting methods.  
> qual é a diferença entre **nível** versus **grau**?  
> Grau… termo adotado no início deste capítulo

#### A31 — p. 19 (PDF 45) — Highlight
**Trecho:** `SDLC?` (RQ sobre lacunas para previsão orientada a processos)  
**Comentário:**
> Quais lacunas existem para a previsão orientada a processos no SDLC?  
> quais critérios para esta definição?  
> qual é o desafio versus o que os trabalhos relacionados apresentam?

#### A32 — p. 20 (PDF 46) — Highlight  **[prioridade]**
**Trecho:** `Comparison N/A (omitted)` na tabela PICO  
**Comentário:**
> ******** C – Comparador ou Controle (C – Comparators / Control)  
> Este componente é opcional, mas crucial para estudos que buscam comparar resultados. Ele define com o que a intervenção ou exposição será comparada.  
> Alternativas: Uma intervenção padrão, outro tratamento, placebo.  
> Ausência de Intervenção: Não fazer nada, tratamento usual.  
> Outra Exposição: Pacientes sem a exposição (ex: não-fumantes).  
> Exemplos: Comparador: Outro medicamento / Tratamento convencional / Ausência de intervenção.

#### A33 — p. 20 (PDF 46) — Highlight  **[prioridade]**
**Trecho:** string de busca de process mining (`"process mining" OR "process discovery" OR …`)  
**Comentário:**
> ******** O problema é investigado pela aderência aos diversos tipos da MP?

#### A34 — p. 22 (PDF 48) — Highlight
**Trecho:** título *Inclusion and Exclusion Criteria*  
**Comentário:**
> são apresentados apenas na Table 3.5: Inclusion and exclusion criteria, que está na seção Quality Assessment

#### A35 — p. 23 (PDF 49) — Highlight
**Trecho:** `Control papers`  
**Comentário:**
> qual é o critério para esta seleção?

#### A36 — p. 25 (PDF 51) — Highlight  **[prioridade]**
**Trecho:** `described in detail?` (checklist de qualidade)  
**Comentário:**
> **** como caracterizar esta situação?

#### A37 — p. 25 (PDF 51) — Highlight  **[prioridade]**
**Trecho:** `described reproducibly?`  
**Comentário:**
> ************* Reprodutibilidade é uma característica priorizada por você, sendo assim é importante que o apresentado e descrito no seu projeto garanta esta característica

#### A38 — p. 26 (PDF 52) — Highlight  **[prioridade]**
**Trecho:** `Data extraction form.`  
**Comentário:**
> ******* What is the level of integration between PM and stochastic methods?  
> Integration maturity assessment  
> Qual característica expressa esta questão?  
> O que significa **Unified**?

#### A39 — p. 43 (PDF 69) — Highlight  **[prioridade]**
**Trecho:** `no paper in the reviewed corpus instantiates an L3 architecture…`  
**Comentário:**
> **** O que seria L3 architecture?  
> Integration Level L0 None / L1 Sequential / L2 Pipeline / L3 Unified  
> architecture e integration level são sinônimos?  
> Alguma aproximação pode ser identificada, mas existe um esforço do leitor  
> PÁGINA 49  
> Table 3.15: Integration levels in the 169-study confirmed set and PATHCAST positioning.

#### A40 — p. 45 (PDF 71) — Highlight  **[prioridade]**
**Trecho:** título *Research Gap Identification*  
**Comentário:**
> **** de que forma este GAP identificado dialoga com a DOR que motiva o projeto?

#### A41 — p. 49 (PDF 75) — Highlight
**Trecho:** `Table 3.15: Integration levels in the 169-study confirmed set and PATHCAST positioning.`  
**Comentário:**
> é importante reeditar esta tabela para facilitar a leitura

---

### Capítulo 4 — The Proposed Method: PATHCAST

#### A42 — p. 67 (PDF 93) — Highlight
**Trecho:** `Figure 4.2: PATHCAST component overview.`  
**Comentário:**
> Boa apresentação

---

## 3. Temas recorrentes (agrupamento para revisão)

O revisor volta várias vezes aos mesmos eixos. Itens com `******` estão em negrito na lista abaixo.

### T1. Qual é a “dor”? (motivação do problema)
- **A12** — prematuro entrar em PM sem apresentar a dor.
- **A15** — Research Problem: dores geradas; trabalhos que tentam minimizá-las e limitações.
- **A24** — por cada trabalho relacionado: dor, contribuição, limitação.
- **A25** — cada contribuição reduz a dor / a lacuna?
- **A40** — o gap da SLR dialoga com a dor do projeto?

### T2. Alinhar objetivo / contribuição / hipótese / RQs
- A3, A5, A6, **A7** — objetivo no resumo vs. Seção 1 vs. 1.2.1; usar verbo de dizer.
- A17, A18 — objetivo confundido com contribuição.
- A19 — hipótese já foi proposta quando o texto diz “proposed hypotheses”?
- A20 — objetivo específico de avaliação empírica vs. motivação e lacuna.
- A21 — RQs × objetivos específicos × percurso metodológico.

### T3. Precisão terminológica
- A1 — padronizar termos (ex.: *pipeline* em várias formas).
- A13 — evitar juízo de valor (“bridges the gap”, “rich event data”).
- **A4** — o que é “base mais informativa”?
- **A8** — “repositórios de software” vs. repositórios de processos de desenvolvimento.
- **A9** — o que são “distribuições de resultados”?
- **A11** — completar lista de siglas (SPMF e demais simplificações).
- **A30** — *level* vs. *grau* de integração.
- **A38 / A39** — o que é L3 / Unified; architecture ≠ integration level?
- A41 — reeditar Tabela 3.15 para leitura.

### T4. Referências que sustentam o problema
- **A14** — Cook & Wolf 1998 / Poncin 2011 / Rubin 2007 vs. Manifesto de PM (2011).
- **A16** — problemas do pipeline ad hoc sem referências.

### T5. Protocolo da SLR (Cap. 3)
- **A28 / A29** — critério de classificação e definição das RQs da revisão.
- A31 — critérios para “lacunas” no SDLC.
- **A32** — PICO: Comparison omitido; justificar o C.
- **A33** — a busca cobre os tipos de mineração de processos?
- A34 — critérios de inclusão/exclusão só aparecem na Tabela 3.5 (Quality Assessment).
- A35 — critério de seleção dos *control papers*.
- **A36** — como caracterizar “described in detail?”.
- **A37** — reprodutibilidade precisa estar garantida no próprio projeto.

### T6. Fundação metodológica (Cap. 2)
- **A27** — analisar potencial e limitações das escolhas (vale para a seção inteira), não só encadear fórmulas.

---

## 4. Índice rápido (página impressa → IDs)

| Página tese | PDF | IDs |
|-------------|-----|-----|
| Capa | 1 | A1, A2 |
| ii (Resumo) | 8 | A3–A10 |
| xx (Siglas) | 26 | A11 |
| 1 | 27 | A12 |
| 2 | 28 | A13, A14, A15 |
| 3 | 29 | A16, A17, A18 |
| 4 | 30 | A19, A20, A21, A22 |
| 5 | 31 | A23, A24 |
| 6 | 32 | A25 |
| 7 | 33 | A26 |
| 11 | 37 | A27 |
| 18 | 44 | A28, A29 |
| 19 | 45 | A30, A31 |
| 20 | 46 | A32, A33 |
| 22 | 48 | A34 |
| 23 | 49 | A35 |
| 25 | 51 | A36, A37 |
| 26 | 52 | A38 |
| 43 | 69 | A39 |
| 45 | 71 | A40 |
| 49 | 75 | A41 |
| 67 | 93 | A42 |
