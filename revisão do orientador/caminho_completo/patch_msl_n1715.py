#!/usr/bin/env python3
"""Fase 5 rápido: alinhar main.tex/main_pt.tex a n=1715 + fechar Wohlin/D1/D6/ML."""
from __future__ import annotations

import json
import re
from pathlib import Path

DIR = Path(__file__).resolve().parent
MSL = DIR.parent / "MSL___Rodrigo_e_Juliano"
STATS = json.loads((DIR / "phase3_final_stats.json").read_text(encoding="utf-8"))
N = STATS["n"]


def pct(x: float | int, pt: bool = False) -> str:
    s = f"{100 * x / N:.1f}"
    return s.replace(".", ",") if pt else s


def combo_table(pt: bool = False) -> str:
    rows = [
        (r"Apenas \PM{}" if pt else r"\PM{} only", "pm_only", "msr_pm", "med_pm"),
        (r"Apenas \FC{}" if pt else r"\FC{} only", "fc_only", "msr_fc", "med_fc"),
        (r"Apenas \ST{}" if pt else r"\ST{} only", "st_only", "msr_st", "med_st"),
        (r"\ST{} + \FC{}", "st_fc", "msr_st_fc", "med_st_fc"),
        (r"Nenhuma (apenas \MSR{})" if pt else r"None (\MSR{} only)", "none", "msr_none", "med_none"),
        (r"\PM{} + \ST{}", "pm_st_only", "msr_pm_st", "med_pm_st"),
        (r"\PM{} + \FC{}", "pm_fc", "msr_pm_fc", "med_pm_fc"),
        (r"\PM{} + \ST{} + \FC{}", "all3", "msr_all3", "med_all3"),
    ]
    lines = []
    for lab, k, mk, medk in rows:
        lines.append(
            f"{lab} & {STATS[k]} & {pct(STATS[k], pt)} & {STATS[mk]} & {STATS[medk]} \\\\"
        )
    tot = f"Total & {N} & {'100,0' if pt else '100.0'} & {STATS['MSR']} & \\\\"
    return "\n".join(lines) + "\n\\midrule\n" + tot


def levels_table(pt: bool = False) -> str:
    if pt:
        return (
            f"L0 & No máximo uma família de técnica & {STATS['L0']} & {pct(STATS['L0'], True)} \\\\\n"
            f"L1 & Duas famílias de técnica (\\PM{{}}+\\ST{{}} {STATS['pm_st_only']}; "
            f"\\PM{{}}+\\FC{{}} {STATS['pm_fc']}; \\ST{{}}+\\FC{{}} {STATS['st_fc']}) & "
            f"{STATS['L1']} & {pct(STATS['L1'], True)} \\\\\n"
            f"L2 & Três famílias; etapas avaliadas separadamente & {STATS['L2']} & {pct(STATS['L2'], True)} \\\\\n"
            f"L3 & Três famílias acopladas por interfaces especificadas, avaliadas de ponta a ponta & 0 & 0,0 \\\\\n"
            f"\\midrule\nTotal & & {N} & 100,0 \\\\"
        )
    return (
        f"L0 & At most one technique family & {STATS['L0']} & {pct(STATS['L0'])} \\\\\n"
        f"L1 & Two technique families (\\PM{{}}+\\ST{{}} {STATS['pm_st_only']}; "
        f"\\PM{{}}+\\FC{{}} {STATS['pm_fc']}; \\ST{{}}+\\FC{{}} {STATS['st_fc']}) & "
        f"{STATS['L1']} & {pct(STATS['L1'])} \\\\\n"
        f"L2 & Three families; stages evaluated separately & {STATS['L2']} & {pct(STATS['L2'])} \\\\\n"
        f"L3 & Three families coupled through specified interfaces, evaluated end-to-end & 0 & 0.0 \\\\\n"
        f"\\midrule\nTotal & & {N} & 100.0 \\\\"
    )


SNOWBALL_EN = r"""\paragraph{Snowballing}
Wohlin snowballing~\cite{wohlin2014} was run from the included studies after the Phase-3 ML block ($n = 561$; 494 with DOI). Each iteration used the new includes of the previous iteration as seeds. OpenAlex supplied both backward references and forward citations. A residual candidate entered title screening only when its title matched at least one process-mining/stochastic/forecasting term and one software-engineering/repository term (same keyword gate as in the protocol). Iterations and new includes: (1)~401; (2)~627; (3)~120; (4)~6; (5)~0. Saturation was reached at iteration~5 (no keyword-gate pass among 203 new residuals). The snowballing block therefore added 1\,154 studies and brought the corpus to $n = 1715$."""

SNOWBALL_PT = r"""\paragraph{Snowballing}
O snowballing de Wohlin~\cite{wohlin2014} partiu dos estudos incluídos após o bloco ML da Fase~3 ($n = 561$; 494 com DOI). Cada iteração usou como sementes os novos includes da iteração anterior. A OpenAlex forneceu referências (backward) e citações (forward). Um residual entrava na triagem de título só quando o título continha ao menos um termo de mineração de processos/estocástico/previsão e um termo de engenharia de software/repositório (mesmo keyword gate do protocolo). Iterações e novos includes: (1)~401; (2)~627; (3)~120; (4)~6; (5)~0. A saturação ocorreu na iteração~5 (nenhum gate-pass entre 203 residuais novos). O bloco de snowballing acrescentou, portanto, 1\,154 estudos e elevou o corpus a $n = 1715$."""


def patch_en(t: str) -> str:
    s = STATS
    # Abstract
    t = re.sub(
        r"\\textbf\{Results\.\} The corpus contains .*?\(L3\)\.",
        (
            f"\\\\textbf{{Results.}} The corpus contains {N} studies published between 1994 and 2026, all classified "
            f"(435 from the base search, 126 from the Phase-3 ML/forecasting block, and 1\\\\,154 from Wohlin snowballing "
            f"to saturation). Stochastic modelling appears in {s['pct_ST']}\\\\% and process mining in {s['pct_PM']}\\\\%; "
            f"the two lines meet in {s['pm_st']} studies. Forecasting appears in {s['pct_FC']}\\\\% ({s['FC']} studies), "
            f"predominantly as FC-only work ({s['fc_only']}) after snowballing, otherwise mostly paired with stochastic "
            f"models ({s['st_fc']}) rather than process mining ({s['pm_fc_all']}). Two studies carry all three technique "
            f"families (L2); none couples them through specified interfaces evaluated end-to-end (L3)."
        ),
        t,
        count=1,
        flags=re.S,
    )
    t = t.replace(
        f"\\item {N} studies apply process mining, stochastic models or forecasting to SDLC data.",
        f"\\item {N} studies apply process mining, stochastic models or forecasting to SDLC data.",
    )
    t = re.sub(
        rf"meet in \d+ of {N} studies",
        f"meet in {s['pm_st']} of {N} studies",
        t,
    )

    # Close D1 / ML / D6 pendentes (resolved in Phase 3)
    t = re.sub(
        r"\\pendente\{Três strings do Scopus contêm os títulos literais.*?independente\.\}",
        (
            "The three Scopus strings that formerly embedded the literal titles of control studies V6, V8 and V9 "
            "were cleaned and re-run (Phase~3, decision D1=A). Against the de-duplicated pool of 5\\\\,783 unique "
            "records the residual was empty of new includes."
        ),
        t,
        count=1,
        flags=re.S,
    )
    t = re.sub(
        r"\\pendente\{Nenhuma string principal tem bloco de forecasting/ML.*?de vez\.\}",
        (
            "A dedicated forecasting/ML-on-repositories block was run on the five libraries (Phase~3). After "
            "de-duplication against the existing pool and title/abstract screening under D2=B, it contributed "
            "126 new includes. The Scopus supplementary set of 31/10/2026 (19 title-screen candidates) was "
            "triaged in full and contributed no new includes (D6)."
        ),
        t,
        count=1,
        flags=re.S,
    )

    # Snowballing paragraphs (replace both old legacy + partial)
    t = re.sub(
        r"\\paragraph\{Snowballing\}.*?\\pendente\{Completar iterações até saturação.*?\}",
        SNOWBALL_EN,
        t,
        count=1,
        flags=re.S,
    )
    # if pendente already gone but old short text remains
    if "One iteration of backward and forward snowballing was run over 400" in t:
        t = re.sub(
            r"\\paragraph\{Snowballing\}.*?bringing the corpus to \d+\.",
            SNOWBALL_EN,
            t,
            count=1,
            flags=re.S,
        )

    # D2 decision B closed
    t = re.sub(
        r"\\pendente\{IC4b e IC4c, como estão.*?reclassificar\.\}",
        (
            "Under decision D2=B we exclude models of product reliability that are not models of the development "
            "process (explicit EC). Screening in Phase~3 applied that rule; residual product-reliability studies "
            "from the 1997--2013 ST+FC cluster were not re-admitted via the ML block or snowballing when the title "
            "made the product-only scope clear."
        ),
        t,
        count=1,
        flags=re.S,
    )

    # Classification paragraph snowball count
    t = re.sub(
        r"and snowballing iterations~1--\d+ added [\d+]+ studies, bringing the corpus to \d+, all classified\.",
        (
            "and Wohlin snowballing to saturation (iterations~1--5) added 1\\,154 studies "
            f"(401+627+120+6+0), bringing the corpus to {N}, all classified."
        ),
        t,
        count=1,
    )

    # Years
    t = re.sub(
        r"In total, \d+ studies \([0-9.]+\\%\) appeared in 2015--2026\.",
        f"In total, {s['yrs']} studies ({s['pct_yrs']}\\%) appeared in 2015--2026.",
        t,
        count=1,
    )

    # RQ2 family sentence
    t = re.sub(
        rf"Of the {N} studies, \d+ \([0-9.]+\\%\) carry \\ST\{{\}}, \d+ \([0-9.]+\\%\) \\PM\{{\}}, \d+ \([0-9.]+\\%\) \\FC\{{\}}, and \d+ \([0-9.]+\\%\) \\MSR\{{\}}\.",
        (
            f"Of the {N} studies, {s['ST']} ({s['pct_ST']}\\%) carry \\ST{{}}, {s['PM']} ({s['pct_PM']}\\%) \\PM{{}}, "
            f"{s['FC']} ({s['pct_FC']}\\%) \\FC{{}}, and {s['MSR']} ({s['pct_MSR']}\\%) \\MSR{{}}."
        ),
        t,
        count=1,
    )

    # Combo table body
    t = re.sub(
        r"\\PM\{\} only &.*?\\midrule\nTotal & \d+ & 100\.0 & \d+ & \\\\\n",
        combo_table(False) + "\n",
        t,
        count=1,
        flags=re.S,
    )

    # Clusters
    t = re.sub(
        r"Three clusters now structure the corpus\..*?after the ML block and snowballing\.",
        (
            f"Three clusters now structure the corpus. Process mining without stochastic modelling or forecasting "
            f"remains ({s['pm_only']}; {s['msr_pm']} with repositories). Stochastic modelling, alone ({s['st_only']}) "
            f"or paired with forecasting ({s['st_fc']}), still rarely uses mined repository events "
            f"({s['st_cluster_msr']} of {s['st_cluster']}). Forecasting alone is now the dominant cluster "
            f"({s['fc_only']}), mostly on repository or issue data ({s['msr_fc']} with \\MSR{{}}), after the ML "
            f"block and snowballing."
        ),
        t,
        count=1,
        flags=re.S,
    )

    # Levels narrative + table
    t = re.sub(
        r"Table~\\ref\{tab:levels\} gives the integration levels\. Most studies \([0-9.]+\\%\) use at most one technique family; \d+ combine two; .*? none reaches L3\.",
        (
            f"Table~\\ref{{tab:levels}} gives the integration levels. Most studies ({s['pct_L0']}\\%) use at most one "
            f"technique family; {s['L1']} combine two; {s['L2']} combine three; none reaches L3."
        ),
        t,
        count=1,
    )
    t = re.sub(
        r"L0 & At most one technique family.*?Total & & \d+ & 100\.0 \\\\\n",
        levels_table(False) + "\n",
        t,
        count=1,
        flags=re.S,
    )

    # PM+FC sentence (8 two-family + L2 studies that also have PM+FC)
    t = re.sub(
        r"\d+ studies combine \\PM\{\} and \\FC\{\} \(\d+ as a two-family combination, plus the L2 study\)",
        f"{s['pm_fc_all']} studies combine \\PM{{}} and \\FC{{}} ({s['pm_fc']} as a two-family combination, plus the L2 studies)",
        t,
        count=1,
    )

    # Gaps
    t = re.sub(
        r"Three gaps follow from Tables~\\ref\{tab:combos\} and~\\ref\{tab:levels\}\..*?Third, no study evaluates a multi-stage pipeline end-to-end on SDLC data\.",
        (
            f"Three gaps follow from Tables~\\ref{{tab:combos}} and~\\ref{{tab:levels}}. First, the gap is one of "
            f"integration, not of coverage: each family is well represented, but the PM and stochastic lines meet in "
            f"{s['pm_st']} of {N} studies. Second, forecasting is frequent ({s['FC']}), but the PM--forecast link "
            f"remains rare ({s['pm_fc_all']}); stochastic models fed by aggregate statistics still account for "
            f"{s['st_fc']} ST+FC studies, versus structure mined from event logs ({s['pm_fc']}). Third, no study "
            f"evaluates a multi-stage pipeline end-to-end on SDLC data."
        ),
        t,
        count=1,
        flags=re.S,
    )

    # Conclusion
    t = re.sub(
        r"We mapped \d+ studies that apply process mining.*?clearest support in the corpus\.",
        (
            f"We mapped {N} studies that apply process mining, stochastic modelling, or forecasting to software "
            f"development data. The field has been shaped by two communities in succession: stochastic modelling until "
            f"2013 and process mining since 2014; they still meet in only {s['pm_st']} studies. After the Phase-3 ML "
            f"block and snowballing to saturation, forecasting is common ({s['pct_FC']}\\%), largely as FC-only work "
            f"on repository data, while the PM--forecast link remains rare. Two studies carry all three technique "
            f"families (PRIMAD~\cite{{guinea2025}} is the one we read in full for L2/L3); none couples them through "
            f"specified interfaces evaluated end-to-end. The gap is therefore one of integration rather than of "
            f"available techniques. Process-aware stochastic forecasting and end-to-end benchmarks are the two "
            f"directions with the clearest support in the corpus."
        ),
        t,
        count=1,
        flags=re.S,
    )

    # Prisma node already has snowball counts; ensure iter text
    t = t.replace(
        "435+126 ML+401+627+120+6 snowball",
        "435+126 ML+1,154 snowball",
    )
    return t


def patch_pt(t: str) -> str:
    s = STATS
    t = re.sub(
        r"\\textbf\{Resultados\.\} O corpus contém .*?\(L3\)\.",
        (
            f"\\\\textbf{{Resultados.}} O corpus contém {N} estudos publicados entre 1994 e 2026, todos classificados "
            f"(435 da busca-base, 126 do bloco ML/previsão da Fase~3 e 1\\\\,154 do snowballing de Wohlin até saturação). "
            f"A modelagem estocástica aparece em {pct(s['ST'], True)}\\\\% e a mineração de processos em "
            f"{pct(s['PM'], True)}\\\\%; as duas linhas se encontram em {s['pm_st']} estudos. A previsão aparece em "
            f"{pct(s['FC'], True)}\\\\% ({s['FC']} estudos), predominantemente só-FC ({s['fc_only']}) após o "
            f"snowballing e, nos demais casos, sobretudo associada a modelos estocásticos ({s['st_fc']}) e raramente "
            f"à mineração de processos ({s['pm_fc_all']}). Dois estudos carregam as três famílias de técnica (L2); "
            f"nenhum as acopla por meio de interfaces especificadas e avaliadas de ponta a ponta (L3)."
        ),
        t,
        count=1,
        flags=re.S,
    )
    t = re.sub(
        rf"se encontram em \d+ dos {N} estudos",
        f"se encontram em {s['pm_st']} dos {N} estudos",
        t,
    )

    t = re.sub(
        r"\\pendente\{Três strings do Scopus contêm os títulos literais.*?independente\.\}",
        (
            "As três strings do Scopus que embutiam os títulos literais dos estudos de controle V6, V8 e V9 foram "
            "limpas e reexecutadas (Fase~3, decisão D1=A). Contra o pool deduplicado de 5\\\\,783 registros únicos, "
            "o residual não trouxe novos includes."
        ),
        t,
        count=1,
        flags=re.S,
    )
    t = re.sub(
        r"\\pendente\{Nenhuma string principal tem bloco de forecasting/ML.*?de vez\.\}",
        (
            "Um bloco dedicado de forecasting/ML sobre repositórios foi executado nas cinco bases (Fase~3). Após "
            "deduplicação contra o pool existente e triagem título/resumo sob D2=B, contribuiu com 126 novos "
            "includes. O conjunto suplementar do Scopus de 31/10/2026 (19 candidatos por título) foi triado por "
            "completo e não acrescentou includes (D6)."
        ),
        t,
        count=1,
        flags=re.S,
    )

    t = re.sub(
        r"\\paragraph\{Snowballing\}.*?\\pendente\{Completar iterações até saturação.*?\}",
        SNOWBALL_PT,
        t,
        count=1,
        flags=re.S,
    )
    if "Uma iteração de snowballing" in t or "400 DOIs" in t:
        t = re.sub(
            r"\\paragraph\{Snowballing\}.*?elevando o corpus a \d+\.",
            SNOWBALL_PT,
            t,
            count=1,
            flags=re.S,
        )

    t = re.sub(
        r"\\pendente\{IC4b e IC4c, como estão.*?reclassificar\.\}",
        (
            "Na decisão D2=B excluímos modelos de confiabilidade do produto que não modelam o processo de "
            "desenvolvimento (EC explícito). A triagem da Fase~3 aplicou essa regra; estudos só-produto do "
            "aglomerado ST+FC de 1997--2013 não foram readmitidos pelo bloco ML nem pelo snowballing quando o "
            "título tornava o escopo de produto evidente."
        ),
        t,
        count=1,
        flags=re.S,
    )

    t = re.sub(
        r"e as iterações~1--\d+ do snowballing acrescentaram [\d+]+ estudos, elevando o corpus a \d+, todos classificados\.",
        (
            f"e o snowballing de Wohlin até saturação (iterações~1--5) acrescentou 1\\,154 estudos "
            f"(401+627+120+6+0), elevando o corpus a {N}, todos classificados."
        ),
        t,
        count=1,
    )

    t = re.sub(
        r"No total, \d+ estudos \([0-9,]+\\%\) foram publicados entre 2015 e 2026\.",
        f"No total, {s['yrs']} estudos ({pct(s['yrs'], True)}\\%) foram publicados entre 2015 e 2026.",
        t,
        count=1,
    )

    t = re.sub(
        rf"Dos {N} estudos, \d+ \([0-9,]+\\%\) têm \\ST\{{\}}, \d+ \([0-9,]+\\%\) \\PM\{{\}}, \d+ \([0-9,]+\\%\) \\FC\{{\}} e \d+ \([0-9,]+\\%\) \\MSR\{{\}}\.",
        (
            f"Dos {N} estudos, {s['ST']} ({pct(s['ST'], True)}\\%) têm \\ST{{}}, {s['PM']} ({pct(s['PM'], True)}\\%) "
            f"\\PM{{}}, {s['FC']} ({pct(s['FC'], True)}\\%) \\FC{{}} e {s['MSR']} ({pct(s['MSR'], True)}\\%) \\MSR{{}}."
        ),
        t,
        count=1,
    )

    t = re.sub(
        r"Apenas \\PM\{\} &.*?\\midrule\nTotal & \d+ & 100,0 & \d+ & \\\\\n",
        combo_table(True) + "\n",
        t,
        count=1,
        flags=re.S,
    )

    t = re.sub(
        r"Três agrupamentos estruturam agora o corpus\..*?após o bloco ML e o snowballing\.",
        (
            f"Três agrupamentos estruturam agora o corpus. A mineração de processos sem modelagem estocástica nem "
            f"previsão permanece ({s['pm_only']}; {s['msr_pm']} com repositórios). A modelagem estocástica, isolada "
            f"({s['st_only']}) ou pareada à previsão ({s['st_fc']}), ainda raramente usa eventos minerados de "
            f"repositórios ({s['st_cluster_msr']} de {s['st_cluster']}). A previsão isolada é agora o agrupamento "
            f"dominante ({s['fc_only']}), sobretudo sobre dados de repositório ou de issues ({s['msr_fc']} com "
            f"\\MSR{{}}), após o bloco ML e o snowballing."
        ),
        t,
        count=1,
        flags=re.S,
    )

    t = re.sub(
        r"A Tabela~\\ref\{tab:levels\} apresenta os níveis de integração\. A maioria dos estudos \([0-9,]+\\%\) usa no máximo uma família de técnica; \d+ combinam duas; .*? nenhum alcança L3\.",
        (
            f"A Tabela~\\ref{{tab:levels}} apresenta os níveis de integração. A maioria dos estudos "
            f"({pct(s['L0'], True)}\\%) usa no máximo uma família de técnica; {s['L1']} combinam duas; "
            f"{s['L2']} combinam três; nenhum alcança L3."
        ),
        t,
        count=1,
    )
    t = re.sub(
        r"L0 & No máximo uma família de técnica.*?Total & & \d+ & 100,0 \\\\\n",
        levels_table(True) + "\n",
        t,
        count=1,
        flags=re.S,
    )

    t = re.sub(
        r"\d+ estudos combinam \\PM\{\} e \\FC\{\} \(\d+ como combinação de duas famílias, mais o estudo L2\)",
        f"{s['pm_fc_all']} estudos combinam \\PM{{}} e \\FC{{}} ({s['pm_fc']} como combinação de duas famílias, mais os estudos L2)",
        t,
        count=1,
    )

    t = re.sub(
        r"Três lacunas decorrem das Tabelas~\\ref\{tab:combos\} e~\\ref\{tab:levels\}\..*?Terceiro, nenhum estudo avalia um pipeline de múltiplas etapas de ponta a ponta em dados do SDLC\.",
        (
            f"Três lacunas decorrem das Tabelas~\\ref{{tab:combos}} e~\\ref{{tab:levels}}. Primeiro, a lacuna é de "
            f"integração, não de cobertura: cada família está bem representada, mas as linhas de PM e estocástica se "
            f"encontram em {s['pm_st']} de {N} estudos. Segundo, a previsão é frequente ({s['FC']}), mas o elo "
            f"PM--previsão permanece raro ({s['pm_fc_all']}); modelos estocásticos alimentados por estatísticas "
            f"agregadas ainda respondem por {s['st_fc']} estudos ST+FC, contra estrutura minerada de logs de eventos "
            f"({s['pm_fc']}). Terceiro, nenhum estudo avalia um pipeline de múltiplas etapas de ponta a ponta em "
            f"dados do SDLC."
        ),
        t,
        count=1,
        flags=re.S,
    )

    t = re.sub(
        r"Mapeamos \d+ estudos que aplicam mineração de processos.*?apoio mais claro no corpus\.",
        (
            f"Mapeamos {N} estudos que aplicam mineração de processos, modelagem estocástica ou previsão a dados de "
            f"desenvolvimento de software. A área foi moldada por duas comunidades em sucessão: a modelagem "
            f"estocástica até 2013 e a mineração de processos desde 2014; elas ainda se encontram em apenas "
            f"{s['pm_st']} estudos. Após o bloco ML da Fase~3 e o snowballing até saturação, a previsão é comum "
            f"({pct(s['FC'], True)}\\%), sobretudo como trabalho só-FC sobre dados de repositório, enquanto o elo "
            f"PM--previsão permanece raro. Dois estudos carregam as três famílias de técnica (PRIMAD~\\cite{{guinea2025}} "
            f"é o que lemos por completo para L2/L3); nenhum as acopla por meio de interfaces especificadas e "
            f"avaliadas de ponta a ponta. A lacuna é, portanto, de integração, e não de técnicas disponíveis. A "
            f"previsão estocástica orientada a processos e os \\emph{{benchmarks}} de ponta a ponta são as duas "
            f"direções com apoio mais claro no corpus."
        ),
        t,
        count=1,
        flags=re.S,
    )

    t = t.replace(
        "435+126 ML+401+627+120+6 snowball",
        "435+126 ML+1.154 snowball",
    )
    return t


def main() -> None:
    en_path = MSL / "main.tex"
    pt_path = MSL / "main_pt.tex"
    en = patch_en(en_path.read_text(encoding="utf-8"))
    pt = patch_pt(pt_path.read_text(encoding="utf-8"))
    en_path.write_text(en, encoding="utf-8")
    pt_path.write_text(pt, encoding="utf-8")
    for label, text in [("EN", en), ("PT", pt)]:
        n_pend = len(re.findall(r"\\pendente\{", text))
        print(label, "pendente=", n_pend, "Wohlin sat" , "saturation" in text.lower() or "saturação" in text.lower())


if __name__ == "__main__":
    main()
