# Plano de Revisão — Round 1, Reviewer 2 (combinado com itens pendentes do Reviewer 1)

Manuscrito: *Process Mining and Stochastic Modeling for Software Process Forecasting: A Systematic Literature Review with an LLM-Assisted Protocol* (submissão IST/Elsevier, pacote `article_ist/`).

**Achado crítico antes de tudo:** o `revision_plan_round1.md` (Reviewer 1) descreve ações, mas **nenhuma foi aplicada ao manuscrito** — confirmado via git log (`cap3_article_body.tex` não é tocado desde 13/mai/2026) e leitura linha a linha do arquivo atual. Isso significa que W1, W3, W4 e W6 do Reviewer 1 continuam abertos e devem ser resolvidos **na mesma passada** que os itens do Reviewer 2, porque tocam exatamente as mesmas linhas (datas de busca, seção "Positioning of PATHCAST", RA1–RA4, tabela de proveniência). Este plano já incorpora essa fusão — não existe mais um "plano do Reviewer 1" separado a executar depois.

Arquivo-fonte principal: `article_ist/cap3_article_body.tex` (1824 linhas; idêntico a `overleaf_package/cap3_article_body.tex`). Também tocar `main.tex`, `cover_letter.tex`, e os `\input` em `results/**`.

Ordem de execução: por criticidade × esforço.

---

## 1. [BLOQUEADOR / ESTRUTURAL] M2–M6 — Recall/Lost-Evidence contra gold-standard humano

**Problema:** todo o κ reportado é LLM-vs-LLM (Haiku 4.5 vs. Sonnet 4.6). Não existe amostra humana dupla-cega, não existe Recall/Lost-Evidence, não existe matriz de confusão, e itens incertos ("maybe", "pending", divergência do verificador) são fechados como exclusão em vez de escalados para arbitragem humana (Seção 2.3 EC5-extended, linha 229-234; Seção 6.2, linha 1600-1601: "intentionally biases the protocol toward false negatives"). Isto é mais grave que a leitura do Reviewer 1 (W1): o Reviewer 2 trata isso como **pré-condição de aceitação**, não como limitação a ser mitigada com um plano futuro — ele explicitamente diz que os achados F1–F5 "are not yet supportable" sem essa medição.

**Ações:**
- [ ] **Decisão a tomar com você antes de qualquer redação** (ver seção de decisões pendentes ao final): rodar double-screening humano real vs. formalizar limitação. Diferente do round 1, aqui a rota "só formalizar como limitação futura" tem alto risco de nova rejeição — M2 é citado como razão central do "Major Revision".
- [ ] Se optar por validação real: amostra estratificada dual-screened por humano cego às decisões do LLM — mínimo defensável no T/A (maior filtro, maior risco de evidência perdida): 10% do working set (≈234 de 2.340) ou uma amostra por estrato de dificuldade (ex.: todos os "maybe", + amostra aleatória dos "exclude"). Reportar Recall, Lost Evidence (1-Recall) e IC ao lado do κ cross-model existente.
- [ ] Reportar matriz de confusão completa (TP/FP/FN/TN em contagens, não percentuais), MCC e Weighted MCC com razão de custo FN:FP justificada (LLM4SCREENLIT).
- [ ] Corrigir o tratamento de itens incertos: itens "maybe"/"pending"/divergência do verificador devem ser tratados como positivos e encaminhados a revisão humana, não fechados sob EC5-extended (Seção 2.3, linha 229-234; Seção 6.2). Os 595 registros auxiliares sem abstract e os 16 ainda pendentes (Tabela 18, Seção 6.3) são o ponto de maior risco de evidência perdida — dar tratamento humano explícito a essa fatia, mesmo que pequena.
- [ ] Adicionar métricas âncoradas em custo em vez de acurácia/especificidade, dado o desbalanceamento extremo (~4,7% de include rate no T/A, Tabela 11).
- [ ] Atualizar Seções 2.4, 6.2 e 6.4 com os novos números humano-LLM.

**Esforço:** alto se validação real (dias); médio se for reformular como limitação + plano formalizado com cronograma concreto — mas nesse caso o risco de rejeição no round 2 permanece alto segundo a leitura do próprio revisor.
**Bloqueia resubmissão:** Sim — é o único item que o revisor qualifica como "não sustenta ainda os achados".

**ATUALIZAÇÃO (09/jul/2026) — evidência quantificada real de Lost Evidence no T/A (Fase A, não-destrutiva):**

Identificamos e corrigimos a causa raiz de por que 72,4% do working set (1.695/2.340,
principalmente Scopus e ACM) foi triado pelo LLM só com título: `extractors/scopus.py` usa a
Scopus Search API (`dc:description`), que a Elsevier deixa vazia na maioria dos registros — o
abstract real só sai por uma API separada (Abstract Retrieval), nunca chamada pelo pipeline
original.

Rodamos a cascata completa de 8 fontes (`pipeline/enrich.py`, já usada no corpus auxiliar) no
working set inteiro e depois **re-triamos via o mesmo protocolo, modelo e prompt do LLM
original** (`claude-haiku-4-5-20251001`, ver `pipeline/abstract_recovery_rescreen.py`) só o
subconjunto que ganhou abstract nesta rodada — sem tocar `ta_screening_results.csv` oficial
(hash conferido idêntico antes/depois) nem qualquer contagem já reportada no artigo:

- Cobertura de abstract: **27,6% → 75,9%** (645→1.776 de 2.340); Scopus 24,5%→74,6%, ACM
  21,7%→89,1%, IEEE já era 100%.
- 1.131 papers re-triados com o abstract real. **35,4% mudaram de decisão** (400/1.131).
- Tabela de transição completa: `results/screening/ta_rescreen_full_cascade_results.csv`;
  resumo em `results/screening/abstract_recovery_rescreen_summary.txt`.
- Especificamente `exclude→include`/`exclude→maybe` (evidência que tinha sido perdida por
  triagem só-por-título e foi recuperada com o abstract real): **4 de 1.131** — pequeno em
  proporção, mas é evidência **medida e nomeável**, não hipotética, exatamente o tipo de dado
  que M2 exige. (Nota metodológica: 6/1.131 respostas vieram com JSON truncado por exceder
  `MAX_TOKENS=512` com abstracts reais mais longos — corrigido via extração regex do JSON
  parcial antes de fechar a tabela; documentado em `abstract_recovery_rescreen_summary.txt`,
  seção 4.)
- **Isto NÃO foi propagado** para a fila de full-text, QA, extração, nem para 169/381/404 —
  é uma "Fase B" separada (reconstruir fila de FT, FT-triar os promovidos, QA/extração dos
  novos includes) que exige decisão explícita do autor antes de tocar os números oficiais do
  artigo.

**Uso recomendado na carta de resposta:** substituir a discussão hipotética de Lost Evidence
por este achado real — não resolve M2 por completo (ainda falta o double-screening humano
real, item 1 permanece bloqueador), mas fortalece a resposta com uma causa raiz identificada,
corrigida no nível de T/A, e uma medição concreta do tamanho do problema (pequeno em % mas
real e documentado) em vez de um reconhecimento genérico da limitação.

---

## 2. [BLOQUEADOR / TRIVIAL] M12 — Contradição direta Tabela 13 vs. texto (IC1∩IC2∩IC3)

**Problema:** o texto afirma repetidamente "apenas 1 de 169/381 satisfaz IC1∩IC2∩IC3" (linhas 1182, 1343, 1359), mas a Tabela 13 (`tab:positioning`, linha 1420) lista o nível L2 ("Three ICs matched") com **contagem 4**, e cita PRIMAD, Incerto e López-Pintado como exemplos — sendo que o próprio texto (linha 1164-1167) descreve Incerto e López-Pintado como IC1∩IC2 apenas (dois critérios, não três). A tabela está confundindo a definição do nível L2 com a coluna de exemplos representativos.

**Ações:**
- [ ] Corrigir a Tabela 13: ou renomear o critério de L2 (ex. "Two ICs matched, partial bridge" com contagem correta), ou corrigir a lista de exemplos para não incluir papers que só satisfazem duas ICs.
- [ ] Conferir consistência com a contagem "4" — se ela está correta para "duas ICs" em vez de "três", ajustar a legenda da tabela e cross-referenciar com o texto de RQ3.1/F4.

**Esforço:** trivial (~30 min), é um erro autocontido de rotulagem — mas é o tipo de inconsistência que mina credibilidade instantaneamente se reaparecer.
**Bloqueia resubmissão:** Sim, é citado nominalmente pelo revisor como falha de reconciliação.

---

## 3. [BLOQUEADOR / MÉDIO] M14 — Pacote Zenodo restrito

**Problema:** o revisor afirma que o registro Zenodo citado como "complete replication package" está com os arquivos em modo RESTRICTED (login necessário). Não conseguimos reproduzir essa alegação a partir dos arquivos-fonte (todos citam consistentemente `10.5281/zenodo.20130276` via a macro `\zenododoi`; nenhum texto descreve o pacote como restrito) — **isto precisa ser verificado diretamente no Zenodo, não no LaTeX**.

**Ações:**
- [ ] **Ação sua, fora do repositório:** acessar `https://zenodo.org/records/20130276` e confirmar se os arquivos estão públicos ou restritos. Se restritos, alterar a visibilidade para pública antes de resubmeter — isto é pré-condição dura (LLM4SCREENLIT R7, SEGRESS item 27).
- [ ] Conferir se existe um segundo DOI de versão (ex. `10.5281/zenodo.15719919`, citado pelo revisor mas não encontrado em nenhum arquivo-fonte atual) — Zenodo gera DOIs de versão diferentes do "concept DOI"; garantir que cover letter, main.tex e Seção 6.5 apontem todos para o mesmo DOI (concept DOI, que resolve sempre para a versão mais recente).
- [ ] Confirmar que o pacote publicado corresponde exatamente à submissão atual (mesmo commit/hash).
- [ ] Resolver junto o item m16: a lista de tabelas descrita na Seção 6.5 ("apenas a tabela de 169 estudos") não bate com a Data-availability statement do `main.tex` ("tabelas de 169 e 212 estudos") — alinhar as duas descrições.

**Esforço:** baixo-médio, mas depende de uma ação externa (Zenodo) que só você pode fazer.
**Bloqueia resubmissão:** Sim — sem isso, nenhuma reivindicação empírica é verificável pelo revisor.

---

## 4. [ESTRUTURAL] W1(round1)/M2-M6 — ver item 1. W3(round1)/m4 — datas de busca ainda erradas

**Problema:** confirmado que a correção do Reviewer 1 (W3) nunca foi aplicada — `cap3_article_body.tex:153` ainda diz "January 1994 to December 2026"; Tabela 3 (linhas 165-169) ainda filtra "1994–2026" nas 4 bases; IC1 na Tabela 5 (linha 247) idem; linha 740 do corpo do texto diz "spans three decades (1995–2026)". Além disso, a linha da SpringerLink na Tabela 3 (linha 168) **não tem filtro de data nenhum**, o que é uma lacuna adicional (m4) não notada no round 1.

**Ações:**
- [ ] Substituir em todas as ocorrências pela janela real: "January 1994 to December 2025 (full calendar years); searches executed on 12 April 2026; publications dated 2026 already indexed at execution time were retained" (redação já existe em `tese/TESE_DOUTORADO_PATHCAST/capitulos/cap3_slr_revised.tex:176-181`).
- [ ] Corrigir: `cap3_article_body.tex:153`, Tabela 3 (165-169, incluindo a linha da SpringerLink — adicionar o filtro de data faltante ou justificar explicitamente por que essa base não tem filtro), Tabela 5/IC1 (linha 247), linha 740, `main.tex` (abstract/highlights), `cover_letter.tex`.
- [ ] Declarar explicitamente a data de execução da busca por base, se elas diferirem (SEGRESS item 6, m4).
- [ ] Regenerar o pacote de replicação Zenodo se ele citar a janela antiga.

**Esforço:** ~1h (é mecânico, mas com muitas ocorrências espalhadas — fazer um grep de "2026" e "1994" em todo `article_ist/` antes de considerar concluído).
**Bloqueia resubmissão:** Sim, se reaparecer — já foi apontado por dois revisores independentes agora.

---

## 5. [ESTRUTURAL] W4+W6(round1)/M1/m3 — Dominância retórica e status de PATHCAST — nenhuma correção aplicada

**Problema:** confirmado que nenhuma mitigação do round 1 foi aplicada:
- Seção 5.2 continua se chamando "Positioning of PATHCAST" (linha 1397), sem nenhuma frase de ressalva sobre não ser contribuição validada empiricamente neste artigo.
- RA1–RA4 (Seção 5.4, linhas 1458-1481) **cada um termina com "Maps to Stage X of PATHCAST"** — exatamente o oposto de "agenda da comunidade" pedido pelo Reviewer 1 e cobrado de novo pelo m3 do Reviewer 2 ("tie each [RA] to the specific evidence gaps you found, with study counts, rather than to PATHCAST stages").
- Pelo menos 9 ocorrências de "PATHCAST solves/addresses/targets this" dentro de RQ1-RQ3/F1-F5 (linhas 923, 942, 971, 998, 1012, 1147, 1178, 1238, 1394) — nenhuma foi neutralizada.
- QA8 (Tabela 6, linha 371) tem como justificativa textual "QA8 reflects the centrality of process model quality **in the PATHCAST pipeline**" — o próprio rubric de qualidade se referencia ao framework do autor, o que reforça a crítica de falta de neutralidade.
- M1: PATHCAST/SPMF são citados repetidamente como contribuição, mas o "companion technical work" (`article_method/`, que existe e tem título e conteúdo reais) nunca é citado — nenhuma `\cite{}`, DOI ou arXiv ID. Section 5.4/RA4 e a Conclusion mencionam "companion empirical work"/"companion technical work" sem link algum.

**Ações:**
- [ ] Renomear Seção 5.2 para algo como "PATHCAST: An Emerging Research Agenda", com 1-2 frases explícitas de que não é uma contribuição validada empiricamente neste SLR e do que faltaria para maturidade de framework (contratos de estágio, avaliação empírica, comparação com frameworks existentes).
- [ ] Reescrever RA1–RA4 para amarrar a achados/gaps específicos com contagens de estudos (ex. "121 de 169 estudos não fazem X"), removendo o mapeamento explícito "Maps to Stage N of PATHCAST" do corpo principal — se quiser manter a rastreabilidade, mover para uma nota de rodapé ou tabela suplementar, não como frase de fechamento de cada RA.
- [ ] Grep de "PATHCAST" em `cap3_article_body.tex` fora das Seções 5.2-5.4 e reescrever cada ocorrência nas linhas listadas acima para o padrão neutro: "this gap motivates frameworks such as PATHCAST (Section 5.2)" em vez de "PATHCAST addresses/targets/solves this".
- [ ] Reescrever a justificativa de QA8 na Tabela 6 sem referência a PATHCAST — usar um critério genérico de qualidade de modelo de processo.
- [ ] Resolver M1: se `article_method/` tiver um preprint público (arXiv, Zenodo, SSRN) até a resubmissão, citá-lo com DOI/URL real. Se não, reformular as duas menções ("companion technical/empirical work") como "future work by the authors, not yet published" — não deixar uma citação implícita sem link, pois isso é exatamente o que o revisor sinalizou como não verificável.

**Esforço:** médio (~3-4h de reescrita pontual + decisão sobre publicar/citar o companion paper).
**Bloqueia resubmissão:** Parcialmente — não é o item central, mas foi levantado por dois revisores agora, o que aumenta a probabilidade de rejeição por "falta de neutralidade" se ignorado de novo.

---

## 6. [ESTRUTURAL] W2+W5(round1) — Tabela única de proveniência — ainda não existe; 6a e 6b são A MESMA causa raiz em dois estágios do pipeline (CONFIRMADO, 07/jul/2026)

**Problema:** confirmado que a tabela/figura de funil (169/381/404/315) nunca foi criada. A investigação inicial via dois sintomas aritméticos distintos (6a, na construção do working set; 6b, no pool 381/404), mas a auditoria de `results/frozen/`, `results/working_set/` e `pipeline/dedup_review.py` confirma que **é um único bug estrutural do pipeline, visível em dois estágios**:

**Causa raiz única:** a deduplicação global do corpus (`pipeline/dedup.py`, rodada uma única vez sobre os 8.347 registros brutos das 26 queries → `results/frozen/deduplicated_high_recall_2026-04-12.json`, que alimenta a Tabela 9) e a seleção do working set (`results/working_set/`, que alimenta a Tabela 10) **não são a mesma operação, nem uma subconjunto estrito da outra**, apesar de o artigo narrar como se fossem. O `results/working_set/README.md` documenta que o recorte operacional usa só 9 das 26 queries brutas (as 6 do Scopus + `ieee_manual_01` + `acm_principal` + `acm_msr`), "rebaixando" Springer inteiro, WoS inteiro, o restante do IEEE e o snowball para um corpus "high-recall auxiliar" separado — e roda sua **própria** passada de dedup, isolada, só dentro desse recorte de 9 queries, nunca comparando contra Springer/WoS/IEEE-restante. Como `dedup.py` decide o sobrevivente de um par duplicado por "riqueza de metadados" (quem tem mais campos preenchidos), um paper do Scopus que teria perdido para uma cópia mais rica do Springer/WoS na dedup global (Tabela 9) nunca encontra essa cópia na dedup isolada do working set — e sobrevive sem ser mesclado, inflando a contagem de Scopus/ACM no working set (6a). **O mesmo paper, então, pode entrar no pipeline duas vezes: uma via sua cópia Scopus no working set (tier 169), outra via sua cópia Springer/WoS no corpus auxiliar** — que é exatamente o padrão que `pipeline/dedup_review.py` describe no seu próprio docstring como motivação de criação: *"qa_combined_381.csv mixes a working_set tier (169 studies) with an auxiliary tier (212 studies) that was not deduplicated against the working set before QA/extraction"* (6b).

Ou seja: **6b (as 63/64 duplicatas cross-tier encontradas e corrigidas em `dedup_apply.py`) é a manifestação, no estágio de QA/extração, do mesmo bug que produz 6a (o descompasso Scopus/ACM na Tabela 9 vs. 10) no estágio de construção do working set.** A correção já aplicada em 6b (dedup pós-hoc via `duplicate_candidates_review.csv` + `dedup_apply.py`) resolve o sintoma no nível de estudo confirmado (318/340), mas **não corrige a causa no nível de registro** (Tabelas 9/10 continuam com a contagem antiga, pois nenhuma dedup cross-tier foi reaplicada nesse estágio anterior).

**6a. Working-set construction (Tabela 9 vs. Tabela 10) — causa raiz CONFIRMADA (é a mesma de 6b), correção ainda NÃO aplicada neste estágio.**
- Tabela 9 (`tab:retrieval`, retenção pós-dedup por fonte, fonte: `results/frozen/report_high_recall_2026-04-12.txt`) vs. Tabela 10 (`tab:working-set`, composição do working set por fonte, fonte: `results/working_set/README.md`): Scopus no working set (2.197) **excede** o total deduplicado da Scopus inteira (1.852) em 345 registros; ACM idem (46 vs. 34, excesso de 12). Verificado: dos 2.377 registros brutos das 6 queries Scopus, 1.950 têm DOI e apenas 1.863 DOIs são distintos — ou seja, ~87 registros só dentro do Scopus já são a mesma cópia sob DOIs repetidos/`internal_id` diferentes, e a dedup do working set não os funde porque nunca é comparada contra a dedup global.
- A nota de rodapé 5 (linha 478-482) tenta explicar via "364 registros de controle/manuais adicionados diretamente ao working set", mas 345+12=357 ≠ 364 (falta reconciliar 7 registros — provavelmente resíduo do mesmo efeito em outras fontes menores).
- **Fix recomendado (mais barato do que reprocessar o pipeline inteiro):** rodar `pipeline/dedup_review.py` (ou uma variante) comparando o working set inteiro (2.340) contra o corpus auxiliar inteiro (3.807) por DOI/título normalizado — o mesmo método já usado para achar os 63/64 duplicatas de 6b — **antes** do T/A screening, não depois da QA. Isso deve reduzir tanto a Tabela 10 quanto potencialmente os números de estudos auxiliares confirmados, então precisa rodar cedo o suficiente para propagar a todo o funil, não só a 381/404.

**6b. Duplicação de estudos no pool combinado 381/404 (QA + extração) — CAUSA RAIZ CONFIRMADA (mesma de 6a), correção parcialmente feita.**

Durante a preparação das planilhas de double-screening humano (Comentário M2), a construção do script `pipeline/human_kappa.py` já havia motivado uma auditoria de deduplicação (`results/auxiliary/dedup_summary.txt`, gerada na sessão de trabalho do Reviewer 1/W1) que **confirma um bug real e já documentado**, distinto do item 6a:

> "381-tier (working_set + auxiliary): 381 -> 318 distinct studies (63 duplicates removed)
> 404-tier (381 + second auxiliary pass): 404 -> 340 distinct studies (64 duplicates removed)
> QA-passed (>=4/8) before dedup, 381-tier: 315/381 (82.7%)
> QA-passed (>=4/8) after dedup, 381-tier: 259/318 (81.4%)
> QA-passed (>=4/8) after dedup, 404-tier: 279/340 (82.1%)"

Ou seja: 63 dos 381 registros do subset analítico combinado (e 64 dos 404) são o **mesmo estudo pontuado duas vezes sob `internal_id` diferentes** (ex.: reimpressões, como o caso G060 — capítulo IGI Global republicado 3×, resolvido como 1 estudo canônico `internal_id=2647ea07`; e o caso G045 — Petri net CI/CD publicado em ISSREW'22 e RAMS'23, mantido como 2 estudos distintos por decisão editorial explícita). Os demais 62 grupos foram auto-resolvidos como duplicatas inequívocas (mantendo a cópia do working-set quando havia conflito).

**Isto muda diretamente as respostas a M11, m11 e M13:**
- A base real do subset analítico não é 381/404, e sim **318/340** após dedup — todo "N=381"/"N=404" no corpo do artigo, tabelas e percentuais de F1–F5/RQ1–RQ3/taxonomia SPMF precisa ser reconferido contra os números corrigidos.
- A taxa de aprovação em QA cai de 82,7% para 81,4% (381-tier) — pequena, mas deve ser corrigida.
- A alegação-manchete "apenas 1 de 404 satisfaz IC1∩IC2∩IC3" **precisa ser reverificada**: se PRIMAD (o único paper triplo-IC) não foi um dos 64 registros removidos como duplicata, o denominador correto passa a ser "1 de 340", não "1 de 404" — isso precisa ser confirmado explicitamente antes de responder ao revisor, não assumido.
- Arquivos de correção **já gerados e existentes** (mas ainda não propagados ao texto do artigo): `results/auxiliary/qa_combined_381_dedup.csv`, `extraction_combined_381_dedup.csv`, `qa_combined_404_dedup.csv`, `extraction_combined_404_dedup.csv`. O próprio `dedup_summary.txt` já traz a nota: *"ACTION REQUIRED: update cap3_article_body.tex — every occurrence of '381' and '404' ... must be reviewed against the corrected counts above before resubmission."*
- Nota: por ora não há evidência de que este bug afete o **169** (working-set tier confirmado) diretamente — o `dedup_summary.txt` não reporta mudança nesse número, só em 381/404. Confirmar isso explicitamente antes de escrever a carta de resposta.

**Outras reconciliações menores do mesmo item:**
- Seção 3.4 (linha 550) implica 886-643=243 artigos sem abstract após enriquecimento, mas a Conclusão (linha 1755) diz "238/886" — diferença de 5, independente dos bugs 6a/6b.
- M13: Seção 2.5 diz que os 33 estudos abaixo do corte de QA "não são usados na base de evidência F1-F5", mas F1-F5 são computados sobre 169/381 (ex. "121 de 169"), que parecem incluí-los — declarar explicitamente qual é a base de F1-F5 (169? 315 pós-QA? 259/318 pós-dedup+QA?).

**Ações:**
- [x] **6a+6b — CAUSA RAIZ UNIFICADA CONFIRMADA (07/jul/2026):** o working set (Tabela 10) e o corpus auxiliar nunca foram deduplicados um contra o outro antes do T/A screening — só uma dedup tardia, pós-hoc, no estágio de QA/extração (`pipeline/dedup_review.py` + `dedup_apply.py`), pegou parte do problema (63/64 de 381/404). O efeito em Tabela 9/10 (6a) é a mesma causa vista mais cedo no funil, ainda não corrigida nesse estágio.
- [ ] **Fix estrutural (recomendado, resolve 6a na origem):** rodar uma dedup cross-tier completa — working set (2.340) vs. corpus auxiliar inteiro (3.807) por DOI/título normalizado, mesmo método de `dedup_review.py` — **antes** do T/A screening. Avaliar o impacto no nº de estudos auxiliares confirmados (212+23), não só nas contagens por fonte da Tabela 9/10.
- [ ] **Fix mínimo (se não houver tempo para reprocessar o T/A):** documentar explicitamente no artigo que Tabela 9 (dedup global, `results/frozen/`) e Tabela 10 (dedup isolada do recorte operacional, `results/working_set/`) usam passadas de deduplicação diferentes e por isso não são estritamente aninhadas por fonte — com uma nota de rodapé explicando o porquê (a dedup do working set nunca compara contra Springer/WoS/IEEE-restante) — e reconhecer isso como limitação de rastreabilidade, não tentar forçar os números a bater sem reprocessar.
- [ ] **6b (fechar a propagação):** substituir todas as ocorrências de "381"/"404" no corpo do artigo, tabelas e figuras pelos valores deduplicados (318/340), usando os CSVs `*_dedup.csv` já gerados como fonte da verdade. Isto inclui recalcular F1–F5, RQ1–RQ3, taxonomia SPMF e a Tabela 13 (item 2 deste plano) sobre a base corrigida.
- [x] **6b — CONFIRMADO (07/jul/2026):** PRIMAD (`internal_id=ed0ab009`) é o único paper `IC1|IC2|IC3` antes e depois da dedup, nos dois tiers — verificado em `extraction_combined_381.csv` (raw), `extraction_combined_381_dedup.csv` e `extraction_combined_404_dedup.csv`. O numerador (1) não muda, só o denominador. **Ação obrigatória:** substituir "1 de 404 (0,3%)" por "1 de 340 (0,29%)" no Abstract/highlights/cover letter, e "1 de 381" por "1 de 318 (0,31%)" onde aparecer no corpo (linhas 1343, 1359). "1 de 169" (linha 1182, working-set tier) não é afetado pela dedup do pool 381/404 e permanece inalterado.
- [ ] Criar a tabela/figura de funil única logo após "Overview of Included Studies" (~linha 746), já incorporando a dedup: 8.347 → 5.783 (dedup) → +364 controle/manual → 2.340 working set → 169 confirmados (working-set tier) → +212 aux1 = 381 (**318 após dedup**) → +23 aux2 = 404 (**340 após dedup**) → 259/318 (ou 279/340) retidos pós-QA (≥4/8). Rotular cada número com o tier e com o status "pré/pós-dedup". Se o fix estrutural (cross-tier antes do T/A) for aplicado, os números 2.340/212/23 também mudam e precisam ser recalculados antes de fechar esta tabela.
- [ ] Reconciliar 238 vs. 243 (Seção 3.4 vs. Conclusão) — usar um único valor derivado da mesma query.
- [ ] Declarar explicitamente a base de F1-F5 (M13) usando os números pós-dedup.
- [ ] Regenerar o pacote de replicação Zenodo (item 3, M14) para incluir os arquivos `*_dedup.csv`, `dedup_summary.txt` e (se aplicado) o resultado da dedup cross-tier estrutural, já que passam a fazer parte da cadeia de evidência dos números reportados.

**Esforço:** o fix estrutural (dedup cross-tier antes do T/A) é alto — pode mudar contagens em todo o funil e exigiria re-triagem parcial; o fix mínimo (documentar a diferença metodológica entre Tabela 9 e 10 como limitação) é baixo (~1h) mas não elimina o problema, só o explica; propagar 6b (318/340) é médio (~3-4h de revisão linha a linha, causa raiz já resolvida).
**Bloqueia resubmissão:** Não seria fatal isoladamente, mas agora que 6a e 6b são reconhecidamente o mesmo bug estrutural do pipeline (não dois erros de redação independentes), a decisão entre fix estrutural vs. fix mínimo é uma decisão de escopo/tempo que vale alinhar com você antes — ver "Decisões pendentes" ao final deste documento.

**ATUALIZAÇÃO (07/jul/2026) — decisão resolvida via checagem automatizada read-only:** rodei uma comparação completa DOI/título entre o working set inteiro (2.340) e o corpus auxiliar inteiro (3.807) — sem alterar nenhum arquivo do pipeline. Resultado: 368 registros duplicados entre os dois pools, mas **só 25 tocam algum estudo confirmado (404-tier)**, e nenhum desses 25 causa double-count real — em todos os 25 casos, a cópia do working set foi **excluída** na triagem e só a cópia auxiliar foi **incluída** (nunca as duas ao mesmo tempo). Ou seja: **os 404/340 não escondem mais duplicatas além das 63/64 já corrigidas por `dedup_apply.py`.**

**Conclusão prática: o fix estrutural (reprocessar dedup cross-tier antes do T/A) NÃO é necessário para corrigir a contagem 404/340 — basta o fix mínimo (nota de rodapé explicando a diferença Tabela 9 vs. 10) para o item 6a.** Isso remove a decisão nº 5 da lista de "decisões pendentes" ao final deste documento — pode seguir direto com o fix mínimo.

**Achado secundário (não bloqueia, mas vale registrar):** os 25 casos revelam que o mesmo paper recebeu decisões de triagem **opostas** sob dois `internal_id` diferentes (cópia do working set excluída, cópia auxiliar incluída) — ex.: "Modeling and Predicting Software Failure Costs", "Cost-Effective Build Outcome Prediction Using Cascaded Classifiers", "NHPP models with Markov switching for software reliability". Isto não é um bug de contagem, é evidência concreta de inconsistência do screener LLM — relevante como dado de apoio ao Comentário M2 (reliability/recall), não como correção obrigatória. Ação opcional: revisar manualmente se alguma das 25 exclusões do working set foi um falso negativo (a cópia auxiliar foi incluída com razão, então a cópia do working set deveria ter sido incluída também) — mas isso é trabalho de qualificação de evidência para M2, não de correção de contagem para M11/M13.

---

## 7. [REENQUADRAMENTO] Título, tipo de estudo e SEGRESS (M15, título/abstract)

**Problema:** o revisor argumenta que o desenho do estudo (RQs descritivas, classificação, contagens, taxonomia, sem síntese de resultados de estudos primários) é uma **mapping study**, não uma SLR — mas o título usa "Systematic Literature Review". O próprio abstract já mistura os dois enquadramentos (Objective: "to map the state of the art"; Method cita Petersen et al. "for mapping" ao lado de Kitchenham/Charters). Adicionalmente, o método é reportado contra Kitchenham & Charters (2007)/Petersen (2015)/Wohlin, não contra SEGRESS (Kitchenham, Madeyski & Budgen, TSE 2023), que é o padrão atual para relatar secondary studies em SE.

**Ações:**
- [ ] Decidir: renomear o título para "...: A Systematic Mapping Study..." (rota recomendada, dado que RoB/QA se torna opcional sob SEGRESS §4.3.2 e resolve parte de M9), OU manter "SLR" e adicionar síntese de resultados de estudos primários (mudança muito mais cara — não recomendada neste ciclo).
- [ ] Reestruturar o relato conforme o checklist SEGRESS (o fluxo PRISMA 2020 já existe — passo incremental) e anexar o checklist preenchido como material suplementar.
- [ ] Adicionar ao abstract: uma frase de limitações e uma frase sobre a abordagem de validação (SEGRESS item 2) — atualmente o abstract não menciona nenhuma das duas.
- [ ] Conferir a suposta "four-direZction" no abstract — não reproduzimos o erro no `main.tex` atual (o texto já lê "four-direction" corretamente); confirmar contra o PDF exato que foi enviado ao revisor antes de responder que já está corrigido.

**Esforço:** médio (~1 dia, decisão de título + checklist SEGRESS + pequenas edições de abstract).
**Bloqueia resubmissão:** Não isoladamente, mas governa a aplicabilidade de vários outros itens (M9 RoB opcional torna-se defensável só se reclassificado como mapping study).

---

## 8. [REENQUADRAMENTO] M9 — Quality Assessment: terminologia, propósito e threshold

**Problema:** SEGRESS não usa mais "quality assessment" (usa Risk of Bias para estudos individuais e Certainty of Evidence para o corpo de evidência); o checklist Dybå & Dingsøyr usado aqui mede qualidade de relato, não RoB. O propósito do QA (por que é feito, como o resultado é usado) não é declarado. O threshold 4/8 (Seção 2.5, linha 371) não é justificado. QA7 ("reproducible (data and/or code available)", Tabela 6 linha 365) conflora "código/dados disponíveis" com "reprodutível" — e isso importa porque F2 e a alegação "reproducibility is poor" (Seção 4.7.2, linha 1232-1236) dependem diretamente dessa métrica.

**Ações:**
- [ ] Se o título virar "mapping study" (item 7): declarar explicitamente que RoB/QA é opcional sob SEGRESS §4.3.2 e justificar por que foi mantido (ex.: usado como filtro de síntese, não como julgamento de RoB).
- [ ] Renomear a seção/tabela para deixar claro que mede "qualidade de relato" (reporting quality), não risco de viés.
- [ ] Justificar o corte 4/8 (por que 50%, não outro valor) — idealmente com uma análise de sensibilidade (o repositório já tem `pipeline/sensitivity.py` e Tabela 16 `tab:sensitivity` — verificar se ela já cobre isso e citá-la aqui).
- [ ] Reescrever QA7 separando "código/dados disponíveis" de "reprodutível" (podem ser dois critérios, ou um só renomeado para não implicar reprodutibilidade verificada).
- [ ] Declarar como o resultado do QA é usado (seleção, interpretação, investigação, validação ou ponderação) — hoje é só gate binário de inclusão/exclusão.

**Esforço:** baixo-médio (~2-3h, é redação + checar se a análise de sensibilidade já existe).
**Bloqueia resubmissão:** Não isoladamente, mas alimenta F2 diretamente — se F2 for citado no abstract, precisa estar bem fundamentado.

---

## 9. [PRESENTATION] M7, M8, m1, m2, m9, m10 — Papel do humano, protocolo/registro, rationale, histórico

**Problema (agrupado, todos de esforço baixo-médio):**
- M7: "manually verified by the author" (linhas 324-325, 1523-1525) não especifica critério nem confiabilidade — falta declarar nº de revisores, independência, detalhes de automação.
- M8: não há declaração de protocolo/registro (SEGRESS 24a/24b).
- m1: Introdução (linha 1-25) não posiciona a review contra nenhuma SLR/mapping study tópica prévia.
- m2: desenvolvimento histórico é raso (só o "seminal arc" de 3 trabalhos, Seção 4.6.1) para um escopo de 30 anos/404 estudos.
- m9: falta engajar com LLM4SCREENLIT, a referência mais diretamente relevante ao desenho do estudo.
- m10: backbone metodológico (Kitchenham/Petersen/Wohlin/PRISMA 2020/Dybå & Dingsøyr) é razoável, só precisa se ajustar ao M15.

**Ações:**
- [ ] Seção 2.4/6.2: declarar explicitamente que houve 1 revisor humano (o autor), sem segundo revisor humano independente, e discutir o impacto disso como desvio das diretrizes de SR (SEGRESS item 23c) — nomear a limitação em vez de deixar implícita.
- [ ] Adicionar declaração de protocolo/registro (se não houve registro formal, dizer isso explicitamente — "no protocol was pre-registered; this is disclosed as a limitation").
- [ ] Expandir a Introdução com 3-5 frases posicionando contra SLRs/mapping studies próximas (ou declarar ausência, se for o caso, como parte da justificativa).
- [ ] Expandir Seção 4.6.1 com uma síntese curta de como PM-em-SE, modelagem estocástica de software e previsão por ML evoluíram separadamente — ligando à alegação de F4 ("structural property of the literature").
- [ ] Citar e discutir LLM4SCREENLIT explicitamente no corpo (não só como referência de rodapé) — é a comparação mais natural para justificar/contrastar o desenho do protocolo.

**Esforço:** baixo-médio agregado (~3-4h).
**Bloqueia resubmissão:** Não, mas soma pontos de credibilidade metodológica facilmente resolvíveis.

---

## 10. [PRESENTATION] m11, M11 — Referências e reconciliações menores

**Problema:** lista de referências tem só 36 entradas (confirmado), majoritariamente metodológicas — nenhuma tabela/apêndice lista os 169/404 estudos incluídos com citação; eles só existem em CSVs externos no Zenodo. Rótulos de critérios trocam entre "IC1-IC3/IC4a-IC4d" (protocolo) e "IC1/IC4a, IC2/IC4b..." (Seção 4) — inconsistente.

**Ações:**
- [ ] Adicionar um apêndice ou tabela suplementar (pode ser só no material suplementar, mas citável no corpo) listando os 169 (ou 404) estudos incluídos com referência completa, keyed à planilha de extração — resolve M11 e reduz dependência total do Zenodo para auditoria.
- [ ] Unificar o esquema de rótulos de critérios em todo o artigo (escolher IC1-IC3 + IC4a-IC4d e usar consistentemente).

**Esforço:** médio (gerar a lista de 169/404 com BibTeX é mecânico, mas trabalhoso pelo volume).
**Bloqueia resubmissão:** Não, mas M11 é citado explicitamente como requisito de rastreabilidade (SEGRESS item 17).

---

## 11. [ESTATÍSTICO] m7, M10, m8 — Intervalos de confiança, paradoxo do kappa, independência dos raters

**Problema:** nenhum IC é reportado para κ ou proporções-manchete. Tabela 15 (T/A auxiliar): Po=97,4% com κ=0,000 — paradoxo de prevalência/base-rate, não desacordo real; o texto atual (Seção 6.2, linha 1557-1578) só narra a linha de FT (κ=0,004/0,000, Po=84,8%, n=276) e nunca comenta a linha de T/A (n=39, Po=97,4%) que fica "enterrada" só na tabela. Independência dos raters (dois LLMs da mesma provedora) não é discutida.

**Ações:**
- [ ] Adicionar ICs à Tabela 14/15 (bootstrap ou fórmula fechada para κ) e às proporções-manchete (F1-F5).
- [ ] Adicionar prose explícita para a linha de T/A da Tabela 15 explicando o paradoxo de prevalência (Po alto + κ baixo não significa desacordo).
- [ ] Adicionar uma frase reconhecendo que os dois "raters" são modelos da mesma família/provedora, o que pode inflar a concordância vs. um checador humano independente.

**Esforço:** baixo-médio (~2h para IC + redação; ICs de κ multi-classe podem exigir bootstrap simples).
**Bloqueia resubmissão:** Não isoladamente, mas M10 é citado como "leitura equivocada" — corrigir é rápido e evita a impressão de erro estatístico básico.

---

## Nota sobre m5, m6 (achados adicionais, baixa prioridade individual mas fáceis)

- **m5 (linha 180-181 vs. 434-435):** reconciliar a descrição do snowballing — Seção 2.2.3 diz "de todos os estudos primários incluídos" (logicamente impossível como descrição de protocolo), Seção 3.1 diz "do conjunto de controle". Usar a versão do conjunto de controle (é a correta cronologicamente) e apagar a menção a "estudos incluídos" da Seção 2.2.3.
- **m6:** conjunto de validação de 10 papers com 100% de recall (Tabela 4) é pequeno demais para calibrar recall com confiança — expandir o conjunto de validação (ex. para 20-30 papers) ou explicitamente temperar a alegação de recall no texto.

**Esforço:** baixo (~1h para ambos).

---

## Resumo executivo (ordem de execução recomendada)

| # | Item | Criticidade | Esforço | Bloqueia resubmissão? |
|---|------|------|------|------|
| 1 | M2–M6 — recall/gold-standard humano | Bloqueador | Alto (dias) ou médio (plano+parcial) | Sim |
| 2 | M12 — Tabela 13 vs. texto (IC1∩IC2∩IC3) | Bloqueador | Trivial (30min) | Sim |
| 3 | M14 — Zenodo restrito + DOI único | Bloqueador | Baixo-médio (ação externa) | Sim |
| 4 | W3(r1)/m4 — datas de busca ainda erradas | Estrutural | Baixo (~1h) | Sim, se reaparecer |
| 5 | W4+W6(r1)/M1/m3 — dominância e status de PATHCAST | Estrutural | Médio (~3-4h) | Parcial |
| 6 | W2+W5(r1)/M11/M13/m11/m16 — funil e reconciliação de números | Estrutural | Médio-alto | Não isoladamente, mas padrão recorrente |
| 7 | M15/título — SEGRESS + mapping study | Reenquadramento | Médio (~1 dia) | Não isoladamente, mas habilita #8 |
| 8 | M9 — QA/RoB terminologia e threshold | Reenquadramento | Baixo-médio | Não |
| 9 | M7,M8,m1,m2,m9,m10 — papel humano/protocolo/rationale/histórico | Apresentação | Baixo-médio | Não |
| 10 | m11,M11 — referências e rótulos | Apresentação | Médio | Não |
| 11 | m7,M10,m8 — IC, paradoxo kappa, independência | Estatístico | Baixo-médio | Não |
| — | m5, m6 — snowballing, validação de busca | Menor | Baixo | Não |

---

## Decisões pendentes com você (bloqueiam a redação da carta de resposta)

1. **Item 1 (M2-M6):** rodar double-screening humano real (mesmo que parcial, ex. 10% do T/A) antes de resubmeter, ou assumir o risco de formalizar como limitação + plano com cronograma concreto? Diferente do round 1, aqui a segunda rota tem risco elevado de nova rejeição — vale decidir isso primeiro pois muda o texto de praticamente todas as seções de validade (2.4, 6.2, 6.4) e o resumo executivo do abstract.
2. **Item 3 (M14):** você precisa checar o Zenodo diretamente — não há como confirmar/negar a partir do LaTeX. Confirme se o registro `10.5281/zenodo.20130276` está público ou restrito, e se existe de fato um segundo DOI de versão.
3. **Item 5 (M1):** o `article_method/` (o paper metodológico do PATHCAST) tem conteúdo real e completo mas nenhum identificador citável. Ele será submetido/depositado como preprint antes desta resubmissão (permitindo citação real), ou as menções devem ser reformuladas como "future work not yet published"?
4. **Item 7 (M15/título):** aceitar reclassificar o artigo como "Systematic Mapping Study" (recomendado, resolve M9 e a crítica de tipo de estudo de uma vez) ou manter "SLR" e assumir o custo de adicionar síntese de resultados?
5. ~~Item 6 (6a/6b — dedup cross-tier)~~ — **RESOLVIDO (07/jul/2026):** checagem automatizada read-only (working set 2.340 vs. auxiliar 3.807 completos) confirmou que os 404/340 não têm duplicatas ocultas além das 63/64 já corrigidas. Fix mínimo (nota de rodapé) é suficiente; fix estrutural não é necessário. Ver detalhes na "ATUALIZAÇÃO" dentro do item 6.
