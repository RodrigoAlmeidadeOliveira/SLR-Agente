# Status — Caminho completo (SMS)

Última atualização: 2026-11-11

## Legenda

- `[ ]` pendente · `[~]` em andamento · `[x]` concluído · `[!]` bloqueado (precisa humano)

## Fase 0 — Escopo ✅

## Fase 1 — Corpus fechado ✅ (n=435)

## Fase 2 — Auditabilidade da seleção  ← em andamento

- [~] **2.1** Pré-registro
  - [x] Arquivo local 2026-10-06 identificado
  - [!] Depositar OSF/Zenodo → preencher `phase2_preregistration_deposit.md`
- [x] **2.2** Heurística S1/S3 descrita (`phase2_S1_S3_heuristics.md`) + texto no `main*.tex`
  - Achado: `decision == sug_decision` em **100%** das linhas S1/S3
- [~] **2.3** Re-triagem cega
  - [x] Amostra n=117 (47 includes + 70 excludes) — `phase2_blind_rescreen_*.csv`
  - [x] Script `classify_phase2_blind_interactive.py`
  - [!] Codificar (começar pelos 47 includes) + κ
- Protocolo: `06_PROTOCOLO_FASE2_AUDITABILIDADE.md`

## Fase 3 — Completude da busca

- [ ] D1 Scopus · bloco ML · 19 suplementares · snowballing Wohlin

## Fase 4 — RQ3 + SPMF

- [x] Template 435 · [!] extração humana

## Fase 5 — Editorial

- [ ] `\pendente{}` · Zenodo · compilar

## Ação humana agora (Fase 2)

```bash
cd "revisão do orientador/caminho_completo"
# 1) Depositar pré-registro (OSF/Zenodo) e anotar DOI em phase2_preregistration_deposit.md

# 2) Re-triagem cega — começar pelos includes:
python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --includes-only --pending-only
python3 classify_phase2_blind_interactive.py --coder Juliano --rater B --includes-only --pending-only
python3 classify_phase2_blind_interactive.py --score
```
