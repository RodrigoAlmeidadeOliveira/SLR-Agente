# Pré-classificação — escopo completo da escalada

| Arquivo | n | include | exclude | not_assessable | método |
|---|---:|---:|---:|---:|---|
| `01b_E1_TO_SCREEN_only.xlsx` | 574 | 82 | 456 | 36 | agentes (título/abstract) |
| `02b_E2_S2_TO_SCREEN_only.xlsx` | 497 | 53 | 399 | 45 | agentes (título/abstract) |
| `03b_E2_S1_TO_SCREEN_only.xlsx` | 2383 | 29 | 1821 | 533 | heurística tipada + regras Tabela 5 |
| `04b_E2_S3_TO_SCREEN_only.xlsx` | 551 | 14 | 195 | 342 | heurística tipada + regras Tabela 5 |

## Como revisar

1. Edite as 6 colunas oficiais (`access_basis` … `evidence_location`) — já vêm com a sugestão.
2. Use `sug_*` / `sug_confidence` como referência.
3. Priorize: **includes (verde)** → **low confidence (laranja)** → **not_assessable (amarelo)** → amostragem de excludes.

## Cores

- Verde = include · Vermelho = exclude · Amarelo = not_assessable · Laranja = confidence low

## Nota S1/S3

Pré-classificação heurística (palavras-chave + regras da Tabela 5). Mais sujeita a erro que E1/S2; revise com mais cuidado os includes e os `low`.

## Status final (escopo completo)

Pré-classificação aplicada em **E1 + S2 + S1 + S3** (listas `*b_*_TO_SCREEN_only.xlsx`).

| Lista | n | include | exclude | not_assessable |
|-------|---|---------|---------|----------------|
| E1 | 574 | 82 | 456 | 36 |
| S2 | 497 | 53 | 399 | 45 |
| S1 | 2383 | 29 | 1821 | 533 |
| S3 | 551 | 14 | 195 | 342 |

Arquivo de priorização humana: `00_REVIEW_PRIORITY_includes_low_na.xlsx` (includes + low + NA ≈ 1223 linhas).

**Como usar:** revisar colunas oficiais (`decision`, `ic_matched`, `ec_applied`, …); `sug_*` é rascunho. Em S1/S3 muitos NA = abstract vazio / sem DOI — buscar PDF ou marcar `access_basis=not_accessible`.

### Update S1 agent merge
Lotes 1–2 (`decisions_01/02.json`) mesclados em `03b`: 298 linhas `preclass_source=agent_batches_01_02` (6 include). Restante permanece `heuristic`.
Lotes 7–8 mesclados: +298 linhas `agent_batches_07_08` (8 include).
Lotes 5–6 mesclados: +298 linhas `agent_batches_05_06` (1 include).
Lotes 3–4: agente reportou erro, mas `decisions_03/04.json` existiam — mesclados (`agent_batches_03_04`).

### FN23 consensus revisit
Planilha `01c_E1_FN23_consensus_revisit.xlsx`: re-triagem independente dos 23 FN (consenso=include).
Resultado sug: {'include': 17, 'exclude': 5, 'not_assessable': 1}; concordam com consenso include: 17/23.
Linhas DISAGREE em laranja — revisar antes de contar no recall FT.

### S2 includes revisit
53 antigos include re-triados: {'include': 32, 'exclude': 19, 'not_assessable': 2}; flipped=21. Fonte `revisit_includes_v2`.
