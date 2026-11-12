# Status — Caminho completo (SMS)

Última atualização: 2026-11-11

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
2. **D1 busca ✅** — V6=480, V8=5, V9=187; união 668. Dedup vs pool **5783**: já vistos 638; **residual real=30** (25 de 2026 pós-corte abril) → `phase3_D1_residual_vs_pool_screen.csv` (triagem pendente). Artefato antigo vs-só-435: `phase3_D1_unique_new_vs_corpus435.csv`.
3. **Bloco ML:** rodar 5 bases; dedup; triar (sem defect prediction).
4. **Snowballing Wohlin** a partir dos 435 (+ novos includes), até saturação.
5. Atualizar `studies.json`, figs, `main*.tex`, PRISMA.

## Fase 4–5

Template RQ3 pronto · extração / editorial depois da busca.
