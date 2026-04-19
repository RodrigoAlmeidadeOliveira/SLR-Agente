#!/usr/bin/env python3
"""
SLR PATHCAST — Agente de Extração de Referências
=================================================
Extrai, deduplica, valida e exporta referências para a SLR
"From Discovery to Forecasting: Process Mining and Stochastic Modeling
Applied to Software Development Processes".

Uso:
  python main.py run scopus            # extrai do Scopus (todas as queries)
  python main.py run ieee              # extrai do IEEE Xplore
  python main.py run springer          # extrai do Springer
  python main.py run all               # extrai de todas as bases com API

  python main.py import acm --file export.bib --query-id acm_principal
  python main.py import wos --file export.ris --query-id wos_principal
  python main.py import wos --file export.txt --format plaintext
  python main.py import csv --file planilha.csv --db acm

  python main.py pipeline              # dedup + validate + export (usa combined.json)
  python main.py snowball              # snowballing automático via OpenAlex
  python main.py validate              # só valida os 10 papers de controle
  python main.py export                # re-exporta RIS/CSV/BibTeX/relatório
  python main.py status                # mostra resumo dos resultados atuais
  python main.py queries               # lista todas as queries configuradas

  # Triagem de títulos e resumos (T/A)
  python main.py screen --enrich --poll          # fluxo completo: enriquece → envia → aguarda
  python main.py screen --enrich --dry-run       # preview com abstracts buscados (sem enviar)
  python main.py screen --poll                   # envia e aguarda (usa working_set_enriched se existir)
  python main.py screen                          # envia batch e imprime batch_id
  python main.py screen --collect <batch_id>     # coleta resultados de batch existente
  python main.py screen --dry-run                # preview do prompt sem enviar
  python main.py screen --stats                  # mostra estatísticas da triagem atual

  # Full-text screening (fase 2)
  python main.py fulltext                        # exporta fila + stats (ação padrão)
  python main.py fulltext --export               # gera ft_screening_results.csv priorizado
  python main.py fulltext --enrich-abstracts     # tenta recuperar abstracts na cascata S2→OA→Crossref→CORE
  python main.py fulltext --enrich-urls          # busca PDFs open-access via Semantic Scholar
  python main.py fulltext --llm-rescreen --poll  # LLM re-tria "maybe" com abstract
  python main.py fulltext --collect <batch_id>   # coleta resultados de batch LLM
  python main.py fulltext --stats                # progresso atual do full-text screening

  # Download de PDFs (papers confirmados para leitura integral)
  python main.py download-pdfs                   # baixa PDFs dos 76+3 papers (ft_decision=include)
  python main.py download-pdfs --dry-run         # preview sem baixar
  python main.py download-pdfs --stats           # resumo do manifesto de downloads
  python main.py download-pdfs --force           # re-baixar mesmo se já existir
  python main.py download-pdfs --limit 10        # processar apenas 10 papers
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv

# ------------------------------------------------------------------ #
#  Setup                                                              #
# ------------------------------------------------------------------ #

colorama_init(autoreset=True)
load_dotenv()

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))
RAW_DIR = RESULTS_DIR / "raw"
COMBINED_FILE = RESULTS_DIR / "combined.json"
DEDUP_FILE = RESULTS_DIR / "deduplicated.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Helpers                                                            #
# ------------------------------------------------------------------ #

def _get_api_key(name: str) -> str:
    key = os.getenv(f"{name.upper()}_API_KEY", "")
    if not key:
        print(
            f"{Fore.RED}✗ Variável {name.upper()}_API_KEY não configurada.{Style.RESET_ALL}\n"
            f"  Copie .env.example para .env e preencha as chaves de API."
        )
        sys.exit(1)
    return key


def _load_existing(path: Path):
    """Carrega JSON de papers existente, ou retorna lista vazia."""
    from pipeline.export import load_json
    if path.exists():
        return load_json(path)
    return []


def _save_combined(papers):
    """Salva/atualiza o arquivo combined.json acrescentando novos papers."""
    from pipeline.export import save_json, load_json
    existing = _load_existing(COMBINED_FILE)
    existing_ids = {p.internal_id for p in existing}
    new_papers = [p for p in papers if p.internal_id not in existing_ids]
    all_papers = existing + new_papers
    save_json(all_papers, COMBINED_FILE)
    if new_papers:
        logger.info(f"[Main] +{len(new_papers)} papers adicionados ao combined.json "
                    f"(total: {len(all_papers)})")
    return all_papers


def _get_delay() -> float:
    try:
        return float(os.getenv("REQUEST_DELAY", "1.0"))
    except ValueError:
        return 1.0


def _get_max_results() -> int:
    try:
        return int(os.getenv("MAX_RESULTS_PER_QUERY", "0"))
    except ValueError:
        return 0


# ------------------------------------------------------------------ #
#  Subcommand: run                                                    #
# ------------------------------------------------------------------ #

def cmd_run(args):
    from config.queries import QUERIES, API_ENABLED
    from pipeline.export import save_json

    databases = list(API_ENABLED) if args.database == "all" else [args.database]
    delay = _get_delay()
    max_results = _get_max_results()

    all_new = []

    for db in databases:
        if db not in API_ENABLED:
            print(f"{Fore.YELLOW}⚠ '{db}' não tem API automatizada. "
                  f"Use 'python main.py import {db}' para importar manualmente.{Style.RESET_ALL}")
            continue

        if db not in QUERIES:
            print(f"{Fore.RED}✗ Base '{db}' não reconhecida.{Style.RESET_ALL}")
            continue

        api_key = _get_api_key(db)
        extractor = _build_extractor(db, api_key, delay, max_results)

        queries = QUERIES[db]
        # Filtrar query específica se --query-id foi passado
        if hasattr(args, "query_id") and args.query_id:
            queries = [q for q in queries if q["id"] == args.query_id]
            if not queries:
                print(f"{Fore.RED}✗ Query ID '{args.query_id}' não encontrada em '{db}'.{Style.RESET_ALL}")
                continue

        for q in queries:
            print(f"\n{Fore.CYAN}→ [{db.upper()}] {q['label']}{Style.RESET_ALL}")
            if q.get("notes"):
                print(f"  {Fore.WHITE}{q['notes']}{Style.RESET_ALL}")

            raw_file = RAW_DIR / f"{q['id']}.json"
            if raw_file.exists() and not getattr(args, "force", False):
                from pipeline.export import load_json
                papers = load_json(raw_file)
                print(f"  {Fore.GREEN}✓ Usando cache: {len(papers)} papers{Style.RESET_ALL}")
            else:
                papers = extractor.extract(q["id"], q["label"], q["query"])
                RAW_DIR.mkdir(parents=True, exist_ok=True)
                save_json(papers, raw_file)

            all_new.extend(papers)
            print(f"  {Fore.GREEN}✓ {len(papers)} papers extraídos{Style.RESET_ALL}")

    if all_new:
        _save_combined(all_new)
        print(f"\n{Fore.GREEN}✓ Extração concluída. "
              f"Execute 'python main.py pipeline' para deduplicar e exportar.{Style.RESET_ALL}")


def _build_extractor(db: str, api_key: str, delay: float, max_results: int):
    if db == "scopus":
        from extractors.scopus import ScopusExtractor
        return ScopusExtractor(api_key, delay, max_results)
    elif db == "ieee":
        from extractors.ieee import IEEEExtractor
        return IEEEExtractor(api_key, delay, max_results)
    elif db == "springer":
        from extractors.springer import SpringerExtractor
        return SpringerExtractor(api_key, delay, max_results)
    elif db == "wos":
        from extractors.wos import WoSExtractor
        return WoSExtractor(api_key, delay, max_results)
    else:
        raise ValueError(f"Extrator não implementado para: {db}")


# ------------------------------------------------------------------ #
#  Subcommand: import                                                 #
# ------------------------------------------------------------------ #

def cmd_import(args):
    db = args.database
    filepath = Path(args.file)
    query_id = getattr(args, "query_id", "") or f"{db}_import"
    query_label = getattr(args, "query_label", "") or f"{db.upper()} manual import"
    fmt = getattr(args, "format", "auto")

    if not filepath.exists():
        print(f"{Fore.RED}✗ Arquivo não encontrado: {filepath}{Style.RESET_ALL}")
        sys.exit(1)

    suffix = filepath.suffix.lower()

    if fmt == "bibtex" or (fmt == "auto" and suffix == ".bib"):
        from extractors.manual_import import import_bibtex
        papers = import_bibtex(filepath, db, query_id, query_label)

    elif fmt == "ris" or (fmt == "auto" and suffix in (".ris", ".txt") and db != "wos_plain"):
        from extractors.manual_import import import_ris
        papers = import_ris(filepath, db, query_id, query_label)

    elif fmt == "plaintext" or db == "wos" and suffix == ".txt":
        from extractors.manual_import import import_wos_plaintext
        papers = import_wos_plaintext(filepath, query_id, query_label)

    elif fmt == "csv" or (fmt == "auto" and suffix == ".csv"):
        from extractors.manual_import import import_csv
        papers = import_csv(filepath, db, query_id, query_label)

    else:
        print(f"{Fore.RED}✗ Formato não reconhecido. Use --format bibtex|ris|plaintext|csv{Style.RESET_ALL}")
        sys.exit(1)

    print(f"{Fore.GREEN}✓ {len(papers)} papers importados de {filepath.name}{Style.RESET_ALL}")

    # Salva raw file
    from pipeline.export import save_json
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = RAW_DIR / f"{query_id}.json"
    save_json(papers, raw_file)
    _save_combined(papers)
    print(f"{Fore.GREEN}✓ Salvo em {raw_file}{Style.RESET_ALL}")


# ------------------------------------------------------------------ #
#  Subcommand: pipeline                                               #
# ------------------------------------------------------------------ #

def cmd_pipeline(args):
    """Executa dedup → enrich → validate → export sobre combined.json."""
    if not COMBINED_FILE.exists():
        print(f"{Fore.RED}✗ {COMBINED_FILE} não encontrado. "
              f"Execute 'python main.py run <db>' ou 'python main.py import' primeiro.{Style.RESET_ALL}")
        sys.exit(1)

    from pipeline.export import load_json
    from pipeline.dedup import deduplicate, unique_papers
    from pipeline.enrich import enrich_abstracts
    from pipeline.validator import validate, print_validation_report
    from pipeline.export import save_json, save_csv, save_ris, save_bibtex, save_report

    print(f"\n{Fore.CYAN}── Carregando resultados...{Style.RESET_ALL}")
    all_papers = load_json(COMBINED_FILE)
    print(f"  {len(all_papers):,} papers no combined.json")

    print(f"\n{Fore.CYAN}── Deduplicando...{Style.RESET_ALL}")
    deduped = deduplicate(all_papers)
    unique = unique_papers(deduped)
    print(f"  {len(unique):,} únicos ({len(deduped) - len(unique):,} duplicatas removidas)")

    skip_enrich = getattr(args, "no_enrich", False)
    if not skip_enrich:
        print(f"\n{Fore.CYAN}── Enriquecendo abstracts via cascata (S2 → OpenAlex → Crossref → CORE)...{Style.RESET_ALL}")
        deduped, enriched = enrich_abstracts(deduped, delay=_get_delay())
        unique = unique_papers(deduped)
        print(f"  {enriched:,} abstracts preenchidos")
    else:
        print(f"\n{Fore.YELLOW}  (--no-enrich: etapa de enriquecimento ignorada){Style.RESET_ALL}")

    save_json(deduped, DEDUP_FILE)

    print(f"\n{Fore.CYAN}── Validando papers de controle...{Style.RESET_ALL}")
    val_results = validate(unique)
    report_text = print_validation_report(val_results)
    print(report_text)

    print(f"\n{Fore.CYAN}── Exportando...{Style.RESET_ALL}")
    save_csv(deduped, RESULTS_DIR / "all_papers.csv")
    save_csv(unique, RESULTS_DIR / "unique_papers.csv")
    save_ris(unique, RESULTS_DIR / "export.ris")
    save_bibtex(unique, RESULTS_DIR / "export.bib")
    save_report(deduped, unique, val_results, RESULTS_DIR / "report.txt")

    print(f"\n{Fore.GREEN}✓ Pipeline concluído. Arquivos em: {RESULTS_DIR}/{Style.RESET_ALL}")
    _print_file_list()


# ------------------------------------------------------------------ #
#  Subcommand: enrich                                                 #
# ------------------------------------------------------------------ #

def cmd_enrich(args):
    """Enriquece abstracts via cascata por DOI e título."""
    source = DEDUP_FILE if DEDUP_FILE.exists() else COMBINED_FILE
    if not source.exists():
        print(f"{Fore.RED}✗ Nenhum resultado. Execute 'run' ou 'pipeline' primeiro.{Style.RESET_ALL}")
        sys.exit(1)

    from pipeline.export import load_json, save_json
    from pipeline.enrich import enrich_abstracts

    print(f"\n{Fore.CYAN}── Carregando {source.name}...{Style.RESET_ALL}")
    papers = load_json(source)
    sem_abstract = sum(1 for p in papers if not getattr(p, "abstract", ""))
    print(f"  {len(papers):,} papers | {sem_abstract:,} sem abstract")

    print(f"\n{Fore.CYAN}── Consultando cascata de metadados...{Style.RESET_ALL}")
    papers, enriched = enrich_abstracts(papers, delay=_get_delay())

    save_json(papers, source)
    print(f"\n{Fore.GREEN}✓ {enriched:,} abstracts preenchidos. Salvo em {source}{Style.RESET_ALL}")


# ------------------------------------------------------------------ #
#  Subcommand: snowball                                               #
# ------------------------------------------------------------------ #

def cmd_snowball(args):
    """Executa snowballing automático (backward/forward/both) via OpenAlex."""
    source = DEDUP_FILE if DEDUP_FILE.exists() else COMBINED_FILE
    if not source.exists():
        print(f"{Fore.RED}✗ Nenhum resultado. Execute 'run' ou 'pipeline' primeiro.{Style.RESET_ALL}")
        sys.exit(1)

    from pipeline.export import load_json, save_json
    from pipeline.snowball import snowball, print_snowball_report

    direction = getattr(args, "direction", "both")
    limit = getattr(args, "limit", 0)
    dry_run = getattr(args, "dry_run", False)

    print(f"\n{Fore.CYAN}── Carregando corpus ({source.name})...{Style.RESET_ALL}")
    papers = load_json(source)
    papers_with_doi = sum(1 for p in papers if p.doi)
    print(f"  {len(papers):,} papers | {papers_with_doi:,} com DOI (seeds)")

    if limit > 0:
        print(f"  {Fore.YELLOW}--limit {limit}: usando apenas os primeiros {limit} seeds{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}── Iniciando snowball {direction.upper()}...{Style.RESET_ALL}")
    new_papers, stats = snowball(papers, direction=direction, limit=limit, delay=_get_delay())

    report = print_snowball_report(stats, new_papers)
    print(report)

    if not new_papers:
        print(f"\n{Fore.YELLOW}Nenhum paper novo encontrado.{Style.RESET_ALL}")
        return

    if dry_run:
        print(f"\n{Fore.YELLOW}(--dry-run: novos papers NÃO foram salvos){Style.RESET_ALL}")
        return

    # Salva os novos papers no raw dir e no combined.json
    from pipeline.export import save_json as _save_json
    snowball_raw = RAW_DIR / f"snowball_{direction}.json"
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Se já existe arquivo de snowball anterior, mescla
    existing_snowball = []
    if snowball_raw.exists():
        try:
            existing_snowball = load_json(snowball_raw)
        except Exception:
            pass

    all_snowball = existing_snowball + new_papers
    _save_json(all_snowball, snowball_raw)

    _save_combined(new_papers)
    print(f"\n{Fore.GREEN}✓ {len(new_papers)} novos papers salvos em {snowball_raw}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}  Execute 'python main.py pipeline --no-enrich' para re-deduplicar e exportar.{Style.RESET_ALL}")


# ------------------------------------------------------------------ #
#  Subcommand: validate                                               #
# ------------------------------------------------------------------ #

def cmd_validate(args):
    source = DEDUP_FILE if DEDUP_FILE.exists() else COMBINED_FILE
    if not source.exists():
        print(f"{Fore.RED}✗ Nenhum resultado encontrado. Execute 'run' ou 'import' primeiro.{Style.RESET_ALL}")
        sys.exit(1)

    from pipeline.export import load_json
    from pipeline.dedup import unique_papers
    from pipeline.validator import validate, print_validation_report

    all_papers = load_json(source)
    unique = unique_papers(all_papers)
    val_results = validate(unique)
    print(print_validation_report(val_results))


# ------------------------------------------------------------------ #
#  Subcommand: export                                                 #
# ------------------------------------------------------------------ #

def cmd_export(args):
    source = DEDUP_FILE if DEDUP_FILE.exists() else COMBINED_FILE
    if not source.exists():
        print(f"{Fore.RED}✗ Nenhum resultado. Execute 'pipeline' primeiro.{Style.RESET_ALL}")
        sys.exit(1)

    from pipeline.export import load_json, save_csv, save_ris, save_bibtex, save_report
    from pipeline.dedup import unique_papers

    all_papers = load_json(source)
    unique = unique_papers(all_papers)

    save_csv(all_papers, RESULTS_DIR / "all_papers.csv")
    save_csv(unique, RESULTS_DIR / "unique_papers.csv")
    save_ris(unique, RESULTS_DIR / "export.ris")
    save_bibtex(unique, RESULTS_DIR / "export.bib")
    save_report(all_papers, unique, None, RESULTS_DIR / "report.txt")

    print(f"{Fore.GREEN}✓ Exportação concluída.{Style.RESET_ALL}")
    _print_file_list()


# ------------------------------------------------------------------ #
#  Subcommand: status                                                 #
# ------------------------------------------------------------------ #

def cmd_status(args):
    from collections import Counter

    print(f"\n{Fore.CYAN}SLR PATHCAST — Status{Style.RESET_ALL}")
    print("-" * 50)

    # Raw files
    raw_files = list(RAW_DIR.glob("*.json")) if RAW_DIR.exists() else []
    print(f"\n  Raw results ({len(raw_files)} queries executadas):")
    for f in sorted(raw_files):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            print(f"    {f.stem:<40} {len(data):>5,} papers")
        except Exception:
            print(f"    {f.stem:<40}  (erro ao ler)")

    for label, fpath in [("Combined", COMBINED_FILE), ("Deduplicated", DEDUP_FILE)]:
        if fpath.exists():
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                unique = sum(1 for p in data if not p.get("is_duplicate"))
                print(f"\n  {label}: {len(data):,} total, {unique:,} únicos")
            except Exception:
                print(f"\n  {label}: (erro ao ler)")
        else:
            print(f"\n  {label}: não gerado ainda")

    # Arquivos de exportação
    export_files = [
        RESULTS_DIR / "export.ris",
        RESULTS_DIR / "export.bib",
        RESULTS_DIR / "unique_papers.csv",
        RESULTS_DIR / "report.txt",
    ]
    print("\n  Exports:")
    for f in export_files:
        status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if f.exists() else f"{Fore.RED}✗{Style.RESET_ALL}"
        print(f"    {status} {f.name}")

    print()


# ------------------------------------------------------------------ #
#  Subcommand: queries                                                #
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
#  Subcommand: screen                                                 #
# ------------------------------------------------------------------ #

def cmd_screen(args):
    """Triagem de títulos e resumos via Anthropic Batches API."""
    from pipeline.screening import (
        run_screening, print_and_save_stats,
        RESULTS_CSV, SCREENING_DIR,
    )

    # Apenas exibir estatísticas
    if getattr(args, "stats", False):
        print_and_save_stats()
        return

    # Arquivo de entrada
    input_csv = Path(getattr(args, "input", "") or
                     "results/working_set/operational_screening_primary_unique.csv")
    if not input_csv.exists():
        print(f"{Fore.RED}✗ Arquivo não encontrado: {input_csv}{Style.RESET_ALL}")
        sys.exit(1)

    # Chave Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key and not getattr(args, "dry_run", False):
        print(
            f"{Fore.RED}✗ ANTHROPIC_API_KEY não configurada.{Style.RESET_ALL}\n"
            f"  Adicione ANTHROPIC_API_KEY=... ao seu .env"
        )
        sys.exit(1)

    run_screening(
        input_csv=input_csv,
        api_key=api_key,
        poll=getattr(args, "poll", False),
        poll_interval=getattr(args, "poll_interval", 60),
        batch_id=getattr(args, "collect", None),
        dry_run=getattr(args, "dry_run", False),
        limit=getattr(args, "limit", 0),
        force=getattr(args, "force", False),
        enrich=getattr(args, "enrich", False),
    )


# ------------------------------------------------------------------ #
#  Subcommand: enrich-ws                                              #
# ------------------------------------------------------------------ #

def cmd_enrich_ws(args):
    """Enriquece abstracts da working set via cascata de fontes (sem precisar da chave Anthropic)."""
    from pipeline.screening import load_working_set, enrich_working_set, ENRICHED_WS_CSV, SCREENING_DIR

    input_csv = Path(getattr(args, "input", "") or
                     "results/working_set/operational_screening_primary_unique.csv")
    if not input_csv.exists():
        print(f"{Fore.RED}✗ Arquivo não encontrado: {input_csv}{Style.RESET_ALL}")
        sys.exit(1)

    # Se já existe enriquecida e não é --force, usa ela
    source = input_csv
    if ENRICHED_WS_CSV.exists() and not getattr(args, "force", False):
        print(f"{Fore.YELLOW}⚠ Arquivo enriquecido já existe: {ENRICHED_WS_CSV}{Style.RESET_ALL}")
        print(f"  Use --force para re-enriquecer a partir do zero.")
        source = ENRICHED_WS_CSV

    print(f"\n{Fore.CYAN}── Carregando working set: {source.name}...{Style.RESET_ALL}")
    papers = load_working_set(source)
    total = len(papers)
    sem = sum(1 for p in papers if not (p.get("abstract") or "").strip())
    com_doi = sum(1 for p in papers if (p.get("doi") or "").strip() and not (p.get("abstract") or "").strip())

    print(f"  {total:,} papers | sem abstract: {sem:,} | com DOI (buscáveis): {com_doi:,}")

    if sem == 0:
        print(f"\n{Fore.GREEN}✓ Todos os papers já têm abstract. Nada a enriquecer.{Style.RESET_ALL}")
        return

    delay = _get_delay()
    s2_only = getattr(args, "s2_only", False)
    fonte = "Semantic Scholar apenas" if s2_only else "Semantic Scholar + OpenAlex fallback"
    print(f"\n{Fore.CYAN}── Buscando abstracts ({fonte}, delay={delay}s/lote)...{Style.RESET_ALL}")
    papers, n_enriched = enrich_working_set(papers, delay=delay, s2_only=s2_only)

    sem_depois = sum(1 for p in papers if not (p.get("abstract") or "").strip())
    print(f"\n{Fore.GREEN}✓ {n_enriched:,} abstracts preenchidos.{Style.RESET_ALL}")
    print(f"  Ainda sem abstract: {sem_depois:,} (provavelmente sem DOI ou não indexados no OpenAlex)")
    print(f"  Working set enriquecida salva em: {ENRICHED_WS_CSV}")


# ------------------------------------------------------------------ #
#  Subcommand: fulltext                                               #
# ------------------------------------------------------------------ #

def cmd_fulltext(args):
    """Full-text screening: export fila priorizada, enriquece URLs, LLM re-triagem."""
    from pipeline.fulltext import run_fulltext

    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Pelo menos uma ação deve ser especificada
    do_export      = getattr(args, "export", False)
    do_enrich_abstracts = getattr(args, "enrich_abstracts", False)
    do_enrich_urls = getattr(args, "enrich_urls", False)
    do_llm         = getattr(args, "llm_rescreen", False)
    do_collect     = getattr(args, "collect", None)
    do_stats       = getattr(args, "stats", False)
    do_screen_blanks = getattr(args, "screen_blanks", False)

    if not any([do_export, do_enrich_abstracts, do_enrich_urls, do_llm, do_collect, do_stats, do_screen_blanks]):
        # sem flags → exporta fila + stats (ação padrão útil)
        do_export = True
        do_stats = True

    from pipeline.fulltext import TA_RESULTS_CSV
    if not TA_RESULTS_CSV.exists():
        print(
            f"{Fore.RED}✗ Triagem T/A não encontrada: {TA_RESULTS_CSV}\n"
            f"  Execute 'python main.py screen --poll' primeiro.{Style.RESET_ALL}"
        )
        sys.exit(1)

    run_fulltext(
        export=do_export,
        enrich_abstracts=do_enrich_abstracts,
        enrich_urls=do_enrich_urls,
        llm_rescreen=do_llm,
        confirm_includes=getattr(args, "confirm_includes", False),
        screen_blanks=do_screen_blanks,
        collect=do_collect,
        stats=do_stats,
        poll=getattr(args, "poll", False),
        poll_interval=getattr(args, "poll_interval", 60),
        dry_run=getattr(args, "dry_run", False),
        force=getattr(args, "force", False),
        api_key=api_key,
        delay=_get_delay(),
    )


def cmd_download_pdfs(args):
    """Download PDFs para os papers confirmados para leitura integral."""
    from pipeline.pdf_downloader import download_pdfs, print_download_stats

    if getattr(args, "stats", False):
        print_download_stats()
        return

    email = os.getenv("OPENALEX_EMAIL", os.getenv("EMAIL", "slr@research.example"))

    import csv
    subset = getattr(args, "subset", "default")

    if subset == "pending-doi-no-pdf":
        from pipeline.finalization import PENDING_DOI_NO_PDF_CSV

        if not PENDING_DOI_NO_PDF_CSV.exists():
            print(
                f"{Fore.RED}✗ Arquivo não encontrado: {PENDING_DOI_NO_PDF_CSV}\n"
                f"  Execute 'python main.py finalize' primeiro.{Style.RESET_ALL}"
            )
            sys.exit(1)

        with open(PENDING_DOI_NO_PDF_CSV, encoding="utf-8-sig", newline="") as f:
            target = list(csv.DictReader(f))
        print(f"{Fore.CYAN}Alvo: {len(target)} papers (pendentes com DOI e sem PDF){Style.RESET_ALL}")
    else:
        # Carrega fila FT
        from pipeline.fulltext import FT_RESULTS_CSV
        if not FT_RESULTS_CSV.exists():
            print(
                f"{Fore.RED}✗ ft_screening_results.csv não encontrado.\n"
                f"  Execute 'python main.py fulltext --export' primeiro.{Style.RESET_ALL}"
            )
            sys.exit(1)

        with open(FT_RESULTS_CSV, encoding="utf-8", newline="") as f:
            papers = list(csv.DictReader(f))

        # Filtra: ft_decision=include  OU  (ta_decision=include E ft_decision em branco)
        target = [
            p for p in papers
            if p.get("ft_decision") == "include"
            or (p.get("ta_decision") == "include" and not (p.get("ft_decision") or "").strip())
        ]
        print(f"{Fore.CYAN}Alvo: {len(target)} papers (FT include + T/A include pendente){Style.RESET_ALL}")

    download_pdfs(
        target,
        email,
        delay=float(os.getenv("REQUEST_DELAY", "1.5")),
        force=getattr(args, "force", False),
        limit=getattr(args, "limit", 0),
        dry_run=getattr(args, "dry_run", False),
    )


def cmd_queries(args):
    from config.queries import QUERIES

    db_filter = getattr(args, "database", None)
    print(f"\n{Fore.CYAN}SLR PATHCAST — Queries Configuradas{Style.RESET_ALL}")

    for db, queries in QUERIES.items():
        if db_filter and db != db_filter:
            continue
        print(f"\n{Fore.YELLOW}[{db.upper()}]{Style.RESET_ALL} ({len(queries)} queries)")
        for q in queries:
            print(f"  {q['id']}")
            print(f"    Label: {q['label']}")
            if q.get("notes"):
                print(f"    Notes: {q['notes']}")
            if getattr(args, "show_query", False):
                print(f"    Query:\n{_indent(q['query'], 6)}")
        print()


def cmd_finalize(args):
    """Gera artefatos para finalizar a SLR: pendências FT, includes atuais e snapshot PRISMA."""
    from pipeline.finalization import export_finalization_artifacts, FT_RESULTS_CSV

    if not FT_RESULTS_CSV.exists():
        print(
            f"{Fore.RED}✗ ft_screening_results.csv não encontrado.\n"
            f"  Execute 'python main.py fulltext --export' primeiro.{Style.RESET_ALL}"
        )
        sys.exit(1)

    artifacts = export_finalization_artifacts()
    print(f"\n{Fore.CYAN}── Artefatos de finalização gerados{Style.RESET_ALL}")
    print(f"  Pendentes FT:   {artifacts['pending_review_count']}")
    print(f"  Includes atuais:{artifacts['included_count']}")
    print(f"  Review sheet:   {artifacts['pending_review_path']}")
    print(f"  Includes:       {artifacts['included_path']}")
    print(f"  PRISMA:         {artifacts['prisma_summary_path']}")


def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line for line in text.splitlines())


def _print_file_list():
    print("\n  Arquivos gerados:")
    for fname in ["all_papers.csv", "unique_papers.csv", "export.ris", "export.bib", "report.txt"]:
        fpath = RESULTS_DIR / fname
        if fpath.exists():
            print(f"    ✓ {fpath}")


# ------------------------------------------------------------------ #
#  CLI Parser                                                         #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="SLR PATHCAST — Agente de Extração de Referências",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Extrai referências via API")
    p_run.add_argument(
        "database",
        choices=["scopus", "ieee", "springer", "wos", "all"],
        help="Base de dados a extrair",
    )
    p_run.add_argument("--query-id", help="Executar apenas esta query (ex: scopus_principal)")
    p_run.add_argument("--force", action="store_true", help="Ignorar cache e re-extrair")
    p_run.set_defaults(func=cmd_run)

    # import
    p_import = sub.add_parser("import", help="Importa arquivo exportado manualmente")
    p_import.add_argument("database", choices=["acm", "wos", "scopus", "ieee", "springer", "control", "csv", "unknown"])
    p_import.add_argument("--file", required=True, help="Caminho do arquivo a importar")
    p_import.add_argument("--query-id", default="", help="ID da query para rastreabilidade")
    p_import.add_argument("--query-label", default="", help="Label legível da query")
    p_import.add_argument(
        "--format", default="auto",
        choices=["auto", "bibtex", "ris", "plaintext", "csv"],
        help="Formato do arquivo (auto detecta pela extensão)",
    )
    p_import.set_defaults(func=cmd_import)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Dedup + enrich + validate + export")
    p_pipe.add_argument(
        "--no-enrich", action="store_true",
        help="Pular enriquecimento de abstracts via cascata de fontes"
    )
    p_pipe.set_defaults(func=cmd_pipeline)

    # snowball
    p_snow = sub.add_parser("snowball", help="Snowballing automático via OpenAlex")
    p_snow.add_argument(
        "--direction",
        choices=["backward", "forward", "both"],
        default="both",
        help="Direção: backward (referências), forward (citações) ou both (padrão)",
    )
    p_snow.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Processar apenas os primeiros N seeds com DOI (0 = todos)",
    )
    p_snow.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar resultados sem salvar no corpus",
    )
    p_snow.set_defaults(func=cmd_snowball)

    # enrich
    p_enrich = sub.add_parser("enrich", help="Preenche abstracts via cascata (S2, OpenAlex, Crossref, CORE)")
    p_enrich.set_defaults(func=cmd_enrich)

    # validate
    p_val = sub.add_parser("validate", help="Valida os 10 papers de controle")
    p_val.set_defaults(func=cmd_validate)

    # export
    p_exp = sub.add_parser("export", help="Re-exporta RIS/CSV/BibTeX/relatório")
    p_exp.set_defaults(func=cmd_export)

    # status
    p_status = sub.add_parser("status", help="Resumo dos resultados atuais")
    p_status.set_defaults(func=cmd_status)

    # enrich-ws
    p_ews = sub.add_parser("enrich-ws", help="Enriquece abstracts da working set via cascata de fontes")
    p_ews.add_argument(
        "--input",
        default="results/working_set/operational_screening_primary_unique.csv",
        help="CSV de entrada (padrão: working set operacional)",
    )
    p_ews.add_argument(
        "--force", action="store_true",
        help="Re-enriquecer a partir do zero mesmo que já exista versão enriquecida",
    )
    p_ews.add_argument(
        "--s2-only", action="store_true",
        help="Usar apenas Semantic Scholar (pula OpenAlex fallback) — útil quando OA está rate-limited",
    )
    p_ews.set_defaults(func=cmd_enrich_ws)

    # screen
    p_screen = sub.add_parser("screen", help="Triagem de títulos e resumos via Anthropic Batches API")
    p_screen.add_argument(
        "--input",
        default="results/working_set/operational_screening_primary_unique.csv",
        help="CSV de entrada (padrão: working set operacional)",
    )
    p_screen.add_argument(
        "--poll", action="store_true",
        help="Aguardar o batch terminar antes de encerrar",
    )
    p_screen.add_argument(
        "--poll-interval", type=int, default=60, metavar="N",
        help="Segundos entre cada verificação de status (padrão: 60)",
    )
    p_screen.add_argument(
        "--collect", metavar="BATCH_ID",
        help="Coletar resultados de um batch_id já concluído",
    )
    p_screen.add_argument(
        "--dry-run", action="store_true",
        help="Mostrar preview do prompt sem enviar o batch",
    )
    p_screen.add_argument(
        "--limit", type=int, default=0, metavar="N",
        help="Processar apenas os primeiros N papers pendentes (0=todos)",
    )
    p_screen.add_argument(
        "--force", action="store_true",
        help="Re-triar papers já com decisão",
    )
    p_screen.add_argument(
        "--enrich", action="store_true",
        help="Buscar abstracts no OpenAlex antes de enviar o batch (recomendado na primeira execução)",
    )
    p_screen.add_argument(
        "--stats", action="store_true",
        help="Mostrar estatísticas da triagem atual e encerrar",
    )
    p_screen.set_defaults(func=cmd_screen)

    # fulltext
    p_ft = sub.add_parser("fulltext", help="Full-text screening: fila priorizada, URLs OA, LLM re-triagem")
    p_ft.add_argument(
        "--export", action="store_true",
        help="Gerar/atualizar ft_screening_results.csv com fila priorizada",
    )
    p_ft.add_argument(
        "--enrich-abstracts", dest="enrich_abstracts", action="store_true",
        help="Buscar abstracts na cascata Semantic Scholar, OpenAlex, Crossref e CORE",
    )
    p_ft.add_argument(
        "--enrich-urls", dest="enrich_urls", action="store_true",
        help="Buscar PDFs open-access via Semantic Scholar e adicionar coluna ft_oa_url",
    )
    p_ft.add_argument(
        "--llm-rescreen", dest="llm_rescreen", action="store_true",
        help="LLM re-triagem dos papers 'maybe' com abstract disponível",
    )
    p_ft.add_argument(
        "--collect", metavar="BATCH_ID",
        help="Coletar resultados de batch LLM já concluído",
    )
    p_ft.add_argument(
        "--stats", action="store_true",
        help="Mostrar estatísticas de progresso do full-text screening",
    )
    p_ft.add_argument(
        "--poll", action="store_true",
        help="Aguardar o batch LLM terminar antes de encerrar",
    )
    p_ft.add_argument(
        "--poll-interval", dest="poll_interval", type=int, default=60, metavar="N",
        help="Segundos entre polls (padrão: 60)",
    )
    p_ft.add_argument(
        "--confirm-includes", dest="confirm_includes", action="store_true",
        help="Incluir papers T/A 'include' (com abstract) na re-triagem LLM — segunda opinião",
    )
    p_ft.add_argument(
        "--screen-blanks", dest="screen_blanks", action="store_true",
        help="Triar LLM todos os papers sem decisão FT (blancos), independente de abstract",
    )
    p_ft.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="Mostrar preview do prompt LLM sem enviar o batch",
    )
    p_ft.add_argument(
        "--force", action="store_true",
        help="Reconstruir fila do zero / re-triar papers já com decisão FT",
    )
    p_ft.set_defaults(func=cmd_fulltext)

    # download-pdfs
    p_dl = sub.add_parser("download-pdfs", help="Baixa PDFs dos papers confirmados para leitura integral")
    p_dl.add_argument(
        "--subset",
        choices=["default", "pending-doi-no-pdf"],
        default="default",
        help="Subset alvo para download: default (includes) ou pending-doi-no-pdf",
    )
    p_dl.add_argument(
        "--stats", action="store_true",
        help="Mostrar resumo do manifesto de downloads",
    )
    p_dl.add_argument(
        "--force", action="store_true",
        help="Re-baixar mesmo que o PDF já exista",
    )
    p_dl.add_argument(
        "--limit", type=int, default=0, metavar="N",
        help="Processar apenas os primeiros N papers (0=todos)",
    )
    p_dl.add_argument(
        "--dry-run", dest="dry_run", action="store_true",
        help="Mostrar o que seria feito sem baixar nenhum arquivo",
    )
    p_dl.set_defaults(func=cmd_download_pdfs)

    # queries
    p_queries = sub.add_parser("queries", help="Lista todas as queries configuradas")
    p_queries.add_argument("--database", help="Filtrar por base")
    p_queries.add_argument("--show-query", action="store_true", help="Mostrar texto completo")
    p_queries.set_defaults(func=cmd_queries)

    # finalize
    p_finalize = sub.add_parser("finalize", help="Gera planilha dos full texts pendentes e snapshot PRISMA atual")
    p_finalize.set_defaults(func=cmd_finalize)

    return parser


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

def main():
    # Garante que o diretório de trabalho é o do script
    os.chdir(Path(__file__).parent)

    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
