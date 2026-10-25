#!/bin/sh
# Build corpus version V against lexicon L, inside a one-shot container of the
# deployed murfulu-api image on the production host (docs/ENGINEERING.md, "v13
# was built on the server"). Steps 1–3 of the recipe, --no-release throughout:
# nothing is served until `deploy/server.sh release V L`.
#
#   docker run -d --name murfulu-build-V --memory 7g --memory-swap 7g --cpus 6 \
#     --network murfulu_default -v ~/murfulu/data:/data:ro \
#     -v ~/murfulu/build:/build -v ~/murfulu/deploy:/deploy:ro \
#     murfulu-api:latest sh /deploy/build_corpus.sh v13 lexicon-20261012
#
# Inputs in /build/inputs (rsynced from the Mac): ganjoor.s3db,
# poet_centuries.json, suspect-claims-v4.json. Outputs in /build.
set -eu
V=${1:?usage: build_corpus.sh v13 lexicon-20261012}
L=${2:?usage: build_corpus.sh v13 lexicon-20261012}
cd /app
export MURFULU_LEXICON_PATH=/data/$L.sqlite
export MURFULU_GANJOOR_PATH=/build/inputs/ganjoor.s3db
export MURFULU_GANJOOR_CENTURIES=/build/inputs/poet_centuries.json
export MURFULU_SEMANTIC_PATH=/data/semantic-v4.json
export MURFULU_ELASTICSEARCH_URL=http://elasticsearch:9200
echo "== step 1 precompute $(date -u +%T)"
python tools/run_precompute.py --corpus-version "$V" \
  --out "/build/derivations-$V.jsonl" --elasticsearch --no-release \
  --affix-map-out "/build/affix-map-$V.json" \
  --sisters-out "/build/sisters-$V-all.json" --sisters-keep 0 \
  --suspect-claims /build/inputs/suspect-claims-v4.json
echo "== step 2 ingest $(date -u +%T)"
python tools/run_ingest.py --corpus-version "$V" --no-release \
  --report-out "/build/corpus_report-$V.json" \
  --affix-map "/build/affix-map-$V.json"
echo "== step 3 productivity + typicality $(date -u +%T)"
python tools/run_productivity.py --from "/build/derivations-$V.jsonl" \
  --out "/build/rule_productivity-$V.json"
python tools/measure_typicality_spread.py \
  --from "/build/derivations-$V.jsonl" --out "/build/typicality-$V.json"
echo "== done $(date -u +%T)"
