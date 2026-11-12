# Status — Caminho completo (SMS)

Última atualização: 2026-11-12

## Fase 0–1 ✅ · Fase 2.1–2.2 ✅

- Pré-registro: Zenodo **10.5281/zenodo.24148068**
- [ ] Fase 2.3 re-triagem cega (paralelo)

## Fase 3 — Completude da busca  ← em andamento

Artefatos prontos:

| Item | Arquivo |
|------|---------|
| D1 strings limpas | `phase3_D1_scopus_strings_cleaned.md` |
| Bloco ML (5 bases) | `phase3_ML_block_strings.md` |
| D6 19 suplementares | `phase3_d6_19_screen.csv` |
| Ledger | `phase3_search_ledger.csv` |
| Snowballing | `03_PROTOCOLO_SNOWBALLING.md` |

### Ordem de execução (humano + bases)

1. **D6 ✅** — 19/19 `exclude_other` (D2=B JIT/defect); 0 no corpus → n=435 inalterado. Ledger preenchido.
2. **D1 ✅** — residual 30/30 `exclude_other` vs pool 5783; **included_new=0**; n=435 inalterado. Strings V6/V8/V9 limpas validadas.
3. **Bloco ML ✅** — 126 includes aplicados; **n=561** em `studies.json`; figs + apêndice + tabelas EN/PT atualizados.
4. **Snowballing Wohlin iter1 — fetch ✅** — **494/494**, raw 23294 → residual 13612; gate **703 maybe** / 12909 exclude (bulk-accepted). Triar: `classify_phase3_snowball_interactive.py --pending-only --only-sug maybe`.
5. Atualizar `studies.json`, figs, `main*.tex`, PRISMA após includes do snowball.


## Fase 4–5

Template RQ3 pronto · extração / editorial depois da busca.
