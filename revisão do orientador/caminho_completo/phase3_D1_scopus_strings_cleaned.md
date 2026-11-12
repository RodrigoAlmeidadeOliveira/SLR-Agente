# D1 — Strings Scopus sem títulos literais (V6, V8, V9)

Fonte original (apêndice IST / `cap3_article_body.tex`). Removidos apenas os `OR ("…título literal…")`.

Filtro comum (manter):
`AND PUBYEAR > 1993 AND PUBYEAR < 2027 AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp")) AND LIMIT-TO(LANGUAGE, "English")`

## String afetada V6 (Whittaker)

**Antes:** tinha `OR ("A Markov chain model for statistical software testing")`

**Depois (colar no Scopus):**

```
TITLE-ABS-KEY( (("Markov chain" OR "Markov model") AND ("statistical software testing" OR "software testing" OR "software reliability")) ) AND PUBYEAR > 1993 AND PUBYEAR < 2027 AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp")) AND LIMIT-TO(LANGUAGE, "English")
```

## String afetada V8 (Rogge-Solti)

**Antes:** tinha `OR ("Prediction of Remaining Service Execution Time Using Stochastic Petri Nets with Arbitrary Firing Delays")`

**Depois:**

```
TITLE-ABS-KEY( (("stochastic Petri net" OR "stochastic workflow net" OR "GSPN") AND ("remaining service time" OR "service execution time" OR "remaining time")) ) AND PUBYEAR > 1993 AND PUBYEAR < 2027 AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp")) AND LIMIT-TO(LANGUAGE, "English")
```

## String afetada V9 (Rozinat)

**Antes:** tinha `OR ("Discovering Simulation Models")`

**Depois:**

```
TITLE-ABS-KEY( (("process mining" OR "process discovery" OR "workflow mining") AND ("simulation model" OR "simulation models" OR "process simulation" OR "discovering simulation models" OR "colored Petri") AND ("event log" OR "process model" OR "business process")) ) AND PUBYEAR > 1993 AND PUBYEAR < 2027 AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp")) AND LIMIT-TO(LANGUAGE, "English")
```

## Procedimento

1. Rodar as 3 strings no Scopus (documentar data/hora).
2. Exportar CSV/RIS → `phase3_exports/D1_V6.csv` etc.
3. Deduplicar contra `studies.json` (n=435) por DOI/título.
4. Triar só `unique_new`.
5. Registrar em `phase3_search_ledger.csv`.
6. Verificar se V6/V8/V9 ainda são recuperados pelos termos canônicos (sanity check do control set).
