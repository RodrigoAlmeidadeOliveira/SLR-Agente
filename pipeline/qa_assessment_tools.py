from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

FT_SCREENING_CSV = Path("results/screening/ft_screening_results.csv")
PDF_V4_XLSX = Path("results/pdf_leitura_individual_v4.xlsx")
QA_XLSX = Path("results/qa_assessment.xlsx")
QA_CSV = Path("results/qa_assessment.csv")
QA_SUMMARY_TXT = Path("results/qa_assessment_summary.txt")
QA_SUMMARY_TEX = Path("results/qa_assessment_summary.tex")

QA_COLUMNS = [f"QA{i}" for i in range(1, 9)]


def load_included_studies() -> pd.DataFrame:
    ft = pd.read_csv(FT_SCREENING_CSV)
    included = ft[ft["ft_decision"].astype(str).str.lower() == "include"].copy()
    included = included.sort_values(by=["year", "title"], na_position="last").reset_index(drop=True)

    pdf = pd.read_excel(PDF_V4_XLSX)
    pdf_dois = {str(v).strip().lower() for v in pdf["doi_cod"].fillna("") if str(v).strip()}
    pdf_titles = {str(v).strip().lower() for v in pdf["nome_do_artigo"].fillna("") if str(v).strip()}

    included["has_pdf_subset"] = included.apply(
        lambda row: (
            str(row.get("doi", "")).strip().lower() in pdf_dois
            or str(row.get("title", "")).strip().lower() in pdf_titles
        ),
        axis=1,
    )
    return included


def load_pdf_enrichment() -> pd.DataFrame:
    pdf = pd.read_excel(PDF_V4_XLSX).copy()
    pdf["doi_norm"] = pdf["doi_cod"].fillna("").astype(str).str.strip().str.lower()
    pdf["title_norm"] = pdf["nome_do_artigo"].fillna("").astype(str).str.strip().str.lower()
    return pdf


def build_qa_sheet() -> pd.DataFrame:
    included = load_included_studies()
    pdf = load_pdf_enrichment()

    included["doi_norm"] = included["doi"].fillna("").astype(str).str.strip().str.lower()
    included["title_norm"] = included["title"].fillna("").astype(str).str.strip().str.lower()

    pdf_by_doi = pdf.drop_duplicates(subset=["doi_norm"]).set_index("doi_norm")
    pdf_by_title = pdf.drop_duplicates(subset=["title_norm"]).set_index("title_norm")

    def pick_pdf_value(row: pd.Series, col: str):
        doi_key = row["doi_norm"]
        title_key = row["title_norm"]
        if doi_key and doi_key in pdf_by_doi.index:
            return pdf_by_doi.at[doi_key, col]
        if title_key and title_key in pdf_by_title.index:
            return pdf_by_title.at[title_key, col]
        return pd.NA

    df = included[
        [
            "internal_id",
            "title",
            "doi",
            "year",
            "venue",
            "source_db",
            "ft_decision",
            "ft_rationale",
            "ft_matched_ic",
            "ft_matched_ec",
            "has_pdf_subset",
            "doi_norm",
            "title_norm",
        ]
    ].copy()
    df = df.rename(
        columns={
            "title": "nome_do_artigo",
            "doi": "doi",
            "year": "ano",
            "venue": "venue",
            "source_db": "fonte",
            "ft_decision": "ft_decision",
            "ft_rationale": "ft_rationale",
            "ft_matched_ic": "ft_matched_ic",
            "ft_matched_ec": "ft_matched_ec",
            "has_pdf_subset": "tem_pdf_local",
        }
    )

    for col in [
        "abstract",
        "resultados",
        "relevancia_para_slr",
        "metodo",
        "tipo_de_evidencia",
        "ameacas_limitacoes",
        "contexto",
        "fonte_dos_dados",
        "tecnica_principal",
        "rq_atendida",
        "ic_ec_acionados",
        "fase_do_sdlc",
        "nivel_de_integracao",
        "prioridade_de_leitura",
    ]:
        df[col] = df.apply(lambda row, c=col: pick_pdf_value(row, c), axis=1)

    for col in QA_COLUMNS:
        df[col] = pd.NA

    df["qa_total"] = pd.NA
    df["qa_include"] = pd.NA
    df["qa_status"] = "pendente"
    df["qa_notes"] = ""
    df = df.drop(columns=["doi_norm", "title_norm"])
    return df


def _contains_any(text: str, terms: list[str]) -> bool:
    text = (text or "").lower()
    return any(term in text for term in terms)


def infer_qa_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    notes: list[str] = []

    def as_text(value) -> str:
        return "" if pd.isna(value) else str(value)

    for idx, row in out.iterrows():
        title = as_text(row.get("nome_do_artigo", ""))
        abstract = as_text(row.get("abstract", ""))
        rationale = as_text(row.get("ft_rationale", ""))
        results = as_text(row.get("resultados", ""))
        evidence = as_text(row.get("tipo_de_evidencia", ""))
        data_source = as_text(row.get("fonte_dos_dados", ""))
        technique = as_text(row.get("tecnica_principal", ""))
        limitations = as_text(row.get("ameacas_limitacoes", ""))
        context = as_text(row.get("contexto", ""))
        combined = " ".join([title, abstract, rationale, results, evidence, data_source, technique, context]).lower()

        qa = {}
        qa["QA1"] = 1 if len(abstract.strip()) > 80 or len(rationale.strip()) > 80 else 0
        qa["QA2"] = 1 if _contains_any(combined, ["software", "github", "jira", "devops", "repository", "software process", "ci/cd"]) else 0
        qa["QA3"] = 1 if (data_source and "não identificada" not in data_source.lower()) or _contains_any(combined, ["event log", "svn", "git", "github", "jira", "issue", "repository", "pipeline"]) else 0
        qa["QA4"] = 1 if (technique and "não identificada" not in technique.lower()) or _contains_any(combined, ["process mining", "conformance", "markov", "petri", "simulation", "stochastic"]) else 0
        qa["QA5"] = 1 if evidence in {"Estudo empírico com dados reais.", "Avaliação experimental."} else 0
        qa["QA6"] = 1 if limitations and "não ficaram explícitas" not in limitations.lower() else 0
        qa["QA7"] = 1 if _contains_any(combined, ["github", "open source", "open-source", "jira repositories", "python enhancement", "nasa"]) else 0
        qa["QA8"] = 1 if _contains_any(combined, ["fitness", "precision", "generalization", "correctness", "usefulness", "understandability"]) else 0

        for col, value in qa.items():
            if pd.isna(row.get(col)):
                out.at[idx, col] = value

        notes.append("QA inferido automaticamente a partir de screening FT e enriquecimento PDF v4.")

    out["qa_notes"] = out["qa_notes"].fillna("")
    out["qa_notes"] = out["qa_notes"].astype(str).str.strip()
    out.loc[out["qa_notes"] == "", "qa_notes"] = notes
    out.loc[out["qa_status"] == "pendente", "qa_status"] = "inferido"
    return out


def save_qa_sheet() -> pd.DataFrame:
    df = build_qa_sheet()
    df = infer_qa_scores(df)
    df = recalculate_scores(df)
    QA_XLSX.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(QA_XLSX, index=False)
    df.to_csv(QA_CSV, index=False, encoding="utf-8-sig")
    return df


def _numeric_series(df: pd.DataFrame) -> pd.Series:
    totals = pd.to_numeric(df["qa_total"], errors="coerce").dropna()
    return totals


def recalculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for col in QA_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    has_any_qa = out[QA_COLUMNS].notna().any(axis=1)
    out.loc[has_any_qa, "qa_total"] = out.loc[has_any_qa, QA_COLUMNS].fillna(0).sum(axis=1)
    out.loc[~has_any_qa, "qa_total"] = pd.NA

    qa_total_num = pd.to_numeric(out["qa_total"], errors="coerce")
    out["qa_include"] = out["qa_include"].astype("object")
    out.loc[qa_total_num.notna(), "qa_include"] = qa_total_num[qa_total_num.notna()].ge(4)
    out.loc[qa_total_num.isna(), "qa_include"] = pd.NA

    out.loc[qa_total_num.notna(), "qa_status"] = "avaliado"
    out.loc[qa_total_num.isna(), "qa_status"] = out.loc[qa_total_num.isna(), "qa_status"].fillna("pendente")
    return out


def compute_summary(df: pd.DataFrame) -> dict[str, str | int | float]:
    df = recalculate_scores(df)
    assessed_mask = df[QA_COLUMNS].notna().any(axis=1) | pd.to_numeric(df["qa_total"], errors="coerce").notna()
    assessed = df.loc[assessed_mask].copy()
    totals = _numeric_series(assessed)

    assessed_count = int(len(assessed))
    retained_count = int((totals >= 4).sum()) if assessed_count else 0
    excluded_count = int((totals < 4).sum()) if assessed_count else 0

    mean_score = float(totals.mean()) if assessed_count else math.nan
    std_score = float(totals.std(ddof=1)) if assessed_count > 1 else math.nan
    median_score = float(totals.median()) if assessed_count else math.nan
    q1 = float(totals.quantile(0.25)) if assessed_count else math.nan
    q3 = float(totals.quantile(0.75)) if assessed_count else math.nan

    total_included = int(len(df))
    assessed_pct = (assessed_count / total_included * 100) if total_included else 0.0

    return {
        "studies_assessed": assessed_count,
        "studies_assessed_pct": assessed_pct,
        "score_gte_4": retained_count,
        "score_lt_4": excluded_count,
        "mean": mean_score,
        "std": std_score,
        "median": median_score,
        "q1": q1,
        "q3": q3,
        "total_included_set": total_included,
    }


def format_summary(summary: dict[str, str | int | float]) -> str:
    def fmt(v: float) -> str:
        return "TBD" if pd.isna(v) else f"{v:.2f}"

    lines = [
        f"Studies assessed: {summary['studies_assessed']} ({summary['studies_assessed_pct']:.1f}% of included set)",
        f"Studies with score >= 4/8: {summary['score_gte_4']}",
        f"Studies with score < 4/8: {summary['score_lt_4']}",
        f"Mean QA score: {fmt(summary['mean'])} (SD = {fmt(summary['std'])})",
        f"Median QA score: {fmt(summary['median'])} (IQR = {fmt(summary['q1'])}--{fmt(summary['q3'])})",
        f"Total included set considered for QA: {summary['total_included_set']}",
    ]
    return "\n".join(lines)


def format_summary_latex(summary: dict[str, str | int | float]) -> str:
    def fmt(v: float) -> str:
        return "TBD" if pd.isna(v) else f"{v:.2f}"

    return "\n".join(
        [
            f"Studies assessed & {summary['studies_assessed']} & Absolute count and {summary['studies_assessed_pct']:.1f}\\% of included set \\\\",
            f"Studies with score $\\geq 4/8$ & {summary['score_gte_4']} & Retained for synthesis \\\\",
            f"Studies with score $< 4/8$ & {summary['score_lt_4']} & Excluded after QA \\\\",
            f"Mean QA score & {fmt(summary['mean'])} & Mean and standard deviation ({fmt(summary['std'])}) \\\\",
            f"Median QA score & {fmt(summary['median'])} & Median and interquartile range ({fmt(summary['q1'])}--{fmt(summary['q3'])}) \\\\",
        ]
    )


def save_summary() -> str:
    if not QA_XLSX.exists():
        save_qa_sheet()
    df = pd.read_excel(QA_XLSX)
    df = infer_qa_scores(df)
    df = recalculate_scores(df)
    df.to_excel(QA_XLSX, index=False)
    df.to_csv(QA_CSV, index=False, encoding="utf-8-sig")
    summary = compute_summary(df)
    text = format_summary(summary)
    tex = format_summary_latex(summary)
    QA_SUMMARY_TXT.write_text(text, encoding="utf-8")
    QA_SUMMARY_TEX.write_text(tex, encoding="utf-8")
    return text


def main() -> None:
    df = save_qa_sheet()
    print(f"QA sheet saved: {QA_XLSX}")
    print(f"QA CSV saved: {QA_CSV}")
    print(f"Rows pre-populated: {len(df)}")
    print(f"Studies with local PDF match: {int(df['tem_pdf_local'].sum())}")
    print()
    print(save_summary())
    print()
    print(f"LaTeX summary saved: {QA_SUMMARY_TEX}")


if __name__ == "__main__":
    main()
