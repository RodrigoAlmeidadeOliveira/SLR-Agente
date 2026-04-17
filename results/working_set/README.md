# Working Set Operacional

Este diretório contém o recorte operacional criado a partir do corpus
high-recall congelado em `2026-04-12`.

## Objetivo

Reduzir o volume de triagem inicial para uma faixa operacional compatível com a
SLR, preservando a cobertura mínima dos artigos de controle e mantendo o corpus
high-recall intacto em `results/frozen/`.

## Consultas incluídas no recorte operacional

- `scopus_principal`
- `scopus_complementar`
- `scopus_fronteira`
- `scopus_markov_testing`
- `scopus_stochastic_petri`
- `scopus_simulation_bridge`
- `ieee_manual_01`
- `acm_principal`
- `acm_msr`
- `control_papers_bib` apenas para validação

## Consultas rebaixadas para high-recall auxiliar

- `springer_1` a `springer_10`
- `snowball_both`
- `acm_extra_refs`
- `wos_principal`
- `wos_complementar`
- `wos_msr`
- `wos_fronteira`
- demais segmentos de `ieee_manual_all`

## Arquivos

- `operational_screening_selected_raw.json`
  - registros brutos do recorte antes da deduplicação
- `operational_screening_unique_with_control.json`
  - únicos do recorte, ainda contendo `control`
- `operational_screening_primary_unique.json`
  - únicos para triagem substantiva
- `operational_screening_control_unique.json`
  - subset `control`, separado
- `operational_screening_primary_unique.csv`
  - planilha principal para screening T/A
- `operational_screening_control_unique.csv`
  - planilha do controle

## Tamanho do recorte

- selecionados brutos: `2.545`
- únicos com controle: `2.343`
- únicos primários: `2.340`
- únicos de controle: `3`

## Cobertura dos control papers

- com `control`: `10/10`
- apenas fontes primárias do recorte: `8/10`

Controles ainda dependentes de `control` neste recorte:

- `V7`
- `V9`

## Uso recomendado

Use `operational_screening_primary_unique.csv` para a triagem de títulos e
resumos. Preserve `results/frozen/` como baseline auditável da busca completa.
