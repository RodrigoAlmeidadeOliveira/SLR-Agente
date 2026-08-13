# Reconciliação Round 1 — Reviewer 1 (2026-08-13)

Manuscrito ainda em `article_ist/cap3_article_body.tex` (submissão maio/2026).
Carta-rascunho: `response_letter_round1.md` (placeholders `[VALUE]` / `[X]`).

Classificação: DONE = fonte já reflete o pedido **e** o check da skill passa.
Nada abaixo está DONE no manuscrito, salvo onde indicado.

| ID | Pedido do revisor | Severidade | Status | Evidência |
|----|-------------------|------------|--------|-----------|
| W1 | Double-screening humano + QA + extração, amostra representativa | estrutural | **PARTIAL** | Dados coletados; manuscrito ainda só cita κ cross-model |
| W2 | Unificar/esclarecer 169 / 381 / 404 | crítica | **NOT-DONE** | Body ainda tem 11× “381” e 5× “404” |
| W3 | Corrigir janela de busca (dez/2026 vs submissão mai/2026) | crítica | **NOT-DONE** | `cap3_article_body.tex:153` ainda “January 1994 to December 2026”; Tabela 2 “1994--2026” |
| W4 | Reduzir dominância retórica do PATHCAST nas RQs/achados | percepção | **NOT-DONE** | 25 ocorrências de PATHCAST no body |
| W5 | Transparência QA ↔ síntese (169 / 315 / 404) | crítica | **NOT-DONE** | Ligado a W2; 315 ainda no texto; cortes corretos são 259/318 e 279/340 |
| W6 | PATHCAST como agenda, não contribuição validada | estrutural leve | **NOT-DONE** | Seção ainda “Positioning of PATHCAST” |

---

## W1 — o que já existe (não precisa de mais leitura humana)

Double-screening cego concluído e κ computado em 13/ago/2026:

| Estágio | n | κ multi | interpretação | Po |
|---------|---|---------|---------------|----|
| T/A | 468 | **0,250** | fair | 64,7% |
| T/A binário | 468 | **0,335** | fair | 87,6% |
| FT | 177 | **0,122** | slight | 44,6% |
| QA (ambos include) | 31 | — | Po 67,7–100% por critério | MAE qa_total **1,19** |

Fonte: `results/human_validation/human_kappa_report.txt`.

**Interpretação honesta (não omitir na carta):**
- Cross-model original (Haiku vs Sonnet) era ~0,69 — o humano-LLM é **substancialmente mais baixo**, sobretudo no FT.
- FT: você incluiu bem mais papers que o LLM (128 include vs. o screener primário mais restritivo); Po 44,6% com κ 0,122 é desacordo real de critério, não só prevalência.
- Extração em texto livre (RQ / main_finding / limitations) tem 0% exact-match — reportar concordância só nos campos categóricos (`stochastic_technique` 80,6%, `dataset_source` 54,8%, `study_type` 45,2%).
- Protocolo FT fechado: nenhum `include` sem QA (`ft_0136` e `ft_0154` → exclude).

A carta-rascunho **não pode** preencher `[VALUE]` como se o κ humano validasse o screener no mesmo nível do κ cross-model. Tem de reportar os dois, explicar a divergência, e tratar o κ FT baixo como limitação + decisão editorial (humano como árbitro na amostra).

---

## W2 + W5 — números corretos (dados já gerados; texto não)

Já em `results/auxiliary/dedup_summary.txt` / `revision_plan_round1.md`:

| Corte | No paper agora | Correto |
|-------|----------------|---------|
| Combined analytical | 381 | **318** |
| Final confirmed | 404 | **340** |
| QA-passed no combined | 315/381 | **259/318 (81,4%)** |
| QA-passed no final | — | **279/340 (82,1%)** |

Working-set 169 permanece. Falta: figura de proveniência, “N = …, tier = …” em cada tabela/figura, e recalcular percentuais RQ1–RQ3/F1–F5 nos CSVs `*_dedup.csv`.

---

## W3 — redação já existe na tese, não no artigo

`tese/.../cap3_slr_revised.tex` já tem: janela jan/1994–dez/2025, execução **12 abril 2026**, 2026 indexados retidos. Propagar para `cap3_article_body.tex`, Tabela 2, `main.tex`, `cover_letter.tex`.

---

## W4 + W6 — só reescrita

PATHCAST fora de Positioning/Agenda: só gap neutro. Retitular Positioning → agenda emergente; RA1–RA4 como propostas da comunidade.

---

## Ordem recomendada no manuscrito (não bloqueada por decisão sua)

1. W3 datas (30 min)
2. W2+W5 números + funil (4–6 h; o mais arriscado se ficar 381/404)
3. W1 inserir tabela humano-LLM + limitação honesta do κ FT
4. W4+W6 reenquadramento PATHCAST
5. Preencher `response_letter_round1.md` (sem placeholders) e recompilar

---

## Decisão editorial pendente (W1 carta)

Como tratar κ FT = 0,122 na carta: (a) humano como gold standard na amostra 20%, divergências resolvidas a favor do humano; (b) discutir critérios IC/EC que o LLM aplicou mais estritamente. Recomendação: (a)+(b), sem inflar o κ.
