#!/usr/bin/env bash
# Murfulu on the production host (Ubuntu + Docker, docs/DEPLOY.md §0), next to
# Sokhan. Run from the repo root on the Mac, on a network that reaches the host:
#   deploy/server.sh <command>
#
#   env       create the server .env from deploy/server.env.example (once; keeps an existing one)
#   tunnel    copy the Cloudflare tunnel credentials to the server (once)
#   data      rsync the lexicon and the measured artefacts the API reads — safe to re-run
#   deploy    rsync the code and rebuild/restart the app (never the tunnel)  ← the normal deploy
#   corpus V  snapshot passages + documents/word_types/derivations-V on the fallback, restore on the server
#   release V [L]  serve corpus version V (and lexicon L): aliases + .env + api; the rollback too
#   db        copy the Postgres database fallback → server (pg_dump | pg_restore --clean) and compare
#   db-back   the same, server → fallback: run it before a rollback if anyone wrote on the server
#   migrate   alembic upgrade head on the server
#   check     health, served corpus version, a generation, L16 — on the server, not public
#   counts    ES document counts and Postgres rows, fallback vs server
#   cutover   check, stop the fallback's connector, copy the DB once more, start the server's
#   rollback  stop the server's connector and start the fallback's again
#   ps|logs   status / follow logs
#
# The fallback is the machine that served before: MURFULU_FALLBACK_SSH_HOST in
# deploy/host.env, or the Mac when that is unset. Hosts, how to reach them and
# which tunnel are local files, never in git: deploy/host.env, deploy/ssh_config
# and deploy/cloudflared/config.yml, each copied from the *.example beside it.
# Sokhan runs on the same host as compose project `mana`: nothing here may touch it.
set -euo pipefail
cd "$(dirname "$0")/.."

SSH_CONFIG="$PWD/deploy/ssh_config"   # absolute: `data` runs rsync from inside data/
HOST_ENV="$PWD/deploy/host.env"
[ -n "${1:-}" ] || { sed -n '2,25p' "$0"; exit 1; }
TUNNEL_CONFIG="$PWD/deploy/cloudflared/config.yml"
for local_file in "$HOST_ENV" "$SSH_CONFIG"; do
  [ -f "$local_file" ] || {
    echo "${local_file#"$PWD"/} is missing: copy ${local_file#"$PWD"/}.example and fill it in (docs/DEPLOY.md §0)" >&2
    exit 1
  }
done
# shellcheck source=/dev/null
. "$HOST_ENV"
SERVER=${MURFULU_SSH_HOST:?set MURFULU_SSH_HOST in deploy/host.env}
REMOTE_DIR=${MURFULU_REMOTE_DIR:-murfulu}
SITE=murfulu.mosaic-hub.de
COMPOSE="docker compose -p murfulu -f docker-compose.prod.yml -f docker-compose.server.yml"
APP_SERVICES="db elasticsearch api web caddy"
# The fallback, kept running for the rollback: another host's stack when
# deploy/host.env names one (its connector is murfulu_cloudflared, stopped
# while the server serves), otherwise the Mac's (its connector the LaunchAgent).
FALLBACK=${MURFULU_FALLBACK_SSH_HOST:-}
FALLBACK_DIR=${MURFULU_FALLBACK_REMOTE_DIR:-murfulu}
FB_NAME=${FALLBACK:-Mac}
MAC_COMPOSE="docker compose -p murfulu -f docker-compose.prod.yml"
MAC_AGENT=com.cloudflared.murfulu
MAC_PLIST="$HOME/Library/LaunchAgents/$MAC_AGENT.plist"
MAC_PLIST_PARKED="$HOME/Library/LaunchAgents/disabled/$MAC_AGENT.plist"

remote() { ssh -F "$SSH_CONFIG" "$SERVER" "$@"; }
fallback() { ssh -F "$SSH_CONFIG" "$FALLBACK" "$@"; }
RSYNC=(rsync -az -e "ssh -F $SSH_CONFIG")

# `docker` and the stack's `docker compose` on the fallback, arguments passed as they are.
fb_docker()  { if [ -n "$FALLBACK" ]; then fallback "docker $(printf '%q ' "$@")"; else docker "$@"; fi; }
fb_compose() { if [ -n "$FALLBACK" ]; then fallback "cd $FALLBACK_DIR && $COMPOSE $(printf '%q ' "$@")"; else $MAC_COMPOSE "$@"; fi; }

fb_es()     { fb_compose exec -T elasticsearch curl -sS "$@"; }
server_es() { remote "cd $REMOTE_DIR && $COMPOSE exec -T elasticsearch curl -sS $(printf '%q ' "$@")"; }

# Exact rows and a checksum of every row, per table, so a copy is compared by
# content and not only by size. Prints "table rows md5".
TABLE_SQL="select table_name || ' ' || (xpath('/row/c/text()', query_to_xml(format(
  'select count(*) || '' '' || md5(coalesce(string_agg(t::text, '''' order by t::text), '''')) as c from %I.%I t',
  table_schema, table_name), false, true, '')))[1]::text
  from information_schema.tables where table_schema = 'public' and table_type = 'BASE TABLE' order by 1"
psql_fb()     { fb_compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "$0"' "$1"; }
psql_server() { remote "cd $REMOTE_DIR && $COMPOSE exec -T db sh -c 'psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -Atc \"\$0\"' $(printf '%q' "$1")"; }

dump_fb()        { fb_compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-privileges'; }
dump_server()    { remote "cd $REMOTE_DIR && $COMPOSE exec -T db sh -c 'pg_dump -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -Fc --no-owner --no-privileges'"; }
RESTORE='pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --no-privileges --single-transaction'
restore_fb()     { fb_compose exec -T db sh -c "$RESTORE"; }
restore_server() { remote "cd $REMOTE_DIR && $COMPOSE exec -T db sh -c $(printf '%q' "$RESTORE")"; }

compare_db() {
  local mac server
  mac=$(psql_fb "$TABLE_SQL"); server=$(psql_server "$TABLE_SQL")
  echo "table                      rows ($FB_NAME / server)   content"
  LC_ALL=C join -a1 -a2 -e '-' -o 0,1.2,2.2,1.3,2.3 <(echo "$mac" | LC_ALL=C sort) <(echo "$server" | LC_ALL=C sort) |
    awk '{ printf "%-26s %8s / %-8s   %s\n", $1, $2, $3, ($4 == $5 ? "same" : "DIFFERENT") }'
  [ "$mac" = "$server" ] && echo "Postgres: identical" || { echo "Postgres: DIFFERENT" >&2; return 1; }
}

compare_es() {
  local index mac server ok=0
  printf '%-18s %12s %12s\n' index "$FB_NAME" server
  for index in passages documents word_types derivations; do
    mac=$(fb_es "localhost:9200/$index/_count" | sed -E 's/.*"count":([0-9]+).*/\1/')
    server=$(server_es "localhost:9200/$index/_count" | sed -E 's/.*"count":([0-9]+).*/\1/')
    printf '%-18s %12s %12s\n' "$index" "$mac" "$server"
    [ "$mac" = "$server" ] || ok=1
  done
  echo "aliases on the server:"; server_es 'localhost:9200/_cat/aliases?h=alias,index'
  return $ok
}

# The site behind the tunnel: 401 at the password wall is the answer that matters.
public_status() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 "https://$SITE/"; }

case "${1:-}" in
  env)
    remote "mkdir -p $REMOTE_DIR && cd $REMOTE_DIR && if [ -f .env ]; then echo '.env exists, left unchanged'; else
      (umask 077; cat > .env) && echo '.env created'; fi" < deploy/server.env.example
    # The site login moves as it is, from the fallback that serves it now, so
    # everyone's saved password keeps working. Piped, never echoed; merged on
    # the server only where the value is still empty.
    if [ -n "$FALLBACK" ]; then fallback "cat $FALLBACK_DIR/.env"; else cat .env; fi |
      grep -E '^MURFULU_SITE_(USER|PASSWORD_HASH)=' | remote "umask 077; cat > $REMOTE_DIR/.env.site"
    remote "bash -s $REMOTE_DIR" <<'EOF'
set -e
cd "$1"
while IFS= read -r line; do
  key=${line%%=*}
  grep -qE "^$key=.+" .env && continue
  grep -v "^$key=" .env > .env.new || true
  printf '%s\n' "$line" >> .env.new
  mv .env.new .env
  echo "$key copied from the fallback"
done < .env.site
rm -f .env.site
if ! grep -qE '^POSTGRES_PASSWORD=.+' .env; then
  grep -v '^POSTGRES_PASSWORD=' .env > .env.new || true
  echo "POSTGRES_PASSWORD=$(openssl rand -hex 24)" >> .env.new
  mv .env.new .env
  echo "POSTGRES_PASSWORD generated on the server"
fi
chmod 600 .env
EOF
    ;;
  tunnel)
    # The tunnel id is the one deploy/cloudflared/config.yml names.
    tunnel_id=$(sed -nE 's/^tunnel: *([0-9a-f-]+) *$/\1/p' "$TUNNEL_CONFIG" 2>/dev/null || true)
    [ -n "$tunnel_id" ] || { echo "no tunnel id in deploy/cloudflared/config.yml (from config.yml.example)" >&2; exit 1; }
    remote "mkdir -p $REMOTE_DIR/deploy/cloudflared"
    scp -q -F "$SSH_CONFIG" ~/.cloudflared/"$tunnel_id".json "$SERVER:$REMOTE_DIR/deploy/cloudflared/"
    # cloudflared runs as a non-root user inside its container
    remote "chmod 644 $REMOTE_DIR/deploy/cloudflared/$tunnel_id.json"
    ;;
  data)
    # Exactly the files the server .env points at (MURFULU_*_PATH), plus the
    # lexicon's SQLite sidecars so the read-only mount sees what the Mac sees.
    # Not the other corpus versions' artefacts, not the backups.
    remote "mkdir -p $REMOTE_DIR/data"
    files=$(sed -nE 's#^MURFULU_[A-Z_]+_PATH=/data/##p' deploy/server.env.example)
    lexicon=$(sed -nE 's#^MURFULU_LEXICON_PATH=/data/##p' deploy/server.env.example)
    extra=$(cd data && ls "$lexicon"-wal "$lexicon"-shm 2>/dev/null || true)
    (cd data && "${RSYNC[@]}" --info=progress2 $files $extra "$SERVER:$REMOTE_DIR/data/")
    ;;
  deploy)
    "${RSYNC[@]}" --delete \
      --exclude .git --exclude /data --exclude /build --exclude .env --exclude .claude \
      --exclude node_modules --exclude /web/dist --exclude /web/test-results \
      --exclude __pycache__ --exclude .venv --exclude .mypy_cache --exclude .pytest_cache \
      --exclude .ruff_cache --exclude '*.egg-info' --exclude '/deploy/cloudflared/*.json' \
      --exclude /deploy/host.env --exclude '/deploy/host.*.env' --exclude /deploy/ssh_config \
      --exclude /.denylist --exclude .DS_Store \
      ./ "$SERVER:$REMOTE_DIR/"
    remote "cd $REMOTE_DIR && $COMPOSE up -d --build $APP_SERVICES && docker image prune -f --filter label=com.docker.compose.project=murfulu >/dev/null"
    ;;
  corpus)
    version=${2:?usage: deploy/server.sh corpus v12}
    indices="passages,documents-$version,word_types-$version,derivations-$version"
    repo="release-$version"
    # A repository of its own for this release, so the directory that travels
    # holds these four indices and nothing from earlier snapshots.
    if ! fb_es -f "localhost:9200/_snapshot/$repo/$version" >/dev/null 2>&1; then
      fb_compose exec -T -u root elasticsearch chown -R elasticsearch:root /snapshots
      fb_es -f -X PUT "localhost:9200/_snapshot/$repo" -H 'content-type: application/json' \
        -d "{\"type\":\"fs\",\"settings\":{\"location\":\"/snapshots/$repo\"}}"; echo
      fb_es -f -X PUT "localhost:9200/_snapshot/$repo/$version?wait_for_completion=true" \
        -H 'content-type: application/json' \
        -d "{\"indices\":\"$indices\",\"include_global_state\":false}" | head -c 400; echo
    fi
    remote "cd $REMOTE_DIR && $COMPOSE up -d --wait elasticsearch"
    fb_container=$(fb_compose ps -q elasticsearch)
    server_container=$(remote "cd $REMOTE_DIR && $COMPOSE ps -q elasticsearch")
    if remote "docker exec $server_container test -d /snapshots/$repo"; then
      echo "snapshot already on the server"
    else
      fb_docker cp "$fb_container:/snapshots/$repo" - | remote "docker cp - $server_container:/snapshots/"
    fi
    remote "docker exec -u root $server_container chown -R elasticsearch:root /snapshots"
    server_es -f -X PUT "localhost:9200/_snapshot/$repo" -H 'content-type: application/json' \
      -d "{\"type\":\"fs\",\"settings\":{\"location\":\"/snapshots/$repo\",\"readonly\":true}}"; echo
    if server_es -f "localhost:9200/documents-$version" >/dev/null 2>&1; then
      echo "documents-$version already restored on the server"
    else
      server_es -f -X POST "localhost:9200/_snapshot/$repo/$version/_restore?wait_for_completion=true" \
        -H 'content-type: application/json' \
        -d "{\"indices\":\"$indices\",\"include_global_state\":false,\"include_aliases\":true}" | head -c 400; echo
    fi
    # The aliases are what the app reads; make sure they point at this version.
    server_es -f -X POST 'localhost:9200/_aliases' -H 'content-type: application/json' -d "{\"actions\":[
      {\"add\":{\"index\":\"documents-$version\",\"alias\":\"documents\"}},
      {\"add\":{\"index\":\"word_types-$version\",\"alias\":\"word_types\"}},
      {\"add\":{\"index\":\"derivations-$version\",\"alias\":\"derivations\"}}]}"; echo
    compare_es
    ;;
  release)
    # Serve corpus version V (already on the server) with lexicon L, or move
    # back to an earlier one — this is the rollback too:
    #   deploy/server.sh release v12 lexicon-20260808
    # All three aliases move in one request; the server .env's version paths
    # (and the lexicon, when given) follow, and only the api is recreated.
    version=${2:?usage: deploy/server.sh release v13 [lexicon-20261012]}
    lexicon=${3:-}
    remote "cd $REMOTE_DIR && for f in rule_productivity corpus_report typicality; do test -f data/\$f-$version.json || { echo \"data/\$f-$version.json missing\" >&2; exit 1; }; done"
    [ -z "$lexicon" ] || remote "test -f $REMOTE_DIR/data/$lexicon.sqlite"
    actions=""
    for alias in documents word_types derivations; do
      actions="$actions{\"remove\":{\"index\":\"$alias-*\",\"alias\":\"$alias\"}},{\"add\":{\"index\":\"$alias-$version\",\"alias\":\"$alias\"}},"
    done
    server_es -f -X POST 'localhost:9200/_aliases' -H 'content-type: application/json' \
      -d "{\"actions\":[${actions%,}]}"; echo
    remote "cd $REMOTE_DIR && sed -i -E \
      -e 's#^(MURFULU_(PRODUCTIVITY|CORPUS_REPORT|TYPICALITY)_PATH=/data/[a-z_]+-)v[0-9]+\.json#\1$version.json#' \
      ${lexicon:+-e 's#^MURFULU_LEXICON_PATH=.*#MURFULU_LEXICON_PATH=/data/$lexicon.sqlite#'} .env &&
      grep -E '^MURFULU_[A-Z_]+_PATH=' .env && $COMPOSE up -d --wait api"
    server_es 'localhost:9200/_cat/aliases?h=alias,index'
    ;;
  db)
    remote "cd $REMOTE_DIR && $COMPOSE up -d --wait db"
    dump_fb | restore_server
    compare_db
    ;;
  db-back)
    dump_server | restore_fb
    compare_db
    ;;
  migrate) remote "cd $REMOTE_DIR && $COMPOSE run --rm api alembic upgrade head" ;;
  check)
    remote "cd $REMOTE_DIR && $COMPOSE ps --format 'table {{.Service}}\t{{.Status}}'"
    remote "cd $REMOTE_DIR && $COMPOSE exec -T api python -" < deploy/check_api.py
    # Through Caddy by the name it answers to (DEPLOY.md §6): no credentials → 401.
    remote "cd $REMOTE_DIR && $COMPOSE exec -T caddy wget -S -q -O /dev/null --header 'Host: $SITE' http://127.0.0.1/ 2>&1 | head -1 || true"
    ;;
  counts)
    compare_es || true
    compare_db || true
    ;;
  cutover)
    # 0. Nothing switches unless the server answers every check (exits 1 otherwise).
    remote "cd $REMOTE_DIR && $COMPOSE exec -T api python -" < deploy/check_api.py
    # 1. The fallback stops serving: stopped or parked, never removed.
    if [ -n "$FALLBACK" ]; then
      fallback "cd $FALLBACK_DIR && $COMPOSE stop cloudflared"
      echo "$FALLBACK connector murfulu_cloudflared stopped (container kept)"
    else
      if launchctl print "gui/$(id -u)/$MAC_AGENT" >/dev/null 2>&1; then
        launchctl bootout "gui/$(id -u)/$MAC_AGENT"
      fi
      mkdir -p "$(dirname "$MAC_PLIST_PARKED")"
      [ -f "$MAC_PLIST" ] && mv "$MAC_PLIST" "$MAC_PLIST_PARKED"
      echo "Mac connector stopped; plist parked in ~/Library/LaunchAgents/disabled/"
    fi
    # 2. Nothing can write on the fallback any more, so this copy is the last one.
    dump_fb | restore_server
    compare_db
    # 3. The server starts serving.
    remote "cd $REMOTE_DIR && $COMPOSE up -d cloudflared"
    sleep 15
    echo "https://$SITE/ → $(public_status) (401 expected)"
    ;;
  rollback)
    remote "cd $REMOTE_DIR && $COMPOSE stop cloudflared"
    if [ -n "$FALLBACK" ]; then
      fallback "cd $FALLBACK_DIR && $COMPOSE start cloudflared"
    else
      [ -f "$MAC_PLIST_PARKED" ] && mv "$MAC_PLIST_PARKED" "$MAC_PLIST"
      launchctl bootstrap "gui/$(id -u)" "$MAC_PLIST" 2>/dev/null || launchctl kickstart -k "gui/$(id -u)/$MAC_AGENT"
    fi
    sleep 15
    echo "server connector stopped, $FB_NAME connector started; https://$SITE/ → $(public_status) (401 expected)"
    echo "Writes made on the server since the cutover are only there: deploy/server.sh db-back copies them back."
    ;;
  ps)   remote "cd $REMOTE_DIR && $COMPOSE ps" ;;
  logs) remote "cd $REMOTE_DIR && $COMPOSE logs -f --tail=100 ${2:-}" ;;
  *)    sed -n '2,25p' "$0"; exit 1 ;;
esac
