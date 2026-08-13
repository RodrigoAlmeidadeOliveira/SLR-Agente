# Prioridade de revisão — Capítulo 3 (SLR) frente à banca DRC

Fonte: anotações `drdrc` em `TESE_DOUTORADO_PATHCAST_20260610_DRC.pdf`  
Arquivo a editar: `capitulos/cap3_slr_revised.tex`  
Regra: um eixo por vez. P0 destrava P1; não reeditar a Tabela 3.15 antes de fechar L0–L3.

**Estado (2026-08-13):** P0-1, P0-2, P0-3 e P1-1…P1-5 aplicados em `capitulos/cap3_slr_revised.tex`. P2 (siglas, critério operacional de lacuna, restyle da Tabela 3.15) ainda aberto.

Critério de prioridade:
- **P0** — ataca a tese do capítulo (“PATHCAST preenche L3”) ou foi marcado com `******` *e* o texto atual é inconsistente.
- **P1** — pergunta de protocolo que a banca fará na defesa; o conteúdo existe, falta explicitar.
- **P2** — clareza / front matter; não muda o argumento.

---

## Ordem de execução (não pular)

```
P0-1  Definir L0–L3 uma vez, cedo, e usar só essa definição
P0-2  Classificação da SLR: critério + RQs + grau/nível
P0-3  Gap da SLR ↔ dor do projeto (ponte para o Cap. 1)
P1-1  PICO Comparison omitido — justificar
P1-2  Control papers — critério de seleção
P1-3  String de busca ↔ tipos de mineração de processos
P1-4  QA2/QA3/QA7 — rubrica operacional + reprodutibilidade desta tese
P1-5  Tabela de IC/EC não flutuar para Quality Assessment
P2-1  Siglas (SPMF e demais)
P2-2  Critério operacional de “lacuna” (RQ3.2)
P2-3  Tabela 3.15 — só depois de P0-1
```

---

## P0 — Fazer primeiro

### P0-1. Uma definição só de L0–L3 (A38, A39, A41)

**Por que é o primeiro item.** O revisor perguntou “o que é L3 architecture?”, se *architecture* = *integration level*, e o que significa *Unified*. Isso não é só vocabulário: o capítulo **usa três definições diferentes** do mesmo rótulo.

| Onde | O que o texto diz hoje |
|------|-------------------------|
| Tabela de extração (`tab:extraction`) | `L0 None / L1 Sequential / L2 Pipeline / L3 Unified` |
| RQ3.1 (prosa, ~p. 43) | L1 = estocástico sem discovery; L2 = acoplamento parcial; L3 = PM→Markov→MC→ML |
| Tabela 3.15 (`tab:positioning`, p. 49) | L0 = ≤1 IC; L1 = 2 ICs; L2 = 3 ICs; L3 = 4 ICs + pipeline unificado |

Enquanto isso não for uma definição só, reeditar a Tabela 3.15 (A41) só troca um problema por outro.

**Ação (um bloco, cedo no protocolo — imediatamente após as RQs ou no início de Data Extraction):**

1. Definir **Integration Level** como escala de *composição metodológica*, não de “arquitetura de software”.
2. Escolher **uma** operacionalização e copiá-la para extração, RQ3.1 e Tabela 3.15. Recomendação (alinha PATHCAST e a banca):

   | Nível | Nome | Operacionalização |
   |-------|------|-------------------|
   | L0 | Isolated | Uma família técnica; sem encadeamento |
   | L1 | Sequential | Duas famílias no mesmo estudo, sem contrato entre estágios |
   | L2 | Pipeline | Três famílias com ponte parcial (falta contrato formal ou fechamento ML) |
   | L3 | Unified | PM → Markov → MC → ML com contratos entre estágios, validado em logs SDLC |

3. Na primeira ocorrência de L3 na prosa (hoje ~p. 43), apontar para essa definição — não esperar a Tabela 3.15.
4. Proibir “L3 architecture” na prosa; usar “L3 integration level (Unified)”.
5. Colisão de namespace a resolver no mesmo passe: **IC1–IC3 dos critérios de inclusão** (período, idioma, peer-review) ≠ **IC1–IC3 das famílias técnicas** na síntese. Renomear as famílias (ex.: TF-PM / TF-ST / TF-FC / TF-ML) *ou* prefixar “content IC4a–d”. Sem isso, “L2 = three ICs matched” é ilegível.

**Pronto quando:** grep de `L0\|L1\|L2\|L3` no capítulo mostra a mesma definição em extração, RQ3.1 e tabela de posicionamento; zero ocorrências de “L3 architecture” como rótulo (só a frase que o proíbe); síntese usa TF-PM/TF-ST/TF-FC/TF-ML, não IC1–IC3, para famílias técnicas.

---

### P0-2. Critério de classificação da SLR + RQs + “grau” vs “nível” (A28, A29, A30)

**Texto atual.** A introdução promete “identify, classify, and synthesize”, mas não diz *classificar segundo o quê*. As RQs usam “level of integration”; o parágrafo de abertura usa “degree of integration”.

**Ação:**

1. Um parágrafo após o objetivo da SLR, explicitando os **três eixos de classificação** (já existentes na taxonomia SPMF, mas anunciados só no fim):
   - paisagem de aplicação (RQ1 → SDLC Coverage);
   - técnicas e métodos de previsão (RQ2 → Analytical Depth AD1–AD4);
   - integração PM × estocástico (RQ3.1 → Integration Level L0–L3).
2. Padronizar o termo: **level / nível** (L0–L3). Trocar “degree/grau” no parágrafo de abertura e em qualquer outra ocorrência, *ou* uma nota de uma linha: “grau = nível L0–L3”.
3. Na Tabela `tab:slr-rqs`, RQ3.1: expected output “Integration maturity assessment (L0–L3, def. §…)” em vez de um rótulo solto.

**Pronto quando:** o leitor sabe, na p. 18, *como* um paper será classificado, antes de ver resultados.

---

### P0-3. Gap da SLR dialoga com a dor do projeto (A40)

**Texto atual.** `Research Gap Identification` (F1–F5) é forte empiricamente e já mapeia F1→D1, F3→D3, F4→D5, F5→D4. O revisor não pede mais números: pede a **ponte com a dor** (comentários A12/A15/A24 do Cap. 1).

**Ação (um parágrafo de abertura em `\subsection{Research Gap Identification}`):**

> A dor operacional que motiva PATHCAST é a previsão de processos de desenvolvimento feita sobre métricas de repositório, sem a estrutura do fluxo. Os cinco achados abaixo mostram que essa dor não é um vazio de técnicas isoladas, e sim a ausência de composição L3 validada em dados de SDLC.

Depois, uma linha por finding: F1 = a dor persiste porque o campo para em descrição; F4 = a dor persiste porque as técnicas não se encadeiam; etc.

**Pronto quando:** F1–F5 respondem “por que essa dor ainda existe”, não só “o que falta na literatura”.

---

## P1 — Protocolo (banca vai perguntar)

### P1-1. PICO Comparison = N/A (A32) — 1 parágrafo

Não inventar um comparador na busca. Declarar:

- a SLR é de **mapeamento do cenário**, não de eficácia comparativa;
- C é omitido **de propósito** (Kitchenham/Petersen: C opcional em mapping studies);
- o comparador entra na **avaliação empírica** de PATHCAST (modelos só com métricas tradicionais de repositório vs. features de processo).

Trocar na tabela PICO: `N/A (omitted)` → `Omitted by design (mapping study; comparator deferred to PATHCAST evaluation)`.

### P1-2. Critério de seleção dos control papers (A35)

A Tabela `tab:validation-set` justifica cada paper, mas não diz **como os 10 foram escolhidos**. Acrescentar um parágrafo antes da tabela:

- cobertura das quatro interseções de conteúdo (PM×SE, estocástico×SE, PPM seminal, ponte PM→simulação);
- mix seminal + contemporâneo;
- pelo menos um por biblioteca-alvo quando possível;
- independência da string (escolhidos *a priori*).

Corrigir de passagem a inconsistência 10 vs 12 (“control set of 10 papers” vs “12 control papers” na recuperação).

### P1-3. String de busca vs tipos de MP (A33)

O revisor pergunta se o problema é investigado pela aderência aos tipos de mineração de processos.

**Ação:** após o Block I, um mapeamento explícito:

| Tipo van der Aalst | Termos na string | Campo de extração |
|---|---|---|
| Discovery | process discovery, workflow mining, process mining | PM Technique Category |
| Conformance | conformance checking | idem |
| Enhancement / prediction | predictive process monitoring, remaining time, process forecasting | Prediction Target + Stochastic Method |

Enhancement “clássico” (performance extension) não tem termo próprio — dizer isso e que é capturado no campo de extração, não na string.

### P1-4. Rubrica QA2 / QA3 / QA7 e reprodutibilidade *desta* tese (A36, A37)

QA2 “described in detail?” e QA3 “described reproducibly?” estão como 0/1 sem âncora. O revisor ainda cobra que **esta tese** cumpra o que cobra dos outros.

**Ação:**

1. Rubrica de uma linha por critério (pode ir para o apêndice, com ponte no capítulo):
   - QA2 = 1 sse há domínio SDLC + tipo de organização/projeto + artefato de dados.
   - QA3 = 1 sse fonte, janela temporal e unidade de caso são reconstruíveis.
   - QA7 = 1 sse há dataset público e/ou código (já existe o número 6.5%).
2. Em Threats / Replication Package: uma frase de fechamento — o pacote PATHCAST é desenhado para passar QA3 e QA7, precisamente os critérios mais fracos do corpus (14.8% dataset público; 6.5% QA7).

### P1-5. IC/EC visíveis na seção certa (A34)

O revisor viu o título *Inclusion and Exclusion Criteria* e a tabela só em Quality Assessment → **float**. Forçar a tabela a permanecer na subseção (`[H]` / `\FloatBarrier`) ou transformar em `longtable` in-place. Não mudar o conteúdo dos critérios neste item.

---

## P2 — Depois de P0/P1

### P2-1. Lista de siglas (A11)

Em `frontmatter/glossary.tex` faltam pelo menos: **SPMF**, PPM, CRPS, IC/EC, L0–L3 (ou “IL”), AD1–AD4, QA1–QA8. A banca foi à lista, não achou SPMF (taxonomia §3.5.3), e generalizou: definições simplificadas no texto sem entrada na lista.

### P2-2. Critério de “lacuna” na RQ3.2 (A31)

Operacionalizar gap = (i) ausência de L3 no corpus; (ii) teto descritivo (F1); (iii) reprodutibilidade baixa (F2/QA7). Uma frase na Tabela de RQs e um critério no início de RQ3.2.

### P2-3. Reeditar Tabela 3.15 (A41) — **somente após P0-1**

- uma coluna “Definição operacional” (a mesma de P0-1);
- separar contagem 169-set vs 73-PDF (já existe, mas está densa);
- PATHCAST numa linha de rodapé, não competindo com “representative example” dos papers.

---

## Fora deste capítulo (não misturar)

Estes itens da banca **não** são do Cap. 3, mas P0-3 fica incompleto sem eles:

| ID | Onde | O que |
|----|------|-------|
| A12, A15, A24 | Cap. 1 | Nomear a dor *antes* de process mining; trabalhos relacionados × dor × limitação |
| A1 | tese inteira | Padronizar *pipeline* |
| A7, A17, A18 | Resumo + Cap. 1 | Um único enunciado de objetivo |

---

## Status vs. fonte atual

| ID DRC | Item | Status no `cap3_slr_revised.tex` |
|--------|------|----------------------------------|
| A28 | critério de classificação | **DONE** (três eixos em `\ref{sec:slr-il-def}`) |
| A29 | RQs bem definidas | **DONE** (RQ3.1 aponta para `tab:il-def`) |
| A30 | grau vs nível | **DONE** (degree → level; tabela L0–L3) |
| A31 | critério de lacuna | PARTIAL (P0-3 ponte dor feita; P2-2 operacionalização RQ3.2 ainda aberta) |
| A32 | PICO C | **DONE** |
| A33 | tipos de MP na busca | **DONE** (`tab:block-i-pm-types`) |
| A34 | IC/EC na seção errada | **DONE** (`[H]` + `\FloatBarrier`) |
| A35 | seleção dos controls | **DONE** (critério a priori + 10 vs 12 records) |
| A36 | QA2 “in detail” | **DONE** (âncoras QA2/QA3/QA7) |
| A37 | reprodutibilidade desta tese | **DONE** (frase QA3/QA7 no pacote) |
| A38 | Unified / RQ3.1 | **DONE** |
| A39 | L3 architecture | **DONE** (definição única; frase proibida) |
| A40 | gap ↔ dor | **DONE** (abertura de F1–F5) |
| A41 | Tabela 3.15 | **PARTIAL** — definição alinhada a `tab:il-def`; coluna IC-count removida (não relabel). Layout P2-3 (169 vs 73 densos) ainda pode ser refinado. |
| A11 | SPMF na lista de siglas | NOT-DONE (P2-1) |
