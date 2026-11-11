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
2. Classificar os 53 ready com o prompt interativo:

```bash
cd "revisão do orientador/caminho_completo"
python3 classify_ready_interactive.py --coder Rodrigo --lot A --pending-only
# Juliano:
python3 classify_ready_interactive.py --coder Juliano --lot B --pending-only
```

3. Classificar os **23** restantes (`needs_human`):

```bash
python3 classify_needs_human_interactive.py --coder Rodrigo --pending-only
# ou lotes A (12) / B (11):
python3 classify_needs_human_interactive.py --coder Rodrigo --lot A --pending-only
```

Atalhos: `o` DOI · `p` colar abstract · `3` EC5b · grava e aplica em `studies.json` a cada item.
