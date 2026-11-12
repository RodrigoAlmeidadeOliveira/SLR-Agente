#!/usr/bin/env bash
# Build Zenodo v3 replication tree (corpus n=1710 + caminho_completo + screening stack).
# No PDFs of primary studies, no secrets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
META="$ROOT/article_ist/zenodo_upload"
STAGING="$META/SLR_PATHCAST_Replication_v3"
ZIP="$META/SLR_PATHCAST_Replication_v3.zip"
MSL="$ROOT/revisão do orientador/MSL___Rodrigo_e_Juliano"
CC="$ROOT/revisão do orientador/caminho_completo"

rm -rf "$STAGING"
mkdir -p "$STAGING"

RSYNC=(rsync -a --copy-links
  --exclude '__pycache__/'
  --exclude '.DS_Store'
  --exclude '.env'
  --exclude '*.pyc'
  --exclude '*.pdf'
  --exclude '.git/'
  --exclude '*.bak'
  --exclude '*.bak.*'
  --exclude '*.bak_*'
  --exclude 'studies.json.bak*'
  --exclude 'phase1_L0_audit_sample.bak.csv'
  --exclude 'phase1_title_only_*.bak.csv'
)

# --- Base screening / pipeline stack (same as v2) ---
"${RSYNC[@]}" "$ROOT/config/" "$STAGING/config/"
"${RSYNC[@]}" "$ROOT/extractors/" "$STAGING/extractors/"
"${RSYNC[@]}" "$ROOT/pipeline/" "$STAGING/pipeline/"
"${RSYNC[@]}" "$ROOT/scripts/" "$STAGING/scripts/"
mkdir -p "$STAGING/docs"
cp "$ROOT/docs/prompts_llm_screening.md" "$STAGING/docs/"

cp "$ROOT/article_ist/zenodo_package/LICENSE" "$STAGING/LICENSE"
cp "$ROOT/article_ist/zenodo_package/requirements.txt" "$STAGING/requirements.txt"
cp "$META/README_v3.md" "$STAGING/README.md"
cp "$META/CITATION_v3.cff" "$STAGING/CITATION.cff"
cp "$META/.zenodo_v3.json" "$STAGING/.zenodo.json"

mkdir -p "$STAGING/results"

copy_results_dir () {
  local name="$1"
  if [[ -d "$ROOT/results/$name" ]]; then
    "${RSYNC[@]}" \
      --exclude 'pdfs/' \
      --exclude 'top30_pdfs/' \
      --exclude 'ft_pdfs_local/' \
      --exclude 'pending_manual_review/*.pdf' \
      "$ROOT/results/$name/" "$STAGING/results/$name/"
  fi
}

for d in raw frozen screening kappa working_set auxiliary ec5_recovery \
         sensitivity final_review snowball_v2 spotcheck extraction \
         human_validation; do
  copy_results_dir "$d"
done

for f in qa_assessment.csv qa_assessment.xlsx qa_assessment_llm.csv \
         qa_assessment_llm_raw.jsonl qa_assessment_summary.tex \
         qa_assessment_summary.txt qa_peritem_summary.tex \
         combined.json deduplicated.json all_papers.csv unique_papers.csv \
         export.bib export.ris \
         pdf_leitura_individual.csv pdf_leitura_individual_v2.csv \
         pdf_leitura_individual_v3.csv pdf_leitura_individual_v4.csv \
         pdf_leitura_individual_v4.xlsx; do
  if [[ -e "$ROOT/results/$f" ]]; then
    cp "$ROOT/results/$f" "$STAGING/results/"
  fi
done

rm -f "$STAGING/results/human_validation/"*wip* 2>/dev/null || true

# --- Canonical n=1710 corpus (manuscript source of truth) ---
mkdir -p "$STAGING/corpus_n1710"
cp "$MSL/studies.json" "$STAGING/corpus_n1710/"
cp "$MSL/figs.py" "$STAGING/corpus_n1710/"
cp "$MSL/figs_pt.py" "$STAGING/corpus_n1710/"
cp "$MSL/appendix_studies.tex" "$STAGING/corpus_n1710/"
cp "$MSL/appendix_studies_pt.tex" "$STAGING/corpus_n1710/"
cp "$MSL/references.bib" "$STAGING/corpus_n1710/"

python3 - <<'PY' "$MSL" "$STAGING/corpus_n1710" "$CC"
import csv, json, sys
from pathlib import Path
msl, out, cc = map(Path, sys.argv[1:])
studies = json.loads((msl / "studies.json").read_text())
rq3 = {}
with (cc / "phase4_rq3_extraction_template.csv").open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        rq3[row["internal_id"]] = row
fields = [
    "internal_id", "year", "role", "families", "level_technique",
    "title", "doi", "venue",
]
out_csv = out / "included_studies_1710.csv"
with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for s in studies:
        r = rq3.get(s["id"], {})
        w.writerow({
            "internal_id": s["id"],
            "year": s.get("year", r.get("year", "")),
            "role": s.get("role", r.get("role", "")),
            "families": s.get("fam", r.get("families", "")),
            "level_technique": s.get("pat", r.get("level_technique", "")),
            "title": r.get("title", ""),
            "doi": r.get("doi", ""),
            "venue": r.get("venue", ""),
        })
assert len(studies) == 1710, len(studies)
print(f"wrote {out_csv} rows={len(studies)}")
PY

# --- Caminho completo (protocols, sheets, scripts) ---
mkdir -p "$STAGING/caminho_completo"
"${RSYNC[@]}" \
  --exclude 'phase3_exports/' \
  "$CC/" "$STAGING/caminho_completo/"

# Keep compact ML-export samples if present (full dumps are large / re-downloadable)
if [[ -d "$CC/phase3_exports" ]]; then
  mkdir -p "$STAGING/caminho_completo/phase3_exports"
  # README pointer only — avoid 20MB+ bibliographic dumps in the zip
  cat > "$STAGING/caminho_completo/phase3_exports/README.md" <<'EOF'
# phase3_exports

Full ML-block bibliographic exports used in Phase 3 are omitted from this
Zenodo zip for size. Screening decisions derived from them are in
`../phase3_ML_*.csv` and `../phase3_snowball_iter*_screen.csv`.

To rebuild the export set, follow `../05_PROTOCOLO_BUSCA_ML_E_D1.md`.
EOF
fi

# Safety
if find "$STAGING" -iname '*.pdf' | grep -q .; then
  echo "ERROR: PDF leaked into staging" >&2
  find "$STAGING" -iname '*.pdf' >&2
  exit 1
fi
if find "$STAGING" -iname '.env' | grep -q .; then
  echo "ERROR: .env leaked" >&2
  exit 1
fi

# Sanity: n=1710
python3 - <<'PY' "$STAGING"
import csv, json, sys
from pathlib import Path
root = Path(sys.argv[1])
n = len(json.loads((root / "corpus_n1710/studies.json").read_text()))
with (root / "corpus_n1710/included_studies_1710.csv").open(newline="", encoding="utf-8") as f:
    n_csv = sum(1 for _ in csv.DictReader(f))
with (root / "caminho_completo/phase4_rq3_extraction_template.csv").open(newline="", encoding="utf-8") as f:
    rq3 = sum(1 for _ in csv.DictReader(f))
assert n == 1710 and n_csv == 1710 and rq3 == 1710, (n, n_csv, rq3)
print("sanity ok: studies.json / included_studies_1710 / rq3 =", n)
PY

(
  cd "$STAGING"
  find . -type f | sed 's|^\./||' | sort > FILE_MANIFEST.txt
)

rm -f "$ZIP"
(
  cd "$META"
  zip -r -q "$(basename "$ZIP")" "$(basename "$STAGING")"
)

echo "STAGING=$STAGING"
du -sh "$STAGING" "$ZIP"
echo "files=$(wc -l < "$STAGING/FILE_MANIFEST.txt")"
echo "pdfs_in_zip=$(unzip -l "$ZIP" | grep -ci '\.pdf$' || true)"
