#!/bin/sh
# Build corpus version V against lexicon L on the Mac, outside Docker: steps
# 1-3 of deploy/build_corpus.sh with Mac paths, --no-release throughout, so
# nothing is served until the aliases are moved. Needs the forwarder of
# tools/es_forward.py on 127.0.0.1:9201. Peak 7.2 GB, 7.5 minutes for v15
# (2026-11-12, lexicon-20261111): too much for a container beside the rest of
# Docker Desktop on the Mac, and for the VPS beside Sokhan (docs/ENGINEERING.md).
#
#   tools/build_corpus_mac.sh v15 lexicon-20261111
set -eu
V=${1:?usage: build_corpus_mac.sh v15 lexicon-20261111}
L=${2:?usage: build_corpus_mac.sh v15 lexicon-20261111}
cd "$(dirname "$0")/.."
export MURFULU_LEXICON_PATH="$PWD/data/$L.sqlite"
export MURFULU_GANJOOR_PATH="${MURFULU_GANJOOR_PATH:-$HOME/Projects/mosaic/mana/data/ganjoor.s3db}"
export MURFULU_GANJOOR_CENTURIES="${MURFULU_GANJOOR_CENTURIES:-$HOME/Projects/mosaic/stemma/data/poet_centuries.json}"
export MURFULU_SEMANTIC_PATH="$PWD/data/semantic-v4.json"
export MURFULU_ELASTICSEARCH_URL="${MURFULU_ELASTICSEARCH_URL:-http://127.0.0.1:9201}"
PY=.venv/bin/python
echo "== step 1 precompute $(date +%T)"
$PY tools/run_precompute.py --corpus-version "$V" \
  --out "build/derivations-$V.jsonl" --elasticsearch --no-release \
  --affix-map-out "build/affix-map-$V.json" \
  --sisters-out "build/sisters-$V-all.json" --sisters-keep 0 \
  --suspect-claims build/suspect-claims-v4.json
echo "== step 2 ingest $(date +%T)"
$PY tools/run_ingest.py --corpus-version "$V" --no-release \
  --report-out "data/corpus_report-$V.json" \
  --affix-map "build/affix-map-$V.json"
echo "== step 3 productivity + typicality $(date +%T)"
$PY tools/run_productivity.py --from "build/derivations-$V.jsonl" \
  --out "data/rule_productivity-$V.json"
$PY tools/measure_typicality_spread.py \
  --from "build/derivations-$V.jsonl" --out "data/typicality-$V.json"
echo "== done $(date +%T)"
