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

## Próxima ação humana (bloqueante)

1. Assinar `00_DECISOES.md` (em especial **D2=B**).
2. Classificar `phase1_title_only_ready_to_classify.csv` (53 estudos; colunas `suggest_*` são só heurística).
3. Recuperar os 27 de `phase1_title_only_needs_human.csv`.
