"""
Extração de dados via LLM para os 169 estudos incluídos na SLR PATHCAST.

Fluxo:
  1. python pipeline/extract_llm.py --run          # submete batch Anthropic (papers com PDF)
  2. python pipeline/extract_llm.py --collect <id> # salva resultados no template
  3. python pipeline/extract_llm.py --run-abstract # submete papers sem PDF (só abstract/título)
  4. python pipeline/extract_llm.py --collect-abstract <id>

  --dry-run   mostra prompt do primeiro paper sem enviar
  --poll      aguarda batch terminar antes de encerrar
  --force     re-extrai papers que já têm main_finding preenchido
"""
from __future__ import annotations

import csv
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")

EXTRACT_CSV  = Path("results/extraction/extraction_template.csv")
EXTRACT_PDF  = Path("results/extraction/pdfs")
BATCHES_LOG  = Path("results/extraction/extraction_batches.json")

MODEL      = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024
BATCH_SIZE = 100
PDF_MAX_CHARS = 6000  # ~4 páginas

EXTRACTION_FIELDS = [
    "research_question",
    "study_type",
    "research_contribution",
    "pm_technique",
    "stochastic_technique",
    "software_artifact",
    "software_process",
    "dataset_source",
    "dataset_public",
    "tool_used",
    "main_finding",
    "limitations",
    "replication_package",
]


# ── PDF text extraction ───────────────────────────────────────────────────────

def _extract_pdf_text(pdf_path: Path, max_chars: int = PDF_MAX_CHARS) -> str:
    try:
        import pdfplumber
    except ImportError:
        logger.error("pdfplumber não instalado no ambiente atual.")
        return ""

    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:8]:
                t = page.extract_text() or ""
                t = re.sub(r"\(cid:\d+\)", "", t)
                text_parts.append(t)
                if sum(len(x) for x in text_parts) >= max_chars:
                    break
    except Exception as exc:
        logger.warning(f"Erro ao extrair PDF {pdf_path.name}: {exc}")
        return ""

    full = "\n".join(text_parts)
    return full[:max_chars].strip()


# ── Prompt ────────────────────────────────────────────────────────────────────

def _build_extraction_prompt(paper: dict, text: str) -> str:
    title   = paper.get("title", "")
    authors = paper.get("authors", "") or "não disponível"
    year    = paper.get("year", "")
    venue   = paper.get("venue", "") or paper.get("journal_name", "") or "não disponível"
    ics     = paper.get("ft_matched_ic", "")
    abstract = paper.get("abstract", "").strip()

    content_block = ""
    if text:
        content_block = f"\n**Texto do paper (primeiras páginas):**\n{text}\n"
    elif abstract:
        content_block = f"\n**Resumo:**\n{abstract}\n"
    else:
        content_block = "\n*(Texto completo e resumo não disponíveis — use apenas título/venue/ICs)*\n"

    return f"""Você é um pesquisador fazendo extração de dados para a SLR PATHCAST sobre Process Mining e Modelagem Estocástica em Processos de Software.

**Título:** {title}
**Autores:** {authors}
**Ano:** {year}  |  **Venue:** {venue}
**Critérios de inclusão atendidos:** {ics}
{content_block}
Retorne SOMENTE um objeto JSON válido com exatamente estes campos:

{{
  "research_question": "pergunta de pesquisa principal (1-2 frases)",
  "study_type": "case_study | experiment | survey | tool | theoretical | simulation | mixed",
  "research_contribution": "discovery | conformance | enhancement | prediction | simulation | framework | hybrid (múltiplos separados por |)",
  "pm_technique": "alpha | inductive_miner | heuristic | conformance_checking | social_network | declarative | other | none (múltiplos por |)",
  "stochastic_technique": "markov_chain | stochastic_petri_net | monte_carlo | system_dynamics | other | none (múltiplos por |)",
  "software_artifact": "commits | issues | ci_cd | ide_logs | vcs | jira | github | other | none (múltiplos por |)",
  "software_process": "development | testing | maintenance | code_review | bug_fixing | deployment | requirements | other (múltiplos por |)",
  "dataset_source": "open_source | industrial | academic | synthetic | not_specified",
  "dataset_public": "sim | não | parcial | não_mencionado",
  "tool_used": "nomes das ferramentas (ex: ProM, pm4py, Disco) ou não_mencionado",
  "main_finding": "principal resultado/contribuição (2-3 frases)",
  "limitations": "limitações reportadas (1-2 frases) ou não_mencionado",
  "replication_package": "sim | não | parcial | não_mencionado"
}}

Responda APENAS com o JSON, sem texto adicional."""


# ── Anthropic batch helpers ───────────────────────────────────────────────────

def _submit_batch(candidates: list[dict], api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    requests_list = []
    for paper in candidates:
        pdf_file = (paper.get("pdf_file") or "").strip()
        text = ""
        if pdf_file:
            pdf_path = EXTRACT_PDF / pdf_file
            if pdf_path.exists():
                text = _extract_pdf_text(pdf_path)

        prompt = _build_extraction_prompt(paper, text)
        requests_list.append({
            "custom_id": paper["internal_id"],
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            },
        })

    logger.info(f"[EXTRACT] Enviando batch com {len(requests_list)} papers...")
    batch = client.messages.batches.create(requests=requests_list)
    logger.info(f"[EXTRACT] Batch criado: {batch.id}")
    return batch.id


def _poll_batch(batch_id: str, api_key: str, interval: int = 60) -> None:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    print(f"  Aguardando batch {batch_id}... (Ctrl+C para interromper)")
    while True:
        b = client.messages.batches.retrieve(batch_id)
        rc = b.request_counts
        print(f"  [{time.strftime('%H:%M:%S')}] {b.processing_status} — "
              f"succeeded: {rc.succeeded} | errored: {rc.errored} | processing: {rc.processing}")
        if b.processing_status == "ended":
            break
        time.sleep(interval)


def _collect_results(batch_id: str, api_key: str, rows: list[dict]) -> int:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    b = client.messages.batches.retrieve(batch_id)
    if b.processing_status != "ended":
        print(f"  Batch {batch_id} ainda em processamento ({b.processing_status}).")
        return 0

    index = {r["internal_id"]: r for r in rows}
    saved = 0

    for result in client.messages.batches.results(batch_id):
        iid = result.custom_id
        if result.result.type != "succeeded":
            logger.warning(f"[EXTRACT] {iid} — erro: {result.result.type}")
            continue

        raw = result.result.message.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"[EXTRACT] {iid} — JSON inválido: {raw[:120]}")
            continue

        row = index.get(iid)
        if row is None:
            continue

        for field in EXTRACTION_FIELDS:
            val = data.get(field, "")
            if val:
                row[field] = str(val).strip()
        saved += 1

    _save_csv(rows)
    logger.info(f"[EXTRACT] {saved} extrações salvas em {EXTRACT_CSV}")
    return saved


# ── CSV helpers ───────────────────────────────────────────────────────────────

def _load_template() -> tuple[list[dict], list[str]]:
    with open(EXTRACT_CSV, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = reader.fieldnames or list(rows[0].keys())
    return rows, fieldnames


def _save_csv(rows: list[dict]) -> None:
    _, fieldnames = _load_template()
    with open(EXTRACT_CSV, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _log_batch(batch_id: str, mode: str, count: int) -> None:
    BATCHES_LOG.parent.mkdir(parents=True, exist_ok=True)
    log = []
    if BATCHES_LOG.exists():
        log = json.loads(BATCHES_LOG.read_text())
    log.append({"batch_id": batch_id, "mode": mode, "count": count,
                 "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    BATCHES_LOG.write_text(json.dumps(log, indent=2))


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_run(api_key: str, *, dry_run: bool, poll: bool, poll_interval: int,
            force: bool, abstract_only: bool) -> None:
    from colorama import Fore, Style
    rows, _ = _load_template()

    if abstract_only:
        candidates = [
            r for r in rows
            if not (r.get("pdf_file") or "").strip()
            and (r.get("abstract") or r.get("title"))
            and (force or not (r.get("main_finding") or "").strip())
        ]
        mode = "abstract"
        label = "sem PDF (abstract/título)"
    else:
        candidates = [
            r for r in rows
            if (r.get("pdf_file") or "").strip()
            and (EXTRACT_PDF / r["pdf_file"]).exists()
            and (force or not (r.get("main_finding") or "").strip())
        ]
        mode = "pdf"
        label = "com PDF"

    print(f"\n{Fore.CYAN}── LLM extraction ({label}): {len(candidates)} papers...{Style.RESET_ALL}")

    if not candidates:
        print(f"  {Fore.YELLOW}Nenhum paper elegível. Use --force para re-extrair.{Style.RESET_ALL}")
        return

    if dry_run:
        p = candidates[0]
        pdf_file = (p.get("pdf_file") or "").strip()
        text = _extract_pdf_text(EXTRACT_PDF / pdf_file) if pdf_file else ""
        print(f"\n{Fore.YELLOW}--dry-run — prompt para '{p['title'][:60]}'::{Style.RESET_ALL}")
        print(_build_extraction_prompt(p, text)[:1200])
        return

    batches_sent = []
    for start in range(0, len(candidates), BATCH_SIZE):
        chunk = candidates[start:start + BATCH_SIZE]
        bid = _submit_batch(chunk, api_key)
        batches_sent.append((bid, chunk))
        _log_batch(bid, mode, len(chunk))
        print(f"  {Fore.GREEN}✓ Batch enviado: {bid}  ({len(chunk)} papers){Style.RESET_ALL}")

        if poll:
            print(f"\n{Fore.CYAN}── Aguardando batch {bid}...{Style.RESET_ALL}")
            _poll_batch(bid, api_key, poll_interval)
            n = _collect_results(bid, api_key, rows)
            print(f"  {Fore.GREEN}✓ {n} extrações salvas{Style.RESET_ALL}")

    if not poll:
        print(f"\n{Fore.YELLOW}Para coletar resultados:{Style.RESET_ALL}")
        for bid, _ in batches_sent:
            print(f"  python pipeline/extract_llm.py --collect {bid}")


def cmd_collect(batch_id: str, api_key: str, abstract_only: bool) -> None:
    from colorama import Fore, Style
    rows, _ = _load_template()
    print(f"\n{Fore.CYAN}── Coletando resultados do batch {batch_id}...{Style.RESET_ALL}")
    n = _collect_results(batch_id, api_key, rows)
    print(f"  {Fore.GREEN}✓ {n} extrações salvas em {EXTRACT_CSV}{Style.RESET_ALL}")

    filled = sum(1 for r in rows if (r.get("main_finding") or "").strip())
    total  = len(rows)
    print(f"  Progresso: {filled}/{total} papers com main_finding preenchido")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    from colorama import init
    init(autoreset=True)

    parser = argparse.ArgumentParser(description="Extração de dados via LLM para SLR PATHCAST")
    parser.add_argument("--run", action="store_true", help="Submeter batch (papers com PDF)")
    parser.add_argument("--run-abstract", dest="run_abstract", action="store_true",
                        help="Submeter batch (papers sem PDF, usando abstract/título)")
    parser.add_argument("--collect", metavar="BATCH_ID", help="Coletar resultados de batch PDF")
    parser.add_argument("--collect-abstract", dest="collect_abstract", metavar="BATCH_ID",
                        help="Coletar resultados de batch abstract")
    parser.add_argument("--poll", action="store_true", help="Aguardar batch terminar")
    parser.add_argument("--poll-interval", dest="poll_interval", type=int, default=60)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-extrair mesmo papers já extraídos")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("ANTHROPIC_API_KEY não configurada.")
        sys.exit(1)

    if args.run:
        cmd_run(api_key, dry_run=args.dry_run, poll=args.poll,
                poll_interval=args.poll_interval, force=args.force, abstract_only=False)
    elif args.run_abstract:
        cmd_run(api_key, dry_run=args.dry_run, poll=args.poll,
                poll_interval=args.poll_interval, force=args.force, abstract_only=True)
    elif args.collect:
        cmd_collect(args.collect, api_key, abstract_only=False)
    elif args.collect_abstract:
        cmd_collect(args.collect_abstract, api_key, abstract_only=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
