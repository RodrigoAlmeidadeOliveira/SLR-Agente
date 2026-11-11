# Status — Caminho completo (SMS)

Última atualização: 2026-11-11

## Legenda

- `[ ]` pendente · `[~]` em andamento · `[x]` concluído · `[!]` bloqueado (precisa humano)

## Fase 0 — Escopo

- [x] Trancar D3=A e D5=A
- [x] Defaults do caminho completo para D1=A, D2=B, D4=A, D6=incorporar (`00_DECISOES.md`)
- [x] Assinaturas Rodrigo / Juliano / Scalabrin (marcadas no arquivo)

## Fase 1 — Corpus fechado

- [x] **1.1** Classificar/excluir 76 title-only → **n=435**, title-only=0; figs + `main*.tex` atualizados
- [x] **1.2** Auditoria L0: amostra 55/55 acordo com LLM (0% erro) — `phase1_L0_audit_report.md`
  - [ ] Opcional: 2º coder ≥20% para κ
- [!] **1.3** PRIMAD: preencher `phase1_primad_reading_notes.md`
- [~] **1.4** Buraco 2013: hits brutos OK (263 unique); vale é pós-triagem — `phase1_2013_gap_notes.md`
  - [ ] Amostra de excludes 2013 (opcional, para fechar a narrativa)

## Fase 2 — Auditabilidade da seleção

- [!] Pré-registro OSF/Zenodo (DOI/link)
- [!] Protocolo de re-triagem sem âncora (amostra) + κ
- [!] Descrever heurística S1/S3

## Fase 3 — Completude da busca

- [ ] D1: retirar títulos literais; reexecutar Scopus afetado
- [ ] Bloco forecasting/ML nas 5 bases
- [!] Triagem dos 19 suplementares + demais hits do bloco ML
- [!] Snowballing Wohlin até saturação (ver `03_PROTOCOLO_SNOWBALLING.md`)
- [ ] Atualizar ledger + PRISMA

## Fase 4 — Extração RQ3 + SPMF

- [x] Template dos **435** classificados (`phase4_rq3_extraction_template.csv`)
- [!] Extração humana (dois extratores ou extrator+verificador)
- [!] Preencher Tabela de fases / fontes / algoritmos
- [!] SPMF nos classificados
- [!] Mapa de venues / research type

## Fase 5 — Fechamento editorial

- [ ] Conferir refs novas (DOI/páginas)
- [ ] Confirmar `\journal{}`
- [ ] Zenodo: renomear CSV; incluir `figs.py` + `studies.json`
- [ ] Remover todos os `\pendente{}` em `main.tex` e `main_pt.tex`
- [ ] Compilar EN/PT e checar números

## Bloqueios atuais (precisam de Rodrigo/Juliano)

1. Ler PRIMAD (PDF) → `phase1_primad_reading_notes.md` (confirma L2)
2. Opcional: 2º coder L0 para κ; amostra de excludes 2013
3. Fase 3 (D1 strings + bloco ML + snowballing) — maior carga restante
