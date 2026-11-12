# Status — Caminho completo (SMS)

Última atualização: 2026-11-12

## Fase 0–1 ✅ · Fase 2.1–2.2 ✅

- Pré-registro: Zenodo **10.5281/zenodo.24148068**
- [x] Fase 2.3 **completa n=117**: A+B κ=1.00; vs original 79.3% (16 incl→excl + 8 excl→incl); flips **aplicados** → n=1710 (−6 in-corpus / +8; 10 ie já ausentes)

## Fase 3 — Completude da busca  ✅

| Item | Resultado |
|------|-----------|
| D6 | 19/19 exclude; +0 |
| D1 | residual 30 exclude; +0; n=435 |
| Bloco ML | +126 → n=561 |
| Snowballing Wohlin | iters 1–5: +401+627+120+6+**0** (saturação) → n=1715 bruto |
| IC1 pós-snowball | **−7** (year&lt;1994) → **corpus final n=1708** |
| Ledger | `phase3_snowballing_ledger.csv` + `phase3_snowball_SATURATION.md` |

Manuscrito EN/PT: prosa Wohlin até saturação; D1/D6/ML/D2 fechados; IC1 aplicado; tabelas/figs/apêndice em **n=1708**.

## Fase 4 — RQ3 + SPMF

| Artefato | Estado |
|----------|--------|
| `phase4_rq3_priority_sheet.csv` | **291/291 core ✅** |
| `phase4_rq3_priority_summary.md` | crosstabs |
| `phase4_rq3_extraction_template.csv` | 291/1708 core; resto aberto |
| Venues OpenAlex | **1523/1708 (89%)** venue; pub_type journal 794 / conf 648 / ws 27 |
| SPMF | **aplicada** (AD×SC×TI); `figs/spmf_map.pdf`; tab no `main*.tex` |
| `phase4_ic1_flag_screen.csv` | 7/7 exclude ✅ |

```bash
# venues (próximo)
python3 classify_phase4_rq3_interactive.py --sheet full --mode venue --pending-only --compact
# paralelo F2.3:
python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --includes-only --pending-only
```

## Fase 5 — Editorial

Fechado: Wohlin; D1/D6/ML/D2; IC1; RQ3 priority no `main*.tex` (tabs sdlc/tech + RA1/RA3).

`\pendente{}` no manuscrito: **0** (F2.3 includes κ, venues, RQ3 priority, SPMF fechados). Opcional: 70 excludes da amostra cega.
