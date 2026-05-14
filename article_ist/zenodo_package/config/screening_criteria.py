"""
Critérios de inclusão/exclusão para triagem de títulos e resumos — SLR PATHCAST.

Escopo: "From Discovery to Forecasting: Process Mining and Stochastic Modeling
         Applied to Software Development Processes"
"""

INCLUSION_CRITERIA = [
    {
        "id": "IC1",
        "label": "Process Mining em Software",
        "description": (
            "O estudo aplica ou propõe técnicas de process mining (descoberta de processos, "
            "conformance checking, workflow mining, análise de event logs, predictive process "
            "monitoring) sobre artefatos de desenvolvimento de software (commits, issues, "
            "pull requests, logs de CI/CD, rastreadores de bugs, repositórios VCS, etc.)."
        ),
    },
    {
        "id": "IC2",
        "label": "Modelagem Estocástica em Processos de Software",
        "description": (
            "O estudo usa ou propõe modelos estocásticos (cadeias de Markov, simulação Monte Carlo, "
            "redes de Petri estocásticas, matrizes de transição, processos absorventes) para modelar "
            "ou analisar processos ou fluxos de trabalho de desenvolvimento de software."
        ),
    },
    {
        "id": "IC3",
        "label": "Forecasting/Predição de Métricas de Processo",
        "description": (
            "O estudo propõe ou avalia métodos de previsão ou predição de métricas de processo de "
            "software (lead time, cycle time, tempo restante, throughput, taxa de defeitos, "
            "probabilidade de conclusão) usando modelos baseados em dados ou event logs."
        ),
    },
    {
        "id": "IC4",
        "label": "Mineração de Repositórios para Análise de Processo",
        "description": (
            "O estudo minera repositórios de software (GitHub, Jira, issue trackers, VCS, "
            "logs de build) para descobrir, analisar ou melhorar modelos de processo de "
            "desenvolvimento de software."
        ),
    },
]

EXCLUSION_CRITERIA = [
    {
        "id": "EC1",
        "label": "Domínio fora de Software",
        "description": (
            "O domínio de aplicação primário não é desenvolvimento de software (ex: saúde, "
            "manufatura, cadeia de suprimentos, finanças, educação geral) e o estudo não "
            "demonstra aplicabilidade direta a processos de software."
        ),
    },
    {
        "id": "EC2",
        "label": "Software como ferramenta, não domínio",
        "description": (
            "'Software' aparece apenas como ferramenta de implementação ou plataforma, "
            "não como o domínio de processo sendo analisado. O processo estudado não é "
            "o processo de desenvolvimento/engenharia de software em si."
        ),
    },
    {
        "id": "EC3",
        "label": "Algoritmo sem aplicação a processos de software",
        "description": (
            "Artigo puramente algorítmico ou teórico que não inclui aplicação ou avaliação "
            "em processos de desenvolvimento de software."
        ),
    },
    {
        "id": "EC4",
        "label": "Estudo secundário fora do escopo",
        "description": (
            "É uma revisão sistemática, survey ou mapeamento que não trata especificamente "
            "de process mining ou modelagem estocástica em engenharia de software."
        ),
    },
]

# Prompt de sistema para o LLM
SYSTEM_PROMPT = """\
Você é um especialista em revisão sistemática da literatura (SLR) na área de \
process mining e engenharia de software. Sua tarefa é realizar a triagem de \
título/resumo (T/A) para a SLR PATHCAST.

**Escopo da SLR PATHCAST:**
Intersecção entre (1) process mining, (2) modelagem estocástica, \
(3) forecasting/predição e (4) processos de desenvolvimento de software. \
O foco é em estudos que analisam, descobrem ou preveem características de \
processos de SW usando event logs, repositórios ou modelos estocásticos.

**CRITÉRIOS DE INCLUSÃO** (ao menos UM deve ser atendido para incluir):
IC1 – Process Mining em Software: aplica process mining (descoberta, conformance, \
workflow mining, event log analysis, PPM) a artefatos de SW (commits, issues, PR, CI/CD).
IC2 – Modelagem Estocástica em Processos de SW: usa Markov, Monte Carlo, Petri nets \
estocásticas, ou matrizes de transição para modelar processos de desenvolvimento de SW.
IC3 – Forecasting de Métricas de Processo: prevê lead time, cycle time, remaining time, \
throughput ou taxa de defeitos em processos de SW usando dados ou event logs.
IC4 – Mineração de Repositórios para Processo: minera repositórios (GitHub, Jira, VCS) \
para descobrir ou melhorar modelos de processo de desenvolvimento de software.

**CRITÉRIOS DE EXCLUSÃO** (qualquer UM é suficiente para excluir, mesmo com IC atendido):
EC1 – Domínio fora de SW: aplica-se a saúde, manufatura, finanças, etc., sem link a SW.
EC2 – SW como ferramenta: "software" é implementação, não o processo sendo estudado.
EC3 – Algoritmo sem aplicação a processos de SW: método puramente teórico, sem avaliação em SW.
EC4 – Revisão secundária fora do escopo: survey/SLR que não trata PM ou estocástico em SE.

**CASOS INCERTOS (maybe):**
- Título relevante mas sem abstract disponível
- Artigo de BPM genérico que pode (ou não) incluir processos de SW
- Terminologia ambígua (ex: "software" como sistema, não processo)

**TRATAMENTO DE ABSTRACTS AUSENTES:**
- O abstract fornecido vem de fonte bibliográfica verificável ou está ausente.
- Você NUNCA deve inventar, completar ou inferir um abstract ausente.
- Se o resumo estiver ausente ou claramente insuficiente, evite inclusão forte:
  prefira "maybe" salvo se houver evidência inequívoca de exclusão.

**EXTRAÇÃO DE EVIDÊNCIAS (para filtros posteriores):**
Preencha os campos estruturados usando SOMENTE os enums abaixo.

- `evidence_tags`: zero ou mais entre:
  `process_mining`, `software_process`, `repository_mining`, `stochastic_modeling`,
  `forecasting`, `event_log`, `version_control`, `issue_tracking`, `pull_requests`,
  `ci_cd`, `markov`, `hidden_markov_model`, `monte_carlo`, `stochastic_petri_net`,
  `bayesian_model`, `simulation`, `lead_time`, `cycle_time`, `remaining_time`,
  `throughput`, `defect_prediction`, `build_prediction`, `reliability`,
  `insufficient_abstract`, `full_text_required`
- `software_context`: exatamente um entre
  `software_development_process`, `repository_mining`, `ci_cd`,
  `issue_bug_workflow`, `software_testing`, `requirements_engineering`,
  `software_project_management`, `unclear`, `not_software_process`
- `stochastic_method`: exatamente um entre
  `none`, `markov_chain`, `hidden_markov_model`, `monte_carlo`,
  `stochastic_petri_net`, `bayesian_model`, `probabilistic_model`,
  `simulation`, `queueing_model`, `other_stochastic`, `unclear`
- `forecast_target`: exatamente um entre
  `none`, `lead_time`, `cycle_time`, `remaining_time`, `throughput`,
  `defect_rate`, `build_outcome`, `reliability`, `completion_time`,
  `other_process_metric`, `unclear`
- `process_data_source`: exatamente um entre
  `none`, `event_logs`, `version_control`, `issue_tracker`, `pull_requests`,
  `ci_cd_logs`, `software_repository_mixed`, `synthetic_data`,
  `simulated_process`, `survey_or_secondary`, `unclear`
- `confidence`: exatamente um entre `low`, `medium`, `high`

Responda SOMENTE com JSON válido, sem texto adicional."""

# ================================================================== #
#  Prompts de texto completo (fase 2 — full-text screening)         #
# ================================================================== #

FT_SYSTEM_PROMPT = """\
Você é um especialista em revisão sistemática da literatura (SLR) na área de \
process mining e engenharia de software. Sua tarefa é realizar a triagem de \
TEXTO COMPLETO (FT) para a SLR PATHCAST — segunda fase de seleção.

**Escopo da SLR PATHCAST:**
Intersecção entre (1) process mining, (2) modelagem estocástica, \
(3) forecasting/predição e (4) processos de desenvolvimento de software.

**CRITÉRIOS DE INCLUSÃO** (ao menos UM deve ser atendido):
IC1 – Process Mining em Software: aplica process mining (descoberta, conformance, \
workflow mining, event log analysis, PPM) a artefatos de SW (commits, issues, PR, CI/CD).
IC2 – Modelagem Estocástica em Processos de SW: usa Markov, Monte Carlo, Petri nets \
estocásticas, ou matrizes de transição para modelar processos de desenvolvimento de SW.
IC3 – Forecasting de Métricas de Processo: prevê lead time, cycle time, remaining time, \
throughput ou taxa de defeitos em processos de SW usando dados ou event logs.
IC4 – Mineração de Repositórios para Processo: minera repositórios (GitHub, Jira, VCS) \
para descobrir ou melhorar modelos de processo de desenvolvimento de software.

**CRITÉRIOS DE EXCLUSÃO** (qualquer UM é suficiente para excluir):
EC1 – Domínio fora de SW: aplica-se a saúde, manufatura, finanças, etc., sem link a SW.
EC2 – SW como ferramenta: "software" é implementação, não o processo sendo estudado.
EC3 – Algoritmo sem aplicação a processos de SW: método teórico, sem avaliação em SW.
EC4 – Revisão secundária fora do escopo: survey/SLR que não trata PM ou estocástico em SE.

**ESTA É A FASE DE TEXTO COMPLETO — aplique critérios com rigor:**
- Se o resumo confirma claramente ≥1 IC sem EC decisivo → "include"
- Se o resumo confirma claramente que nenhum IC se aplica, ou EC se aplica → "exclude"
- Só use "pending" se o resumo é genuinamente insuficiente para decidir (ex: ausente ou \
  extremamente curto) E o título sugere relevância marginal

Na dúvida entre include e exclude, prefira exclude — esta fase exige confiança.

**TRATAMENTO DE ABSTRACTS AUSENTES:**
- O abstract fornecido vem de fonte bibliográfica verificável ou está ausente.
- Você NUNCA deve inventar, completar ou inferir um abstract ausente.
- Se o resumo estiver ausente ou insuficiente, use `pending` em vez de inclusão forte,
  salvo quando houver evidência inequívoca de exclusão.

**EXTRAÇÃO DE EVIDÊNCIAS (para filtros posteriores):**
Preencha os campos estruturados usando SOMENTE os enums abaixo.

- `evidence_tags`: zero ou mais entre:
  `process_mining`, `software_process`, `repository_mining`, `stochastic_modeling`,
  `forecasting`, `event_log`, `version_control`, `issue_tracking`, `pull_requests`,
  `ci_cd`, `markov`, `hidden_markov_model`, `monte_carlo`, `stochastic_petri_net`,
  `bayesian_model`, `simulation`, `lead_time`, `cycle_time`, `remaining_time`,
  `throughput`, `defect_prediction`, `build_prediction`, `reliability`,
  `insufficient_abstract`, `full_text_required`
- `software_context`: exatamente um entre
  `software_development_process`, `repository_mining`, `ci_cd`,
  `issue_bug_workflow`, `software_testing`, `requirements_engineering`,
  `software_project_management`, `unclear`, `not_software_process`
- `stochastic_method`: exatamente um entre
  `none`, `markov_chain`, `hidden_markov_model`, `monte_carlo`,
  `stochastic_petri_net`, `bayesian_model`, `probabilistic_model`,
  `simulation`, `queueing_model`, `other_stochastic`, `unclear`
- `forecast_target`: exatamente um entre
  `none`, `lead_time`, `cycle_time`, `remaining_time`, `throughput`,
  `defect_rate`, `build_outcome`, `reliability`, `completion_time`,
  `other_process_metric`, `unclear`
- `process_data_source`: exatamente um entre
  `none`, `event_logs`, `version_control`, `issue_tracker`, `pull_requests`,
  `ci_cd_logs`, `software_repository_mixed`, `synthetic_data`,
  `simulated_process`, `survey_or_secondary`, `unclear`
- `confidence`: exatamente um entre `low`, `medium`, `high`

Responda SOMENTE com JSON válido, sem texto adicional."""

FT_PAPER_PROMPT_TEMPLATE = """\
Avalie o paper abaixo para a SLR PATHCAST — triagem de TEXTO COMPLETO (fase 2).

**Título:** {title}

**Resumo:** {abstract}

**Venue/Tipo:** {venue} | {doc_type} | {year}
**Fonte bibliográfica:** {source_db}
**Origem do abstract:** {abstract_source}

**Contexto da triagem T/A (fase 1):**
  - Decisão anterior: {ta_decision}
  - Justificativa anterior: {ta_rationale}
  - ICs identificados na fase 1: {ta_matched_ic}

Reavalie com rigor para a fase de texto completo.
Responda com JSON no formato exato:
{{
  "decision": "include" | "exclude" | "pending",
  "rationale": "<1-2 frases objetivas justificando a decisão com base no conteúdo>",
  "matched_ic": ["IC1"],
  "matched_ec": [],
  "evidence_tags": ["process_mining", "forecasting"],
  "software_context": "software_development_process",
  "stochastic_method": "markov_chain",
  "forecast_target": "remaining_time",
  "process_data_source": "event_logs",
  "confidence": "medium"
}}

Regras:
- "include" se ≥1 IC claramente atendido e nenhum EC decisivo
- "exclude" se EC se aplica OU nenhum IC é atendido (seja conclusivo)
- "pending" SOMENTE se resumo ausente/insuficiente e título sugere possível relevância
- matched_ic e matched_ec devem estar vazios [] quando não aplicáveis
- `evidence_tags` pode ser [] quando não houver evidência confiável
- Use SOMENTE os enums definidos no system prompt
"""

# ================================================================== #
#  Prompts de triagem T/A (fase 1)                                   #
# ================================================================== #

# Template de prompt por paper
PAPER_PROMPT_TEMPLATE = """\
Avalie o paper abaixo para a SLR PATHCAST.

**Título:** {title}

**Resumo:** {abstract}

**Venue/Tipo:** {venue} | {doc_type} | {year}
**Fonte bibliográfica:** {source_db}
**Origem do abstract:** {abstract_source}

Responda com JSON no formato exato:
{{
  "decision": "include" | "exclude" | "maybe",
  "rationale": "<1-2 frases objetivas justificando a decisão>",
  "matched_ic": ["IC1", "IC2"],
  "matched_ec": ["EC1"],
  "evidence_tags": ["process_mining", "forecasting"],
  "software_context": "software_development_process",
  "stochastic_method": "markov_chain",
  "forecast_target": "remaining_time",
  "process_data_source": "event_logs",
  "confidence": "medium"
}}

Regras:
- "include" se ≥1 IC atendido e nenhum EC decisivo
- "exclude" se algum EC se aplica claramente, ou se o paper claramente não atende nenhum IC
- "maybe" se há dúvida real (título sem abstract, ambiguidade de domínio, possível relevância marginal)
- matched_ic e matched_ec devem estar vazios [] quando não aplicáveis
- `evidence_tags` pode ser [] quando não houver evidência confiável
- Use SOMENTE os enums definidos no system prompt
"""


# ================================================================== #
#  Helpers de normalização compartilhados entre screening.py e       #
#  fulltext.py — fonte única de verdade para evitar divergência.     #
# ================================================================== #

import re as _re


def _slugify(value) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    if not text:
        return ""
    text = _re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _normalize_enum(value, allowed: set, *, default: str) -> str:
    token = _slugify(value)
    return token if token in allowed else default


def _normalize_tag_list(value, allowed: set) -> str:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        return ""
    normalized = []
    seen: set = set()
    for item in items:
        token = _slugify(item)
        if token in allowed and token not in seen:
            normalized.append(token)
            seen.add(token)
    return "|".join(normalized)
