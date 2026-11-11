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

### Classificação interativa dos 53 ready (recomendado)

```bash
cd "revisão do orientador/caminho_completo"
python3 classify_ready_interactive.py --status
python3 classify_ready_interactive.py --coder Rodrigo --lot A --pending-only
python3 classify_ready_interactive.py --coder Juliano --lot B --pending-only
```

- Lote **A** = 27 primeiros · Lote **B** = 26 últimos (por `internal_id`).
- Em cada card: lê título/abstract → `decision` → toggle de famílias → `level` calculado → grava no CSV.
- Atalho `s` / aceitar sugestão usa `suggest_*` só como ponto de partida.
- `o` abre o DOI no browser · `k` skip · `q` sai (progresso já salvo).

1. Rodar o script acima (ou preencher manualmente o CSV).
2. Preencher `decision` ∈ {`classify`,`EC5a`,`EC5b`,`exclude_other`}, `families`, `level`, `coder`, `date`.
3. Para os restantes sem abstract:

```bash
python3 classify_needs_human_interactive.py --coder Rodrigo --pending-only
```

Recuperar abstract/PDF via `o` (DOI) ou `p` (colar abstract); se impossível → `3` (EC5b). O script aplica em `studies.json` a cada save.

4. Após fechar a fila, regenerar figuras: `cd ../MSL___Rodrigo_e_Juliano && python3 figs.py && python3 figs_pt.py`.

## Auditoria L0 (n=55) — amostra ainda válida sobre os 323 L0 atuais

Arquivo: `phase1_L0_audit_sample.csv`

```bash
python3 classify_L0_audit_interactive.py --status
python3 classify_L0_audit_interactive.py --coder Rodrigo --pending-only
```

1. Codificar `human_families` (e `match_llm` y/n vs coluna LLM).
2. Segundo coder em ≥20% da amostra (reabrir com `--coder Juliano` e campos paralelos, ou duplicar CSV).
3. Reportar: taxa de erro (família faltando ou sobrando), κ, impacto em L0/L1.

## PRIMAD

Arquivo a criar: `phase1_primad_reading_notes.md`

- Quem leu o PDF
- Seções/páginas da avaliação por componente
- Confirmação L2 vs L3
