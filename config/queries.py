"""
Search strings para SLR PATHCAST — todas as bases.
Versão validada em 10/04/2026 (Scopus principal: 1.628 resultados).

Estrutura:
    QUERIES[database] = [
        {"id": str, "label": str, "query": str, "notes": str},
        ...
    ]
"""

QUERIES = {

    # ------------------------------------------------------------------ #
    #  SCOPUS                                                             #
    # ------------------------------------------------------------------ #
    "scopus": [
        {
            "id": "scopus_principal",
            "label": "Principal",
            "notes": "Validada: 1.628 resultados em 10/04/2026",
            "query": """TITLE-ABS-KEY(
  ("software engineering" OR "software development" OR "software process"
   OR "software lifecycle" OR "SDLC" OR "DevOps" OR "CI/CD"
   OR "continuous integration" OR "agile development"
   OR "issue tracking" OR "version control" OR "code review"
   OR "pull request" OR "software repository" OR "software evolution")
  AND
  (
    "process mining" OR "process discovery" OR "conformance checking"
    OR "workflow mining" OR "predictive process monitoring"
    OR "event log analysis" OR "process intelligence"

    OR ("Monte Carlo simulation" AND ("software" OR "process mining"
        OR "throughput" OR "lead time"))

    OR ("Markov chain" AND ("software" OR "process mining"
        OR "workflow" OR "development process"))

    OR (("stochastic model" OR "transition probability" OR "absorbing chain")
        AND ("software" OR "process mining"))

    OR (("remaining time prediction" OR "outcome prediction"
        OR "cycle time prediction" OR "lead time prediction") AND "software")

    OR ("event log" AND ("software" OR "repository" OR "JIRA" OR "GitHub"))
  )
)
AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp"))
AND LIMIT-TO(LANGUAGE, "English")""",
        },
        {
            "id": "scopus_complementar",
            "label": "Complementar (MSR → Process Modeling)",
            "notes": "Captura estudos MSR sem terminologia canônica de PM",
            "query": """TITLE-ABS-KEY(
  ("mining software repositories" OR "software repository mining"
   OR "software archaeology" OR "mining commit logs"
   OR "GitHub mining" OR "Jira mining")
  AND
  ("process model" OR "workflow" OR "state transition"
   OR "Markov" OR "Monte Carlo" OR "stochastic"
   OR "lead time" OR "cycle time" OR "throughput"
   OR "transition matrix" OR "sojourn time")
)
AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp"))
AND LIMIT-TO(LANGUAGE, "English")""",
        },
        {
            "id": "scopus_markov_testing",
            "label": "Markov + Software Testing (focal V6)",
            "notes": "Busca cirúrgica para Whittaker & Thomason (1994) e vizinhança, evitando Markov em saúde/economia",
            "query": """TITLE-ABS-KEY(
  (
    ("Markov chain" OR "Markov model")
    AND
    ("statistical software testing" OR "software testing" OR "software reliability")
  )
  OR
  (
    "A Markov chain model for statistical software testing"
  )
)
AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp"))
AND LIMIT-TO(LANGUAGE, "English")""",
        },
        {
            "id": "scopus_stochastic_petri",
            "label": "Stochastic Petri Net + Remaining Time (focal V8)",
            "notes": "Busca focal para remaining/service execution time em BPM, sem abrir para stochastic genérico",
            "query": """TITLE-ABS-KEY(
  (
    ("stochastic Petri net" OR "stochastic workflow net" OR "GSPN")
    AND
    ("remaining service time" OR "service execution time" OR "remaining time")
  )
  OR
  (
    "Prediction of Remaining Service Execution Time Using Stochastic Petri Nets with Arbitrary Firing Delays"
  )
)
AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp"))
AND LIMIT-TO(LANGUAGE, "English")""",
        },
        {
            "id": "scopus_simulation_bridge",
            "label": "Process Mining + Simulation Models (focal V9)",
            "notes": "Busca focal para a ponte PM→simulation, exigindo contexto de process mining/process discovery",
            "query": """TITLE-ABS-KEY(
  (
    ("process mining" OR "process discovery" OR "workflow mining")
    AND
    ("simulation model" OR "simulation models" OR "process simulation"
     OR "discovering simulation models" OR "colored Petri")
    AND
    ("event log" OR "process model" OR "business process")
  )
  OR
  (
    "Discovering Simulation Models"
  )
)
AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp"))
AND LIMIT-TO(LANGUAGE, "English")""",
        },
        {
            "id": "scopus_fronteira",
            "label": "Fronteira (Stochastic + PM + SE)",
            "notes": "Corrigida v2: termos genéricos qualificados com contexto SE",
            "query": """TITLE-ABS-KEY(
  ("Monte Carlo" OR "Markov chain" OR "stochastic simulation"
   OR "probabilistic forecast" OR "stochastic model"
   OR "absorbing Markov" OR "transition matrix")
  AND
  ("process mining" OR "event log" OR "workflow mining"
   OR "process model" OR "business process")
  AND
  ("software development" OR "software engineering" OR "software process"
   OR "DevOps" OR "SDLC" OR "issue tracker" OR "commit log"
   OR "build pipeline")
)
AND PUBYEAR > 1993 AND PUBYEAR < 2027
AND (LIMIT-TO(DOCTYPE, "ar") OR LIMIT-TO(DOCTYPE, "cp"))
AND LIMIT-TO(LANGUAGE, "English")""",
        },
    ],

    # ------------------------------------------------------------------ #
    #  IEEE XPLORE                                                        #
    # ------------------------------------------------------------------ #
    "ieee": [
        {
            "id": "ieee_exec1",
            "label": "Execução 1: PM Core + SE",
            "notes": "311 artigos em 10/04/2026",
            "query": (
                '("process mining" OR "conformance checking" OR "process discovery"'
                ' OR "workflow mining" OR "event log analysis"'
                ' OR "predictive process monitoring")'
                ' AND'
                ' ("software engineering" OR "software development"'
                ' OR "software process" OR "SDLC"'
                ' OR "DevOps" OR "continuous integration"'
                ' OR "agile development")'
            ),
        },
        {
            "id": "ieee_exec2",
            "label": "Execução 2: Stochastic qualificado + SE",
            "notes": "v2: adicionado 'software testing' no grupo secundário (captura V6)",
            "query": (
                '(("Monte Carlo simulation" OR "Markov chain"'
                ' OR "stochastic process model" OR "process simulation")'
                ' AND'
                ' ("software" OR "process mining" OR "throughput" OR "lead time"))'
                ' AND'
                ' ("software engineering" OR "software development"'
                ' OR "software process" OR "SDLC" OR "software testing")'
            ),
        },
        {
            "id": "ieee_exec3",
            "label": "Execução 3: Forecasting Terms qualificado + SE",
            "notes": "25 artigos em 10/04/2026",
            "query": (
                '(("remaining time prediction" OR "lead time prediction"'
                ' OR "cycle time prediction" OR "process forecasting"'
                ' OR "outcome prediction" OR "event log construction")'
                ' AND "software")'
                ' AND'
                ' ("software engineering" OR "software development"'
                ' OR "software process")'
            ),
        },
        {
            "id": "ieee_exec4",
            "label": "Execução 4: MSR + Process Modeling (Complementar)",
            "notes": "v2: adicionado 'process mining' no grupo secundário (captura V10)",
            "query": (
                '("mining software repositories" OR "software repository mining"'
                ' OR "software archaeology" OR "mining commit logs"'
                ' OR "GitHub mining" OR "Jira mining")'
                ' AND'
                ' ("process model" OR "workflow" OR "state transition"'
                ' OR "Markov" OR "Monte Carlo" OR "stochastic"'
                ' OR "process mining" OR "process analysis")'
            ),
        },
    ],

    # ------------------------------------------------------------------ #
    #  SPRINGER LINK                                                       #
    # ------------------------------------------------------------------ #
    "springer": [
        {
            "id": "springer_1",
            "label": "process mining + software development",
            "notes": "Busca 1",
            "query": '"process mining" "software development"',
        },
        {
            "id": "springer_2",
            "label": "process mining + software process",
            "notes": "Busca 2",
            "query": '"process mining" "software process"',
        },
        {
            "id": "springer_3",
            "label": "process mining + software engineering",
            "notes": "Busca 3",
            "query": '"process mining" "software engineering"',
        },
        {
            "id": "springer_4",
            "label": "Markov chain + software process",
            "notes": "Busca 4",
            "query": '"Markov chain" "software process"',
        },
        {
            "id": "springer_5",
            "label": "Monte Carlo + software process",
            "notes": "Busca 5",
            "query": '"Monte Carlo" "software process"',
        },
        {
            "id": "springer_6",
            "label": "mining software repositories + process model",
            "notes": "Busca 6",
            "query": '"mining software repositories" "process model"',
        },
        {
            "id": "springer_7",
            "label": "stochastic + software process + event log",
            "notes": "Busca 7",
            "query": '"stochastic" "software process" "event log"',
        },
        {
            "id": "springer_8",
            "label": "predictive process monitoring + software",
            "notes": "Busca 8",
            "query": '"predictive process monitoring" "software"',
        },
        {
            "id": "springer_9",
            "label": "conformance checking + software development",
            "notes": "Busca 9",
            "query": '"conformance checking" "software development"',
        },
        {
            "id": "springer_10",
            "label": "workflow mining + software",
            "notes": "Busca 10",
            "query": '"workflow mining" "software"',
        },
        {
            "id": "springer_11",
            "label": "statistical software testing + Markov chain",
            "notes": "Busca focal para V6 sem abrir demais o ruído",
            "query": '"statistical software testing" "Markov chain"',
        },
        {
            "id": "springer_12",
            "label": "stochastic Petri net + remaining service time",
            "notes": "Busca focal para V8",
            "query": '"stochastic Petri net" "remaining service time"',
        },
        {
            "id": "springer_13",
            "label": "discovering simulation models + process mining",
            "notes": "Busca focal para V9",
            "query": '"discovering simulation models" "process mining"',
        },
    ],

    # ------------------------------------------------------------------ #
    #  ACM DIGITAL LIBRARY — sem API pública                             #
    #  Use: manual_import com arquivos BibTeX exportados do site          #
    # ------------------------------------------------------------------ #
    "acm": [
        {
            "id": "acm_principal",
            "label": "Principal",
            "notes": "Exportar manualmente do ACM DL como BibTeX e importar via: python main.py import acm --file <arquivo.bib>",
            "query": (
                '(Abstract:"process mining" OR Abstract:"conformance checking"'
                ' OR Abstract:"process discovery" OR Abstract:"workflow mining"'
                ' OR Abstract:"event log analysis" OR Abstract:"process intelligence"'
                ' OR Abstract:"predictive process monitoring")'
                ' AND'
                ' (Abstract:"software engineering" OR Abstract:"software development"'
                ' OR Abstract:"software process" OR Abstract:"SDLC"'
                ' OR Abstract:"DevOps" OR Abstract:"continuous integration"'
                ' OR Abstract:"agile development" OR Abstract:"issue tracking"'
                ' OR Abstract:"software repository" OR Abstract:"software project")'
            ),
        },
        {
            "id": "acm_complementar",
            "label": "Complementar (Stochastic qualificado)",
            "notes": "Exportar manualmente do ACM DL como BibTeX e importar",
            "query": (
                '((Abstract:"Monte Carlo" OR Abstract:"Markov chain"'
                ' OR Abstract:"stochastic model" OR Abstract:"process simulation"'
                ' OR Abstract:"stochastic Petri net")'
                ' AND'
                ' (Abstract:"software" OR Abstract:"process mining"'
                ' OR Abstract:"throughput" OR Abstract:"lead time"))'
                ' AND'
                ' (Abstract:"software engineering" OR Abstract:"software development"'
                ' OR Abstract:"software process" OR Abstract:"SDLC"'
                ' OR Abstract:"software testing")'
            ),
        },
        {
            "id": "acm_msr",
            "label": "Complementar MSR",
            "notes": "Exportar manualmente do ACM DL como BibTeX e importar",
            "query": (
                '(Abstract:"mining software repositories"'
                ' OR Abstract:"software repository mining"'
                ' OR Abstract:"software archaeology"'
                ' OR Abstract:"GitHub mining" OR Abstract:"Jira mining")'
                ' AND'
                ' (Abstract:"process model" OR Abstract:"workflow"'
                ' OR Abstract:"state transition" OR Abstract:"Markov"'
                ' OR Abstract:"Monte Carlo" OR Abstract:"lead time"'
                ' OR Abstract:"cycle time" OR Abstract:"throughput"'
                ' OR Abstract:"process mining" OR Abstract:"process analysis")'
            ),
        },
    ],

    # ------------------------------------------------------------------ #
    #  WEB OF SCIENCE — requer acesso institucional                       #
    #  Use: manual_import com arquivos RIS/TXT exportados                 #
    # ------------------------------------------------------------------ #
    "wos": [
        {
            "id": "wos_principal",
            "label": "Principal",
            "notes": "Exportar do WoS como RIS e importar via: python main.py import wos --file <arquivo.ris>",
            "query": (
                'TS=("process mining" OR "process discovery" OR "conformance checking"'
                '    OR "workflow mining" OR "event log analysis" OR "process intelligence"'
                '    OR "predictive process monitoring")'
                ' AND'
                ' TS=("software engineering" OR "software development" OR "software process"'
                '    OR "SDLC" OR "DevOps" OR "continuous integration" OR "agile development"'
                '    OR "issue tracking" OR "code review" OR "software project"'
                '    OR "software repository" OR "software maintenance"'
                '    OR "software evolution")'
            ),
        },
        {
            "id": "wos_complementar",
            "label": "Complementar (Stochastic qualificado)",
            "notes": "Exportar do WoS como RIS e importar",
            "query": (
                'TS=(("Monte Carlo simulation" OR "Markov chain" OR "stochastic model"'
                '     OR "transition probability" OR "absorbing chain" OR "process simulation")'
                '    AND ("software" OR "process mining" OR "workflow" OR "throughput"))'
                ' AND'
                ' TS=("software engineering" OR "software development" OR "software process"'
                '    OR "SDLC" OR "DevOps")'
            ),
        },
        {
            "id": "wos_msr",
            "label": "Complementar MSR",
            "notes": "Exportar do WoS como RIS e importar",
            "query": (
                'TS=("mining software repositories" OR "software repository mining"'
                '    OR "software archaeology" OR "mining commit logs"'
                '    OR "GitHub mining" OR "Jira mining")'
                ' AND'
                ' TS=("process model" OR "workflow" OR "state transition"'
                '    OR "Markov" OR "Monte Carlo" OR "stochastic"'
                '    OR "lead time" OR "cycle time" OR "throughput"'
                '    OR "transition matrix" OR "sojourn time")'
            ),
        },
        {
            "id": "wos_fronteira",
            "label": "Fronteira",
            "notes": "Exportar do WoS como RIS e importar",
            "query": (
                'TS=("Monte Carlo" OR "Markov chain" OR "stochastic simulation"'
                '    OR "probabilistic forecast" OR "stochastic model"'
                '    OR "absorbing Markov" OR "transition matrix")'
                ' AND'
                ' TS=("process mining" OR "event log" OR "workflow mining"'
                '    OR "process model" OR "business process")'
                ' AND'
                ' TS=("software development" OR "software engineering"'
                '    OR "software process" OR "DevOps" OR "SDLC"'
                '    OR "issue tracker" OR "commit log" OR "build pipeline")'
            ),
        },
    ],
}

# Quais bancos suportam extração automática via API
API_ENABLED = {"scopus", "ieee", "springer", "wos"}

# Quais bancos requerem importação manual de arquivo
MANUAL_IMPORT = {"acm"}
