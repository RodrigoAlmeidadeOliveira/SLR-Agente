# Status — Caminho completo (SMS)

Última atualização: 2026-11-04

## Legenda

- `[ ]` pendente · `[~]` em andamento · `[x]` concluído · `[!]` bloqueado (precisa humano)

## Fase 0 — Escopo

- [x] Trancar D3=A e D5=A
- [x] Defaults do caminho completo para D1=A, D2=B, D4=A, D6=incorporar (`00_DECISOES.md`)
- [!] Assinatura Rodrigo / Juliano / Scalabrin

## Fase 1 — Corpus fechado

- [~] **1.1** Classificar/excluir 76 title-only
  - [x] Worksheet com metadados (`phase1_title_only_worksheet.csv`)
  - [x] Enriquecimento automático de abstracts (OpenAlex/Crossref): 39/76
  - [x] Merge com `ft_screening_results.csv` (quando houver abstract)
  - [x] Fila humana sem abstract (`phase1_title_only_needs_human.csv`)
  - [x] Fila pronta para classificar (`phase1_title_only_ready_to_classify.csv`)
  - [!] Classificação humana das famílias + níveis
  - [ ] Aplicar EC5b aos irrecuperáveis
  - [ ] Atualizar `studies.json` → `figs.py` / `figs_pt.py` → tabelas/apêndice
- [~] **1.2** Auditoria L0
  - [x] Amostra estratificada n=55 (`phase1_L0_audit_sample.csv`)
  - [!] Codificação humana + κ / taxa de erro
- [!] **1.3** PRIMAD: leitor + páginas da avaliação por componente
- [!] **1.4** Verificar buraco de 2013 nas exportações

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

- [x] Template dos 380 classificados (`phase4_rq3_extraction_template.csv`) — regenerar após Fase 1
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

1. Classificar a fila `phase1_title_only_ready_to_classify.csv`
2. Recuperar PDF/abstract da fila `phase1_title_only_needs_human.csv`
3. Auditar amostra L0
4. Ler PRIMAD (PDF completo) e anotar seções
5. Assinar `00_DECISOES.md` (sobretudo D2)
