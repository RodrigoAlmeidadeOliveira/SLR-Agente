# Escalada Round-2 — o que revisar

Pasta: `results/human_validation_round2/escalation/`

## Ordem prática

| # | Arquivo | Ação | Volume |
|---|---------|------|--------:|
| 0 | `00_ADD_NOW_corpus.csv` | Só **adicionar ao corpus** (já julgados include) | 33 |
| 1 | `01b_E1_TO_SCREEN_only.csv` | **Triar agora (E1)** | 574 |
| 2 | `02b_E2_S2_TO_SCREEN_only.csv` | **Triar em seguida (E2-S2)** | 497 |
| 3 | `03b_E2_S1_TO_SCREEN_only.csv` | Só se Recall auxiliar < 0.90 após S2 | 2383 |
| 4 | `04b_E2_S3_TO_SCREEN_only.csv` | Só se ainda < 0.90 | 551 |

**Mínimo esperado para fechar o limiar:** E1 + S2 + S1 ≈ **3454** papers.

Arquivos sem `b_` / `TO_SCREEN` incluem também os já julgados na amostra R2 (`REUSE_R2_CONSENSUS`).

## Regra de triagem (pré-registro)

- Rater A: todos os registros da lista ativa
- Rater B: todo `include` do A + 20% aleatório dos `exclude` do A
- Após cada estrato E2: recalcular Recall auxiliar; **parar** se ≥ 0.90
