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

## Fase atual: 4 (RQ3/SPMF) · Fase 3 ✅ · F5 parcial · n=1708

1. Extração prioritária: `python3 classify_phase4_rq3_interactive.py --sheet priority --pending-only`
2. Venues + SPMF no full sheet.
3. Paralelo F2.3 (cego):

```bash
python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --includes-only --pending-only
```
