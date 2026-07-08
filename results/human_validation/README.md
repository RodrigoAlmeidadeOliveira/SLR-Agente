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

**Coluna `local_pdf_path` (adicionada em 07/jul/2026):** aponta para um PDF já
baixado localmente em `results/pdfs/`, `results/extraction/pdfs/` ou
`results/final_review/top30_pdfs/`, cruzado por DOI (13 casos) ou por título
(3 casos, conferidos manualmente). Preenchida em apenas **16 de 177 linhas
(9%)** — nos outros 161 casos, abra o texto via `doi`/`url`/`ft_oa_url`.

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
