# Caminho completo — execução das pendências do SMS

Operacionaliza o plano com **D3=A** (extração humana RQ3) e **D5=A** (snowballing Wohlin até saturação), mais defaults fortes para D1/D2/D4/D6.

## Ordem de leitura

1. `00_DECISOES.md` — decisões trancadas (assinar)
2. `01_STATUS.md` — checklist vivo
3. Protocolos `02`–`05`
4. Planilhas `phase1_*` e `phase4_*`

## Manuscrito

Fonte: `../MSL___Rodrigo_e_Juliano/` (`main.tex`, `main_pt.tex`, `studies.json`, `figs.py`).

Só atualizar o `.tex` depois que os dados da fase correspondente estiverem fechados (evitar editar `\pendente` “no olho”).

## Próxima ação humana (Fase 2)

1. Depositar pré-registro em OSF/Zenodo → `phase2_preregistration_deposit.md`.
2. Re-triagem cega (amostra 117; começar pelos 47 includes):

```bash
cd "revisão do orientador/caminho_completo"
python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --includes-only --pending-only
python3 classify_phase2_blind_interactive.py --coder Juliano --rater B --includes-only --pending-only
python3 classify_phase2_blind_interactive.py --score
```

Protocolo: `06_PROTOCOLO_FASE2_AUDITABILIDADE.md`.
