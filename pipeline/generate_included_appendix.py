"""Generate the included-studies appendix (SEGRESS item 17 / Reviewer 2 M11).

Source of truth: results/auxiliary/qa_combined_404_dedup.csv (340 distinct studies)
joined with extraction_combined_404_dedup.csv (IC fields) and FT screening (authors).

Usage:
    python -m pipeline.generate_included_appendix
"""
from __future__ import annotations

import html
import logging
import re
from pathlib import Path
from urllib.parse import quote

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(".")
QA = Path("results/auxiliary/qa_combined_404_dedup.csv")
EXT = Path("results/auxiliary/extraction_combined_404_dedup.csv")
FT = Path("results/screening/ft_screening_results.csv")
CSV_OUT = Path("results/final_review/included_studies_340.csv")
TEX_OUTS = [
    Path("results/final_review/included_studies_appendix.tex"),
]


_CYRILLIC = str.maketrans({
    "А": "A", "Б": "B", "В": "V", "Г": "H", "Ґ": "G", "Д": "D", "Е": "E",
    "Є": "Ye", "Ж": "Zh", "З": "Z", "И": "Y", "І": "I", "Ї": "Yi", "Й": "Y",
    "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P", "Р": "R",
    "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "Kh", "Ц": "Ts", "Ч": "Ch",
    "Ш": "Sh", "Щ": "Shch", "Ь": "", "Ю": "Yu", "Я": "Ya", "Ё": "Yo", "Э": "E",
    "Ы": "Y", "Ъ": "",
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ye", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "yi", "й": "y",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "yu", "я": "ya", "ё": "yo", "э": "e",
    "ы": "y", "ъ": "",
})


def _tex_escape(s) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return "---"
    text = html.unescape(str(s))
    text = text.replace("\xa0", " ").replace("\u2009", " ")
    text = (text.replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2018", "'").replace("\u2019", "'")
                .replace("\u2013", "-").replace("\u2014", "-")
                .replace("\u00ab", '"').replace("\u00bb", '"')
                .replace("\u2032", "'").replace("\u2033", "''")
                .replace("\u2034", "'''").replace("\u2026", "..."))
    if re.search(r"[\u0400-\u04FF]", text):
        text = text.translate(_CYRILLIC)
    text = re.sub(r"\s+", " ", text).strip()
    repl = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for a, b in repl:
        text = text.replace(a, b)
    # Latin Extended-A is outside inputenc utf8's default coverage (pdflatex).
    latin_ext = {
        "Š": r"{\v{S}}", "š": r"{\v{s}}", "Č": r"{\v{C}}", "č": r"{\v{c}}",
        "Ž": r"{\v{Z}}", "ž": r"{\v{z}}", "Ř": r"{\v{R}}", "ř": r"{\v{r}}",
        "Ň": r"{\v{N}}", "ň": r"{\v{n}}", "Ě": r"{\v{E}}", "ě": r"{\v{e}}",
        "Ť": r"{\v{T}}", "ť": r"{\v{t}}", "Ď": r"{\v{D}}", "ď": r"{\v{d}}",
        "Ů": r"{\r{U}}", "ů": r"{\r{u}}", "Ł": r"{\L{}}", "ł": r"{\l{}}",
        "Ń": r"{\'N}", "ń": r"{\'n}", "Ś": r"{\'S}", "ś": r"{\'s}",
        "Ź": r"{\'Z}", "ź": r"{\'z}", "Ż": r"{\.Z}", "ż": r"{\.z}",
        "Ą": r"{\k{A}}", "ą": r"{\k{a}}", "Ę": r"{\k{E}}", "ę": r"{\k{e}}",
        "Ș": r"{\c{S}}", "ș": r"{\c{s}}", "Ț": r"{\c{T}}", "ț": r"{\c{t}}",
        "Ă": r"{\u{A}}", "ă": r"{\u{a}}", "Ő": r"{\H{O}}", "ő": r"{\H{o}}",
        "Ű": r"{\H{U}}", "ű": r"{\H{u}}",
    }
    for a, b in latin_ext.items():
        text = text.replace(a, b)
    return text


def _norm_doi(s) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s, flags=re.I)
    return s.strip()


def _origin_label(v) -> str:
    if pd.isna(v) or str(v).strip() == "":
        return "Aux2"
    v = str(v).strip().lower()
    if v == "working_set":
        return "WS"
    if v == "auxiliary":
        return "Aux1"
    return v


def _doi_cell(doi: str, iid: str) -> str:
    """Clickable DOI that wraps in a p-column (xurl + \\nolinkurl)."""
    if doi:
        target = "https://doi.org/" + quote(doi, safe="/()-._;:")
        return rf"\href{{{target}}}{{\nolinkurl{{{doi}}}}}"
    return rf"\nolinkurl{{{_tex_escape(iid)}}}"


def _tf_label(ic) -> str:
    """Map pipeline IC1–IC4 (technique families) to TF-* used in the manuscript."""
    if ic is None or (isinstance(ic, float) and pd.isna(ic)) or str(ic).strip() == "":
        return "---"
    mapping = {"IC1": "TF-PM", "IC2": "TF-ST", "IC3": "TF-FC", "IC4": "TF-MSR"}
    parts = [p.strip() for p in str(ic).split("|")]
    return "|".join(mapping.get(p, p) for p in parts if p)


def _year(v) -> str:
    if pd.isna(v):
        return "---"
    try:
        return str(int(float(v)))
    except (TypeError, ValueError):
        return str(v)[:4]


def _authors_short(s) -> str:
    if pd.isna(s) or not str(s).strip():
        return ""
    raw = str(s).strip()
    # keep first author + et al. if multiple
    parts = re.split(r";|, and | and ", raw)
    first = parts[0].strip().rstrip(",")
    if len(parts) > 1 or ";" in raw:
        return first + " et al."
    return first


def build() -> pd.DataFrame:
    qa = pd.read_csv(QA)
    ext = pd.read_csv(EXT)
    keep_ext = ext[["internal_id", "ft_matched_ic", "source_db"]].drop_duplicates("internal_id")
    df = qa.merge(keep_ext, on="internal_id", how="left")

    by_id, by_doi = {}, {}
    if FT.exists():
        ft = pd.read_csv(FT, usecols=lambda c: c in {"internal_id", "authors", "venue", "doi"},
                         low_memory=False)
        for _, row in ft.iterrows():
            a = row.get("authors")
            if pd.isna(a) or not str(a).strip():
                continue
            a = str(a).strip()
            iid = str(row.get("internal_id", "")).strip()
            if iid and iid not in by_id:
                by_id[iid] = a
            d = _norm_doi(row.get("doi"))
            if d and d not in by_doi:
                by_doi[d] = a

    df["doi_n"] = df["doi"].map(_norm_doi)
    df["authors"] = [
        by_id.get(str(i), "") or by_doi.get(d, "")
        for i, d in zip(df["internal_id"], df["doi_n"])
    ]
    df["origin_label"] = df["origin"].map(_origin_label)
    df["year_s"] = df["year"].map(_year)
    df["qa_n"] = pd.to_numeric(df["qa_total"], errors="coerce")
    df = df.sort_values(["year_s", "title"], kind="mergesort").reset_index(drop=True)
    df.insert(0, "seq", range(1, len(df) + 1))
    return df


def write_csv(df: pd.DataFrame) -> None:
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    out = df[["seq", "internal_id", "year_s", "authors", "title", "doi_n",
              "origin_label", "source_db", "ft_matched_ic", "qa_n", "qa_include"]].copy()
    out.columns = ["seq", "internal_id", "year", "authors", "title", "doi",
                   "origin", "source_db", "ic", "qa_total", "qa_include"]
    out.to_csv(CSV_OUT, index=False)
    logger.info("Wrote %s (%d rows)", CSV_OUT, len(out))


def write_tex(df: pd.DataFrame) -> None:
    n = len(df)
    n_doi = int((df["doi_n"] != "").sum())
    lines = [
        r"% Auto-generated by pipeline/generate_included_appendix.py --- do not edit by hand.",
        r"\begingroup\small",
        r"\setlength{\tabcolsep}{3pt}",
        r"\begin{longtable}{r c >{\raggedright\arraybackslash}p{1.7cm} p{6.05cm} >{\raggedright\arraybackslash}p{3.2cm} l c r}",
        rf"\caption{{Confirmed primary studies after cross-tier deduplication "
        rf"($N={n}$; {n_doi} with a DOI). Column \texttt{{ID}} is the "
        rf"\texttt{{internal\_id}} key used in the extraction and QA sheets of the "
        rf"replication package. Origin: WS~=~working-set tier; Aux1~=~first auxiliary "
        rf"pass; Aux2~=~second auxiliary pass. Column TF maps content criteria "
        rf"IC4a--IC4d to TF-PM/ST/FC/MSR. QA is the Dyb{{\aa}} and Dings{{\o}}yr "
        rf"reporting-quality total (0--8).}}",
        r"\label{tab:included-studies}\\",
        r"\toprule",
        r"\# & Year & Authors & Title & DOI / ID & Origin & TF & QA \\",
        r"\midrule",
        r"\endfirsthead",
        rf"\multicolumn{{8}}{{c}}{{\tablename\ \thetable{{}} --- continued from previous page}}\\",
        r"\toprule",
        r"\# & Year & Authors & Title & DOI / ID & Origin & TF & QA \\",
        r"\midrule",
        r"\endhead",
        r"\midrule",
        rf"\multicolumn{{8}}{{r}}{{\emph{{Continued on next page}}}}\\",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
    ]
    for _, row in df.iterrows():
        seq = int(row["seq"])
        year = _tex_escape(row["year_s"])
        auth = _tex_escape(_authors_short(row["authors"])) or "---"
        title = _tex_escape(row["title"])
        iid = str(row["internal_id"])
        doi_cell = _doi_cell(row["doi_n"], iid)
        origin = _tex_escape(row["origin_label"])
        ic = _tf_label(row.get("ft_matched_ic"))
        qa = "---" if pd.isna(row["qa_n"]) else f"{int(row['qa_n'])}"
        lines.append(
            f"{seq} & {year} & {auth} & {title} & {doi_cell} & {origin} & {ic} & {qa} \\\\"
        )
    lines += [
        r"\end{longtable}",
        r"\endgroup",
        "",
        r"\noindent\textit{Notes.} "
        r"Studies without a recoverable DOI are identified by the short internal "
        r"identifier used in the replication package. "
        r"Author strings are taken from the working-set full-text screening metadata "
        r"when available (first author + et~al.); auxiliary-tier rows may show "
        r"``---'' because that tier was screened from title/abstract metadata. "
        r"The machine-readable companion table is "
        r"\texttt{included\_studies\_340.csv} in the replication package "
        r"(DOI~\zenododoi).",
    ]
    body = "\n".join(lines) + "\n"
    for path in TEX_OUTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        logger.info("Wrote %s", path)


def main() -> None:
    df = build()
    assert len(df) == 340, f"expected 340 distinct studies, got {len(df)}"
    write_csv(df)
    write_tex(df)
    n_doi = int((df["doi_n"] != "").sum())
    n_auth = int((df["authors"] != "").sum())
    print(f"Included-studies appendix: n={len(df)}  DOI={n_doi}  authors={n_auth}")


if __name__ == "__main__":
    main()
