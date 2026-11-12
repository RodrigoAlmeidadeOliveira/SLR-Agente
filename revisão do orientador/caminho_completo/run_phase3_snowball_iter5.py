#!/usr/bin/env python3
"""Fase 3 · Snowballing Wohlin — iteração 5 (OpenAlex forward+backward).

Sementes: phase3_snowball_iter5_seeds.csv (n=627 includes iter2; DOI no seeds).
Dedup contra results/unique_papers.csv + corpus 962 + residual iter1.
Keyword gate: ≥1 termo PM/ST/FC e ≥1 termo SE/SDLC/repo.

Uso:
  python3 run_phase3_snowball_iter5.py --status
  python3 run_phase3_snowball_iter5.py --fetch          # retoma progresso
  python3 run_phase3_snowball_iter5.py --finalize        # só com fetch 100%
  python3 run_phase3_snowball_iter5.py --finalize --force  # parcial (não usar na triagem)
  python3 run_phase3_snowball_iter5.py --fetch --limit 20  # piloto
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests

DIR = Path(__file__).resolve().parent
ROOT = DIR.parent.parent
SEEDS = DIR / "phase3_snowball_iter5_seeds.csv"
RAW = DIR / "phase3_snowball_iter5_raw.csv"
PROGRESS = DIR / "phase3_snowball_iter5_progress.json"
SCREEN = DIR / "phase3_snowball_iter5_screen.csv"
SUMMARY = DIR / "phase3_snowball_iter5_summary.md"
UNIQUE = ROOT / "results" / "unique_papers.csv"
STUDIES = DIR.parent / "MSL___Rodrigo_e_Juliano" / "studies.json"
ML_INCLUDES = DIR / "phase3_ML_includes_applied.csv"
SB1_INCLUDES = DIR / "phase3_snowball_iter1_includes_applied.csv"
SB2_INCLUDES = DIR / "phase3_snowball_iter2_includes_applied.csv"
SB3_INCLUDES = DIR / "phase3_snowball_iter3_includes_applied.csv"
SB4_INCLUDES = DIR / "phase3_snowball_iter4_includes_applied.csv"
SB1_SCREEN = DIR / "phase3_snowball_iter1_screen.csv"
SB2_SCREEN = DIR / "phase3_snowball_iter2_screen.csv"
SB3_SCREEN = DIR / "phase3_snowball_iter3_screen.csv"
SB4_SCREEN = DIR / "phase3_snowball_iter4_screen.csv"
INCLUDED_506 = ROOT / "results" / "final_review" / "included_studies_506.csv"

MAILTO = "rodrigoalmeidadeoliveira@gmail.com"
OA = "https://api.openalex.org"
SLEEP = 0.25
# Cap forward citation pages (200/page) to avoid hung mega-hubs / stalled cursors
MAX_FORWARD_PAGES = 25
REQ_TIMEOUT = 25
API_KEY = (
    os.environ.get("OPENALEX_API_KEY")
    or os.environ.get("OPENALEX_KEY")
    or os.environ.get("OA_API_KEY")
    or ""
).strip()


class RateLimitError(RuntimeError):
    pass


class FetchFailed(RuntimeError):
    pass

PM_ST_FC = re.compile(
    r"\b(process mining|process discovery|conformance checking|event log|"
    r"petri|markov|monte carlo|stochastic|forecast|prediction|predictive|"
    r"remaining time|lead time|cycle time|effort estimation|"
    r"throughput|simulation model)\b",
    re.I,
)
SE_SDLC = re.compile(
    r"\b(software|sdlc|devops|ci/?cd|github|jira|repository|pull request|"
    r"commit|issue tracker|agile|scrum|kanban|software development|"
    r"software engineering|open.?source|software project)\b",
    re.I,
)


def norm_doi(d: str) -> str:
    d = (d or "").strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d


def ntitle(t: str) -> str:
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def oa_get(url: str, params: dict | None = None, retries: int = 6) -> dict | list | None:
    params = dict(params or {})
    params.setdefault("mailto", MAILTO)
    if API_KEY:
        params.setdefault("api_key", API_KEY)
    headers = {"User-Agent": f"SLR-Agente-snowball/1.0 (mailto:{MAILTO})"}
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=REQ_TIMEOUT)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                # Free IP budget exhausted or short burst — escalate after a few waits
                wait = 5 + attempt * 10
                print(f"    OpenAlex 429 — wait {wait}s (attempt {attempt+1}/{retries})", flush=True)
                time.sleep(wait)
                if attempt >= retries - 1:
                    raise RateLimitError(r.text[:300])
                continue
            if r.status_code in {500, 502, 503}:
                time.sleep(2 + attempt * 3)
                continue
            return None
        except RateLimitError:
            raise
        except requests.RequestException as e:
            time.sleep(2 + attempt * 2)
            if attempt >= retries - 1:
                raise FetchFailed(str(e)) from e
    return None


def load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"done_seeds": [], "n_raw": 0}


def save_progress(p: dict) -> None:
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def append_raw(rows: list[dict]) -> None:
    fields = [
        "iteration",
        "direction",
        "seed_id",
        "seed_doi",
        "candidate_title",
        "candidate_doi",
        "candidate_year",
        "candidate_oaid",
        "source_engine",
    ]
    new_file = not RAW.exists()
    with RAW.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def work_to_row(w: dict, direction: str, seed_id: str, seed_doi: str) -> dict:
    ids = w.get("ids") or {}
    doi = norm_doi(ids.get("doi") or "")
    year = w.get("publication_year") or ""
    title = w.get("display_name") or w.get("title") or ""
    oaid = (w.get("id") or "").replace("https://openalex.org/", "")
    return {
        "iteration": 5,
        "direction": direction,
        "seed_id": seed_id,
        "seed_doi": seed_doi,
        "candidate_title": title,
        "candidate_doi": doi,
        "candidate_year": year,
        "candidate_oaid": oaid,
        "source_engine": "OpenAlex",
    }


def fetch_seed(seed: dict) -> list[dict]:
    """Return citation rows. Raises RateLimitError/FetchFailed — caller must NOT mark done."""
    doi = norm_doi(seed.get("doi") or "")
    if not doi:
        return []
    sid = seed["internal_id"]
    work = oa_get(f"{OA}/works/doi:{quote(doi)}")
    time.sleep(SLEEP)
    if not work or not isinstance(work, dict) or not work.get("id"):
        # DOI not in OpenAlex — legitimate empty; OK to mark done
        return []
    out: list[dict] = []
    # backward: referenced works (hydrate in batches)
    refs = work.get("referenced_works") or []
    for i in range(0, len(refs), 50):
        chunk = refs[i : i + 50]
        ids = "|".join(x.replace("https://openalex.org/", "") for x in chunk)
        res = oa_get(f"{OA}/works", {"filter": f"openalex_id:{ids}", "per-page": 50})
        time.sleep(SLEEP)
        for w in (res or {}).get("results") or []:
            out.append(work_to_row(w, "backward", sid, doi))
    # forward: works that cite this work
    oaid = (work.get("id") or "").replace("https://openalex.org/", "")
    if oaid:
        cursor = "*"
        pages = 0
        while cursor:
            pages += 1
            if pages > MAX_FORWARD_PAGES:
                break
            res = oa_get(
                f"{OA}/works",
                {
                    "filter": f"cites:{oaid}",
                    "per-page": 200,
                    "cursor": cursor,
                },
            )
            time.sleep(SLEEP)
            if not res:
                break
            for w in res.get("results") or []:
                out.append(work_to_row(w, "forward", sid, doi))
            cursor = (res.get("meta") or {}).get("next_cursor") or None
    return out


def status() -> None:
    seeds = list(csv.DictReader(SEEDS.open(encoding="utf-8")))
    prog = load_progress()
    done = set(prog.get("done_seeds") or [])
    with_doi = [s for s in seeds if norm_doi(s.get("doi") or "")]
    print(f"Seeds: {len(seeds)} (com DOI: {len(with_doi)})")
    print(f"Fetch: {len(done)}/{len(with_doi)} sementes processadas")
    if RAW.exists():
        n = sum(1 for _ in RAW.open(encoding="utf-8")) - 1
        print(f"Raw hits: {n}")
    else:
        print("Raw hits: 0")
    if SCREEN.exists():
        rows = list(csv.DictReader(SCREEN.open(encoding="utf-8")))
        print(f"Screen residual: {len(rows)}")
        print(Counter(r.get("sug_decision") for r in rows))


def fetch(limit: int | None = None) -> None:
    seeds = [s for s in csv.DictReader(SEEDS.open(encoding="utf-8")) if norm_doi(s.get("doi") or "")]
    prog = load_progress()
    done = set(prog.get("done_seeds") or [])
    pending = [s for s in seeds if s["internal_id"] not in done]
    if limit is not None:
        pending = pending[:limit]
    key_note = "com API key" if API_KEY else "sem API key (mailto only — budget IP compartilhado)"
    print(f"Fetch pendentes: {len(pending)} (já feitos {len(done)}) [{key_note}]")
    for i, seed in enumerate(pending, 1):
        print(
            f"  → [{i}/{len(pending)}] {seed['internal_id']} "
            f"doi={norm_doi(seed.get('doi') or '')}",
            flush=True,
        )
        try:
            rows = fetch_seed(seed)
        except RateLimitError as e:
            prog["rate_limit_paused"] = True
            prog["note"] = f"Paused on 429 at seed {seed['internal_id']}: {str(e)[:200]}"
            save_progress(prog)
            print(
                f"RATE LIMIT — pausado em {seed['internal_id']}. "
                "Defina OPENALEX_API_KEY ou retome após reset do budget diário.",
                flush=True,
            )
            return
        except FetchFailed as e:
            print(f"  !! fetch failed (não marca done): {e}", flush=True)
            continue
        if rows:
            append_raw(rows)
        done.add(seed["internal_id"])
        prog["done_seeds"] = sorted(done)
        prog["n_raw"] = prog.get("n_raw", 0) + len(rows)
        prog.pop("rate_limit_paused", None)
        save_progress(prog)
        print(
            f"  [{i}/{len(pending)}] seed={seed['internal_id']} +{len(rows)} "
            f"raw_acc≈{prog['n_raw']}",
            flush=True,
        )
    print("Fetch concluído para este lote.")


def corpus_keys() -> tuple[set[str], set[str]]:
    dois: set[str] = set()
    titles: set[str] = set()
    S = json.loads(STUDIES.read_text(encoding="utf-8"))
    ids = {r["id"] for r in S}
    for path in (INCLUDED_506, ML_INCLUDES, SB1_INCLUDES, SB2_INCLUDES, SB3_INCLUDES, SB4_INCLUDES):
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                iid = r.get("internal_id") or ""
                if iid and iid not in ids and path == INCLUDED_506:
                    continue
                d = norm_doi(r.get("doi") or "")
                if d:
                    dois.add(d)
                t = ntitle(r.get("title") or "")
                if t:
                    titles.add(t)
    # also drop anything already screened in iter1 residual
    if SB1_SCREEN.exists():
        with SB1_SCREEN.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = norm_doi(r.get("doi") or "")
                if d:
                    dois.add(d)
                t = ntitle(r.get("title") or "")
                if t:
                    titles.add(t)
    if SB2_SCREEN.exists():
        with SB2_SCREEN.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = norm_doi(r.get("doi") or "")
                if d:
                    dois.add(d)
                t = ntitle(r.get("title") or "")
                if t:
                    titles.add(t)
    if SB3_SCREEN.exists():
        with SB3_SCREEN.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = norm_doi(r.get("doi") or "")
                if d:
                    dois.add(d)
                t = ntitle(r.get("title") or "")
                if t:
                    titles.add(t)
    if SB4_SCREEN.exists():
        with SB4_SCREEN.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                d = norm_doi(r.get("doi") or "")
                if d:
                    dois.add(d)
                t = ntitle(r.get("title") or "")
                if t:
                    titles.add(t)
    if UNIQUE.exists():
        with UNIQUE.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                d = norm_doi(r.get("doi") or "")
                if d:
                    dois.add(d)
                t = ntitle(r.get("title") or "")
                if t:
                    titles.add(t)
    return dois, titles


def n_doi_seeds() -> int:
    return sum(1 for s in csv.DictReader(SEEDS.open(encoding="utf-8")) if norm_doi(s.get("doi") or ""))


def finalize(*, force: bool = False) -> None:
    if not RAW.exists():
        print("Sem RAW — rode --fetch primeiro")
        return
    n_done = len(load_progress().get("done_seeds") or [])
    n_need = n_doi_seeds()
    if n_done < n_need and not force:
        print(
            f"Fetch incompleto: {n_done}/{n_need}. "
            "Aguarde o --fetch terminar; depois rode --finalize. "
            "(Use --force só para dump parcial — não triar.)"
        )
        return
    if n_done < n_need and force:
        print(f"AVISO: finalize parcial {n_done}/{n_need} (--force)")
    raw = list(csv.DictReader(RAW.open(encoding="utf-8")))
    print(f"Raw rows: {len(raw)}")
    pool_doi, pool_title = corpus_keys()
    by: dict[tuple, dict] = {}
    order: list[tuple] = []
    for r in raw:
        doi = norm_doi(r.get("candidate_doi") or "")
        title = r.get("candidate_title") or ""
        tn = ntitle(title)
        key = ("doi", doi) if doi else ("title", tn)
        if not tn and not doi:
            continue
        if key not in by:
            by[key] = {
                **r,
                "sources_dirs": [r.get("direction")],
                "seed_ids": [r.get("seed_id")],
            }
            order.append(key)
        else:
            if r.get("direction") not in by[key]["sources_dirs"]:
                by[key]["sources_dirs"].append(r.get("direction"))
            if r.get("seed_id") not in by[key]["seed_ids"]:
                by[key]["seed_ids"].append(r.get("seed_id"))
    union = [by[k] for k in order]
    residual = []
    for r in union:
        doi = norm_doi(r.get("candidate_doi") or "")
        tn = ntitle(r.get("candidate_title") or "")
        if (doi and doi in pool_doi) or (tn and tn in pool_title):
            continue
        blob = f"{r.get('candidate_title') or ''}"
        gate = bool(PM_ST_FC.search(blob) and SE_SDLC.search(blob))
        sug = "maybe" if gate else "exclude_other"
        note = (
            "keyword gate OK — triar IC/EC"
            if gate
            else "falhou keyword gate (PM/ST/FC × SE)"
        )
        residual.append(
            {
                "row": 0,
                "iteration": 5,
                "year": r.get("candidate_year") or "",
                "doi": doi,
                "title": r.get("candidate_title") or "",
                "directions": "+".join(sorted(x for x in r["sources_dirs"] if x)),
                "n_seeds": len(r["seed_ids"]),
                "seed_ids": "|".join(r["seed_ids"][:8]),
                "keyword_gate": "pass" if gate else "fail",
                "sug_decision": sug,
                "sug_note": note,
                "final_decision": "",
                "families": "",
                "level": "",
                "notes": "",
                "coder": "",
                "date": "",
            }
        )
    # prioritize gate-pass first
    residual.sort(key=lambda x: (0 if x["keyword_gate"] == "pass" else 1, x["title"]))
    for i, r in enumerate(residual, 1):
        r["row"] = i
    fields = list(residual[0].keys()) if residual else []
    with SCREEN.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(residual)
    gate_pass = sum(1 for r in residual if r["keyword_gate"] == "pass")
    summary = f"""# Snowballing iteração 5 — sumário

- Sementes com DOI: {n_doi_seeds()}
- Fetch concluído: {len(load_progress().get('done_seeds') or [])}
- Raw citation links: {len(raw)}
- União candidatos: {len(union)}
- Já no pool/corpus: {len(union) - len(residual)}
- Residual novo: {len(residual)}
- Keyword gate pass (maybe): {gate_pass}
- Gate fail (sug exclude): {len(residual) - gate_pass}

Arquivo de triagem: `{SCREEN.name}`
"""
    SUMMARY.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"Wrote {SCREEN.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument(
        "--force",
        action="store_true",
        help="Permite --finalize com fetch incompleto (só diagnóstico)",
    )
    ap.add_argument("--limit", type=int, default=None, help="Máx. sementes neste lote")
    args = ap.parse_args()
    if args.status:
        status()
        return
    if args.fetch:
        fetch(args.limit)
    if args.finalize:
        finalize(force=args.force)
    if not args.status and not args.fetch and not args.finalize:
        ap.print_help()


if __name__ == "__main__":
    main()
