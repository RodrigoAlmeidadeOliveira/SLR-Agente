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

## Fase atual: 3 (busca)

1. D6 — 19 suplementares: `phase3_d6_19_screen.csv` (D2=B → defect/JIT tende a exclude).
2. D1 — 3 strings Scopus: `phase3_D1_scopus_strings_cleaned.md`.
3. Bloco ML — 5 bases: `phase3_ML_block_strings.md`.
4. Snowballing: `03_PROTOCOLO_SNOWBALLING.md`.
5. Ledger: `phase3_search_ledger.csv`.

### Paralelo (Fase 2.3)

```bash
python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --includes-only --pending-only
```
