# Fase 2 — Auditabilidade da seleção

Objetivo: fechar os três `\pendente{}` de Step 2/3 no `main.tex`: pré-registro público, heurística S1/S3, e re-triagem sem âncora + κ.

## 2.1 Pré-registro (depósito público)

**Já existe** (congelado antes da validação round-2):

`article_ist/response_to_reviewers/round2/PREREGISTRATION_round2_validation.md`  
Data no arquivo: **2026-10-06**. Timestamp verificável provisório = commit git que introduziu o arquivo no repositório.

### Ação humana (bloqueante para remover o `\pendente`)

1. Criar projeto OSF **ou** depósito Zenodo com:
   - o Markdown de pré-registro acima;
   - `pipeline/round2_validation.py` (versão da data);
   - opcional: `round2_report.txt`.
2. Anotar DOI/URL em `phase2_preregistration_deposit.md`.
3. Atualizar `main.tex` / `main_pt.tex` com o link.

Enquanto o depósito não existir, o manuscrito cita o arquivo + data 2026-10-06 e declara o depósito público como pendente.

## 2.2 Heurística S1 / S3 (descrição)

Fonte: `results/human_validation_round2/escalation/README_PRECLASS.md` + planilhas `03b` / `04b`.

| Lote | População | n triados | Método de pré-sugestão |
|------|-----------|-----------|------------------------|
| **S1** | auxiliary T/A `exclude` (LLM) | 2383 | Misto: lotes de **agentes** (`preclass_source=agent_batches_*`, 1192 linhas) + **heurística tipada** (`heuristic`, 1191) |
| **S3** | closed EC5-extended / pending sem abstract | 551 | **Heurística tipada** (sem coluna `preclass_source`; includes marcados heuristic no relatório) |

**Heurística tipada (S1 restante + S3):** regras por palavras-chave no título/abstract alinhadas à Tabela de critérios (IC4a–d / EC1–5), com `sug_confidence` ∈ {high, medium, low}. Autoria: equipe do manuscrito (scripts de pré-classificação da escalada E2), não o modelo Haiku do Step 1.

**Agentes (parte de S1):** pré-classificação título/abstract por agentes em lotes `decisions_*.json`, mesclados em `03b` (`agent_batches_01_02` … `07_08`).

**Achado crítico de auditabilidade:** em `03b` e `04b`, `decision == sug_decision` em **100%** das linhas (2383/2383 e 551/551). Ou seja, a planilha oficial não separa julgamento humano da sugestão — daí a necessidade da re-triagem cega (2.3).

Detalhe narrativo para o artigo: `phase2_S1_S3_heuristics.md`.

## 2.3 Re-triagem sem âncora (amostra) + κ

### Amostra (seed 20261111)

Arquivos:

- `phase2_blind_rescreen_sheet.csv` — **para os raters** (sem `original_decision` / `preclass_source`)
- `phase2_blind_rescreen_master.csv` — master com decisão original (só analista)

| Estrato | includes (todos) | excludes (amostra) | Total |
|---------|------------------|--------------------|-------|
| S1 | 33 | 40 | 73 |
| S3 | 14 | 30 | 44 |
| **Total** | **47** | **70** | **117** |

### Protocolo

1. Dois raters (Rodrigo, Juliano) julgam de forma **independente**, cegos à sugestão e à decisão original.
2. Critérios = Tabela IC/EC do manuscrito; base de acesso = abstract → DOI/PDF.
3. Labels: `include` | `exclude` | `not_assessable`.
4. Divergências → consenso (registrar em `consensus_decision`).
5. Métricas:
   - κ Cohen A vs B (pré-consenso);
   - % concordância consenso vs `original_decision` (só assessable);
   - taxa de *flips* include↔exclude.

### Ordem prática sugerida

1. Primeiro os **47 includes** (maior impacto no corpus).
2. Depois os 70 excludes.

Script auxiliar:

```bash
python3 classify_phase2_blind_interactive.py --coder Rodrigo --rater A --pending-only
python3 classify_phase2_blind_interactive.py --coder Juliano --rater B --pending-only
python3 classify_phase2_blind_interactive.py --score
```

## Critério de fechamento da Fase 2

| Item | Fechado quando |
|------|----------------|
| Pré-registro | DOI/URL OSF ou Zenodo preenchido |
| Heurística S1/S3 | Texto no manuscrito + `phase2_S1_S3_heuristics.md` |
| Re-triagem cega | Amostra codificada (mín. 47 includes) + κ reportado no `.tex` |
