"""
Gera parágrafos de síntese para cap3_SLR.tex usando LLM.

Agrupa os 33 papers do top-30 + 3 seminais por cluster IC e chama
claude-sonnet-4-6 para produzir um parágrafo LaTeX revisável por cluster.

Saída: results/final_review/cap3_synthesis_v2.tex

Uso:
  python pipeline/synth_llm.py
  python pipeline/synth_llm.py --dry-run   # mostra prompt do primeiro cluster
"""
from __future__ import annotations

import csv
import os
import sys
import textwrap
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOP30_CSV  = Path("results/final_review/top30_reading_list.csv")
EXTRACT_CSV = Path("results/extraction/extraction_template.csv")
OUTPUT_TEX  = Path("results/final_review/cap3_synthesis_v2.tex")

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048

# ── Cluster definitions ───────────────────────────────────────────────────────

CLUSTERS = [
    {
        "id": "seminal",
        "label": "Seminal arc (IC1 origins)",
        "filter": lambda ics: any(
            x in ["cook1995", "cook1998", "rubin2007"]
            for x in []  # matched by internal_id below
        ),
        "internal_ids": {"87bce30b", "07e55287", "3ddbfd94"},  # Cook95, Cook98, Rubin07
        "tex_comment": "% ANCHOR PARAGRAPH — seminal arc\n"
            "% INSERT at start of \\subsubsection{RQ2.1} or \\subsection{Results/Synthesis}",
        "instruction": (
            "Write ONE cohesive opening paragraph (5-7 sentences) that traces the seminal arc "
            "from Cook & Wolf through Rubin et al., establishing why these works define the "
            "canonical origin of process mining applied to software processes. "
            "Emphasize that Cook & Wolf discovered processes automatically from event traces "
            "and that Rubin et al. first named and applied a process mining framework to SDLC logs."
        ),
    },
    {
        "id": "ic2_ic3",
        "label": "IC2+IC3 — Stochastic techniques for SW forecasting (14 papers in full set)",
        "internal_ids": None,  # all papers with IC2 AND IC3
        "tex_comment": (
            "% IC2+IC3 BLOCK — Stochastic techniques\n"
            "% REPLACES paragraph starting 'The PDF analysis sharpens the stochastic-method picture.'\n"
            "% in \\subsubsection{RQ2.2: Predictive and Stochastic Techniques}"
        ),
        "instruction": (
            "Write TWO paragraphs synthesizing the stochastic-technique sub-families visible in these papers. "
            "Paragraph 1: describe the three sub-families — Markov-chain-based prediction, stochastic Petri nets, "
            "and Monte Carlo simulation — with specific paper examples for each. "
            "Paragraph 2: identify the consistent limitation across all three sub-families: "
            "they parametrize stochastic models from aggregate statistics rather than from mined "
            "transition structures, leaving model states at coarse lifecycle phases. "
            "State this explicitly as the operational definition of Finding F3. "
            "Use \\cite{key} with author-based keys (e.g., \\cite{joshi2024}, \\cite{bhadra2022})."
        ),
    },
    {
        "id": "ic1_ic2",
        "label": "IC1+IC2 — PM + stochastic integration (PRIMAD, Incerto, López-Pintado, Jalote)",
        "internal_ids": None,  # all papers with IC1 AND IC2 (no IC3)
        "tex_comment": (
            "% IC1+IC2 BLOCK — PM+stochastic integration\n"
            "% APPEND after IC2+IC3 block in \\subsubsection{RQ2.2}"
        ),
        "instruction": (
            "Write TWO paragraphs. "
            "Paragraph 1: synthesize the three papers that combine PM and stochastic analysis "
            "(Incerto VLMCs for conformance, López-Pintado stochastic calendars, Jalote IDE logs). "
            "Paragraph 2: introduce PRIMAD (Guinea-Cabrera) as the single study approaching L3 integration "
            "(pm4py + Akka + LightGBM), then explain why it remains at L2: component-level validation only, "
            "no formal inter-stage contracts, no Monte Carlo layer. "
            "Conclude that L3 remains unoccupied. "
            "Use \\cite{key} with author-based keys."
        ),
    },
    {
        "id": "ic1_ic3",
        "label": "IC1+IC3 — PM + forecasting, sequential integration (Gupta, Caldeira, Pourbafrani, Buliga)",
        "internal_ids": None,  # all papers with IC1 AND IC3 (no IC2)
        "tex_comment": (
            "% IC1+IC3 BLOCK — PM+forecasting (sequential)\n"
            "% APPEND after IC1+IC2 block in \\subsubsection{RQ2.2}"
        ),
        "instruction": (
            "Write TWO paragraphs. "
            "Paragraph 1: synthesize this cluster — Gupta (inductive miner + predictive analytics for maintenance), "
            "Pourbafrani/SIMPT (process tree + what-if simulation), Buliga (generative AI + process simulation), "
            "Caldeira (IDE logs + process complexity → cyclomatic complexity correlation r≈0.43). "
            "Paragraph 2: draw the cluster conclusion — PM and prediction are being connected but always as "
            "sequential application, not a unified pipeline with formal contracts; none can express "
            "'probability of completion within k cycles' as a first-class output. "
            "Use \\cite{key} with author-based keys."
        ),
    },
    {
        "id": "ic2_ic4",
        "label": "IC2+IC4 — GitHub repo Markov models (Jo 2023, Jo 2024, Ortu 2023)",
        "internal_ids": None,  # all papers with IC2 AND IC4
        "tex_comment": (
            "% IC2+IC4 BLOCK — Event log sources for Markov models\n"
            "% INSERT at end of \\subsubsection{RQ1.2: Event Log Sources and Construction}"
        ),
        "instruction": (
            "Write ONE paragraph (5-6 sentences) about these studies that construct Markov models "
            "directly from GitHub commit/collaboration traces without an explicit PM step. "
            "Cover Jo et al. (2023, 2024) — discrete-time Markov chains + probabilistic CTL model checking "
            "across five repositories — and Ortu et al. (2023) — Markov + social network analysis of "
            "fault-insertion/fixing patterns in Apache projects. "
            "Conclude that SDLC event logs from public repositories are rich enough for state-transition modelling "
            "(prerequisite for PATHCAST Stage 1), but that the event-to-state mapping is an unstandardised "
            "methodological contribution. "
            "Use \\cite{key} with author-based keys."
        ),
    },
    {
        "id": "rq3_1",
        "label": "RQ3.1 — Integration level mapping over top-33 papers",
        "internal_ids": None,  # all top-33 papers
        "tex_comment": (
            "% RQ3.1 UPDATE — Integration level over top-33\n"
            "% REPLACES/EXTENDS paragraph on integration levels in \\subsubsection{RQ3.1}"
        ),
        "instruction": (
            "Write ONE paragraph (6-8 sentences) mapping the top-ranked papers onto the L0-L3 scale. "
            "State: IC2+IC3 cluster (14 papers) → almost entirely L1; "
            "IC1+IC2 cluster (4 papers) → two highest-integration examples (Incerto, López-Pintado) reach L2; "
            "IC1+IC3 cluster → PM describes/assesses but lacks stochastic layer for distributional forecasts; "
            "PRIMAD → assembles elements from all ICs but evaluation is component-wise (L2). "
            "Conclude unambiguously: the space of L3 systems — "
            "PM → Markov → MC → ML architectures validated on SDLC data — is empty in the current literature, "
            "and PATHCAST is proposed as its first inhabitant. "
            "Use \\cite{key} with author-based keys."
        ),
    },
]


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_csv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";") if p.name.endswith(".csv")
                    else csv.DictReader(fh))


def _load_extraction() -> dict[str, dict]:
    with open(EXTRACT_CSV, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {r["internal_id"]: r for r in rows}


def _load_top33() -> list[dict]:
    with open(TOP30_CSV, encoding="utf-8-sig", newline="") as fh:
        content = fh.read()
    sep = ";" if content.count(";") > content.count(",") else ","
    import io
    rows = list(csv.DictReader(io.StringIO(content), delimiter=sep))
    return rows


def _select_cluster(top33: list[dict], ext: dict[str, dict], cluster: dict) -> list[dict]:
    if cluster["internal_ids"]:
        # fixed set
        selected = [r for r in top33 if r["internal_id"] in cluster["internal_ids"]]
        # also add from ext if not in top33
        for iid in cluster["internal_ids"]:
            if iid not in {r["internal_id"] for r in selected}:
                if iid in ext:
                    selected.append(ext[iid])
        return selected

    # filter by IC cluster
    cid = cluster["id"]
    result = []
    for row in top33:
        ics = row.get("ft_matched_ic", "")
        if cid == "ic2_ic3" and "IC2" in ics and "IC3" in ics:
            result.append(row)
        elif cid == "ic1_ic2" and "IC1" in ics and "IC2" in ics:
            result.append(row)
        elif cid == "ic1_ic3" and "IC1" in ics and "IC3" in ics and "IC2" not in ics:
            result.append(row)
        elif cid == "ic2_ic4" and "IC2" in ics and "IC4" in ics:
            result.append(row)
        elif cid == "rq3_1":
            result.append(row)  # all papers
    return result


def _paper_summary(row: dict, ext: dict[str, dict]) -> str:
    iid = row.get("internal_id", "")
    e = ext.get(iid, row)
    title = row.get("title") or e.get("title", "")
    authors = row.get("authors") or e.get("authors", "")
    year = row.get("year") or e.get("year", "")
    ics = row.get("ft_matched_ic") or e.get("ft_matched_ic", "")
    pm = row.get("pm_technique") or e.get("pm_technique", "")
    stoch = row.get("stochastic_technique") or e.get("stochastic_technique", "")
    contrib = row.get("research_contribution") or e.get("research_contribution", "")
    finding = row.get("main_finding") or e.get("main_finding", "")
    doi = row.get("doi") or e.get("doi", "")
    return (
        f"- [{iid}] {authors} ({year}). \"{title}\"\n"
        f"  ICs: {ics} | PM: {pm} | Stochastic: {stoch} | Contribution: {contrib}\n"
        f"  Main finding: {finding}\n"
        f"  DOI: {doi}"
    )


def _build_prompt(cluster: dict, papers: list[dict], ext: dict[str, dict]) -> str:
    paper_block = "\n\n".join(_paper_summary(p, ext) for p in papers)
    return textwrap.dedent(f"""
        You are writing the synthesis section of a PhD thesis chapter on a Systematic Literature Review
        about Process Mining, Stochastic Modeling, and Software Development Forecasting.
        The proposed system is PATHCAST: a 4-stage pipeline (PM discovery → absorbing Markov chain →
        Monte Carlo forecasting → ML residual correction) applied to SDLC event logs.

        CLUSTER: {cluster['label']}
        PAPERS IN THIS CLUSTER ({len(papers)} papers):
        {paper_block}

        TASK:
        {cluster['instruction']}

        REQUIREMENTS:
        - Write in academic English suitable for a PhD thesis.
        - Use \\cite{{key}} for citations; derive key from first author surname + year
          (e.g., joshi2024, bhadra2022, incerto2025, lopezpintado2023, guinea2025).
        - Output ONLY the LaTeX paragraph(s) — no preamble, no \\begin{{document}}, no section headers.
        - Do NOT use \\textbf{{}} excessively; only for sub-family names if needed.
        - Keep each paragraph 5-8 sentences; aim for 120-180 words per paragraph.
    """).strip()


# ── LLM call ──────────────────────────────────────────────────────────────────

def _call_llm(prompt: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main(dry_run: bool = False) -> None:
    from colorama import Fore, Style, init
    init(autoreset=True)

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key and not dry_run:
        print(f"{Fore.RED}ANTHROPIC_API_KEY não configurada.{Style.RESET_ALL}")
        sys.exit(1)

    top33 = _load_top33()
    ext = _load_extraction()

    print(f"{Fore.CYAN}── Gerando síntese para {len(CLUSTERS)} clusters...{Style.RESET_ALL}")

    output_blocks: list[str] = [
        "% ============================================================",
        "% cap3_synthesis_v2.tex — LLM-generated synthesis paragraphs",
        f"% Model: {MODEL} | Papers: top-33 (top-30 + 3 seminais)",
        "% REVIEW CAREFULLY before inserting into cap3_slr_revised.tex",
        "% ============================================================",
        "",
    ]

    for cluster in CLUSTERS:
        papers = _select_cluster(top33, ext, cluster)
        print(f"  {cluster['id']:12s}: {len(papers)} papers", end="")

        if not papers:
            print(f"  {Fore.YELLOW}(nenhum paper no cluster — skip){Style.RESET_ALL}")
            continue

        prompt = _build_prompt(cluster, papers, ext)

        if dry_run and cluster == CLUSTERS[0]:
            print(f"\n\n{Fore.YELLOW}--dry-run: prompt do cluster '{cluster['id']}'{Style.RESET_ALL}")
            print(prompt[:1500])
            return

        text = _call_llm(prompt, api_key)
        print(f"  {Fore.GREEN}✓{Style.RESET_ALL}  ({len(text)} chars)")

        output_blocks.append(cluster["tex_comment"])
        output_blocks.append("")
        output_blocks.append(text)
        output_blocks.append("")
        output_blocks.append("")

    if not dry_run:
        OUTPUT_TEX.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_TEX.write_text("\n".join(output_blocks), encoding="utf-8")
        print(f"\n{Fore.GREEN}✓ Salvo em {OUTPUT_TEX}{Style.RESET_ALL}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    main(dry_run=dry)
