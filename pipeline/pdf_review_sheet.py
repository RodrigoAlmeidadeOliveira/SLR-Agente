from __future__ import annotations

import csv
import re
import subprocess
import unicodedata
from pathlib import Path

import pandas as pd

PDF_DIR = Path("results/pdfs")
MANIFEST_CSV = PDF_DIR / "download_manifest.csv"
ALL_PAPERS_CSV = Path("results/all_papers.csv")
OUTPUT_XLSX = Path("results/pdf_leitura_individual.xlsx")
OUTPUT_CSV = Path("results/pdf_leitura_individual.csv")
OUTPUT_V2_XLSX = Path("results/pdf_leitura_individual_v2.xlsx")
OUTPUT_V2_CSV = Path("results/pdf_leitura_individual_v2.csv")
OUTPUT_V3_XLSX = Path("results/pdf_leitura_individual_v3.xlsx")
OUTPUT_V3_CSV = Path("results/pdf_leitura_individual_v3.csv")
OUTPUT_V4_XLSX = Path("results/pdf_leitura_individual_v4.xlsx")
OUTPUT_V4_CSV = Path("results/pdf_leitura_individual_v4.csv")

RESULT_HEADINGS = [
    "results",
    "findings",
    "evaluation",
    "experimental results",
    "experiments and results",
    "case study",
    "discussion",
    "conclusion",
    "conclusions",
]

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:a-z0-9]+\b", re.IGNORECASE)
HEADING_RE = re.compile(
    r"(?m)^\s*(?:[IVXLC]+\.\s+|\d+(?:\.\d+)*\s+)?([A-Z][A-Z \-]{2,}|[A-Z][A-Za-z \-]{2,})\s*$"
)
ILLEGAL_XLSX_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]")


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def clean_text(value: str) -> str:
    value = ILLEGAL_XLSX_RE.sub(" ", value)
    value = value.replace("\x0c", "\n")
    value = re.sub(r"-\n", "", value)
    value = re.sub(r"\n{2,}", "\n\n", value)
    return value.strip()


def sentence_split(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    return [c.strip() for c in chunks if len(c.strip()) > 20]


def summarize_text(text: str, max_sentences: int = 3, max_chars: int = 900) -> str:
    if not text:
        return ""
    sentences = sentence_split(text)
    selected: list[str] = []
    total = 0
    for sentence in sentences:
        if total + len(sentence) > max_chars and selected:
            break
        selected.append(sentence)
        total += len(sentence) + 1
        if len(selected) >= max_sentences:
            break
    return " ".join(selected)[:max_chars].strip()


def sanitize_cell(value: str) -> str:
    value = ILLEGAL_XLSX_RE.sub(" ", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def load_manifest() -> dict[str, dict[str, str]]:
    return {
        (row.get("pdf_file") or "").strip(): row
        for row in read_csv_rows(MANIFEST_CSV)
        if (row.get("pdf_file") or "").strip()
    }


def load_paper_indexes() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    doi_index: dict[str, dict[str, str]] = {}
    title_index: dict[str, dict[str, str]] = {}
    for row in read_csv_rows(ALL_PAPERS_CSV):
        doi = normalize_text(row.get("doi", ""))
        title = normalize_text(row.get("title", ""))
        if doi and doi not in doi_index:
            doi_index[doi] = row
        if title and title not in title_index:
            title_index[title] = row
    return doi_index, title_index


def extract_pdf_text(pdf_path: Path) -> str:
    proc = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return clean_text(proc.stdout)


def extract_title_from_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()[:20] if line.strip()]
    if not lines:
        return ""
    title_parts: list[str] = []
    for line in lines:
        low = line.lower()
        if low.startswith(("abstract", "digital object identifier", "received ", "index terms")):
            break
        if "@" in line or low.startswith(("email", "corresponding author")):
            break
        if len(line.split()) <= 1 and title_parts:
            break
        if len(line) < 5:
            continue
        title_parts.append(line)
        if len(" ".join(title_parts)) > 180:
            break
    title = " ".join(title_parts)
    title = re.sub(r"\s+", " ", title).strip(" ,-")
    return title[:300]


def extract_doi(text: str) -> str:
    match = DOI_RE.search(text)
    return match.group(0).rstrip(".,;") if match else ""


def extract_abstract(text: str) -> str:
    patterns = [
        re.compile(
            r"(?is)\babstract\b[\s—:\-]*\s*(.+?)(?=\n\s*(?:index terms|keywords?|i\.\s+[A-Z]|1\.\s+[A-Z]|introduction)\b)"
        ),
        re.compile(
            r"(?is)\babstract\b[\s—:\-]*\s*(.+?)(?=\n\s*[A-Z][A-Z \-]{3,}\s*$)"
        ),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            abstract = summarize_text(match.group(1), max_sentences=5, max_chars=1800)
            if len(abstract) > 80:
                return abstract
    return ""


def extract_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?is)(?:^|\n)\s*(?:[IVXLC]+\.\s+|\d+(?:\.\d+)*\s+)?{re.escape(heading)}\s*\n(.+?)(?=\n\s*(?:[IVXLC]+\.\s+|\d+(?:\.\d+)*\s+)?[A-Z][A-Za-z \-]{{2,}}\s*\n|\Z)"
    )
    match = pattern.search(text)
    if not match:
        return ""
    return summarize_text(match.group(1), max_sentences=4, max_chars=1400)


def result_sentences_from_text(text: str) -> list[str]:
    return [
        sentence
        for sentence in sentence_split(text)
        if any(token in sentence.lower() for token in ["result", "find", "show", "indicate", "improv", "effect"])
    ]


def extract_results(text: str, abstract_hint: str = "") -> str:
    abstract_hits = result_sentences_from_text(abstract_hint)
    if not abstract_hits:
        abstract_hits = result_sentences_from_text(extract_abstract(text))
    if abstract_hits:
        return summarize_text(" ".join(abstract_hits), max_sentences=3, max_chars=900)

    lowered = text.lower()
    for heading in RESULT_HEADINGS:
        if heading in lowered:
            section = extract_section(text, heading)
            if len(section) > 80:
                return section

    result_sentences = result_sentences_from_text(text)
    return summarize_text(" ".join(result_sentences), max_sentences=4, max_chars=1000)


def resolve_metadata(
    pdf_name: str,
    extracted_title: str,
    extracted_doi: str,
    manifest: dict[str, dict[str, str]],
    doi_index: dict[str, dict[str, str]],
    title_index: dict[str, dict[str, str]],
) -> dict[str, str]:
    meta: dict[str, str] = {}
    manifest_row = manifest.get(pdf_name, {})
    if manifest_row:
        meta.update(manifest_row)

    doi_key = normalize_text(meta.get("doi") or extracted_doi)
    if doi_key and doi_key in doi_index:
        meta = {**doi_index[doi_key], **meta}

    title_key = normalize_text(meta.get("title") or extracted_title)
    if title_key and title_key in title_index:
        merged = dict(title_index[title_key])
        merged.update(meta)
        meta = merged

    return meta


def build_assessment(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    relevance = "média"
    if any(term in base for term in ["process mining", "event log", "conformance", "simulation", "markov", "petri net"]):
        relevance = "alta"
    elif any(term in base for term in ["software process", "agile", "devops", "github", "jira"]):
        relevance = "média-alta"

    strengths = []
    if any(term in base for term in ["case study", "experiment", "evaluation", "monte carlo", "dataset"]):
        strengths.append("traz validação empírica")
    if any(term in base for term in ["framework", "model", "approach", "methodology"]):
        strengths.append("propõe método reutilizável")
    if any(term in base for term in ["ontology", "ai", "machine learning", "reinforcement learning"]):
        strengths.append("inclui componente analítico avançado")

    if not strengths:
        strengths.append("tem valor mais conceitual do que operacional")

    return f"Relevância {relevance} para a revisão. {strengths[0].capitalize()}."


def infer_relevance(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    if any(term in base for term in ["process mining", "event log", "conformance checking", "process discovery"]):
        return "Alta: trata diretamente de mineração de processos aplicada ao desenvolvimento de software."
    if any(term in base for term in ["simulation", "petri net", "markov", "digital twin", "stochastic"]):
        return "Alta: aborda modelagem ou simulação de processos de software com potencial analítico forte para a SLR."
    if any(term in base for term in ["jira", "github", "requirements engineering", "agile", "devops"]):
        return "Média-alta: analisa processos ou artefatos de desenvolvimento com aderência prática ao tema."
    return "Média: relação indireta com a SLR, mais útil como contexto, método adjacente ou estudo complementar."


def infer_method(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    methods = []
    if "process mining" in base or "conformance" in base or "event log" in base:
        methods.append("mineração de processos")
    if "simulation" in base or "monte carlo" in base:
        methods.append("simulação")
    if "petri net" in base:
        methods.append("rede de Petri")
    if "markov" in base:
        methods.append("cadeia de Markov")
    if "ontology" in base or "nlp" in base or "ai" in base or "machine learning" in base:
        methods.append("apoio de IA/NLP/ontologia")
    if "case study" in base:
        methods.append("estudo de caso")
    if "framework" in base or "approach" in base or "methodology" in base or "model" in base:
        methods.append("proposta de framework/modelo")
    if not methods:
        return "Método não identificado com clareza no texto extraído; requer leitura manual do artigo."
    return ", ".join(dict.fromkeys(methods)).capitalize() + "."


def infer_evidence_type(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    if any(term in base for term in ["case study", "real project", "industrial", "open-source projects", "jira repositories"]):
        return "Estudo empírico com dados reais."
    if any(term in base for term in ["experiment", "evaluation", "user evaluation", "benchmark"]):
        return "Avaliação experimental."
    if any(term in base for term in ["simulation", "monte carlo"]):
        return "Simulação computacional."
    if any(term in base for term in ["framework", "model", "methodology", "approach"]):
        return "Proposta metodológica com evidência limitada."
    return "Tipo de evidência indefinido a partir da extração automática."


def infer_limitations(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    limits = []
    if any(term in base for term in ["case study", "pilot", "single", "one project", "small software development organization"]):
        limits.append("escopo empírico possivelmente restrito")
    if any(term in base for term in ["simulation", "model", "ontology", "framework"]):
        limits.append("dependência de modelagem e premissas do autor")
    if any(term in base for term in ["students", "novice developers"]):
        limits.append("ameaça de generalização para contexto industrial")
    if any(term in base for term in ["jira", "github", "version control", "ide logging"]):
        limits.append("forte dependência da qualidade e cobertura dos logs/dados")
    if not limits:
        return "Limitações não ficaram explícitas no texto extraído; convém validar na leitura completa."
    return "; ".join(dict.fromkeys(limits)).capitalize() + "."


def build_structured_assessment(title: str, abstract: str, results: str) -> dict[str, str]:
    return {
        "relevancia_para_slr": infer_relevance(title, abstract, results),
        "metodo": infer_method(title, abstract, results),
        "tipo_de_evidencia": infer_evidence_type(title, abstract, results),
        "ameacas_limitacoes": infer_limitations(title, abstract, results),
    }


def infer_context(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    contexts = []
    if any(term in base for term in ["requirements", "requirement engineering"]):
        contexts.append("engenharia de requisitos")
    if any(term in base for term in ["coding", "commit", "pull request", "repository", "refactoring"]):
        contexts.append("desenvolvimento/codificação")
    if any(term in base for term in ["test", "bug", "defect", "review", "quality"]):
        contexts.append("qualidade e testes")
    if any(term in base for term in ["ci/cd", "continuous integration", "continuous delivery", "devops", "build", "release", "deployment"]):
        contexts.append("entrega e DevOps")
    if any(term in base for term in ["multidisciplinary", "healthcare", "microservices", "open source", "opensource"]):
        contexts.append("contexto aplicado específico")
    if not contexts:
        return "Contexto de processo de software não identificado com clareza na extração automática."
    return ", ".join(dict.fromkeys(contexts)).capitalize() + "."


def infer_data_source(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    sources = []
    if any(term in base for term in ["jira", "issue", "bugzilla", "github issues"]):
        sources.append("issue tracker")
    if any(term in base for term in ["github", "git", "svn", "repository", "commit", "version control"]):
        sources.append("repositório/VCS")
    if any(term in base for term in ["ci/cd", "jenkins", "github actions", "build pipeline", "continuous integration", "continuous delivery"]):
        sources.append("pipeline CI/CD")
    if any(term in base for term in ["ide", "fluorite", "eclipse plug-in", "eclipse plugin"]):
        sources.append("logs de IDE")
    if any(term in base for term in ["survey", "questionnaire", "user perceptions"]):
        sources.append("percepção de usuários")
    if not sources:
        return "Fonte dos dados não identificada com clareza na extração automática."
    return ", ".join(dict.fromkeys(sources)).capitalize() + "."


def infer_main_technique(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    if "process mining" in base or "conformance" in base or "process discovery" in base:
        return "Mineração de processos."
    if "markov" in base:
        return "Cadeia de Markov."
    if "petri net" in base:
        return "Rede de Petri estocástica."
    if "simulation" in base or "monte carlo" in base:
        return "Simulação."
    if any(term in base for term in ["machine learning", "reinforcement learning", "ai", "nlp", "ontology"]):
        return "IA/NLP/aprendizado de máquina."
    return "Técnica principal não identificada automaticamente."


def infer_slr_decision(title: str, abstract: str, results: str) -> tuple[str, str]:
    base = f"{title} {abstract} {results}".lower()
    has_pm = any(term in base for term in ["process mining", "process discovery", "conformance", "event log"])
    has_stochastic = any(term in base for term in ["markov", "petri net", "simulation", "stochastic", "monte carlo"])
    has_se_context = any(
        term in base
        for term in [
            "software",
            "github",
            "jira",
            "devops",
            "ci/cd",
            "pull request",
            "commit",
            "repository",
            "requirements engineering",
            "testing",
        ]
    )
    if has_se_context and (has_pm or has_stochastic):
        reason = "Alinha-se ao escopo da SLR por combinar contexto de desenvolvimento de software com técnica de processo, mineração ou modelagem estocástica."
        return "incluir", reason
    if has_se_context:
        reason = "Relaciona-se a software, mas a técnica principal extraída não evidencia com clareza mineração de processos ou modelagem estocástica."
        return "talvez", reason
    reason = "A extração automática não mostrou aderência suficiente ao recorte de processo de software e técnicas-alvo da SLR."
    return "excluir", reason


def infer_rq(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    rqs = []
    if any(term in base for term in ["requirements", "coding", "pull request", "ci/cd", "devops", "software process", "repository"]):
        rqs.append("RQ1")
    if any(term in base for term in ["process mining", "process discovery", "conformance", "markov", "petri net", "simulation", "forecast", "prediction"]):
        rqs.append("RQ2")
    if any(term in base for term in ["integration", "framework", "pipeline", "digital twin", "what-if", "stochastic conformance"]):
        rqs.append("RQ3")
    return ", ".join(rqs) if rqs else "RQ1"


def infer_ic_ec(decision: str, title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    ics = []
    ecs = []
    if any(term in base for term in ["process mining", "process discovery", "conformance", "event log"]):
        ics.append("IC4a")
    if any(term in base for term in ["markov", "petri net", "simulation", "stochastic", "monte carlo"]):
        ics.append("IC4b")
    if any(term in base for term in ["forecast", "prediction", "remaining time", "lead time", "risk", "duration prediction"]):
        ics.append("IC4c")
    if any(term in base for term in ["github", "jira", "repository", "version control", "commit", "pull request", "ci/cd"]):
        ics.append("IC4d")
    if decision == "excluir":
        if not any(term in base for term in ["software", "github", "jira", "devops", "ci/cd", "repository", "commit"]):
            ecs.append("EC1")
        elif not ics:
            ecs.append("EC3")
    if decision == "talvez" and not ics:
        ecs.append("EC3?")
    parts = ics + ecs
    return ", ".join(dict.fromkeys(parts)) if parts else "Requer decisão manual"


def infer_sdlc_phase(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    phases = []
    if any(term in base for term in ["requirements", "requirement engineering"]):
        phases.append("Requisitos")
    if any(term in base for term in ["design", "architecture", "microservices decomposition"]):
        phases.append("Design/Arquitetura")
    if any(term in base for term in ["coding", "commit", "pull request", "github", "repository", "refactoring", "version control"]):
        phases.append("Desenvolvimento")
    if any(term in base for term in ["test", "bug", "defect", "review", "quality"]):
        phases.append("Qualidade/Testes")
    if any(term in base for term in ["ci/cd", "continuous integration", "continuous delivery", "devops", "build", "release", "deployment"]):
        phases.append("Entrega/DevOps")
    return ", ".join(phases) if phases else "Não definido"


def infer_integration_level(title: str, abstract: str, results: str) -> str:
    base = f"{title} {abstract} {results}".lower()
    has_pm = any(term in base for term in ["process mining", "process discovery", "conformance", "event log"])
    has_markov = "markov" in base
    has_mc_or_sim = any(term in base for term in ["simulation", "monte carlo"])
    has_ml = any(term in base for term in ["machine learning", "reinforcement learning", "ai", "nlp"])
    stoch_count = sum([has_markov, "petri net" in base, has_mc_or_sim])
    if has_pm and has_markov and has_mc_or_sim and has_ml:
        return "L3"
    if has_pm and stoch_count >= 1:
        return "L2"
    if has_pm or stoch_count >= 1:
        return "L1"
    return "L0"


def infer_reading_priority(decision: str, relevance: str, evidence: str, integration_level: str) -> str:
    if decision == "incluir" and ("Alta:" in relevance) and integration_level in {"L2", "L3"}:
        return "Alta"
    if decision == "incluir" and ("Alta:" in relevance or "Média-alta:" in relevance):
        return "Alta"
    if decision == "talvez" or evidence == "Tipo de evidência indefinido a partir da extração automática.":
        return "Média"
    return "Baixa"


def iter_pdfs() -> list[Path]:
    return sorted(path for path in PDF_DIR.glob("*.pdf") if path.is_file())


def generate_sheet() -> pd.DataFrame:
    manifest = load_manifest()
    doi_index, title_index = load_paper_indexes()
    rows: list[dict[str, str]] = []

    for pdf_path in iter_pdfs():
        text = extract_pdf_text(pdf_path)
        extracted_title = extract_title_from_text(text)
        extracted_doi = extract_doi(text)
        meta = resolve_metadata(
            pdf_path.name,
            extracted_title,
            extracted_doi,
            manifest,
            doi_index,
            title_index,
        )

        article_name = (meta.get("title") or extracted_title or pdf_path.stem).strip()
        doi = (meta.get("doi") or extracted_doi).strip()
        abstract = (meta.get("abstract") or "").strip()
        if not abstract:
            abstract = extract_abstract(text)
        results = extract_results(text, abstract_hint=abstract)
        assessment = build_assessment(article_name, abstract, results)
        structured = build_structured_assessment(article_name, abstract, results)
        decision, decision_reason = infer_slr_decision(article_name, abstract, results)
        context = infer_context(article_name, abstract, results)
        data_source = infer_data_source(article_name, abstract, results)
        main_technique = infer_main_technique(article_name, abstract, results)
        rq = infer_rq(article_name, abstract, results)
        ic_ec = infer_ic_ec(decision, article_name, abstract, results)
        sdlc_phase = infer_sdlc_phase(article_name, abstract, results)
        integration_level = infer_integration_level(article_name, abstract, results)
        reading_priority = infer_reading_priority(
            decision,
            structured["relevancia_para_slr"],
            structured["tipo_de_evidencia"],
            integration_level,
        )

        rows.append(
            {
                "nome_do_artigo": sanitize_cell(article_name),
                "nome_do_arquivo": sanitize_cell(pdf_path.name),
                "doi_cod": sanitize_cell(doi),
                "abstract": sanitize_cell(abstract),
                "resultados": sanitize_cell(results),
                "avaliacao_codex_chatgpt": sanitize_cell(assessment),
                "relevancia_para_slr": sanitize_cell(structured["relevancia_para_slr"]),
                "metodo": sanitize_cell(structured["metodo"]),
                "tipo_de_evidencia": sanitize_cell(structured["tipo_de_evidencia"]),
                "ameacas_limitacoes": sanitize_cell(structured["ameacas_limitacoes"]),
                "decisao_slr": sanitize_cell(decision),
                "motivo_da_decisao": sanitize_cell(decision_reason),
                "contexto": sanitize_cell(context),
                "fonte_dos_dados": sanitize_cell(data_source),
                "tecnica_principal": sanitize_cell(main_technique),
                "rq_atendida": sanitize_cell(rq),
                "ic_ec_acionados": sanitize_cell(ic_ec),
                "fase_do_sdlc": sanitize_cell(sdlc_phase),
                "nivel_de_integracao": sanitize_cell(integration_level),
                "prioridade_de_leitura": sanitize_cell(reading_priority),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["nome_do_artigo", "nome_do_arquivo"], na_position="last").reset_index(drop=True)
    return df


def main() -> None:
    df = generate_sheet()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)
    df.to_csv(OUTPUT_V2_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_V2_XLSX, index=False)
    df.to_csv(OUTPUT_V3_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_V3_XLSX, index=False)
    df.to_csv(OUTPUT_V4_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_V4_XLSX, index=False)
    print(f"CSV salvo em: {OUTPUT_CSV}")
    print(f"XLSX salvo em: {OUTPUT_XLSX}")
    print(f"CSV v2 salvo em: {OUTPUT_V2_CSV}")
    print(f"XLSX v2 salvo em: {OUTPUT_V2_XLSX}")
    print(f"CSV v3 salvo em: {OUTPUT_V3_CSV}")
    print(f"XLSX v3 salvo em: {OUTPUT_V3_XLSX}")
    print(f"CSV v4 salvo em: {OUTPUT_V4_CSV}")
    print(f"XLSX v4 salvo em: {OUTPUT_V4_XLSX}")
    print(f"Registros: {len(df)}")


if __name__ == "__main__":
    main()
