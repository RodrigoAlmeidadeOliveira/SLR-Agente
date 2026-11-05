# Protocolo — Extração RQ3 + SPMF (D3=A, D4=A)

## Planilha

`phase4_rq3_extraction_template.csv` (380 linhas hoje; regenerar após fechar Fase 1).

## Campos

| Campo | Valores |
|---|---|
| `sdlc_phase` | requirements \| development \| quality \| delivery \| operations (multi com `\|`) |
| `log_source` | Jira \| GitHub \| GitLab \| Jenkins \| IDE \| other |
| `log_construction` | manual \| semi \| automatic |
| `pm_algorithm` | Alpha \| Heuristics \| Inductive \| Fuzzy \| other / NA |
| `stochastic_method` | DTMC \| CTMC \| SPN \| Monte Carlo \| System Dynamics \| other / NA |
| `ml_technique` | texto curto / NA |
| `forecast_target` | lead_time \| cycle_time \| remaining_time \| throughput \| issue_resolution \| outcome \| other / NA |
| `validation_type` | texto curto |
| `research_type` | Wieringa et al. (2006) |
| `venue` | nome do veículo |
| `pub_type` | journal \| conference \| workshop |
| `spmf_analytical_depth` | conforme taxonomia SPMF dos autores |
| `spmf_sdlc_coverage` | idem |
| `spmf_technique_integration` | idem |

## Qualidade

- Preferência: dois extratores independentes.
- Mínimo: um extrator + verificador em amostra estratificada ≥20% com κ reportado.
- Extração LLM anterior (**0% concordância exata**) **não** pode ser reutilizada como dado final.

## Saídas no manuscrito

1. Tabela fase × família (hoje vazia / PENDENTE)
2. Tabela fontes + construção do log
3. Frequências de algoritmos / métodos / alvos
4. Venues e research types
5. Mapa SPMF na discussão (RA / §5)
