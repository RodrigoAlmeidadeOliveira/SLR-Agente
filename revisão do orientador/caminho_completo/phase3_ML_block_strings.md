# Bloco forecasting/ML — strings para as 5 bases

**D2=B:** não incluir *software defect prediction* / JIT defect como IC4c. Foco em métricas de **processo** (lead/cycle/remaining time, issue resolution time, PR merge time, throughput). Hits de defect prediction → `exclude_other` (produto).

## Faceta canônica (adaptar ao dialeto de cada base)

```
("bug fix time" OR "bug-fix time" OR "issue resolution time" OR
 "issue fixing time" OR "effort estimation" OR "lead time prediction" OR
 "cycle time prediction" OR "remaining time prediction" OR
 "pull request" AND (prediction OR forecast) OR
 "mean time to resolve" OR "time to merge")
AND
("machine learning" OR "deep learning" OR "random forest" OR
 "neural network" OR "regression" OR "gradient boosting" OR "XGBoost")
AND
("software" OR "github" OR "jira" OR "repository" OR "issue tracker" OR "pull request")
```

### Scopus (TITLE-ABS-KEY)

```
TITLE-ABS-KEY(
 ("bug fix time" OR "bug-fix time" OR "issue resolution time" OR "issue fixing time"
  OR "effort estimation" OR "lead time prediction" OR "cycle time prediction"
  OR "remaining time prediction" OR "time to merge" OR "mean time to resolve"
  OR (("pull request") AND (prediction OR forecast OR "machine learning")))
 AND
 ("machine learning" OR "deep learning" OR "random forest" OR "neural network"
  OR regression OR "gradient boosting" OR XGBoost OR classification)
 AND
 (software OR github OR jira OR repository OR "issue tracker" OR "pull request")
) AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE,"ar") OR LIMIT-TO(DOCTYPE,"cp")) AND LIMIT-TO(LANGUAGE,"English")
```

### IEEE Xplore

Usar Command Search / All Metadata com a faceta canônica; filtrar 1994–2026; Journals + Conferences.

### ACM DL

`[[All: …]]` com a faceta; Published since 1994.

### Web of Science

TS=(faceta); Indexes SCI-EXPANDED, etc.; 1994–2026; Article OR Proceedings Paper; English.

### SpringerLink

Mesma faceta em “with all of the words” / advanced; documentar limitação da UI.

## Pós-busca

1. Exportar → `phase3_exports/ML_<base>.csv`
2. Dedup entre bases + contra n=435
3. Triagem IC/EC (D2=B)
4. Ledger `phase3_search_ledger.csv`

## D6 — 19 da busca suplementar 31/10/2026

Arquivo de trabalho: `phase3_d6_19_screen.csv`  
Origem: `results/final_review/ml_string_165_screening.csv` (19 `include` por título).

**Expectativa sob D2=B:** a maioria é JIT/defect prediction → `exclude_other`. Confirmar abstract/PDF e gravar `final_decision`.
