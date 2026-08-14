#!/usr/bin/env bash
# Build the Zenodo v2 replication tree and zip (no PDFs, no secrets).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGING="$ROOT/article_ist/zenodo_upload/SLR_PATHCAST_Replication_v2"
ZIP="$ROOT/article_ist/zenodo_upload/SLR_PATHCAST_Replication_v2.zip"
META="$ROOT/article_ist/zenodo_upload"

rm -rf "$STAGING"
mkdir -p "$STAGING"

RSYNC=(rsync -a --copy-links
  --exclude '__pycache__/'
  --exclude '.DS_Store'
  --exclude '.env'
  --exclude '*.pyc'
  --exclude '*.pdf'
  --exclude '.git/'
)

# Code and protocol
"${RSYNC[@]}" "$ROOT/config/" "$STAGING/config/"
"${RSYNC[@]}" "$ROOT/extractors/" "$STAGING/extractors/"
"${RSYNC[@]}" "$ROOT/pipeline/" "$STAGING/pipeline/"
"${RSYNC[@]}" "$ROOT/scripts/" "$STAGING/scripts/"
mkdir -p "$STAGING/docs"
cp "$ROOT/docs/prompts_llm_screening.md" "$STAGING/docs/"

# Metadata
cp "$ROOT/article_ist/zenodo_package/LICENSE" "$STAGING/LICENSE"
cp "$ROOT/article_ist/zenodo_package/requirements.txt" "$STAGING/requirements.txt"
cp "$META/README.md" "$STAGING/README.md"
cp "$META/CITATION.cff" "$STAGING/CITATION.cff"
cp "$META/.zenodo.json" "$STAGING/.zenodo.json"

# Results (selected trees; skip copyright PDFs and backups)
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

# Root-level result tables cited in the manuscript
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

# Drop WIP human sheets (audit trail stays in official csv/xlsx)
rm -f "$STAGING/results/human_validation/"*wip* 2>/dev/null || true

# Safety: no PDFs, no env
if find "$STAGING" -iname '*.pdf' | grep -q .; then
  echo "ERROR: PDF leaked into staging" >&2
  find "$STAGING" -iname '*.pdf' >&2
  exit 1
fi
if find "$STAGING" -iname '.env' | grep -q .; then
  echo "ERROR: .env leaked" >&2
  exit 1
fi

# Manifest
(
  cd "$STAGING"
  find . -type f | sed 's|^\./||' | sort > FILE_MANIFEST.txt
)

rm -f "$ZIP"
(
  cd "$ROOT/article_ist/zenodo_upload"
  zip -r -q "$(basename "$ZIP")" "$(basename "$STAGING")"
)

echo "STAGING=$STAGING"
du -sh "$STAGING" "$ZIP"
echo "files=$(wc -l < "$STAGING/FILE_MANIFEST.txt")"
echo "pdfs_in_zip=$(unzip -l "$ZIP" | grep -ci '\.pdf$' || true)"
