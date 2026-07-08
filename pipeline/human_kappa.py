"""Human-vs-LLM inter-rater agreement for SLR PATHCAST screening (double-screening).

Builds blind review sheets for an independent human rater covering:
  - T/A screening (20% stratified sample, reusing pipeline.kappa's ta_sample_20pct.csv)
  - FT screening + QA rescoring + data extraction, in a single pass per paper
    (20% stratified sample, reusing pipeline.kappa's ft_sample_20pct.csv)

Then computes Cohen's kappa (human vs. primary LLM screener, claude-haiku-4-5)
once the sheets are filled in. This complements pipeline/kappa.py (LLM-vs-LLM
cross-model verification) per Reviewer 1 feedback on the SLR manuscript:
cross-model kappa is not a substitute for an independent human rater.

Blinding protocol: the sheets never expose the LLM's own decision/rationale
for the item being reviewed. Answer keys are written to a separate
_answer_keys/ subdirectory — do not open them before finishing the review.

Usage:
    python -m pipeline.human_kappa --build-sheets   # (re)build blind review sheets
    python -m pipeline.human_kappa --compute        # compute kappa from filled sheets
"""
from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

from pipeline.kappa import _interpret, _kappa

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

KAPPA_DIR = Path("results/kappa")
TA_SAMPLE = KAPPA_DIR / "ta_sample_20pct.csv"
FT_SAMPLE = KAPPA_DIR / "ft_sample_20pct.csv"
# Deduplicated files (pipeline.dedup_apply) — the raw qa_combined_381.csv /
# extraction_combined_381.csv contain 63 cross/within-tier duplicate rows
# (same study scored twice under different internal_id), which made the
# doi/title join below ambiguous. See results/auxiliary/dedup_summary.txt.
QA_COMBINED = Path("results/auxiliary/qa_combined_381_dedup.csv")
EXTRACTION_COMBINED = Path("results/auxiliary/extraction_combined_381_dedup.csv")

HUMAN_DIR = Path("results/human_validation")
ANSWER_KEY_DIR = HUMAN_DIR / "_answer_keys"
TA_SHEET = HUMAN_DIR / "ta_blind_review_sheet.csv"
FT_SHEET = HUMAN_DIR / "ft_qa_extraction_blind_review_sheet.csv"
TA_ANSWER_KEY = ANSWER_KEY_DIR / "ta_answer_key.csv"
FT_ANSWER_KEY = ANSWER_KEY_DIR / "ft_qa_extraction_answer_key.csv"
HUMAN_KAPPA_REPORT_TXT = HUMAN_DIR / "human_kappa_report.txt"
HUMAN_KAPPA_REPORT_TEX = HUMAN_DIR / "human_kappa_report.tex"

QA_FIELDS = [f"QA{i}" for i in range(1, 9)]
EXTRACTION_FIELDS = [
    "research_question", "study_type", "pm_technique", "stochastic_technique",
    "software_process", "dataset_source", "main_finding", "limitations",
]


def _norm_doi(s) -> str:
    s = "" if pd.isna(s) else str(s)
    return s.strip().lower().replace("https://doi.org/", "").replace("http://doi.org/", "")


def _norm_title(s) -> str:
    s = "" if pd.isna(s) else str(s)
    return re.sub(r"\s+", " ", s.strip().lower())


def build_ta_sheet() -> None:
    if not TA_SAMPLE.exists():
        raise FileNotFoundError(f"{TA_SAMPLE} missing — run `python -m pipeline.kappa --sample` first")
    ta = pd.read_csv(TA_SAMPLE)

    bib_cols = ["internal_id", "title", "authors", "year", "abstract", "venue", "doc_type", "keywords", "doi", "url"]
    sheet = ta[bib_cols].copy()
    sheet.insert(0, "review_id", sheet["internal_id"])
    sheet["human_ta_decision"] = ""
    sheet["human_ta_notes"] = ""
    sheet = sheet.sample(frac=1.0, random_state=20260707).reset_index(drop=True)  # shuffle so decision-order gives no signal
    sheet.to_csv(TA_SHEET, index=False, encoding="utf-8")

    key = ta[["internal_id", "ta_decision", "ta_rationale", "ta_matched_ic", "ta_matched_ec"]].copy()
    ANSWER_KEY_DIR.mkdir(parents=True, exist_ok=True)
    key.to_csv(TA_ANSWER_KEY, index=False, encoding="utf-8")

    logger.info(f"[TA] blind sheet: {TA_SHEET} ({len(sheet)} rows, shuffled)")
    logger.info(f"[TA] answer key (do not open yet): {TA_ANSWER_KEY}")


def build_ft_sheet() -> None:
    if not FT_SAMPLE.exists():
        raise FileNotFoundError(f"{FT_SAMPLE} missing — run `python -m pipeline.kappa --sample` first")
    ft = pd.read_csv(FT_SAMPLE).reset_index(drop=True)
    ft["review_id"] = [f"ft_{i:04d}" for i in range(len(ft))]
    ft["_doi_norm"] = ft["doi"].map(_norm_doi)
    ft["_title_norm"] = ft["title"].map(_norm_title)

    qa = pd.read_csv(QA_COMBINED)
    qa["_doi_norm"] = qa["doi"].map(_norm_doi)
    qa["_title_norm"] = qa["title"].map(_norm_title)

    ext = pd.read_csv(EXTRACTION_COMBINED)
    ext = ext.loc[:, ~ext.columns.duplicated()]  # cap3 extraction_combined_381.csv has a duplicated 'origin' header
    ext["_doi_norm"] = ext["doi"].map(_norm_doi)
    ext["_title_norm"] = ext["title"].map(_norm_title)

    def _lookup(row, table, cols):
        if row["_doi_norm"]:
            hit = table[table["_doi_norm"] == row["_doi_norm"]]
            if len(hit) == 1:
                return hit.iloc[0][cols]
        hit = table[table["_title_norm"] == row["_title_norm"]]
        if len(hit) == 1:
            return hit.iloc[0][cols]
        return pd.Series([None] * len(cols), index=cols)

    qa_matched = ft.apply(lambda r: _lookup(r, qa, ["internal_id"] + QA_FIELDS + ["qa_total", "qa_include"]), axis=1)
    ext_matched = ft.apply(lambda r: _lookup(r, ext, EXTRACTION_FIELDS), axis=1)

    n_qa_matched = qa_matched["internal_id"].notna().sum()
    logger.info(f"[FT] matched {n_qa_matched}/{(ft['ft_decision'] == 'include').sum()} LLM-included "
                f"sample papers to QA/extraction records (doi/title join)")

    bib_cols = ["review_id", "title", "authors", "year", "abstract", "doi", "url", "ft_oa_url", "venue", "doc_type"]
    sheet = ft[bib_cols].copy()
    sheet["human_ft_decision"] = ""
    sheet["human_ft_notes"] = ""
    for f in QA_FIELDS:
        sheet[f"human_{f}"] = ""
    sheet["human_qa_notes"] = ""
    for f in EXTRACTION_FIELDS:
        sheet[f"human_{f}"] = ""
    sheet = sheet.sample(frac=1.0, random_state=20260707).reset_index(drop=True)
    sheet.to_csv(FT_SHEET, index=False, encoding="utf-8")

    key = pd.concat(
        [ft[["review_id", "ft_decision", "ft_rationale", "ft_matched_ic", "ft_matched_ec"]],
         qa_matched.add_prefix("llm_qa_"), ext_matched.add_prefix("llm_ext_")],
        axis=1,
    )
    ANSWER_KEY_DIR.mkdir(parents=True, exist_ok=True)
    key.to_csv(FT_ANSWER_KEY, index=False, encoding="utf-8")

    logger.info(f"[FT] blind sheet: {FT_SHEET} ({len(sheet)} rows, shuffled)")
    logger.info(f"[FT] answer key (do not open yet): {FT_ANSWER_KEY}")


README = """\
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

Para cada linha, localize o texto completo (via `doi`, `url` ou `ft_oa_url`) e:

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
"""


def build_sheets() -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    build_ta_sheet()
    build_ft_sheet()
    (HUMAN_DIR / "README.md").write_text(README, encoding="utf-8")
    logger.info(f"Instructions: {HUMAN_DIR / 'README.md'}")


def _report_binary_and_multiclass(name: str, y_llm, y_human, lines: list[str]) -> tuple[str, str]:
    k, info = _kappa(y_llm, y_human)
    lines.append(f"[{name}] n={info.get('n', 0)}")
    lines.append(f"  Cohen's kappa (multi-class): {k:.3f} ({_interpret(k)})")
    lines.append(f"  Observed agreement (Po): {info['po']*100:.1f}%  Expected (Pe): {info['pe']*100:.1f}%")
    lines.append(f"  Categories: {info['categories']}")

    def _bin(d):
        return "include" if d == "include" else "not_include"

    y_llm_b = [_bin(d) for d in y_llm]
    y_human_b = [_bin(d) for d in y_human]
    k_b, info_b = _kappa(y_llm_b, y_human_b)
    lines.append(f"  Cohen's kappa (binary include/not-include): {k_b:.3f} ({_interpret(k_b)})")
    lines.append(f"    Po={info_b['po']*100:.1f}%, Pe={info_b['pe']*100:.1f}%")
    lines.append("")
    return f"{k:.3f} ({_interpret(k)})", f"{k_b:.3f} ({_interpret(k_b)})"


def compute() -> None:
    lines = ["SLR PATHCAST — Human-vs-LLM Inter-rater Agreement Report", "=" * 60,
             "Primary screener (rater 1): claude-haiku-4-5-20251001",
             "Independent rater 2:        human (blind double-screening)", ""]
    tex_rows = []

    if not TA_SHEET.exists() or not TA_ANSWER_KEY.exists():
        lines.append("[TA] sheet or answer key missing; run --build-sheets first")
    else:
        sheet = pd.read_csv(TA_SHEET)
        key = pd.read_csv(TA_ANSWER_KEY)
        df = sheet.merge(key, on="internal_id", how="inner")
        df["human_ta_decision"] = df["human_ta_decision"].fillna("").astype(str).str.strip().str.lower()
        df["ta_decision"] = df["ta_decision"].fillna("").astype(str).str.strip().str.lower()
        valid = df[(df["human_ta_decision"] != "") & (df["ta_decision"] != "")]
        n_total = len(df)
        if len(valid) == 0:
            lines.append(f"[TA] no filled decisions yet (0/{n_total}); fill human_ta_decision first")
        else:
            if len(valid) < n_total:
                lines.append(f"[TA] WARNING: only {len(valid)}/{n_total} rows filled — partial result")
            multi, binary = _report_binary_and_multiclass(
                "TA", valid["ta_decision"].tolist(), valid["human_ta_decision"].tolist(), lines)
            tex_rows.append(f"T/A & {len(valid)} & {multi} & {binary} \\\\")

    if not FT_SHEET.exists() or not FT_ANSWER_KEY.exists():
        lines.append("[FT] sheet or answer key missing; run --build-sheets first")
    else:
        sheet = pd.read_csv(FT_SHEET)
        key = pd.read_csv(FT_ANSWER_KEY)
        df = sheet.merge(key, on="review_id", how="inner")
        df["human_ft_decision"] = df["human_ft_decision"].fillna("").astype(str).str.strip().str.lower()
        df["ft_decision"] = df["ft_decision"].fillna("").astype(str).str.strip().str.lower()
        valid = df[(df["human_ft_decision"] != "") & (df["ft_decision"] != "")]
        n_total = len(df)
        if len(valid) == 0:
            lines.append(f"[FT] no filled decisions yet (0/{n_total}); fill human_ft_decision first")
        else:
            if len(valid) < n_total:
                lines.append(f"[FT] WARNING: only {len(valid)}/{n_total} rows filled — partial result")
            multi, binary = _report_binary_and_multiclass(
                "FT", valid["ft_decision"].tolist(), valid["human_ft_decision"].tolist(), lines)
            tex_rows.append(f"FT & {len(valid)} & {multi} & {binary} \\\\")

            both_include = valid[(valid["human_ft_decision"] == "include") & (valid["ft_decision"] == "include")]
            lines.append(f"[QA] {len(both_include)} papers included by both human and LLM — QA/extraction comparison base")
            if len(both_include) > 0:
                for f in QA_FIELDS:
                    human_col, llm_col = f"human_{f}", f"llm_qa_{f}"
                    if llm_col not in both_include.columns:
                        continue
                    sub = both_include[[human_col, llm_col]].dropna()
                    if len(sub) == 0:
                        continue
                    agree = (sub[human_col].astype(float) == sub[llm_col].astype(float)).mean() * 100
                    lines.append(f"  {f} agreement: {agree:.1f}% (n={len(sub)})")
                if "llm_qa_qa_total" in both_include.columns:
                    sub = both_include[["llm_qa_qa_total"]].copy()
                    human_total = both_include[[f"human_{f}" for f in QA_FIELDS]].apply(pd.to_numeric, errors="coerce").sum(axis=1)
                    mae = (human_total - pd.to_numeric(sub["llm_qa_qa_total"], errors="coerce")).abs().mean()
                    lines.append(f"  qa_total mean absolute difference: {mae:.2f} (n={len(both_include)})")
                lines.append("")
                lines.append("[Extraction] exact-match agreement (case/whitespace-insensitive):")
                for f in EXTRACTION_FIELDS:
                    human_col, llm_col = f"human_{f}", f"llm_ext_{f}"
                    if llm_col not in both_include.columns:
                        continue
                    sub = both_include[[human_col, llm_col]].dropna()
                    if len(sub) == 0:
                        continue
                    norm = lambda s: re.sub(r"\s+", " ", str(s).strip().lower())
                    agree = (sub[human_col].map(norm) == sub[llm_col].map(norm)).mean() * 100
                    lines.append(f"  {f}: {agree:.1f}% (n={len(sub)})")

    lines.append("")
    lines.append("Interpretation thresholds (Landis & Koch 1977):")
    lines.append("  <0.00 poor | 0-0.20 slight | 0.21-0.40 fair | 0.41-0.60 moderate | 0.61-0.80 substantial | >0.80 almost perfect")

    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_KAPPA_REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")

    tex = ["\\begin{table}[htbp]", "\\centering",
           "\\caption{Inter-rater agreement (Cohen's $\\kappa$) between the primary LLM screener "
           "(claude-haiku-4-5) and an independent human rater on a stratified random 20\\% sample. "
           "Interpretation thresholds follow Landis and Koch (1977)~\\cite{landiskoch1977}.}",
           "\\label{tab:human-kappa-results}",
           "\\begin{tabular}{lccc}", "\\toprule",
           "Stage & $N$ & $\\kappa_{\\text{multi}}$ (interpretation) & $\\kappa_{\\text{binary}}$ (interpretation) \\\\",
           "\\midrule", *tex_rows, "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    HUMAN_KAPPA_REPORT_TEX.write_text("\n".join(tex), encoding="utf-8")

    print("\n".join(lines))
    logger.info(f"Reports saved: {HUMAN_KAPPA_REPORT_TXT}, {HUMAN_KAPPA_REPORT_TEX}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-sheets", action="store_true", help="Build blind review sheets for human double-screening")
    ap.add_argument("--compute", action="store_true", help="Compute human-vs-LLM kappa from filled sheets")
    args = ap.parse_args()

    if args.build_sheets:
        build_sheets()
    if args.compute:
        compute()
    if not (args.build_sheets or args.compute):
        ap.print_help()


if __name__ == "__main__":
    main()
