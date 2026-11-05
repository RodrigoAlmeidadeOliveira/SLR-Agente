# Protocolo — classificação dos 76 title-only + auditoria L0

## Famílias (marcar todas que se aplicam)

| Código | Critério |
|---|---|
| TF-PM | Aplica process mining (discovery, conformance, predictive process monitoring) a artefatos de SDLC |
| TF-ST | Usa modelo estocástico (Markov, Monte Carlo, SPN, absorbing chains) para analisar **processo/workflow de desenvolvimento** |
| TF-FC | Propõe/avalia previsão de métricas de processo (lead/cycle/remaining time, throughput; defect rates só se D2=A) |
| TF-MSR | Minera repositórios (GitHub, Jira, VCS, CI/CD) para descobrir/analisar/melhorar modelos de processo |

## Níveis

- L0 ≤1 família de técnica (PM/ST/FC)
- L1 exatamente 2
- L2 as 3, avaliação por componente / sem interfaces especificadas
- L3 as 3, interfaces especificadas, avaliação end-to-end em dados de SDLC

## Regras sob D2=B

Excluir ou não marcar ST/FC quando o modelo for **confiabilidade do produto** ou **uso em teste estatístico** sem processo de desenvolvimento. Registrar EC novo na planilha (`notes`).

## Fluxo dos 76

1. Abrir `phase1_title_only_ready_to_classify.csv` (tem abstract e/ou PDF local).
2. Preencher `decision` ∈ {`classify`,`EC5a`,`EC5b`,`exclude_other`}, `families`, `level`, `coder`, `date`.
3. Para `phase1_title_only_needs_human.csv`: recuperar abstract/PDF via DOI; se impossível → `EC5b`.
4. Após lote fechado, rodar `scripts/apply_title_only_to_studies.py` (a criar) → atualiza `studies.json` e regenera figuras.

## Auditoria L0 (n=55)

Arquivo: `phase1_L0_audit_sample.csv`

1. Codificar `human_families` e `human_level` cego à coluna LLM (ocultar `families_llm` na UI se possível).
2. Segundo coder em ≥20% da amostra.
3. Reportar: taxa de erro (família faltando ou sobrando), κ, impacto em L0/L1.

## PRIMAD

Arquivo a criar: `phase1_primad_reading_notes.md`

- Quem leu o PDF
- Seções/páginas da avaliação por componente
- Confirmação L2 vs L3
