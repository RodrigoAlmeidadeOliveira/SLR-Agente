# Status — Caminho completo (SMS)

Última atualização: 2026-11-12

## Corpus final

**n = 1710** (snowball 1715 → IC1 −7 → 1708 → flips F2.3 +2)

## Fase 0–5 — fechadas

| Fase | Estado |
|------|--------|
| 0 Decisões D1–D6 | ✅ trancadas e assinadas |
| 1 title-only / L0 / PRIMAD / 2013 | ✅ |
| 2 pré-registro + heurística S1/S3 + cego κ | ✅ κ=1,00 (n=117); flips aplicados |
| 3 D1/D2/D6 + ML + Wohlin saturação + IC1 | ✅ |
| 4 RQ3 prioritário 291 + venues OpenAlex + SPMF | ✅ |
| 5 prosa editorial EN/PT | ✅ (Tabela 9 fundida em `tab:rq3-sdlc`; sem `[PENDENTE]` residual) |

## Escopo RQ3 (D3)

- Extração humana **detalhada**: conjunto prioritário **291** (L1/L2 + todo TF-PM).
- Corpus restante (**1419**): cobertura SDLC via códigos SPMF SC mecânicos; venues/pub_type via OpenAlex no full corpus.
- Não há segunda passagem humana campo-a-campo nos 1419 nesta versão (limitação declarada no manuscrito).

## Opcionais aceitos como limitação (não bloqueantes)

- [ ] 2º coder independente na auditoria L0 (amostra 55; 1º coder 55/55)
- Extração RQ3 detalhada dos 1419 restantes (além de SPMF SC)

## Pré-submissão feito

- [x] DOIs: Rama-Maneiro, Panjer, Giger, Burke, Wieringa
- [x] `README` / este status alinhados a n=1710
- [x] Tabela `tab:phases` removida (conteúdo em `tab:rq3-sdlc` com MSR)

## Artefatos-chave

- Corpus: `MSL___Rodrigo_e_Juliano/studies.json`
- RQ3: `phase4_rq3_priority_sheet.csv` + `phase4_rq3_priority_summary.md`
- Venues: `phase4_venues_summary.md`
- SPMF: `phase4_spmf_summary.md` + `figs/spmf_map*.pdf`
- F2.3: `phase2_blind_score_full.md` + `phase2_corpus_flips_applied.csv`
- Pré-registro: Zenodo **10.5281/zenodo.24148068**
