"""
extract_table38.py
Extração estruturada da Tabela 3.8 (SLR PATHCAST) via Anthropic Batches API.

Autor: Rodrigo Almeida de Oliveira
Tese: PATHCAST — PUC-PR, 2026
"""

import argparse
import base64
import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import anthropic

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1500
POLL_INTERVAL = 30
MAX_POLLS = 120

QA_RETAINED_IDS: set[str] = set()

# ---------------------------------------------------------------------------
# VOCABULÁRIO CONTROLADO
# ---------------------------------------------------------------------------
VOCAB: dict[str, list[str]] = {
    "sdlc_phase": [
        "development", "testing", "maintenance", "code_review",
        "bug_fixing", "deployment", "requirements", "multiple", "other", "not_specified",
    ],
    "event_log_source": [
        "commits", "issues", "ci_cd", "ide_logs", "vcs", "jira",
        "github", "gitlab", "jenkins", "other", "none", "not_specified",
    ],
    "event_log_construction": ["manual", "semi_automatic", "automatic", "not_specified"],
    "pm_technique_category": [
        "discovery", "conformance", "enhancement", "prediction",
        "simulation", "framework", "hybrid", "none",
    ],
    "stochastic_method": [
        "markov_chain", "hidden_markov_model", "monte_carlo",
        "stochastic_petri_net", "bayesian_model", "probabilistic_model",
        "simulation", "queueing_model", "vlmc", "other_stochastic", "none",
    ],
    "ml_technique": [
        "random_forest", "xgboost", "catboost", "svm", "naive_bayes",
        "decision_tree", "lstm", "cnn", "transformer", "gradient_boosting",
        "logistic_regression", "reinforcement_learning", "other_ml", "none",
    ],
    "prediction_target": [
        "lead_time", "cycle_time", "remaining_time", "throughput",
        "defect_rate", "build_outcome", "reliability", "completion_time",
        "other_process_metric", "none",
    ],
    "integration_level": ["L0", "L1", "L2", "L3"],
    "validation_type": [
        "case_study", "experiment", "industrial", "simulation",
        "survey", "theoretical", "mixed",
    ],
    "dataset_source": ["open_source", "industrial", "academic", "synthetic", "not_specified"],
    "replication_package": ["yes", "no", "partial", "not_mentioned"],
    "pdf_available": ["yes", "no"],
}

# ---------------------------------------------------------------------------
# PROMPTS
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a systematic literature review extraction assistant.
Your task is to extract structured bibliographic and methodological attributes
from academic papers in the domain of process mining, software engineering,
and stochastic modeling.

You MUST respond with a single valid JSON object and nothing else.
Do not include markdown, code fences, preamble, or explanation.
If a field cannot be determined from the available text, use the
designated null value for that field as specified in the schema."""


def build_extraction_prompt(study: dict) -> str:
    vocab_json = json.dumps(VOCAB, indent=2)
    return f"""Extract the following fields from this academic paper.

PAPER METADATA:
ID: {study.get('id', 'unknown')}
Title: {study.get('title', '')}
Authors: {study.get('authors', '')}
Year: {study.get('year', '')}
Venue: {study.get('venue', '')}

CONTROLLED VOCABULARY (use only these values for enum fields):
{vocab_json}

Return a JSON object with EXACTLY these fields:

{{
  "id": "<copy from metadata>",
  "title": "<paper title>",
  "authors": "<author list>",
  "year": <integer year>,
  "venue": "<journal or conference name>",
  "sdlc_phase": ["<from vocab>"],
  "event_log_source": ["<from vocab>"],
  "event_log_construction": "<from vocab: single value>",
  "pm_technique_category": ["<from vocab>"],
  "specific_algorithms": ["<free text: algorithm names>"],
  "stochastic_method": ["<from vocab>"],
  "ml_technique": ["<from vocab>"],
  "prediction_target": ["<from vocab>"],
  "integration_level": "<L0|L1|L2|L3>",
  "validation_type": "<from vocab: single value>",
  "tool_platform": ["<free text: tool names>"],
  "dataset_n_cases": <integer or null>,
  "dataset_n_events": <integer or null>,
  "dataset_source": "<from vocab: single value>",
  "process_model_fitness": <float 0-1 or null>,
  "process_model_precision": <float 0-1 or null>,
  "replication_package": "<from vocab: single value>",
  "main_finding": "<2-3 sentence summary>",
  "limitations": "<1-2 sentence summary>",
  "rq_coverage": ["RQ1","RQ2","RQ3"],
  "extraction_confidence": "<low|medium|high>",
  "extraction_notes": "<free text: any caveats>"
}}

INTEGRATION LEVEL DEFINITIONS:
L0: Single technique family; no cross-technique chaining
L1: Two families present but no formal reproducible pipeline contract
L2: Partial bridge: PM and stochastic linked but incomplete or missing ML
L3: Unified: PM → Markov → MC → ML with formal inter-stage contracts

RQ COVERAGE:
RQ1: addresses SDLC phases and event log sources/construction
RQ2: addresses process mining algorithms and stochastic/ML techniques
RQ3: addresses integration level and gap analysis

For list fields, return a JSON array even if only one value.
For numeric fields, return null if not reported.
For integration_level, make your best judgment from the methods described.
"""


# ---------------------------------------------------------------------------
# LEITURA DE ENTRADA
# ---------------------------------------------------------------------------
def load_studies(csv_path: str) -> list[dict]:
    studies = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append(dict(row))

    print(f"  Estudos carregados: {len(studies)}")
    with_pdf = sum(1 for s in studies if s.get("pdf_path", "").strip())
    print(f"  Com PDF local:      {with_pdf} ({100 * with_pdf // len(studies)}%)")
    print(f"  Somente metadados:  {len(studies) - with_pdf}")

    qa_ids = {s["id"] for s in studies if s.get("id") in QA_RETAINED_IDS}
    if qa_ids:
        print(f"\n  [ATENÇÃO] {len(qa_ids)} estudos QA-retidos detectados.")
        for sid in sorted(qa_ids):
            print(f"    → {sid}")

    return studies


def read_pdf_base64(pdf_path: str) -> Optional[str]:
    path = Path(pdf_path)
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"  [AVISO] Falha ao ler PDF {pdf_path}: {e}")
        return None


# ---------------------------------------------------------------------------
# CONSTRUÇÃO DOS REQUESTS
# ---------------------------------------------------------------------------
def build_batch_requests(studies: list[dict], test_n: Optional[int] = None) -> list[dict]:
    if test_n:
        studies = studies[:test_n]
        print(f"\n  [MODO TESTE] Limitando a {test_n} estudos.")

    requests_list = []
    for study in studies:
        sid = study.get("id", f"study_{len(requests_list):04d}")
        is_qa = sid in QA_RETAINED_IDS
        prompt = build_extraction_prompt(study)
        pdf_path = study.get("pdf_path", "").strip()
        pdf_b64 = read_pdf_base64(pdf_path) if pdf_path else None

        if pdf_b64:
            content = [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": prompt},
            ]
            source = "pdf"
        else:
            abstract = study.get("abstract", "").strip()
            abstract_block = f"\nABSTRACT:\n{abstract}" if abstract else "\nABSTRACT: Not available."
            content = [{"type": "text", "text": prompt + abstract_block}]
            source = "metadata"

        requests_list.append({
            "custom_id": sid,
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": content}],
                "_meta": {"source": source, "is_qa_retained": is_qa, "title": study.get("title", "")},
            },
        })

    print(f"  Requests preparados: {len(requests_list)}")
    pdf_count = sum(1 for r in requests_list if r["params"]["_meta"]["source"] == "pdf")
    print(f"  Com PDF: {pdf_count} | Somente metadados: {len(requests_list) - pdf_count}")
    return requests_list


def strip_internal_meta(requests_list: list[dict]) -> list[dict]:
    return [
        {"custom_id": r["custom_id"], "params": {k: v for k, v in r["params"].items() if k != "_meta"}}
        for r in requests_list
    ]


# ---------------------------------------------------------------------------
# SUBMISSÃO
# ---------------------------------------------------------------------------
def submit_batch(requests_list: list[dict], client: anthropic.Anthropic) -> str:
    print(f"\n  Submetendo {len(requests_list)} requests ao Batches API...")
    clean = strip_internal_meta(requests_list)
    batch = client.messages.batches.create(requests=clean)
    print(f"  Batch submetido: {batch.id}")
    print(f"  Status inicial:  {batch.processing_status}")
    return batch.id


def save_batch_id(batch_id: str, output_dir: Path) -> None:
    path = output_dir / "batch_id.txt"
    path.write_text(batch_id)
    print(f"  batch_id salvo em: {path}")


# ---------------------------------------------------------------------------
# POLLING
# ---------------------------------------------------------------------------
def poll_until_complete(batch_id: str, client: anthropic.Anthropic) -> None:
    print(f"\n  Aguardando conclusão do batch {batch_id}...")
    print(f"  (verificação a cada {POLL_INTERVAL}s, timeout {MAX_POLLS * POLL_INTERVAL // 60} min)")

    for attempt in range(1, MAX_POLLS + 1):
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        c = batch.request_counts
        total = c.processing + c.succeeded + c.errored + c.canceled + c.expired
        done = c.succeeded + c.errored + c.canceled + c.expired
        print(f"  [{attempt:03d}] {status} — {done}/{total} (✓{c.succeeded} ✗{c.errored})")

        if status == "ended":
            print(f"\n  Batch concluído: {c.succeeded} sucessos, {c.errored} erros")
            return

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Batch {batch_id} não concluiu em {MAX_POLLS * POLL_INTERVAL // 60} minutos.")


# ---------------------------------------------------------------------------
# PARSING E VALIDAÇÃO
# ---------------------------------------------------------------------------
def parse_llm_json(text: str) -> Optional[dict]:
    clean = re.sub(r"```json\s*|```\s*", "", text).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def validate_vocab(extracted: dict) -> list[str]:
    warnings: list[str] = []
    field_map = {
        "sdlc_phase":             ("sdlc_phase", True),
        "event_log_source":       ("event_log_source", True),
        "event_log_construction": ("event_log_construction", False),
        "pm_technique_category":  ("pm_technique_category", True),
        "stochastic_method":      ("stochastic_method", True),
        "ml_technique":           ("ml_technique", True),
        "prediction_target":      ("prediction_target", True),
        "integration_level":      ("integration_level", False),
        "validation_type":        ("validation_type", False),
        "dataset_source":         ("dataset_source", False),
        "replication_package":    ("replication_package", False),
    }
    for field, (vocab_key, is_list) in field_map.items():
        value = extracted.get(field)
        if value is None:
            warnings.append(f"Campo ausente: {field}")
            continue
        allowed = VOCAB.get(vocab_key, [])
        values = value if is_list else [value]
        for v in values:
            if v not in allowed:
                warnings.append(f"Valor inválido em '{field}': '{v}'")
    conf = extracted.get("extraction_confidence")
    if conf not in ("low", "medium", "high", None):
        warnings.append(f"extraction_confidence inválido: '{conf}'")
    return warnings


def parse_batch_results(
    batch_id: str,
    client: anthropic.Anthropic,
    meta_map: dict,
    output_dir: Path,
) -> tuple[list[dict], list[dict]]:
    extractions: list[dict] = []
    errors: list[dict] = []
    raw_dir = output_dir / "raw_responses"
    raw_dir.mkdir(exist_ok=True)

    for result in client.messages.batches.results(batch_id):
        sid = result.custom_id
        meta = meta_map.get(sid, {})
        is_qa = meta.get("is_qa_retained", False)

        if result.result.type == "succeeded":
            text = result.result.message.content[0].text
            (raw_dir / f"{sid}.json").write_text(
                json.dumps({"custom_id": sid, "text": text}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            parsed = parse_llm_json(text)
            if parsed is None:
                errors.append({"id": sid, "error": "json_parse_failure", "raw_text": text[:500]})
                continue
            parsed["_source"] = meta.get("source", "unknown")
            parsed["_is_qa_retained"] = is_qa
            parsed["_needs_human_review"] = is_qa
            vocab_warnings = validate_vocab(parsed)
            parsed["_vocab_warnings"] = vocab_warnings
            if vocab_warnings:
                parsed["_needs_human_review"] = True
            extractions.append(parsed)

        elif result.result.type == "errored":
            errors.append({
                "id": sid,
                "error": result.result.error.type,
                "message": getattr(result.result.error, "message", ""),
            })
        else:
            errors.append({"id": sid, "error": f"unexpected_type: {result.result.type}"})

    return extractions, errors


# ---------------------------------------------------------------------------
# EXPORTAÇÃO
# ---------------------------------------------------------------------------
CSV_FIELDS = [
    "id", "title", "authors", "year", "venue",
    "sdlc_phase", "event_log_source", "event_log_construction",
    "pm_technique_category", "specific_algorithms", "stochastic_method",
    "ml_technique", "prediction_target", "integration_level",
    "validation_type", "tool_platform",
    "dataset_n_cases", "dataset_n_events", "dataset_source",
    "process_model_fitness", "process_model_precision",
    "replication_package", "main_finding", "limitations",
    "rq_coverage", "extraction_confidence", "extraction_notes",
    "_source", "_is_qa_retained", "_needs_human_review", "_vocab_warnings",
]


def flatten_for_csv(record: dict) -> dict:
    flat = {}
    for k, v in record.items():
        if isinstance(v, list):
            flat[k] = "; ".join(str(x) for x in v)
        elif v is None:
            flat[k] = ""
        else:
            flat[k] = str(v)
    return flat


def export_results(extractions: list[dict], errors: list[dict], output_dir: Path) -> None:
    json_path = output_dir / "table38_extractions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(extractions, f, ensure_ascii=False, indent=2)

    csv_path = output_dir / "table38_extractions.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rec in extractions:
            writer.writerow(flatten_for_csv(rec))

    if errors:
        err_path = output_dir / "extraction_errors.json"
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)

    human_review = [r for r in extractions if r.get("_needs_human_review")]
    review_path = output_dir / "human_review_required.json"
    with open(review_path, "w", encoding="utf-8") as f:
        review_export = [
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "reason": "QA-retained" if r.get("_is_qa_retained") else "vocab_warnings",
                "warnings": r.get("_vocab_warnings", []),
            }
            for r in human_review
        ]
        json.dump(review_export, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  EXTRAÇÃO CONCLUÍDA")
    print(f"{'='*60}")
    print(f"  Estudos extraídos:   {len(extractions)}")
    print(f"  Erros de parsing:    {len(errors)}")
    print(f"  Revisão humana req.: {len(human_review)}")

    il_dist: dict[str, int] = {}
    for r in extractions:
        il = r.get("integration_level", "unknown")
        il_dist[il] = il_dist.get(il, 0) + 1
    print(f"\n  Distribuição Integration Level:")
    for level in ["L0", "L1", "L2", "L3", "unknown"]:
        count = il_dist.get(level, 0)
        print(f"    {level}: {count:3d}  {'█' * count}")

    conf_dist: dict[str, int] = {}
    for r in extractions:
        c = r.get("extraction_confidence", "unknown")
        conf_dist[c] = conf_dist.get(c, 0) + 1
    print(f"\n  Confiança de extração:")
    for level in ["high", "medium", "low", "unknown"]:
        print(f"    {level:8s}: {conf_dist.get(level, 0)}")

    print(f"\n  Arquivos em: {output_dir}/")
    print(f"    {csv_path.name}")
    print(f"    {json_path.name}")
    if errors:
        print(f"    extraction_errors.json ({len(errors)} erros)")
    print(f"    human_review_required.json ({len(human_review)} estudos)")
    print(f"    raw_responses/ ({len(extractions) + len(errors)} respostas brutas)")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# MODO TESTE
# ---------------------------------------------------------------------------
def run_test_mode(studies: list[dict], test_n: int, output_dir: Path) -> None:
    print(f"\n  [MODO TESTE] Validando construção de requests (n={test_n})")
    requests_list = build_batch_requests(studies, test_n)

    for i, req in enumerate(requests_list):
        sid = req["custom_id"]
        meta = req["params"]["_meta"]
        print(f"\n  --- Estudo {i + 1}: {sid} ---")
        print(f"  Fonte: {meta['source']} | QA-retido: {meta['is_qa_retained']}")
        print(f"  Título: {meta['title'][:80]}...")
        msg_content = req["params"]["messages"][0]["content"]
        if isinstance(msg_content, list):
            print(f"  Blocos: {[b.get('type') for b in msg_content]}")

    preview_path = output_dir / "batch_requests_preview.json"
    clean = strip_internal_meta(requests_list)
    for r in clean:
        for msg in r["params"]["messages"]:
            if isinstance(msg["content"], list):
                for block in msg["content"]:
                    if block.get("type") == "document":
                        block["source"]["data"] = block["source"]["data"][:50] + "...[truncated]"
    with open(preview_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)
    print(f"\n  Preview salvo: {preview_path}")
    print(f"  Execute sem --test para submeter o batch real.")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extração estruturada da Tabela 3.8 via Anthropic Batches API"
    )
    parser.add_argument("--input", help="CSV de estudos confirmados")
    parser.add_argument("--output", default="extraction_output", help="Diretório de saída")
    parser.add_argument("--batch-id", help="Retomar polling de batch já submetido")
    parser.add_argument("--parse-only", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--test-n", type=int, default=3)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.parse_only:
        if not args.batch_id:
            batch_id_file = output_dir / "batch_id.txt"
            if batch_id_file.exists():
                args.batch_id = batch_id_file.read_text().strip()
            else:
                print("Erro: informe --batch-id ou coloque batch_id.txt no diretório de saída.")
                sys.exit(1)
        client = anthropic.Anthropic()
        meta_map: dict = {}
        preview_path = output_dir / "batch_requests_preview.json"
        if preview_path.exists():
            with open(preview_path) as f:
                for req in json.load(f):
                    meta_map[req["custom_id"]] = {}
        extractions, errors = parse_batch_results(args.batch_id, client, meta_map, output_dir)
        export_results(extractions, errors, output_dir)
        return

    if not args.input:
        parser.error("--input é obrigatório (exceto com --parse-only)")

    print(f"\nCarregando estudos de: {args.input}")
    studies = load_studies(args.input)

    if args.test:
        run_test_mode(studies, args.test_n, output_dir)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Erro: ANTHROPIC_API_KEY não encontrada no ambiente.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    requests_list = build_batch_requests(studies)

    meta_map = {r["custom_id"]: r["params"]["_meta"] for r in requests_list}
    meta_path = output_dir / "meta_map.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_map, f, ensure_ascii=False, indent=2)

    batch_id = submit_batch(requests_list, client)
    save_batch_id(batch_id, output_dir)
    poll_until_complete(batch_id, client)
    extractions, errors = parse_batch_results(batch_id, client, meta_map, output_dir)
    export_results(extractions, errors, output_dir)


if __name__ == "__main__":
    main()
