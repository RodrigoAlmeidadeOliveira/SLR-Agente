# Auditoria de abstracts duplicados — corpus auxiliar (880 papers, aux_pending_enriched.csv)

Detecção automática (abstract idêntico compartilhado por 2+ `internal_id` diferentes) — mesmo
sinal usado para achar a contaminação de 43% no fuzzy-match do working set (Fase A). Nenhuma
destas 12 linhas está entre os 173 estudos auxiliares já confirmados (tier 404) — são
candidatos do pool mais amplo, ainda sujeitos a triagem de full-text.

## Arquivos

- `aux_dup_abstract_suspects.xlsx` / `.csv` — as 12 linhas, agrupadas por `dup_group`
  (0-4), com o abstract completo e duas colunas para você preencher:
  - `audit_decision`: `correto` / `errado` / `incerto` / `duplicata` (se for o mesmo paper
    contado 2x no corpus, não um match errado)
  - `audit_notes`: já vem pré-preenchida com minha leitura preliminar (não confirmada) —
    sobrescreva com sua decisão final.

## Leitura preliminar (não confirmada, é ponto de partida)

- **Grupo 0** (Advanced Process Discovery Techniques ×2, `title_exact`) — abstract bate com o
  tema; parece duplicata do mesmo paper no corpus, não erro de match.
- **Grupo 1** (Apromore vs. reliability, `title_fuzzy` nos dois) — títulos genuinamente
  diferentes compartilhando o mesmo abstract sobre Predictive Process Monitoring. **Risco
  real** — no máximo 1 dos 2 está correto.
- **Grupo 2** (Business Process Deviance Mining ×2, mesmo título, `title_fuzzy`) — abstract bate
  com o tema; provável duplicata, não erro.
- **Grupo 3** (4 títulos bem diferentes — digital twin, decision support, business rules,
  business change) — abstract compartilhado é literalmente **"International audience"**, um
  metadado de repositório (tipo HAL), não um abstract real. **Confirmado junk** — tratar os 4
  como sem abstract.
- **Grupo 4** (Workflow Management ×2, mesmo título, `title_exact`) — abstract bate com o tema
  (livro clássico de workflow management); provável duplicata, não erro.

## Uso recomendado

Só o **Grupo 1** precisa de investigação de verdade (checar DOI de cada um dos 2 papers para
ver qual — se algum — corresponde ao abstract). Grupos 0, 2, 4 são prováveis duplicatas de
estudo (mesmo problema já documentado em `results/auxiliary/dedup_summary.txt` — G045/G060),
não erros de match. Grupo 3 já está confirmado como lixo de metadado, sem necessidade de
verificação adicional — só marcar como "sem abstract" nos 4 registros.
