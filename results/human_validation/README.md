# Double-screening humano — SLR PATHCAST (Reviewer 1, W1)

Protocolo cego: NÃO abra a pasta `_answer_keys/` antes de terminar de preencher
as duas planilhas abaixo. Ela contém as decisões do LLM primário
(claude-haiku-4-5) e serve só para o cálculo de kappa ao final.

## 1. `ta_blind_review_sheet.csv` (title/abstract, n=472, amostra de 20%)

Para cada linha, leia `title` + `abstract` e preencha:
- `human_ta_decision`: `include`, `maybe` ou `exclude`
- `human_ta_notes`: justificativa curta (opcional, mas recomendado)

Critérios (idênticos aos usados pelo LLM, `config/screening_criteria.py`):

**Inclusão (≥1 obrigatório):**
- IC1 — Process Mining em Software: aplica PM (descoberta, conformance, workflow
  mining, event log analysis, PPM) a artefatos de SW (commits, issues, PR, CI/CD).
- IC2 — Modelagem Estocástica em Processos de SW: Markov, Monte Carlo, Petri nets
  estocásticas, matrizes de transição, aplicados a processos de desenvolvimento de SW.
- IC3 — Forecasting de Métricas de Processo: prevê lead time, cycle time, remaining
  time, throughput ou taxa de defeitos usando dados/event logs.
- IC4 — Mineração de Repositórios para Processo: minera GitHub/Jira/VCS para
  descobrir ou melhorar modelos de processo de desenvolvimento de software.

**Exclusão (qualquer 1 já exclui, mesmo com IC atendido):**
- EC1 — Domínio fora de SW (saúde, manufatura, finanças etc.).
- EC2 — "Software" é ferramenta, não é o processo estudado.
- EC3 — Método puramente teórico, sem avaliação em processos de SW.
- EC4 — Survey/SLR secundária fora do escopo (não trata PM/estocástico em SE).

Use `maybe` quando: abstract ausente mas título relevante; BPM genérico que pode
ou não tratar de processos de SW; terminologia ambígua.

## 2. `ft_qa_extraction_blind_review_sheet.csv` (full-text, n=177, amostra de 20%)

Para cada linha, localize o texto completo (via `doi`, `url`, `ft_oa_url` ou,
quando preenchida, `local_pdf_path`) e:

**Coluna `local_pdf_path` (adicionada em 07/jul/2026, atualizada em 08/jul/2026):**
aponta para um PDF já baixado localmente. Preenchida em **37 de 177 linhas
(21%)**: 16 já existiam no repositório (13 por DOI, 3 por título, conferidos
manualmente) + 21 baixados automaticamente via cascata Unpaywall/Semantic
Scholar/OpenAlex/CORE (`pipeline/pdf_downloader.py`) para os que faltavam.
Dos 161 que não tinham PDF local, mais 19 tiveram uma URL open-access
encontrada mas o download automático falhou — vale tentar `results/pdfs/download_manifest.csv`
(coluna `oa_url`, status `oa_found`) antes de recorrer ao `doi`/`url`/`ft_oa_url`
manual. Os **120 restantes** não têm fonte automática (provavelmente pagos) —
use `doi`/`url`/`ft_oa_url` diretamente.

Dois títulos ficaram **deliberadamente sem match** por ambiguidade: "Analysis
of software repositories using process mining" e "Mining Software Process
Lines" bateram no mesmo arquivo (`results/pdfs/c517c93f_process_mining_software_repositories.pdf`)
com pontuação de similaridade parecida — não dá para saber qual dos dois é o
correto sem abrir o PDF, então nenhum dos dois foi preenchido automaticamente.
Se revisar algum desses dois papers, confirme o conteúdo do PDF contra o
título antes de usá-lo (pode ser um terceiro paper diferente dos dois).

**a) Decisão FT** — mesmos critérios IC1-IC4/EC1-EC4 acima, agora com o texto
completo disponível:
- `human_ft_decision`: `include` ou `exclude`
- `human_ft_notes`: justificativa curta

**b) Só se `human_ft_decision = include`**, preencha também (mesmo passe de
leitura, sem reler o paper depois):

Quality Assessment (rubrica QA1-QA8, binário 0/1 cada; ≥4/8 = qualidade aceitável):
- `human_QA1` — Objetivos de pesquisa claramente declarados?
- `human_QA2` — Contexto de engenharia de software descrito em detalhe?
- `human_QA3` — Fonte de dados (event log/repositório/dataset) descrita de forma
  reprodutível?
- `human_QA4` — Técnica de PM ou estocástica formalmente definida (nomeada)?
- `human_QA5` — Resultados validados empiricamente (case study, experimento,
  dados reais — não apenas conceitual)?
- `human_QA6` — Ameaças à validade discutidas?
- `human_QA7` — Estudo reprodutível (dados e/ou código disponíveis)?
- `human_QA8` — Métricas de qualidade de modelo de processo reportadas (fitness,
  precision, F1, MAPE, RMSE etc.)?
- `human_qa_notes`: justificativa curta

Extração de dados:
- `human_research_question`, `human_study_type`, `human_pm_technique`,
  `human_stochastic_technique`, `human_software_process`, `human_dataset_source`,
  `human_main_finding`, `human_limitations` — preencha com texto curto,
  no mesmo padrão dos valores já usados no artigo (ver
  `results/auxiliary/extraction_combined_381.csv` para exemplos de granularidade
  esperada, SEM abrir a linha correspondente a este paper).

## 3. Depois de preencher tudo

```
python -m pipeline.human_kappa --compute
```

Isso junta suas respostas com `_answer_keys/`, calcula Cohen's kappa (T/A e FT,
multi-classe e binário), agreement % por critério QA, e agreement % nos campos
de extração, salvando em `human_kappa_report.txt` / `.tex`.

## Estimativa de esforço
- T/A: ~1-2 min/paper × 472 = ~8-16h.
- FT (leitura completa): ~5-15 min/paper × 177 = ~15-45h; QA+extração no mesmo
  passe não deve adicionar mais que +3-5 min/paper nos papers marcados include.

Pode ser feito em múltiplas sessões — o script de build não sobrescreve
respostas já preenchidas se você rodar `--build-sheets` de novo com os mesmos
arquivos (mas evite rodar de novo depois de começar a preencher: ele regenera
o CSV do zero). Salve backups incrementais se for parar e retomar depois.

## Pendências (10/jul/2026)

- **`53ed8ac4`** ("International Workshops on Business Process Management, BPM 2020")
  — você já decidiu `exclude` quando o abstract ainda era o texto errado sobre
  "family firms/SMFFs" (contaminação de fuzzy match, já corrigida — ver
  `article_ist/response_to_reviewers/audit_log_abstract_recovery_2026-07-09.md`,
  Seção 3). O título é um volume de proceedings inteiro, não um paper — `exclude`
  provavelmente continua certo, mas por outro motivo. Reconfirme quando revisar
  essa linha.
- **`9fe435f5`** ("AtomPy: An open atomic data curation environment for
  astrophysical applications") — o abstract atual parece ser de outro paper
  (bloco de afiliação de "Department of Mechanical and Aeronautical
  Engineering", não sobre astrofísica/curadoria de dados). Ainda sem decisão
  sua nessa linha — cheque o DOI/título antes de decidir.
- Cópia de trabalho `ta_blind_review_sheet_wip.xlsx` já está sincronizada com
  as correções acima (ver log de auditoria) — se você mantém o fluxo de
  trabalho nela, as duas pendências acima também se aplicam lá.
