# Log de auditoria — Recuperação de abstracts, re-screening, dedup cross-tier e FT real

Data: 07–10/jul/2026. Contexto: preparação da resposta ao Reviewer 2 (M2 — Recall/Lost
Evidence; item 6 — dedup cross-tier Tabela 9/10). Este documento consolida achados e ações
que estão espalhados por vários arquivos (`revision_plan_round1_reviewer2.md`,
`results/screening/abstract_recovery_rescreen_summary.txt`,
`results/screening/ft_real_priority_summary.txt`,
`results/auxiliary/fuzzy_match_audit/README.md`) num único registro cronológico.

---

## 1. Dedup cross-tier (item 6 do plano — Tabela 9 vs. Tabela 10)

**Problema original:** Scopus no working set (2.197) excedia o total deduplicado da Scopus
inteira (1.852) — um subconjunto aparentemente maior que seu superconjunto.

**Causa raiz confirmada:** o working set (`results/working_set/`, 9 de 26 queries brutas) e o
corpus auxiliar nunca foram deduplicados um contra o outro antes do T/A screening — só uma
dedup tardia, pós-hoc, no estágio de QA/extração (`pipeline/dedup_review.py` +
`dedup_apply.py`), pegou parte do problema (63/64 duplicatas em 381/404).

**Verificação de impacto real:** rodamos uma comparação completa DOI/título entre o working
set inteiro (2.340) e o corpus auxiliar inteiro (3.807), sem alterar nenhum arquivo do
pipeline. Resultado: 368 registros duplicados entre os dois pools, mas **só 25 tocam algum
estudo confirmado (404-tier)**, e nenhum causa double-count real (a cópia do working set foi
sempre excluída, só a cópia auxiliar foi incluída). **Conclusão: os 404/340 confirmados NÃO
têm duplicatas ocultas além das 63/64 já corrigidas.** O fix estrutural (reprocessar dedup
cross-tier antes do T/A) não é necessário — basta o fix mínimo (nota de rodapé explicando a
diferença metodológica entre Tabela 9 e 10).

**Achado secundário (não bloqueia, mas registrado):** os 25 casos revelam papers que
receberam decisões de triagem opostas sob dois `internal_id` diferentes (cópia do working set
excluída, cópia auxiliar incluída) — evidência de inconsistência do screener, relevante como
dado de apoio ao M2, não como correção de contagem.

Status: **RESOLVIDO.** Falta só aplicar o fix mínimo de redação no artigo (item 6 do plano).

---

## 2. Fase A — recuperação de abstracts + re-screening do working set inteiro

**Motivação:** 72,4% do working set (1.695/2.340, principalmente Scopus e ACM) foi triado
pelo LLM só com título. Causa raiz: `extractors/scopus.py` usa a Scopus Search API
(`dc:description`), que a Elsevier deixa vazia na maioria dos registros — o abstract real só
sai por uma API separada (Abstract Retrieval), nunca chamada pelo pipeline.

**Execução:**
1. Cascata completa de 8 fontes (`pipeline/enrich.py::enrich_abstracts`) rodada no working set
   inteiro (script novo: `pipeline/abstract_recovery_rescreen.py`).
2. Re-screening via o mesmo protocolo/modelo/prompt original (`claude-haiku-4-5-20251001`,
   Batches API) só do subconjunto que ganhou abstract.
3. Nunca tocou `results/screening/ta_screening_results.csv` (oficial) — hash conferido
   idêntico do início ao fim de toda a operação.

**Resultado bruto inicial (antes da auditoria de qualidade, ver Seção 3):** 1.131 papers
recuperados/re-triados; 35,4% mudaram de decisão; 9 casos de `exclude→include/maybe`.

**Problema encontrado durante a verificação de custo:** 6/1.131 respostas do LLM vieram com
JSON truncado (provavelmente por exceder `MAX_TOKENS=512` com abstracts reais mais longos).
Corrigido via extração regex do JSON parcial (5 desses 6 eram `exclude→exclude` de verdade,
não `exclude→maybe` como o fallback ingênuo teria registrado).

**Resultado final, pós-auditoria completa (ver Seção 3):**

| Métrica | Valor final |
|---|---|
| Cobertura de abstract (working set, 2.340) | 27,6% → **74,0%** (645→1.732) |
| Scopus | 24,5% → 72,6% |
| ACM | 21,7% → 89,1% |
| Papers re-triados confiáveis | **1.087** |
| Decisão mudou | **34,2%** (372/1.087) |
| `exclude→include`/`exclude→maybe` (evidência recuperada) | **4** |

Arquivos: `results/screening/working_set_enriched_full_cascade.csv`,
`results/screening/ta_rescreen_full_cascade_results.csv`,
`results/screening/abstract_recovery_rescreen_summary.txt`.

Status: **Fase A concluída e auditada.** Resultados **não propagados** para
`ta_screening_results.csv`, fila de FT, QA/extração, ou contagens 169/381/404 do artigo —
isso é a "Fase B" (ver Seção 5).

---

## 3. Bug de qualidade descoberto: fuzzy match por título contamina abstracts

**Descoberta:** auditoria manual de 102 (de 1.131) abstracts recuperados via fuzzy match por
título (score ≥92 sem match exato de DOI/título) encontrou **44 (43%) com o abstract do paper
ERRADO**.

**Causa raiz:** títulos que representam um **volume inteiro de proceedings** (ex.: "14th
International Conference on Business Process Management, BPM 2016") não têm abstract real,
mas pontuam alto no fuzzy match por repetição de termos genéricos do domínio. Um único
abstract errado (sobre "family firms/SMFFs") foi reaproveitado em **9 volumes de proceedings
da BPM diferentes**; outro (workshop SEPN de 2000) em 3 volumes de Petri Nets; "CEUR Workshop
Proceedings" recebeu literalmente o texto "no abstract" 3×.

**Correção da causa raiz** em `pipeline/enrich.py`:
- Títulos de volume de proceedings agora são bloqueados no fallback por título inteiramente
  (`_is_proceedings_volume_title`).
- Limiar de similaridade elevado de 92 → 95 (`TITLE_MATCH_MIN_SCORE`).
- Nova checagem de overlap de palavras de conteúdo (Jaccard ≥0,5,
  `CONTENT_WORD_JACCARD_MIN`/`_content_word_jaccard`) exigida além do `token_set_ratio`, que
  sozinho é lenient demais para títulos curtos/genéricos.

**Remediação aplicada:**
- As 44 linhas contaminadas revertidas na Fase A (`working_set_enriched_full_cascade.csv` e
  `ta_rescreen_full_cascade_results.csv` — números da Seção 2 já refletem isso).
- 5 linhas com a mesma contaminação corrigidas em
  `results/human_validation/ta_blind_review_sheet.csv`/`.xlsx` (double-screening humano em
  andamento) — nenhuma tinha decisão humana registrada, nada foi perdido.

**Achado mais sério — mesmo bug já estava no material submetido ao Reviewer 2:** a mesma
função (`pipeline.enrich.enrich_abstracts`) já era usada, antes desta sessão, para enriquecer
o corpus auxiliar (`results/auxiliary/aux_pending_enriched.csv`, `aux_reft_enriched.csv`) que
alimenta a triagem de full-text dos 880 papers auxiliares e, por consequência, os 235
estudos auxiliares confirmados já reportados.

**Auditoria do impacto real no artigo submetido:** dos 173 estudos auxiliares confirmados
(tier 404, `origin != working_set`), só **3 têm abstract via fuzzy match por título**:
- `d50fcf26` ("SIMKIT...") — abstract recuperado fala de economia da indústria de software,
  **não menciona SIMKIT** — **provável match errado**, precisa checagem manual contra o DOI.
- `43977ab5` ("Execution-Based Model Profiling") — abstract em alemão, tematicamente
  compatível apesar do idioma — plausível, mas vale checagem manual.
- `0de90ff4` ("Handling Concept Drift...") — abstract correto, menciona concept drift
  explicitamente.

Detecção automática (abstract duplicado entre títulos diferentes, sem match exato) encontrou
mais **12 registros suspeitos no pool auxiliar mais amplo (880)**, nenhum entre os 173 já
confirmados — separados em `results/auxiliary/fuzzy_match_audit/` para auditoria (README
próprio com leitura preliminar de cada um dos 5 grupos).

Status: **Causa raiz corrigida. Impacto real no artigo submetido é pequeno (no máximo 1 de
173 estudos confirmados), mas ainda não confirmado/resolvido — pendente checagem manual do
DOI de `d50fcf26` e `43977ab5`.**

---

## 4. Double-screening humano (M2) — infraestrutura e progresso

- T/A: 468 papers (`results/human_validation/ta_blind_review_sheet.xlsx`), cobertura de
  abstract 27,6%→74% (mesma cascata da Seção 2, aplicada à amostra antes do working set
  inteiro), 5 linhas de contaminação corrigidas.
- FT: 177 papers (`ft_qa_extraction_blind_review_sheet.xlsx`), 37 com PDF local em
  `results/human_validation/ft_pdfs_local/` (16 já existiam no repo, 21 baixados
  automaticamente via `pipeline/pdf_downloader.py`).
- Cópia de trabalho `ta_blind_review_sheet_wip.xlsx` sincronizada com as correções da Seção 3,
  preservando 3 decisões já registradas pelo autor.
- `python -m pipeline.human_kappa --compute` calcula kappa humano-vs-LLM a qualquer momento,
  mesmo com preenchimento parcial.

Status: **Em andamento pelo autor.** Achado pendente de decisão do autor: linha `9fe435f5`
("AtomPy...") tem abstract que parece ser de outro paper (bloco de afiliação de engenharia
mecânica, não sobre astrofísica) — não fazia parte do escopo original da auditoria da Seção 3
(essa é da amostra de 468, auditada só pelo regex de proceedings, não item-a-item como os 102
do working set completo) — vale checagem manual antes de decidir essa linha.

---

## 5. Fase B — bug do `internal_id` corrigido + FT real (PDF) para os 50 papers prioritários

**Achado:** a etapa de "FT screening" do pipeline original, para 99,5% dos casos, não lê o PDF
— alimenta o LLM com o mesmo abstract (`pipeline/fulltext.py::_build_ft_prompt`), só com prompt
mais estrito. "Propagar a Fase A" não é um merge simples; o que precisa de atenção real é um
conjunto específico de 50 papers: 4 nunca passaram por FT nenhuma (excluídos ainda no T/A), e
46 têm decisão divergente entre a re-triagem T/A com abstract real (Fase A) e o "FT screening"
existente (também abstract-only).

**Bug encontrado no caminho, corrigido:** `results/screening/ft_screening_results.csv` tinha a
coluna `internal_id` 100% vazia nas 886 linhas. Causa raiz confirmada via `git log`/`git show`:
um BOM UTF-8 entrou no arquivo (aberto/salvo em Excel ou Numbers em algum momento — mesma
classe de problema já vista com `ta_blind_review_sheet.csv`), e `pipeline/fulltext.py::load_ft_queue()`
(e `pipeline/pdf_band_d_review.py::_load_ft_csv()`) liam com `encoding="utf-8"` (não
`utf-8-sig`), fazendo o BOM virar parte da chave `internal_id` do dict — `save_ft_csv()` então
gravava a coluna vazia silenciosamente (`DictWriter` com `restval=''` padrão). Corrigido: 4
pontos de leitura trocados para `utf-8-sig` (`pipeline/fulltext.py` ×2, `pipeline/pdf_band_d_review.py`,
`main.py`, `pipeline/qa_llm.py`), backfill das 886 linhas via join DOI/título contra
`ta_screening_results.csv`, e 4 duplicatas de `internal_id` reveladas pelo backfill (títulos
genéricos sem DOI — "CEUR Workshop Proceedings" ×3, "ACM International Conference Proceeding
Series" ×2 — mesmo padrão da Seção 3) resolvidas com sufixo `_ambiguous_dupN`.

**FT real executado** (`pipeline/ft_real_priority_review.py`, reaproveita `extract_pdf_text`/
`_build_prompt` de `pipeline/pdf_band_d_review.py`): de 50 papers, **8 tinham PDF disponível**
(2 já localmente, 5 baixados via cascata de OA, 1 já do Band D). Resultado:

| internal_id | T/A+abstract | FT abstract-only | **FT+PDF real** |
|---|---|---|---|
| ba2ff831 | exclude | include | **include** |
| ee562777 | exclude | include | **include** |
| 9188583f | include | exclude | **include** |
| 56d5020d | include | exclude | exclude |
| 9100fc88 | include | exclude | exclude |
| f5eef87b | include | exclude | exclude |
| fa132b7b | include | exclude | exclude |
| d4a1d75c | maybe | include | include |

**3 papers (`ba2ff831`, `ee562777`, `9188583f`) são Lost Evidence recuperada e verificada com
texto completo real** — não abstract, não hipótese. `9188583f` é o caso mais forte: nem a
re-triagem T/A nem o "FT screening" abstract-only original o capturaram como include — só a
leitura real do PDF revelou que atende IC2/IC3.

Status: **Concluído para os 8 com PDF disponível.** Os outros 42 dos 50 continuam sem PDF
(decisão anterior mantida) — precisam de acesso manual (institucional/paywall). Nenhuma
mudança foi propagada para 169/381/404 — decisão de adoção oficial ainda em aberto.

---

## 6. Pendências e decisões em aberto

1. **Adoção oficial da Fase A+B** (atualizar 169/381/404 no texto do artigo com base nos 3
   papers de evidência recuperada e confirmada + qualquer resultado dos 42 pendentes de PDF):
   decisão explícita do autor, ainda não feita.
2. Conseguir PDF para os 42 papers prioritários restantes (acesso institucional/manual) e
   rodar `pipeline/ft_real_priority_review.py --match`/`--run`/`--collect` para eles.
3. Checar `SIMKIT` (`d50fcf26`) e `43977ab5` contra o DOI real (Seção 3).
4. Auditar os 12 suspeitos em `results/auxiliary/fuzzy_match_audit/` (só o Grupo 1 precisa
   investigação de verdade; Grupos 0/2/4 são prováveis duplicatas de estudo, Grupo 3 é lixo
   de metadado confirmado).
5. Reconfirmar a decisão de `53ed8ac4` no double-screening humano (era `exclude` sob abstract
   errado — título continua justificando `exclude`, mas por outro motivo).
6. Checar `9fe435f5` no double-screening humano.
7. As 3 decisões pendentes registradas no fim de `revision_plan_round1_reviewer2.md` (M2:
   rota de validação humana; M14: status do Zenodo; M1: citar ou não `article_method/`; M15:
   reclassificar título para "Mapping Study").
