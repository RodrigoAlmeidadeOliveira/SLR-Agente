# Heurística S1 / S3 — descrição auditável

## Contexto

Após o 1º passe (LLM) falhar o limiar de Recall (0,90), a Etapa 3 re-triou todos os não-includes. Nos estratos auxiliares **S1** e **S3**, as planilhas de trabalho (`03b_E2_S1_*`, `04b_E2_S3_*`) traziam colunas `sug_*` preenchidas **antes** da revisão humana declarada.

## S1 — auxiliary title/abstract exclude (n = 2383)

| `preclass_source` | n | Natureza |
|-------------------|---|----------|
| `heuristic` | 1191 | Regras tipadas (palavras-chave + IC/EC da Tabela de critérios) |
| `agent_batches_01_02` … `07_08` | 1192 | Pré-classificação por agentes em lotes (título/abstract), mesclada depois |

`sug_confidence`: high 987 · medium 845 · low 551.

## S3 — EC5-extended / pending sem abstract (n = 551)

- Sem coluna `preclass_source` na planilha; o relatório round-2 marca os includes como **heuristic**.
- Mesmo esquema `sug_*` + `sug_confidence` (low 384 · high 152 · medium 15).
- Muitos `not_assessable` por falta de abstract/DOI.

## Autoria e escopo

- **Não** é o modelo Haiku do Step 1.
- Heurística tipada: equipe do projeto, alinhada à Tabela IC/EC (`README_PRECLASS.md`: “palavras-chave + regras da Tabela 5”).
- Agentes: lotes `decisions_*.json` mesclados em S1 apenas.

## Problema de auditabilidade

Em ambas as planilhas finais:

`decision == sug_decision` em **100%** das linhas.

Não há, no arquivo oficial, decisão humana **separada** da sugestão. O κ da re-triagem Step 3 sobre S1/S3, se calculado sobre essas colunas, seria artificialmente alto.

## Mitigação (Fase 2.3)

Re-triagem cega na amostra `phase2_blind_rescreen_*.csv`, sem exibir `sug_*` nem a decisão original.
