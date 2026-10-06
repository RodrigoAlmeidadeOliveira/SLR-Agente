# Registro da sessão de 06/10/2026: revisão R2 do artigo IST

Manuscrito: **INFSOF-D-26-00913** (Information and Software Technology), mapping
study "Process Mining and Stochastic Modeling for Software Process Forecasting: A
Systematic Mapping Study with an LLM-Assisted Protocol".
Autores: Rodrigo Almeida de Oliveira, Juliano de Paulo Ribeiro, Edson Emilio Scalabrin.
**Prazo final de reenvio: 22/10/2026.**
Branch de trabalho: `claude/ist-round2`, criado a partir de
`origin/claude/advisor-feedback-closing-round` e publicado no GitHub.

Este arquivo registra o que foi decidido, encontrado e feito nesta sessão, para
dar continuidade ao trabalho sem precisar do histórico do chat.

---

## 1. Ponto de partida: os pareceres da rodada 2

O editor deu uma "última chance". Os dois revisores convergem no mesmo problema central.

**Revisor 1 (9 itens)**
1. O Recall de FT foi 0,246 (cerca de 75% de Lost Evidence), e o corpus não foi corrigido com base nisso.
2. Denominadores inconsistentes: o texto usa 318/259, a Tabela 22 usa 381/315.
3. A janela de elegibilidade não bate com o corpus: há estudos de 1991/1992.
4. PATHCAST ainda aparece nos Resultados ("For PATHCAST, this supports…", "directly justifies Stage 1").
5. A relação entre QA e F1–F5 não é clara (169 vs. 136/169 vs. 259/318).
6. "Full-text screening" é um rótulo enganoso: a etapa usou abstracts.
7. Não está claro se o corpus de 340 veio do protocolo original ou do revisado (16 pending e 595 sem abstract fechados por EC5-extended).
8. A carta de resposta tinha placeholders ("Section [X]", "[N]", texto alternativo) e prometia MCC/WMCC que não estavam na tabela.
9. Ainda aparece "SLR" no texto; a Introdução é curta; a Tabela 13 precisa ser revista.

**Revisor 2**
- A validação humana confirma o problema, mas as conclusões ("only 1 of 340", F1, F3–F5) não mudaram.
- Os 595 + 16 registros continuam fechados por EC5-extended.
- Não houve limiar de Lost Evidence definido antes nem escalonamento.
- **No pacote de replicação, 49 das 51 exclusões humanas de FT são "PDF não acessível"**; o padrão de referência humano precisa de reparo.
- A carta admite que 72,4% do T/A foi feito só pelo título e que o "FT" usou o abstract, mas o manuscrito não diz isso.

---

## 2. Diagnóstico: o que foi encontrado

### 2.1 Onde estão os fontes da R1
O `main` local tinha só a submissão original. Os fontes da R1 estão no branch
`origin/claude/advisor-feedback-closing-round`:
- manuscrito: `article_ist/cap3_article_body.tex` (canônico), `article_ist/overleaf_package/` (usado para compilar) e `article_ist/editorial_manager_attachments/latex_flat/` (só muda os caminhos dos `\input`);
- carta da R1: `article_ist/response_to_reviewers/`;
- validação humana da R1: `results/human_validation/`.

### 2.2 O padrão de referência humano do FT (R1) registrou acesso ao PDF, não elegibilidade
Análise de `results/human_validation/ft_qa_extraction_blind_review_sheet.csv` (n = 177):
- **126 inclusões humanas: todas com PDF local**, quase todas sem nota de justificativa, e todas com QA preenchido (a instrução pedia QA só para quem fosse *include*).
- **51 exclusões humanas: 50 com a nota "PDF não acessível"/"no access file"**; a outra é um "discard".
- Ou seja: na prática, *include* significou "tenho o PDF".
- **Consequência:** o Recall de FT de 0,246 (IC 0,179–0,328) não vale em nenhuma direção e foi retirado. A frase da carta R1 "low FT κ reflects real criteria disagreement" estava errada e foi retratada.
- Os 95 "falsos negativos" foram excluídos pelo LLM por motivo de conteúdo (EC1 = 26, EC3 = 26, EC2 = 16, …), mas **11 deles o LLM marcou como EC5 (inacessível) e o PDF existia**. São candidatos reais a evidência perdida.
- O terceiro avaliador da R1 (que leu os PDFs) aponta como fora de escopo um artigo que o humano incluiu (ft_0079, EC1).

### 2.3 O Recall de T/A (0,250) estava mal especificado
No working set, os registros *maybe* foram encaminhados ao FT (111 include + 775 maybe = 886). Os 54 FN do T/A eram todos *maybe*. **O Recall operacional de T/A é 72/72 = 1,000 (IC 95% 0,949–1,000).**

### 2.4 O pacote da R1 no Editorial Manager estava contaminado
O PDF da R1 incluía também:
- o **manuscrito original** ("SLR", 404 estudos, "PATHCAST … first formally specified L3 pipeline");
- a cover letter original e os highlights antigos;
- o link de Research Data apontando para o DOI restrito antigo (zenodo.20130276).

A carta da R1 tinha placeholders e alternativas não resolvidas ("[added N sentences / …]", `\ref{}` cru). Tinha também a frase "We have not yet propagated the Fase A/B findings…" e prometia a lista de 340 estudos "no próprio artigo", enquanto o Apêndice A dizia "not tabulated in this PDF".

### 2.5 Outros achados
- **Base de informação:** 1.695/2.340 (72,4%) dos registros do working set foram triados no T/A só pelo título (a Scopus Search API não traz o abstract). Após R1, a recuperação de abstracts cobriu 1.131 registros (cobertura 27,6% → 74,0%), com 1.087 re-triagens confiáveis: 372 mudaram (34,2%), 4 passaram de exclude para include/maybe. **Nada disso foi propagado ao corpus.**
- **O "FT" não leu o PDF em cerca de 99,5% dos casos** (`pipeline/fulltext.py::_build_ft_prompt` usa o abstract). Num teste com PDF real em 8 artigos, **3 foram confirmados como evidência perdida**: `ba2ff831`, `ee562777`, `9188583f`. Também **não foram propagados**.
- **Janela de datas:** as buscas reais usaram `PUBYEAR > 1993 AND PUBYEAR < 2027` (1994–2026). A Tabela 3 da R1 dizia "1994–2025", o que não corresponde ao que foi executado. **O WoS não teve filtro de data:** 6 registros anteriores a 1994 vieram do WoS e 1 do ACM. Os estudos de 1991 (`dd71433d`) e 1992 (`37385fbd`) vieram do WoS.
- **Prompt de triagem:**
  - rotulava o escopo como "SLR PATHCAST", mas o conteúdo apenas reescreve IC4a–IC4d;
  - o prompt de FT dizia "**Na dúvida entre include e exclude, prefira exclude**", o que puxa para falsos negativos.
- **Tabela 13 (M12 do R2):**
  - na R0, os níveis contavam 4 famílias, incluindo MSR (95/70/4);
  - na R1, 3 artigos foram rebaixados de L2 para L1 sem mudar a definição (95/73/1);
  - com uma definição única, por famílias de técnica (PM, ST, FC), as contagens são **136/32/1/0** (n = 169) e batem com as interseções do F4 (exatamente duas: 9 + 6 + 17 = 32; as três: 1).
- **O corpus já contém 4 estudos secundários no tema** (mantidos via EC4), que agora entram como trabalhos relacionados na Introdução: Zhang/Kitchenham/Pfahl 2010; Mukala/Cerone/Turini 2015; Thamizharasan/Appavoo 2016; Stepanov/Mitsyuk 2026.

---

## 3. Decisões do autor (06/10/2026)

1. **Refazer o julgamento humano de FT com dois avaliadores:** A = Rodrigo, B = Juliano.
2. **Limiar pré-registrado: Recall ≥ 0,90** (estimativa pontual).
3. **Base única para F1–F5:** todos os estudos distintos confirmados. O QA deixa de ser filtro e vira só análise de sensibilidade (QA ≥ 4/8).
4. **Prazo:** reenvio até 22/10/2026.
5. **Push** do branch autorizado e feito.

---

## 4. O que foi feito, em ordem de commit

| Commit | O quê |
|---|---|
| `1ae94b8` (13:52) | **Pré-registro** `article_ist/response_to_reviewers/round2/PREREGISTRATION_round2_validation.md`, commitado sozinho antes de qualquer coleta |
| `0ef107d` | Ferramental e planilhas cegas: `pipeline/round2_validation.py`, `results/human_validation_round2/` (README, planilhas A/B, `_keys/`), `.gitignore` para o zip |
| `62aff16` | Edições do manuscrito (§5), referências novas, esqueleto da carta de resposta |
| `3d05522` | Pré-preenchimento da planilha FT do avaliador A com as **notas dele mesmo** da R1 |

Branch publicado: `origin/claude/ist-round2` (GitHub `RodrigoAlmeidadeOliveira/SLR-Agente`).

### 4.1 Pré-registro: conteúdo
- **Endpoint primário:** Recall de FT no working set, nos mesmos 177 registros da amostra R1 (`ft_0000`–`ft_0176`). Referência = consenso de 2 avaliadores independentes, cegos ao LLM e um ao outro, julgando pelo texto completo segundo a Tabela 5. Itens inacessíveis viram `not_assessable` e saem do denominador. Métricas: Recall e LE com IC de Wilson, matriz de confusão, MCC, WMCC (FN:FP = 10:1), κ A–B e κ de cada avaliador vs. LLM. **Sucesso: Recall ≥ 0,90.**
- **Limitação declarada:** o avaliador A calculou o relatório da R1 e pode lembrar decisões do LLM. Por isso há uma análise de sensibilidade só com o avaliador B.
- **Endpoint secundário (tier auxiliar),** semente 20261006:
  - S1 = exclusões de T/A do auxiliar (N = 2.423; n = 40);
  - S2 = exclusões de FT e re-FT (N = 537; n = 40);
  - S3 = fechados por EC5-extended (N = 611 = 595 + 16; n = 60).
  - A avalia tudo; B avalia 30% de cada estrato.
  - M = Σ N_s·p̂_s; Recall_aux = I_aux / (I_aux + M), com I_aux = 235. **Sucesso ≥ 0,90.**
- **Escalonamento (obrigatório):**
  - todo registro julgado include por consenso entra no corpus;
  - **E1:** se o Recall de FT < 0,90, humanos re-triam todas as exclusões de FT do working set com texto acessível;
  - **E2:** se o Recall auxiliar < 0,90, escalam-se estratos por ordem de N_s·p̂_s;
  - se não couber até 22/10, **pede-se prorrogação ao editor** em vez de reenviar incompleto.
- **Desvios registrados, todos antes da coleta:**
  1. estrato S0, com 20 includes do LLM do tier auxiliar como chamarizes de cegueira (só uma medida descritiva de precisão);
  2. pré-preenchimento da planilha A com as notas da R1 do próprio avaliador A (nada do LLM, nem o rótulo antigo).

### 4.2 Planilhas e script
- `results/human_validation_round2/`:
  - `ft_eligibility_raterA.xlsx` (177 linhas, com colunas `r1_*`; 126 com extração da R1, 51 com nota de acesso);
  - `ft_eligibility_raterB.xlsx` (177 linhas, em branco);
  - `aux_eligibility_raterA.xlsx` (160 linhas);
  - `aux_eligibility_raterB.xlsx` (48 linhas);
  - `_keys/ft_key.csv` e `_keys/aux_key.csv` (decisão do LLM e estrato; os avaliadores não devem abrir).
- Colunas que o avaliador preenche:
  - `access_basis` (full_text / abstract_only / title_only / not_accessible);
  - `decision` (include / exclude / not_assessable);
  - `ic_matched`, `ec_applied`;
  - `justification` (obrigatória);
  - `evidence_location`.
- `README_avaliadores.md`: regras de cegueira, critérios da Tabela 5, ordem de acesso (PDF local → DOI → CAPES/CAFe → Scholar), **"não use 'na dúvida, exclua'"** e "não crie regras além da Tabela 5". Uma regra minha sobre SRGM e outra sobre predição de defeitos foram retiradas porque contradiziam o IC4c.
- `pipeline/round2_validation.py`:
  - `--build-sheets` (recusa sobrescrever);
  - `--prefill-rater-a` (recusa se já houver decisões);
  - `--build-consensus` (valida o preenchimento e gera `consensus_sheet.xlsx`);
  - `--compute` (gera `round2_report.txt` e `round2_confusion.tex` com o veredito E1/E2 e os registros a adicionar).
  - O fluxo completo foi testado com dados sintéticos numa cópia temporária.
- Pacote do Juliano: `results/human_validation_round2/pacote_avaliador_B_Juliano.zip` (136 MB: planilhas B, README, pré-registro e 132 PDFs). **Fica fora do git** por copyright; enviar por canal privado.

### 4.3 Resultados disponíveis até agora
| Medida | Valor |
|---|---|
| T/A Recall operacional (maybe → FT) | **1,000** (72/72; IC 0,949–1,000) |
| T/A Recall "strict" (como na R1) | 0,250 (18/72), não corresponde ao protocolo aplicado |
| FT Recall R1 | 0,246, **retirado** (referência inválida) |
| R1 T/A: MCC strict / maybe→pos | 0,409 / 0,547 |
| R1 FT: MCC / WMCC | 0,215 / −0,033 (sobre referência inválida) |
| Tamanhos dos estratos auxiliares | S1 2.423 · S2 537 · S3 611 · S0 235 |
| Integração (n = 169, definição única) | L0 136 · L1 32 · L2 1 (PRIMAD) · L3 0 |
| FT Recall R2, Recall auxiliar, κ A–B | **pendentes** (dependem do `--compute`) |

---

## 5. Edições no manuscrito (commit `62aff16`)

Arquivos: `article_ist/cap3_article_body.tex`, `article_ist/main.tex`,
`article_ist/protocol_refs.bib`, sincronizados com `overleaf_package/` e `latex_flat/`.

1. **PATHCAST fora dos Resultados (4.5–4.7).**
   - Removidas 7 frases, incluindo as duas citadas pelo R1, e as descrições que, sem citar o nome, apresentavam a arquitetura do PATHCAST (cadeia absorvente, correção de resíduos) como "nicho vago".
   - A Seção 5.2 virou "Integration Levels"; o PATHCAST ficou como uma hipótese de agenda.
   - A Seção 2.4 agora **declara** o rótulo PATHCAST no prompt e a regra "prefer exclude" do FT.
2. **Janela de datas.**
   - IC1 = 01/01/1994 até a data da busca (12/04/2026).
   - A Tabela 3 mostra os filtros reais (WoS "no date filter"), com uma nota.
   - Os dois estudos pré-1994 foram removidos (Apêndice A).
   - Resumo e Conclusão ajustados.
3. **"SLR" removido** do título da Seção 6, da 2.1, da 4.1, da declaração de IA e do rótulo da Tabela 19 (inclusive no gerador `pipeline/auxiliary_ft.py`).
4. **Tabela 13** refeita com `tabularx` e definição operacional única. A prosa da 4.7.1 foi alinhada (PM+ST = L1). A profundidade da taxonomia SPMF passou a se chamar AD1–AD4. O campo "Integration Level" da extração remete à tabela.
5. **Seção 6.2:**
   - itens renumerados de (i) a (vi);
   - a frase "10/10 ⇒ high recall" virou limitação explícita (o conjunto de controle era conhecido; snowballing semeado pelo controle);
   - o item (iii) foi reescrito: T/A operacional = 1,000, referência FT da R1 retirada, validação R2 com marcadores.
6. **Base de informação:** a Seção 3.3 diz que 72,4% foi decidido só pelo título e descreve a recuperação de abstracts. A 3.4 foi renomeada para "Second-Pass Eligibility Screening ('FT')" e diz que o FT foi baseado em abstract (~99,5%). A caixa do PRISMA foi ajustada.
7. **QA:** deixou de ser filtro; F1–F5 usam todos os confirmados; QA ≥ 4/8 só como sensibilidade (Seções 2.5 e 5.1).
8. **Introdução reescrita:** problema, três comunidades, estudos secundários relacionados, importância, contribuições e estrutura. Foram adicionadas **12 referências com DOI conferido no Crossref**:
   - teinemaa2019outcome, verenich2019remaining, marquezchamorro2018predictive;
   - garcia2019pmmapping (coautor: Scalabrin), thiede2018pmorg;
   - kagdi2007msr, ali2014simulation, hall2012fault;
   - zhang2010simulation, mukala2015floss, thamizharasan2016petri, stepanov2026continuous.
   - Os volumes LNCS de duas entradas foram retirados por não terem sido confirmados.
9. **Marcadores:** a macro `\tbd{…}` (em vermelho) foi criada em `main.tex`, e há **33 ocorrências** para preencher depois do `--compute`. Checagem de liberação: `grep -n "\tbd" *.tex` deve voltar vazio.
10. **Verificação estática** (não há LaTeX local; o build é no Overleaf): citações e labels resolvidos, chaves balanceadas, cópias sincronizadas.

**Carta de resposta:** `article_ist/response_to_reviewers/round2/response_letter_round2.md`. Esqueleto completo, ponto a ponto, sem textos alternativos, com campos ⟦…⟧. Retrata abertamente o Recall de 0,246 e a frase sobre "criteria disagreement".

---

## 6. O que falta (cronograma)

| Data | Etapa | Responsável |
|---|---|---|
| até 14/10 | FT: A decide os 126 com as próprias notas r1_* (~6–8 h) e tenta o CAPES nos 51 sem acesso. Auxiliar: 160 (~10 h) | Rodrigo |
| até 14/10 | FT 177 + auxiliar 48, totalmente às cegas (~28–40 h) | Juliano |
| 15/10 | `--build-consensus`, reunião de consenso, `--compute` | ambos |
| 16–19/10 | **Fase B**: base única F1–F5; adicionar consensos *include* + `ba2ff831`, `ee562777`, `9188583f` + os 4 casos exclude→include/maybe da recuperação de abstracts; remover os 2 pré-1994; regenerar a Tabela 22 e a tabela de sensibilidade de QA; preencher os 33 `\tbd` | Claude + Rodrigo |
| 20–21/10 | Preencher a carta (⟦…⟧), compilar no Overleaf, montar o pacote no Editorial Manager **só com arquivos atuais**, conferir o link de Research Data e o depósito no Zenodo | Rodrigo |
| 22/10 | Reenvio | — |

**Riscos e pendências:**
- Se o E1 disparar, a re-triagem humana de ~570 exclusões não cabe até 22/10. Pelo pré-registro, nesse caso se pede prorrogação; o rascunho existente é `editor_extension_request.md`.
- Critério a fixar no consenso: **confiabilidade de software com Markov em teste** (IC4b ou EC2). Esse caso se repete nos FN (ft_0012, ft_0035, ft_0065, ft_0086, ft_0124).
- Conferir, lendo os artigos, a afirmação da Introdução de que nenhum dos 4 estudos secundários do corpus mapeia PM + estocástico + forecasting juntos.
- Conferir os abstracts suspeitos de match errado do log de auditoria: `d50fcf26` (SIMKIT), `43977ab5`.
- Opcional: um timestamp independente do pré-registro (PR draft ou depósito no OSF/Zenodo).

---

## 7. Hipótese discutida: fazer o julgamento via LLM

**Conclusão: o LLM não pode substituir os avaliadores humanos nesta rodada.** O que se mede é o erro do LLM. Um padrão de referência produzido por outro LLM repete o problema que o R2 criticou ("agreement between two fallible raters shows they agree, not that they are right"), e o pré-registro especifica dois avaliadores humanos. Usar sem declarar seria má conduta.

Usos legítimos, sempre declarados:
1. **Melhorar o teste:** uma triagem FT feita de verdade sobre o PDF, por um modelo **diferente e mais forte que o Haiku 4.5**, validada contra a referência humana. Isso responderia ao item 6 do R1.
2. **Terceiro avaliador auxiliar**, rodado só **depois** que A e B terminarem, para apontar o que reler no consenso. Ele nunca define o rótulo.

Requisitos: a saída do LLM não chega aos avaliadores antes de terminarem; temperatura 0; versão do modelo e prompt no pacote de replicação; declaração na seção de uso de IA; um desvio datado no pré-registro **antes** de rodar.

### 7.1 Prompt de sistema proposto

```text
You are assessing the eligibility of ONE primary study for a systematic mapping
study in software engineering. You will receive the study's full text (extracted
from the PDF) and its bibliographic metadata. Decide eligibility strictly from
the criteria below, using the full text, not only the abstract.

SCOPE
The mapping covers studies that apply process mining, stochastic modelling,
and/or forecasting to SOFTWARE DEVELOPMENT PROCESSES (the process by which
software is built, tested, reviewed, delivered, maintained), using event logs or
software repository data.

INCLUSION — the study must satisfy AT LEAST ONE content criterion:
- IC4a: applies process mining techniques (process discovery, conformance
  checking, predictive process monitoring) to software development artifacts
  (commits, issues, pull requests, CI/CD logs, bug trackers, version control).
- IC4b: uses stochastic models (Markov chains, Monte Carlo simulation,
  stochastic Petri nets, absorbing chains) to analyse software development
  processes or workflows.
- IC4c: proposes or evaluates forecasting of software process metrics (lead
  time, cycle time, remaining time, throughput, defect rates) from event logs or
  repository data.
- IC4d: mines software repositories (GitHub, Jira, VCS, CI/CD platforms) to
  discover, analyse, or improve software process models.

EXCLUSION — any one excludes, even if an IC is met:
- EC1: the application domain is exclusively outside software development
  (healthcare, manufacturing, supply chain, generic business processes) with no
  demonstrated relevance to SDLC processes.
- EC2: software is only the implementation platform or the object whose runtime
  behaviour is modelled; the process analysed is not a software development
  process.
- EC3: purely algorithmic or theoretical contribution with no empirical
  evaluation in a software development context.
- EC4: secondary study (SLR, mapping, survey) that does not specifically address
  process mining or stochastic methods in software engineering.
- Not a primary study (whole proceedings volume, front matter, index, editorial):
  exclude and say so.

FORMAL FILTERS (report, do not re-judge unless clearly violated): published
1 Jan 1994 to 12 Apr 2026; English; peer-reviewed journal, conference or
workshop paper of at least 4 pages.

DECISION RULES
1. Judge what the study actually does, as shown in its method and evaluation
   sections, not what its title or keywords suggest.
2. Do not apply "when in doubt, exclude" and do not apply "when in doubt,
   include". If the text supports a decision, make it; record residual doubt in
   `uncertainty`.
3. Every IC or EC you apply must be supported by a verbatim quote from the full
   text (max. 40 words each) with its location (section heading or page).
4. If the supplied text is not the paper named in the metadata (wrong PDF,
   garbled extraction, only front matter), do not judge eligibility: return
   decision "not_assessable" and explain.
5. Do not use outside knowledge about the paper or its authors.

OUTPUT — return only valid JSON, no other text:
{
  "text_matches_metadata": true | false,
  "access_basis": "full_text" | "abstract_only" | "not_accessible",
  "decision": "include" | "exclude" | "not_assessable",
  "ic_matched": ["IC4a", ...],
  "ec_applied": ["EC1", ...],
  "evidence": [{"criterion": "IC4b", "quote": "...", "location": "Sec. 3.2"}],
  "justification": "<= 60 words, why the decisive criterion applies",
  "uncertainty": "low" | "medium" | "high",
  "uncertainty_reason": "what would change the decision, or empty"
}
```

### 7.2 Mensagem do usuário (por artigo)

```text
METADATA
Title: {title}
Authors: {authors}
Year: {year}
Venue: {venue}
DOI: {doi}

FULL TEXT (extracted from PDF; may contain extraction noise)
<<<
{full_text}
>>>
```

### 7.3 Por que o prompt é assim
- **Sem "na dúvida, exclua",** que estava no prompt original e puxa para falsos negativos.
- **Citação literal com localização** em cada critério: torna a decisão auditável, reduz alucinação e acelera o consenso.
- **`text_matches_metadata`:** os PDFs locais já tiveram troca (ft_0095/ft_0136) e extração corrompida (ft_0016, ft_0044, ft_0069).
- **EC2 cita "runtime behaviour":** é a fronteira dos casos de confiabilidade com Markov. A redação final deve seguir o critério fixado no consenso humano.

---

## 8. Como retomar

1. `git checkout claude/ist-round2`
2. Ler este arquivo, o pré-registro e o README dos avaliadores.
3. Ver se as planilhas estão preenchidas; se estiverem, rodar `python -m pipeline.round2_validation --build-consensus`.
4. Depois do consenso, rodar `python -m pipeline.round2_validation --compute` e seguir a Fase B (§6).
5. Antes do reenvio, estas três buscas devem voltar vazias: `grep -n "\tbd" article_ist/*.tex`, `grep -n "⟦" article_ist/response_to_reviewers/round2/response_letter_round2.md` e uma busca por "SLR" referindo-se a este estudo.
