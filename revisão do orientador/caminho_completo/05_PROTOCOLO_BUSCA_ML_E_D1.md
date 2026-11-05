# Protocolo — Bloco forecasting/ML + D1 (strings Scopus)

## D1 — Títulos literais

1. Localizar as três strings Scopus que contêm títulos de V6, V8, V9.
2. Remover os títulos literais; manter termos canônicos.
3. Reexecutar só as strings afetadas na mesma data-base política (documentar data).
4. Deduplicar contra o corpus atual; triar apenas os novos únicos.
5. Atualizar Tabelas de busca/seleção e ameaça §6.1 (a declaração de títulos literais sai).

## Bloco forecasting/ML (cinco bases)

Sugestão de faceta (ajustar ao dialeto de cada base):

```
("bug fix time" OR "bug-fix time" OR "issue resolution time" OR
 "issue fixing time" OR "effort estimation" OR "lead time prediction" OR
 "cycle time prediction" OR "remaining time prediction" OR
 "software defect prediction" OR "pull request prediction")
AND
("machine learning" OR "deep learning" OR "random forest" OR
 "neural network" OR "regression" OR "classification")
AND
("software" OR "github" OR "jira" OR "repository" OR "issue tracker")
```

Executar em IEEE, ACM, Scopus, WoS, SpringerLink. Deduplicar. Triar com IC/EC (respeitando D2).

## D6 — 19 suplementares (31/10/2026)

Arquivo existente: `results/final_review/ml_string_165_screening.csv`

1. Revisar os 19 includes-por-título com abstract/PDF.
2. Decisão final include/exclude por critério.
3. Incorporar includes ao corpus e à classificação.

## Ledger

`phase3_search_ledger.csv`: source, string_id, date, raw, unique_new, included_new.
