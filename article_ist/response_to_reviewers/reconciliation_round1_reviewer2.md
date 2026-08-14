# Reconciliação Round 1 — Reviewer 2 (2026-08-13)

Manuscrito: `article_ist/cap3_article_body.tex` (ainda o texto da submissão de maio/2026).
Plano prévio: `revision_plan_round1_reviewer2.md`. Carta-rascunho: `response_letter_round1_reviewer2.md` (placeholders).
Cruzamento R1: `reconciliation_round1_reviewer1.md`.

Classificação: DONE = o **fonte do artigo** já reflete o pedido **e** o check passa.
Nenhum item abaixo está DONE no manuscrito.

---

## Achado que muda a carta (M2 / M3 / M4) — calculado 13/ago/2026

O double-screening humano cego está **completo**. O relatório de κ (`human_kappa_report.txt`) só traz concordância. Contra gold-standard **humano**, a matriz é:

Gold = humano `include`. Preditor = LLM primário (Haiku). Binário: `maybe` = não-include.

### T/A (n = 468)

| | Humano include | Humano não-include |
|---|---:|---:|
| **LLM include** | TP = **18** | FP = **4** |
| **LLM não-include** | FN = **54** | TN = **392** |

- Recall = **0,250** (IC Wilson 95%: 0,164–0,361)
- Lost Evidence = **0,750** (54/72 papers que o humano julgou relevantes)
- Precision = 0,818 · Specificity = 0,990 · MCC = 0,409
- WMCC (FN:FP = 10:1) = 0,073

**Todos os 54 FN do T/A são `maybe` do LLM, não `exclude`.** Se `maybe` for tratado como positivo e enviado a humano (LLM4SCREENLIT R6): TP=72, FN=0, Recall=**1,00**, Lost Evidence=**0**. Custo: 105 FP adicionais.

O Lost Evidence no T/A é **escolha de protocolo** (fechar `maybe` como exclusão / EC5-extended), não cegueira do modelo.

### FT (n = 177)

| | Humano include | Humano exclude |
|---|---:|---:|
| **LLM include** | TP = **31** | FP = **3** |
| **LLM exclude** | FN = **95** | TN = **48** |

- Recall = **0,246** (IC Wilson 95%: 0,179–0,328)
- Lost Evidence = **0,754** (95/126)
- Precision = 0,912 · Specificity = 0,941 · MCC = 0,215
- WMCC (10:1) ≈ −0,03

No FT **não há fila `maybe`**. Dos 95 FN: EC1=35, EC3=31, EC2=22, EC5=11. Só 11/95 são “sem PDF”; o resto é desacordo de critério — o humano inclui bem mais.

QA/extração (n=31, ambos include): categóricos ok-a-fracos; texto livre 0% exact-match (`research_question`, `main_finding`, `limitations`).

**Consequência para a manchete:** “only 1 of 404” **não pode** permanecer sem hedge. O revisor estava certo: F1/F3/F4/F5 (“X é raro/ausente”) ainda não são suportáveis como propriedade estrutural da literatura enquanto o screener perde ~¾ dos relevantes na amostra, a menos que (a) se adotem os includes humanos como gold na amostra e se recorte o corpus, ou (b) se restrinja a afirmação ao working-set com Lost Evidence reportado e F1–F5 recalculados/hedgeados.

---

## Checklist atômico

| ID | Pedido | Sev. | Status | Evidência |
|----|--------|------|--------|-----------|
| m1 | Posicionar contra SLRs/mappings tópicos prévios; clarificar EC4 se houver review on-topic | média | **NOT-DONE** | Intro ~5 frases; só Kitchenham/Petersen/Wohlin |
| M1 | PATHCAST/SPMF como hipótese ou citar companion | estrutural | **NOT-DONE** | “companion technical work” sem `\cite`; R1 W4/W6 |
| m2 | Síntese histórica PM-SE / estocástico / ML (apoia F4) | média | **NOT-DONE** | Só “seminal arc” §4.6.1 |
| m3 | RA1–RA4 amarrados a gaps com contagens, não a estágios PATHCAST | média | **NOT-DONE** | Cada RA termina “Maps to Stage N of PATHCAST” |
| M2 | Recall / Lost Evidence vs gold humano; limiar pré-especificado | **bloqueador** | **PARTIAL** | Amostra humana existe; Recall/LE **medidos acima**; ainda **não** no artigo nem na carta; limiar R3 não declarado a priori |
| M3 | Matriz TP/FP/FN/TN, MCC, WMCC (não % / accuracy) | **bloqueador** | **PARTIAL** | Números acima; não no manuscrito |
| M4 | `maybe`/`pending`/sem-abstract → positivo + humano, não exclusão silenciosa | **bloqueador** | **NOT-DONE** | Protocolo publicado ainda enviesa a FN; no T/A isso **explica** os 54 FN |
| M5 | Tier auxiliar κ=0 e 58% do corpus sem checagem humana | alta | **PARTIAL** | κ=0 é paradoxo de prevalência (M10); amostra humana é do working-set, **não** do auxiliar |
| M6 | Re-extração humana agora; agreement por campo | **bloqueador** | **PARTIAL** | n=31 ambos-include; campos livres 0%; não reportado no paper |
| M7 | Papel do humano (nº, independência, automação); desvio SEGRESS 23c | alta | **NOT-DONE** | “manually verified by the author” (l.325) ainda vago; agora há 1 humano cego na amostra 20% |
| M8 | Protocolo / registro (SEGRESS 24a/b) | média | **NOT-DONE** | Ausente |
| M15 | Relatar contra SEGRESS + checklist suplementar | alta | **NOT-DONE** | Ainda Kitchenham 2007 |
| M9 | QA → RoB/reporting quality; propósito; corte 4/8; QA7 ≠ reprodutível | alta | **NOT-DONE** | Depende de retitular mapping (abaixo) |
| m4 | Datas de busca por base; “December 2026” | crítica | **NOT-DONE** | = R1 W3; l.153 ainda “to December 2026” |
| m5 | Snowball: included set vs control set | baixa | **NOT-DONE** | §2.2.3 vs §3.1 |
| m6 | Control set de 10 papers não calibra recall | baixa | **NOT-DONE** | Temperar ou expandir |
| M14 | Zenodo público (R7 / SEGRESS 27) | **bloqueador** | **DONE** | v2 Open: concept `20130275`, v1 `20130276`, v2 `21939471` |
| m7 | IC em κ e em F1–F5 | média | **NOT-DONE** | Wilson do Recall já calculável (acima) |
| M10 | Po=97,4% + κ=0 é paradoxo de prevalência, não desacordo | média | **NOT-DONE** | Texto ainda não interpreta a célula T/A auxiliar |
| m8 | Dois LLMs da mesma provedora não são independentes | média | **NOT-DONE** | Agora há humano; declarar o limite LLM–LLM |
| M11 | Citar os estudos incluídos (apêndice) | alta | **NOT-DONE** | bib ~36 entradas metodológicas |
| m9 | Engajar LLM4SCREENLIT no corpo | alta | **NOT-DONE** | Não aparece no `.tex` |
| m10 | Backbone metodológico ok se M15 for feito | — | n/a | Sem ação isolada |
| M12 | Tabela 13 L2=4 vs “1 paper triplo-IC” | **bloqueador** | **NOT-DONE** | l.1420 ainda “Three ICs matched” count 4 |
| M13 | Denominador F1–F5 vs filtro QA | crítica | **NOT-DONE** | = R1 W5; base correta pós-dedup: declarar 259/318 ou 169 |
| m11 | Tabela 9 vs 10; 6147 vs 5783; PRISMA 238 vs 243; rótulos IC | média | **NOT-DONE** | Funil ainda não unificado |
| m16 | Um único DOI Zenodo; alinhar 6.5 vs Data availability | média | **DONE** | Concept `20130275`; v2 = `21939471` |
| Título | Mapping study vs SLR (SEGRESS item 1) | estrutural | **NOT-DONE** | **Decisão sua** |
| Abstract | Limitações + validação; não afirmar “1 of 404” sem suporte | alta | **NOT-DONE** | `main.tex:121,143` ainda “only 1 of 404” |
| lang | “four-direZction” | trivial | **DONE no source** | `main.tex` já lê “four-direction”; provavelmente PDF antigo |

---

## O que a carta **não** pode dizer

- Que o κ humano “valida” o screener. T/A κ=0,250; FT κ=0,122.
- Que Lost Evidence é “pequeno”. Sob o protocolo publicado: **75%** na amostra.
- Que Fases A/B (abstract recovery, 3 PDFs) substituem M2. São evidência de causa raiz complementar, não gold-standard.

## O que a carta **pode** dizer com honestidade

1. Gold-standard humano existe (T/A 468, FT 177, QA 31).
2. No T/A, o LLM **nunca deu exclude duro** a um paper que o humano incluiu; os 54 FN são `maybe`. R6 teria Recall=1,00.
3. O protocolo publicado (fechar incerteza como exclusão) é exatamente o erro que o revisor e o LLM4SCREENLIT apontam; vamos invertê-lo.
4. No FT o desacordo é real (Recall 0,25); o humano é o árbitro na amostra; F1–F5 serão hedgeados / recalculados.
5. Dedup: 404→340, 381→318; PRIMAD permanece o único triplo-IC; denominador muda, numerador não — **mas** isso não resolve Lost Evidence.

---

## Decisões que só você pode tomar (bloqueiam a carta final)

1. **Manchete e corpus.** (A) promover os includes humanos da amostra ao corpus oficial e recalcular F1–F5; (B) manter 169/340 e hedgear toda raridade com Recall/LE. Recomendação: **A no FT da amostra (95 FN)** é caro; **B + inversão do protocolo M4 + Recall reportado** é a rota mínima crível. “1 of 404” vira “1 of 340 no corpus LLM, com Lost Evidence amostral de 75% no FT”.
2. **Título:** Systematic Mapping Study (recomendado; destrava M9) vs manter SLR.
3. **Zenodo:** abrir arquivos do `20130276` (M14). Sem isso a contribuição empírica continua inverificável.
4. **Companion PATHCAST:** preprint citável ou “future work, not published” (M1 / R1 W6).
5. **Fase B:** promover já os 3 PDFs (`ba2ff831`, `ee562777`, `9188583f`) ou esperar os 42 sem PDF.

---

## Ordem no manuscrito (fusão R1+R2)

1. M12 (Tabela 13) — 30 min, bloqueador barato  
2. m4 / R1 W3 — datas  
3. R1 W2+W5 / M13 / m11 — 318/340 + funil + base F1–F5  
4. M2–M3–M4–M6–M7 — tabela humano, matriz, Recall/LE, inversão `maybe`, extração por campo, papel do humano  
5. M1 / R1 W4+W6 / m3 — PATHCAST como agenda  
6. M15 + título + M9 + m1 + m9 + M8 + M10 + m7 + m8  
7. M11 apêndice de estudos; M14 Zenodo  
8. Carta sem placeholders  

Itens 3–5 da lista de decisões acima continuam **NEEDS-AUTHOR-DATA**.
