"""
Download de PDFs para os papers incluídos na SLR PATHCAST.

Estratégia em cascata por paper:
  1. ft_oa_url        — URL OA já obtida via Semantic Scholar (download direto)
  2. Unpaywall        — DOI → URL OA via api.unpaywall.org (gratuito, requer email)
  3. Semantic Scholar — campo openAccessPdf via /paper/DOI:{doi}
  4. OpenAlex título  — best_oa_location.pdf_url via busca por título
  5. CORE título      — downloadUrl via busca por título (requer CORE_API_KEY)
  6. Manual           — sem fonte automática disponível (lista ao final)

Saída:
  results/pdfs/<internal_id>_<slug>.pdf    — PDFs baixados
  results/pdfs/download_manifest.csv       — status por paper
  results/pdfs/manual_required.txt         — papers que precisam de download manual
"""
from __future__ import annotations

import csv
import logging
import os
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

PDF_DIR = Path("results/pdfs")
MANIFEST_CSV  = PDF_DIR / "download_manifest.csv"
MANUAL_TXT    = PDF_DIR / "manual_required.txt"

MANIFEST_COLS = [
    "internal_id", "title", "doi", "year", "source_db",
    "pdf_status",   # downloaded | oa_found | manual | failed
    "pdf_source",   # ft_oa_url | unpaywall | s2 | —
    "pdf_file",     # filename relativo a results/pdfs/
    "oa_url",       # URL usada (ou tentada)
    "error",
]

HEADERS = {
    "User-Agent": "SLR-PATHCAST/1.0 (mailto:{})"
}


# ================================================================== #
#  Helpers                                                            #
# ================================================================== #

def _slug(title: str, max_len: int = 50) -> str:
    """Gera slug seguro para nome de arquivo."""
    s = unicodedata.normalize("NFKD", title or "untitled")
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[\s_-]+", "_", s)
    return s[:max_len].rstrip("_")


def _norm_doi(doi: str) -> str:
    doi = (doi or "").strip().lower()
    for pfx in ("https://doi.org/", "http://doi.org/",
                "https://dx.doi.org/", "http://dx.doi.org/"):
        if doi.startswith(pfx):
            doi = doi[len(pfx):]
    return doi


def _is_pdf(response: requests.Response) -> bool:
    ct = response.headers.get("Content-Type", "")
    return "pdf" in ct or response.content[:4] == b"%PDF"


def _save_pdf(content: bytes, path: Path) -> bool:
    if content[:4] != b"%PDF":
        return False
    path.write_bytes(content)
    return True


def _download_url(url: str, session: requests.Session, timeout: int = 30) -> Optional[bytes]:
    """Tenta baixar URL; retorna bytes se for PDF, None caso contrário."""
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200 and _is_pdf(resp):
            return resp.content
        return None
    except Exception as exc:
        logger.debug(f"Download failed {url}: {exc}")
        return None


def _norm_title(title: str) -> str:
    s = (title or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _safe_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


_USELESS_URL_PATTERNS = (
    "dx.doi.org/",
    "doi.org/10.",
    "api.elsevier.com",
    "api.crossref.org",
)


def _is_usable_pdf_url(url: str) -> bool:
    """Retorna False para URLs que são redirecionamentos DOI ou endpoints de API fechados."""
    if not url:
        return False
    for pattern in _USELESS_URL_PATTERNS:
        if pattern in url:
            return False
    return True


# ================================================================== #
#  Fontes de URL OA                                                   #
# ================================================================== #

def _unpaywall_url(doi: str, email: str, session: requests.Session) -> Optional[str]:
    """Consulta Unpaywall para obter URL de PDF OA."""
    doi_norm = _norm_doi(doi)
    if not doi_norm:
        return None
    try:
        resp = session.get(
            f"https://api.unpaywall.org/v2/{doi_norm}",
            params={"email": email},
            timeout=15,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        # Prefer best_oa_location.url_for_pdf, fallback to url
        best = data.get("best_oa_location") or {}
        return best.get("url_for_pdf") or best.get("url")
    except Exception as exc:
        logger.debug(f"Unpaywall error for {doi}: {exc}")
        return None


def _s2_oa_url(doi: str, api_key: str, session: requests.Session) -> Optional[str]:
    """Consulta Semantic Scholar paper detail para openAccessPdf."""
    doi_norm = _norm_doi(doi)
    if not doi_norm:
        return None
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    try:
        resp = session.get(
            f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi_norm}",
            params={"fields": "openAccessPdf"},
            headers=headers,
            timeout=15,
        )
        if resp.status_code in (404, 400):
            return None
        if resp.status_code == 429:
            logger.warning("[PDF/S2] rate limit — aguardando 30s")
            time.sleep(30)
            return None
        resp.raise_for_status()
        data = resp.json()
        oa = data.get("openAccessPdf") or {}
        return oa.get("url")
    except Exception as exc:
        logger.debug(f"S2 error for {doi}: {exc}")
        return None


def _openalex_pdf_url_by_title(
    title: str, year: str, email: str, session: requests.Session
) -> Optional[str]:
    """Busca URL de PDF OA via OpenAlex por título (fuzzy ≥ 92)."""
    if not title:
        return None
    title_norm = _norm_title(title)
    year_int = _safe_int(year)
    try:
        resp = session.get(
            "https://api.openalex.org/works",
            params={
                "filter": f"title.search:{title}",
                "select": "display_name,publication_year,open_access,best_oa_location",
                "per-page": 5,
            },
            headers={"User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})"},
            timeout=20,
        )
        if resp.status_code == 429:
            logger.warning("[PDF/OA/title] rate limit — aguardando 60s")
            time.sleep(60)
            return None
        if resp.status_code != 200:
            return None
        for item in resp.json().get("results") or []:
            cand_norm = _norm_title(item.get("display_name") or "")
            if not cand_norm:
                continue
            if cand_norm != title_norm and fuzz.token_set_ratio(title_norm, cand_norm) < 92:
                continue
            cand_year = _safe_int(item.get("publication_year"))
            if year_int and cand_year and abs(year_int - cand_year) > 1:
                continue
            best = item.get("best_oa_location") or {}
            url = best.get("pdf_url") or (item.get("open_access") or {}).get("oa_url")
            if url:
                return url
    except Exception as exc:
        logger.debug(f"[PDF/OA/title] falhou: {exc}")
    return None


def _core_escape_doi(doi: str) -> str:
    return doi.replace("/", "\\/")


def _core_pdf_url_by_doi(
    doi: str, api_key: str, session: requests.Session
) -> Optional[str]:
    """Busca URL de download via CORE por DOI (match exato após normalização)."""
    if not doi or not api_key:
        return None
    doi_norm = doi.strip().lower()
    for pfx in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/"):
        if doi_norm.startswith(pfx):
            doi_norm = doi_norm[len(pfx):]
    try:
        escaped = _core_escape_doi(doi_norm)
        resp = session.get(
            "https://api.core.ac.uk/v3/search/works",
            params={"q": f"doi:{escaped}", "limit": 3},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )
        if resp.status_code == 429:
            logger.warning("[PDF/CORE/doi] rate limit — aguardando 30s")
            time.sleep(30)
            return None
        if resp.status_code != 200:
            return None
        for item in (resp.json().get("results") or []):
            item_doi = (item.get("doi") or "").strip().lower()
            for pfx in ("https://doi.org/", "http://doi.org/"):
                if item_doi.startswith(pfx):
                    item_doi = item_doi[len(pfx):]
            if item_doi != doi_norm:
                continue
            url = item.get("downloadUrl") or item.get("fullTextLink")
            if url and _is_usable_pdf_url(url):
                return url
            for link in (item.get("links") or []):
                if (link.get("type") or "").lower() in ("download", "fulltext", "pdf"):
                    candidate = link.get("url")
                    if candidate and _is_usable_pdf_url(candidate):
                        return candidate
    except Exception as exc:
        logger.debug(f"[PDF/CORE/doi] falhou: {exc}")
    return None


def _core_pdf_url_by_title(
    title: str, year: str, api_key: str, session: requests.Session
) -> Optional[str]:
    """Busca URL de download via CORE por título (fuzzy ≥ 92)."""
    if not title or not api_key:
        return None
    title_norm = _norm_title(title)
    year_int = _safe_int(year)
    try:
        resp = session.get(
            "https://api.core.ac.uk/v3/search/works/",
            params={"q": f'title:"{title}"', "limit": 5},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )
        if resp.status_code in (401, 403, 404):
            return None
        if resp.status_code == 429:
            logger.warning("[PDF/CORE/title] rate limit — aguardando 30s")
            time.sleep(30)
            return None
        if resp.status_code != 200:
            return None
        data = resp.json()
        for item in (data.get("results") or data.get("data") or []):
            cand_norm = _norm_title(item.get("title") or "")
            if not cand_norm:
                continue
            if cand_norm != title_norm and fuzz.token_set_ratio(title_norm, cand_norm) < 92:
                continue
            cand_year = _safe_int(item.get("yearPublished") or item.get("year"))
            if year_int and cand_year and abs(year_int - cand_year) > 1:
                continue
            url = item.get("downloadUrl") or item.get("fullTextLink")
            if url and _is_usable_pdf_url(url):
                return url
            for link in (item.get("links") or []):
                if (link.get("type") or "").lower() in ("download", "fulltext", "pdf"):
                    candidate = link.get("url")
                    if candidate and _is_usable_pdf_url(candidate):
                        return candidate
    except Exception as exc:
        logger.debug(f"[PDF/CORE/title] falhou: {exc}")
    return None


# ================================================================== #
#  Download de um paper                                               #
# ================================================================== #

def _download_paper(
    paper: dict,
    session: requests.Session,
    email: str,
    s2_api_key: str,
    core_api_key: str,
    delay: float,
) -> dict:
    """
    Tenta baixar o PDF de um paper na cascata ft_oa_url → Unpaywall → S2.
    Retorna dict com campos do manifesto.
    """
    pid   = paper["internal_id"]
    title = paper.get("title", "")
    doi   = paper.get("doi", "")
    year  = paper.get("year", "")
    db    = paper.get("source_db", "")

    filename = f"{pid}_{_slug(title)}.pdf"
    filepath = PDF_DIR / filename

    row = {
        "internal_id": pid,
        "title":       title[:120],
        "doi":         doi,
        "year":        year,
        "source_db":   db,
        "pdf_status":  "manual",
        "pdf_source":  "—",
        "pdf_file":    "",
        "oa_url":      "",
        "error":       "",
    }

    # ── Se já existe, pula ──────────────────────────────────────
    if filepath.exists():
        row["pdf_status"] = "downloaded"
        row["pdf_file"]   = filename
        row["pdf_source"] = "cached"
        return row

    sources = []

    # 1. ft_oa_url
    oa = (paper.get("ft_oa_url") or "").strip()
    if oa:
        sources.append(("ft_oa_url", oa))

    # 2. Unpaywall
    if doi:
        time.sleep(delay)
        up_url = _unpaywall_url(doi, email, session)
        if up_url:
            sources.append(("unpaywall", up_url))

    # 3. Semantic Scholar
    if doi and not sources:
        s2_url = _s2_oa_url(doi, s2_api_key, session)
        if s2_url:
            sources.append(("s2", s2_url))

    # 3.5. CORE por DOI
    if doi and core_api_key:
        time.sleep(delay)
        core_doi_url = _core_pdf_url_by_doi(doi, core_api_key, session)
        if core_doi_url:
            sources.append(("core_doi", core_doi_url))

    # 4. OpenAlex por título
    if title:
        time.sleep(delay)
        oa_title_url = _openalex_pdf_url_by_title(title, str(year), email, session)
        if oa_title_url:
            sources.append(("openalex_title", oa_title_url))

    # 5. CORE por título
    if title and core_api_key:
        time.sleep(delay)
        core_title_url = _core_pdf_url_by_title(title, str(year), core_api_key, session)
        if core_title_url:
            sources.append(("core_title", core_title_url))

    # ── Tenta cada fonte ─────────────────────────────────────────
    for source_name, url in sources:
        row["oa_url"] = url
        content = _download_url(url, session)
        if content:
            PDF_DIR.mkdir(parents=True, exist_ok=True)
            if _save_pdf(content, filepath):
                row["pdf_status"] = "downloaded"
                row["pdf_source"] = source_name
                row["pdf_file"]   = filename
                logger.info(f"[PDF] ✓ {pid} via {source_name}")
                return row
        logger.debug(f"[PDF] {source_name} failed for {pid}: {url[:60]}")

    # ── Só OA URL encontrada mas download falhou ─────────────────
    if sources:
        row["pdf_status"] = "oa_found"
        row["pdf_source"] = sources[0][0]
        row["oa_url"]     = sources[0][1]
        row["error"]      = "URL found but download failed (may require auth)"
    else:
        row["pdf_status"] = "manual"
        row["error"]      = "No OA URL found"

    return row


# ================================================================== #
#  Carrega manifesto existente                                        #
# ================================================================== #

def _load_manifest() -> dict[str, dict]:
    if not MANIFEST_CSV.exists():
        return {}
    with open(MANIFEST_CSV, encoding="utf-8", newline="") as f:
        return {r["internal_id"]: r for r in csv.DictReader(f)}


def _save_manifest(rows: list[dict]) -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_COLS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ================================================================== #
#  Ponto de entrada                                                   #
# ================================================================== #

def download_pdfs(
    papers: list[dict],
    email: str,
    *,
    delay: float = 1.5,
    force: bool = False,
    limit: int = 0,
    dry_run: bool = False,
) -> None:
    """
    Baixa PDFs para a lista de papers em cascata de fontes OA.

    Args:
        papers:   Lista de dicts com campos do ft_screening_results.csv
        email:    Email para Unpaywall polite pool
        delay:    Segundos entre requisições Unpaywall
        force:    Re-baixar mesmo se já existir no manifesto
        limit:    Processar apenas os primeiros N papers (0=todos)
        dry_run:  Mostrar o que seria feito sem baixar
    """
    from tqdm import tqdm
    from colorama import Fore, Style

    s2_api_key   = os.getenv("S2_API_KEY") or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    core_api_key = os.getenv("CORE_API_KEY", "").strip()

    # Carrega manifesto anterior
    manifest = _load_manifest()
    all_rows: dict[str, dict] = dict(manifest)

    # Filtra papers já baixados
    not_downloaded = []
    for p in papers:
        pid = p["internal_id"]
        already = manifest.get(pid, {})
        if not force and already.get("pdf_status") == "downloaded":
            continue
        not_downloaded.append(p)

    pending = list(not_downloaded)
    if limit > 0:
        pending = pending[:limit]

    total = len(papers)
    already_done = total - len(not_downloaded)
    outside_limit = max(len(not_downloaded) - len(pending), 0)
    print(f"\n{Fore.CYAN}── PDF Download — {total} papers alvo{Style.RESET_ALL}")
    print(f"  Já baixados no manifesto: {already_done}")
    if limit > 0:
        print(f"  Fora do recorte por --limit: {outside_limit}")
    print(f"  A processar agora: {len(pending)}")

    if dry_run:
        print(f"\n{Fore.YELLOW}--dry-run: nenhum download será feito.{Style.RESET_ALL}")
        core_status = '✓' if core_api_key else '✗ (sem CORE_API_KEY)'
        print(f"  Fontes ativas: ft_oa_url | Unpaywall | S2 | CORE/doi {core_status} | OpenAlex/title | CORE/title {core_status}")
        print("Fontes que seriam consultadas (por paper):")
        for p in pending[:5]:
            oa  = (p.get("ft_oa_url") or "").strip()
            doi = (p.get("doi") or "").strip()
            ttl = str(p.get("title", ""))
            print(f"  {p['internal_id']} | {ttl[:55]}")
            print(f"    ft_oa_url:      {'✓ ' + oa[:50] if oa else '✗'}")
            print(f"    DOI disponível: {'✓ ' + doi if doi else '✗'}")
            print(f"    título:         {'✓' if ttl else '✗'}")
        if len(pending) > 5:
            print(f"  ... e mais {len(pending)-5} papers")
        return

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": f"SLR-PATHCAST/1.0 (mailto:{email})"})

    downloaded = 0
    oa_found   = 0
    manual_req = 0
    failed     = 0

    with tqdm(total=len(pending), desc="Baixando PDFs", unit="paper") as pbar:
        for p in pending:
            row = _download_paper(p, session, email, s2_api_key, core_api_key, delay)
            all_rows[row["internal_id"]] = row

            if row["pdf_status"] == "downloaded":
                downloaded += 1
            elif row["pdf_status"] == "oa_found":
                oa_found += 1
            elif row["pdf_status"] == "manual":
                manual_req += 1
            else:
                failed += 1

            pbar.update(1)
            pbar.set_postfix(ok=downloaded, oa=oa_found, manual=manual_req)

            # Salva manifesto a cada 10 papers (checkpoint)
            if (downloaded + oa_found + manual_req + failed) % 10 == 0:
                _save_manifest(list(all_rows.values()))

    _save_manifest(list(all_rows.values()))
    _write_manual_list(all_rows)

    # Relatório final
    print(f"\n{Fore.GREEN}✓ Download concluído:{Style.RESET_ALL}")
    print(f"  Baixados com sucesso:    {downloaded + already_done}")
    print(f"  URL OA encontrada*:      {oa_found}  (* download falhou, URL disponível)")
    print(f"  Requerem download manual:{manual_req}")
    print(f"  Falhas:                  {failed}")
    print(f"\n  PDFs em:        {PDF_DIR}/")
    print(f"  Manifesto:      {MANIFEST_CSV}")
    print(f"  Lista manual:   {MANUAL_TXT}")


def _write_manual_list(all_rows: dict[str, dict]) -> None:
    """Escreve lista dos papers que precisam de download manual."""
    manual = [r for r in all_rows.values()
              if r.get("pdf_status") in ("manual", "oa_found")]
    if not manual:
        MANUAL_TXT.write_text("Todos os PDFs foram baixados automaticamente.\n", encoding="utf-8")
        return

    lines = [
        "Papers que requerem download manual",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total: {len(manual)}",
        "=" * 80,
        "",
    ]
    for r in sorted(manual, key=lambda x: x.get("year", ""), reverse=True):
        status = r.get("pdf_status", "")
        lines += [
            f"ID:     {r['internal_id']}",
            f"Título: {r['title']}",
            f"DOI:    https://doi.org/{r['doi']}" if r.get("doi") else "DOI:    —",
            f"Status: {status}",
        ]
        if status == "oa_found":
            lines.append(f"URL OA: {r.get('oa_url', '')}  (download automático falhou)")
        lines.append("")

    MANUAL_TXT.write_text("\n".join(lines), encoding="utf-8")


def print_download_stats() -> None:
    """Mostra resumo do manifesto de download existente."""
    if not MANIFEST_CSV.exists():
        print("Manifesto de download não encontrado. Execute --download primeiro.")
        return
    manifest = _load_manifest()
    total = len(manifest)
    from collections import Counter
    status_counts = Counter(r.get("pdf_status", "?") for r in manifest.values())
    source_counts = Counter(r.get("pdf_source", "—") for r in manifest.values()
                            if r.get("pdf_status") == "downloaded")
    print(f"\nManifesto de PDFs — {total} papers")
    print(f"  downloaded:  {status_counts.get('downloaded', 0)}")
    print(f"  oa_found:    {status_counts.get('oa_found', 0)}  (URL disponível, download manual)")
    print(f"  manual:      {status_counts.get('manual', 0)}")
    print(f"  failed:      {status_counts.get('failed', 0)}")
    print(f"\nFonte dos downloads:")
    for src, n in source_counts.most_common():
        print(f"  {src}: {n}")
    print(f"\nArquivos em: {PDF_DIR}/")
