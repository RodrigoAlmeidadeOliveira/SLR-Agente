# Systematic Mapping Study — estado atual

Arquivos: `main.tex` / `main_pt.tex`, `references.bib`, `appendix_studies*.tex`, `figs/`, `figs.py`, `studies.json`, `main.pdf` / `main_pt.pdf`.  
Compilar: `latexmk -pdf main.tex` (e `main_pt.tex`).

Status operacional do caminho completo: `../caminho_completo/01_STATUS.md`.

## Fechado (2026-11-12)

- Corpus final **n = 1710** (busca-base + ML + Wohlin até saturação + IC1 + flips F2.3).
- Fases 0–5 do caminho completo executadas (D1–D6).
- RQ3: prioritário humano **293/293**; full sheet core **1710/1710** (1417 suggestion-assisted).
- L0 2º coder: **11/55** (20%), κ A↔B = 1,00 (com sugestão LLM).
- SPMF + venues OpenAlex no full corpus.
- Parecer orientador/paper-reviewer: correções indispensáveis aplicadas (L2×2, números, RQ3 calibrado, ameaças ML, RA2–RA4, κ L0, registro Step-2).
- Macro `\pendente` removido; sem `[PENDENTE]` no PDF.

## Pré-submissão restante (fora do LaTeX)

1. Atualizar pacote Zenodo de replicação (`10.5281/zenodo.21939600`) com sheets/`studies.json` finais.
2. Confirmar revista-alvo (`\journal{Information and Software Technology}`).
3. Opcional de reforço: L0 B nos 55 sem sugestão; QA amostral nos 1417 suggestion-assisted.

## Versão em português

`main_pt.tex` espelha o EN; figuras `*_pt.pdf`; números no padrão brasileiro.
