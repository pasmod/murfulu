#!/bin/sh
# What a browser is told it may keep, asked of a running `web` container.
#
# index.html names the bundle, so a copy kept after a deploy loads the old
# app: it must say `no-cache`, by every way a reader reaches it — `/`, an app
# path through the fallback, and its own name. The hashed assets are kept for
# a year. Run against the image CI builds:
#
#   docker run -d --rm --name web-cache --add-host api:127.0.0.1 \
#     -p 127.0.0.1:8099:80 murfulu-web
#   tools/check_web_cache.sh http://127.0.0.1:8099
#   docker stop web-cache
#
# `--add-host` only lets nginx start: it resolves the API's name at load.
set -eu
base="${1:-http://127.0.0.1:8099}"
failed=0

# The response headers of one path, or a failure that says which path.
headers() {
  if ! got=$(curl -fsS -o /dev/null -D - "$base$1"); then
    echo "FAIL $1: the request failed" >&2
    return 1
  fi
  printf '%s\n' "$got" | tr -d '\r'
}

# Every header of that name, on one line.
said() {
  printf '%s\n' "$1" | grep -i "^$2:" | tr '\n' ' ' || true
}

for path in / /rules /word/x /index.html; do
  got=$(headers "$path") || { failed=1; continue; }
  cache=$(said "$got" cache-control)
  case "$cache" in
    *no-cache*) echo "ok   $path: $cache" ;;
    *) echo "FAIL $path: expected no-cache, got '${cache:-nothing}'"; failed=1 ;;
  esac
done

if ! page=$(curl -fsS "$base/"); then
  echo "FAIL /: the request failed"
  exit 1
fi
asset=$(printf '%s\n' "$page" | grep -o '/assets/[^"]*\.js' | head -n 1 || true)
if [ -z "$asset" ]; then
  echo "FAIL /: names no script under /assets/"
  exit 1
fi
got=$(headers "$asset") || exit 1
cache=$(said "$got" cache-control)
expires=$(said "$got" expires)
for wanted in public immutable max-age=31536000; do
  case "$cache" in
    *"$wanted"*) ;;
    *) echo "FAIL $asset: no '$wanted' in '${cache:-nothing}'"; failed=1 ;;
  esac
done
if [ -z "$expires" ]; then
  echo "FAIL $asset: no Expires"
  failed=1
fi
[ "$failed" -eq 0 ] && echo "ok   $asset: $cache$expires"
exit "$failed"
