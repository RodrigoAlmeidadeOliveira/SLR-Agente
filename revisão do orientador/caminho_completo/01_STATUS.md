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

1. **D6 (rápido):** decidir os 19 em `phase3_d6_19_screen.csv` (sob D2=B → quase todos exclude defect/JIT).
2. **D1:** rodar 3 strings Scopus limpas; dedup; triar novos.
3. **Bloco ML:** rodar 5 bases; dedup; triar (sem defect prediction).
4. **Snowballing Wohlin** a partir dos 435 (+ novos includes), até saturação.
5. Atualizar `studies.json`, figs, `main*.tex`, PRISMA.

## Fase 4–5

Template RQ3 pronto · extração / editorial depois da busca.
