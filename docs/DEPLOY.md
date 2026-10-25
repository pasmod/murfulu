# Deploying Murfulu to a server

The whole system in Docker, behind one password, with automatic HTTPS. Written
2026-08-17 for `murfulu.mosaic-hub.de`, following the pattern mosaic-studio
already uses on the same domain.

**Read [What this publishes](#7-what-this-publishes) before opening it to
anyone.** Murfulu's own licence is settled and deliberately does not reach the
corpus; Ganjoor's terms are settled too, and they settle *against* publishing.
The password is not a placeholder.

---

## 0. Where production runs (since 2026-10-17)

**On a production host of its own**, next to Sokhan, not on the Mac any more.
Ubuntu 24.04 in WSL → Docker Engine; compose project **`murfulu`** from
`docker-compose.prod.yml` + `docker-compose.server.yml`, code and data in the
SSH user's `~/murfulu`. The tunnel connector runs there as the container
`murfulu_cloudflared` — the same tunnel the Mac used, so the hostname needed no
DNS change. Sokhan's stack on the same machine is compose project `mana`;
nothing in this repository touches it, and nothing here publishes a host port.

**Which machine that is stays out of the repository.** Three local files,
each copied from the `*.example` beside it and gitignored, hold everything
specific to the host:

| file | holds |
|---|---|
| `deploy/host.env` | `MURFULU_SSH_HOST`, the `Host` in `deploy/ssh_config`; `MURFULU_REMOTE_DIR`, the checkout on the server (default `murfulu`, relative to the SSH user's home) |
| `deploy/ssh_config` | the host's address, user and port |
| `deploy/cloudflared/config.yml` | the tunnel id and the name of its credentials file. `deploy` carries it to the server; `tunnel` copies the credentials JSON from `~/.cloudflared/` |

A fresh clone has none of them, and `deploy/server.sh` names the one that is
missing rather than guessing.

Everything is `deploy/server.sh`, run on the Mac from the repo root, over SSH,
from a network that reaches the host:

| | |
|---|---|
| `deploy` | rsync the working tree, rebuild and restart the app — **the normal deploy**. Never starts the tunnel. |
| `check` | on the server, not public: health, served corpus version, `generate پر`, L16, Caddy's 401 |
| `counts` | ES document counts and Postgres rows + per-table checksum, Mac vs server |
| `corpus vN` | (v12's way; v13 was built on the server instead, ENGINEERING) a new corpus version built on the Mac: snapshot of `passages` + the four `*-v13` indices on the Mac into a repository of its own (`/snapshots/release-v13`), streamed into the server's `es_snapshots` volume and restored, aliases set, counts compared. Then set the `*-v13` paths in the server `.env`, `data`, `deploy`. |
| `release v13 [lexicon-20261012]` | serve a corpus version already on the server: all three aliases in one request, the version paths (and the lexicon) in the server `.env`, the api recreated. **Also the rollback**: `deploy/server.sh release v12 lexicon-20260808`. |
| `data` | rsync exactly the files `deploy/server.env.example` names (`MURFULU_*_PATH`) — keep it in step with the server `.env` |
| `env`, `tunnel` | once: the server `.env` (Postgres password generated there; the site login copied from the Mac's `.env` unread, so the same password works) and the tunnel credentials |
| `cutover` / `rollback` | switch which machine serves the site, below |
| `migrate`, `ps`, `logs` | as named |

**`corpus` is slow over a remote link, and that is expected.** v12 on 2026-10-17:
the snapshot took 72 s on the Mac, the ~2.9 GB copy (`docker cp` piped through
SSH) **~55 minutes at ~0.8 MB/s**, the restore under a minute — 58 minutes in
all, with the Mac serving throughout. While `docker cp` runs, `docker exec` into
the server's Elasticsearch container blocks, so watch progress from the host:
`du -sh /var/lib/docker/volumes/murfulu_es_snapshots/_data`. Counts after the
restore, Mac = server: passages 1,427,460 (`_count`; 19,556,734 Lucene docs
with the nested ones), documents 133,148, word_types 411,165, derivations
1,870,987.

**Only one connector at a time.** Two connectors on one tunnel are load-balanced
by Cloudflare, which here would mean two databases answering in turn.
`cutover` parks the Mac's LaunchAgent `com.cloudflared.murfulu` in
`~/Library/LaunchAgents/disabled/` (config and credentials stay in
`~/.cloudflared/`), copies the database once more now that nothing can write on
the Mac, and starts `murfulu_cloudflared`.

**Rollback is one command: `deploy/server.sh rollback`** — stops the server's
connector, moves the LaunchAgent back and starts it. The Mac stack was left
running for exactly this. Rulings, feedback or proposals written on the server
since the cutover exist only there: `deploy/server.sh db-back` copies the
database back to the Mac (run it before or right after the rollback).

**Autostart is Sokhan's.** The Windows task «Sokhan WSL» boots WSL at startup
and logon and keeps it alive; systemd starts Docker, and Docker starts every
container with a restart policy — `restart: always` for the app, `unless-stopped`
for the connector, so a connector stopped by `rollback` stays stopped across a
reboot. **The limitation is the task's:** it runs with the user's stored Windows
password, so after a password change it fails until it is re-entered
(`Set-ScheduledTask -TaskName 'Sokhan WSL' -User <user> -Password <new>`,
admin), and until then murfulu, like Sokhan, only comes back after a login.

**Corpus versions are built on the server since v13** (2026-10-18, ENGINEERING
"Building a corpus version"): 16 minutes in a one-shot container, against
v12's 58 minutes of copying. The Mac's Elasticsearch holds v4–v12 and stops
there; the server holds what it serves (v14) and the two before it (v13,
v12) for the rollback. **Serving v14 since 2026-10-18** (v13 plus the function-word
rule, `data/compare-v13-v14.md`) with karbon 1.2.0's lexicon
(`lexicon-20261012`); **rollback: `deploy/server.sh release v13
lexicon-20261012`** — the code keeps applying the list to live lookups, so a
full return also needs the code reverted and `deploy`. The server `.env`
before v14 is `~/murfulu/.env.bak-v13-20261018`; v12's indices are still
there too (`release v12 lexicon-20260808`).
The server `.env` before v13 is kept as `~/murfulu/.env.bak-v12-20261018`. `docker compose -f
docker-compose.prod.yml` on the Mac still targets the Mac's stack, which is the
fallback now and no longer production.

---

## 1. What you are deploying

Five containers, from `docker-compose.prod.yml`:

```
  reader ──https──▶ caddy  │  murfulu.mosaic-hub.de  →  web:80
                    (TLS +  │                            └─ /api → api:8000
                  password) │
                            db (postgres)      elasticsearch
```

| Container | Role | Reachable from outside? |
|---|---|---|
| `caddy` | HTTPS, Let's Encrypt, the password wall | **Yes** — 80 and 443, the only door |
| `web` | The React app on nginx; proxies `/api` to the API | No |
| `api` | FastAPI: rules, generation, search, questions | No |
| `db` | Postgres — rules, questions, rulings, feedback | No |
| `elasticsearch` | The corpus and the derivations | No |

**Nothing but Caddy publishes a port, and that is the point.** The development
file puts Postgres on 5432 and Elasticsearch on 9200 so a laptop is workable.
Elasticsearch runs with security disabled; on a server a published 9200 is the
whole corpus, writable, to anyone who finds the IP.

---

## 2. What the server needs

| | |
|---|---|
| OS | Linux with Docker and the Compose plugin |
| Ports | 80 and 443 open — Caddy needs both, 80 for the certificate challenge |
| RAM | **4 GB**, and Elasticsearch is nearly all of it |
| Disk | **~8 GB** for the data, plus images |
| DNS | `murfulu.mosaic-hub.de` → the server's public IP, **before** the first start |

Measured, so the disk figure is not a guess:

| | |
|---|---|
| `passages` index | 2.2 GB |
| one corpus version's `derivations` | ~440 MB |
| `documents` and `word_types` | ~250 MB |
| the lexicon and the score artefacts | 93 MB |

Eleven corpus versions are on the development machine. **Ship one.** Only the
version the app is configured for is served; the rest are history and belong on
the laptop that built them.

---

## 3. Configure

```bash
cp .env.example .env
```

Everything above the *Server only* line is what a laptop already needs. Below
it, four settings:

| | |
|---|---|
| `MURFULU_DOMAIN` | the subdomain Caddy answers on and asks for a certificate for |
| `MURFULU_SITE_USER` | who the password belongs to |
| `MURFULU_SITE_PASSWORD_HASH` | a bcrypt hash, **never the password** |
| `MURFULU_DATA_DIR` | where the lexicon and artefacts live on the server |

The hash:

```bash
docker run --rm caddy:2.9.1-alpine caddy hash-password --plaintext 'the-password'
```

Set `POSTGRES_PASSWORD` to something that is not `change-me`, and
`ES_JAVA_OPTS` to `-Xms2g -Xmx2g` if the server has the room.

---

## 4. Get the data there

The app will start without any of this and say so on every screen rather than
showing zeros — but it will have nothing to show. Two things move:

**The lexicon and the measured artefacts**, into `MURFULU_DATA_DIR`:

```bash
rsync -av data/ server:/srv/murfulu/data/
```

**The corpus indices.** Re-ingesting on the server needs the Ganjoor dump and
hours of compute, and the dump does not belong on that server — so the corpus
moves as a snapshot.

**Both compose files declare `path.repo: /snapshots` and an `es_snapshots`
volume.** They did not until 2026-08-17, and without it Elasticsearch refuses to
register any `fs` repository at all — *"location doesn't match any of the
locations specified by path.repo because this setting is empty"*. The version of
this section written the same morning began with a command that could not run.
It is a separate volume from `es_data` so a snapshot survives the cluster being
wiped and rebuilt, which is exactly when it is wanted.

```bash
# on the laptop, with the dev stack running. The volume is created by Docker
# as root and Elasticsearch runs as uid 1000, so it needs an owner once.
docker compose exec -u root elasticsearch chown -R elasticsearch:root /snapshots

curl -X PUT "localhost:9200/_snapshot/out" -H 'content-type: application/json' \
  -d '{"type":"fs","settings":{"location":"/snapshots"}}'
curl -X PUT "localhost:9200/_snapshot/out/v11?wait_for_completion=true" \
  -H 'content-type: application/json' \
  -d '{"indices":"passages,documents-v11,word_types-v11,derivations-v11"}'
```

Measured on v11: **72 seconds, 2.8 GB, 4 of 4 shards**. Move that directory into
the server's `es_snapshots` volume, register the same repository there, and
restore.

**Check the numbers afterwards against `data/corpus_report-v11.json`** —
133,148 documents and 25,497,189 words — the same check a rebuild gets, because
a half-restored index looks exactly like a small corpus.

---

## 4b. Publishing it: a Cloudflare Tunnel, not a public IP

**How the sibling apps on this domain are actually published**, and it is worth
knowing before provisioning a server: `sokhan.mosaic-hub.de` runs from a
workstation and reaches the internet through a Cloudflare Tunnel —
`mosaic/mana/start-prod.sh` brings the stack up and then runs `cloudflared`.
There is no remote host and no SSH.

That changes three things and none of them is a downgrade:

| | server | tunnel |
|---|---|---|
| TLS | Caddy, from Let's Encrypt | Cloudflare, at its edge |
| DNS | an A record you create first | a CNAME `cloudflared` creates |
| port 80/443 | open to the internet | **not open at all** |

**The site address carries its scheme for exactly this reason.** Behind a
tunnel Cloudflare forwards plain HTTP, so Caddy must not ask Let's Encrypt for
a certificate it could never validate:

```bash
MURFULU_SITE_ADDRESS=http://murfulu.mosaic-hub.de   # tunnel
MURFULU_SITE_ADDRESS=murfulu.mosaic-hub.de          # server, auto-HTTPS
MURFULU_BIND=127.0.0.1                              # tunnel: loopback only
MURFULU_BIND=0.0.0.0                                # server: the real address
```

**`MURFULU_BIND` is the one that matters on a laptop.** Publishing Caddy on
`0.0.0.0:80` from a workstation offers the corpus to everything on the same
wifi as well as to `cloudflared`. It defaults to `127.0.0.1`, so the tunnel is
the only route in and the password wall is the only door.

Then, once `MURFULU_SITE_PASSWORD_HASH` is set — **not before**, see §7:

```bash
cloudflared tunnel create murfulu                    # once
cloudflared tunnel route dns murfulu murfulu.mosaic-hub.de
cat > ~/.cloudflared/config-murfulu.yml <<'YAML'
tunnel: <the id printed above>
credentials-file: /Users/you/.cloudflared/<that-id>.json
protocol: http2
ingress:
  - hostname: murfulu.mosaic-hub.de
    service: http://localhost:80
  - service: http_status:404
YAML
cloudflared tunnel --config ~/.cloudflared/config-murfulu.yml run
```

**A tunnel with no wall behind it publishes everything §7 says must not be
published**, and it does it the moment it connects. Set the hash first.

## 5. Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

The schema is built by migration, never by hand.

**Nothing else to set up.** There used to be a step here giving the linguist an
account, because passing the password wall left him able to look and not to
answer. As of 2026-08-17 there is one account, it makes itself on first use,
and everyone behind the wall may rule, propose and grade. The password you set
above is the only credential anyone needs.

---

## 6. Check it

```bash
docker compose -f docker-compose.prod.yml ps          # all five healthy
curl -o /dev/null -w '%{http_code}\n' https://murfulu.mosaic-hub.de/   # 401
curl -o /dev/null -w '%{http_code}\n' -u user:pass \
  https://murfulu.mosaic-hub.de/                                       # 200
```

**The 401 is the test that matters.** It was checked before this was written,
against the running app: no credentials gives 401 on the site *and* on `/api`,
wrong credentials 401, right credentials 200 and the app.

**Check it by the name it answers to.** The commands above use the public
address, and that is not incidental: Caddy's site block is
`{$MURFULU_SITE_ADDRESS}`, so a request carrying any other Host matches no site
at all and is answered with **200 and an empty body**. From the machine itself
`curl http://localhost/` therefore looks exactly like a wall that has been
taken off. Ask for the name instead:

```bash
curl -o /dev/null -w '%{http_code}\n' -H 'Host: murfulu.mosaic-hub.de' http://localhost/
```

Found 2026-08-20, checking a deploy the quick way.

---

## 7. What this publishes

Behind that password sit **19.5 million lines of Ganjoor poetry** and karbon's
**Dehkhoda-derived lexicon**. Three things are not this project's to give, and
none of them is a coding task:

- **The Ganjoor terms — confirmed, and the answer is no warranty.** Their FAQ,
  asked whether the data are free of copyright, answers «لزوماً خیر!»: no legal
  review has been made, most of the content was typed from published books
  whose own status was never established, and free access is not a licence.
  Their service is GPL-3.0; the poetry is not covered by it. **This one is
  settled and it settles against publishing.**
- **karbon's lexicon.** Mounted read-only, under review with the linguist, and
  its terms are karbon's question rather than this repository's.
- **The expert feedback set.** Judgements about the language, not code, and not
  this project's to hand on.

**Murfulu's own licence is settled** — Apache-2.0 since 2026-08-17, PLAN 8.4 —
and it deliberately does not reach any of the three. See NOTICE.

**So the password is not a placeholder waiting on a decision.** Removing
`basic_auth` from the `Caddyfile` is a one-line edit and it publishes all
three, and the first of them is now known to be unpublishable rather than
merely unchecked.

---

## 8. Later

**Deploy on push.** mosaic-studio builds on every push to main through Jenkins
and reports to `studio.mosaic-hub.de`; the same could be done here. Not set up,
because a research app that rebuilds Elasticsearch on a bad push is worse than
one deployed by hand.

**A real sign-in.** The password wall is a wall, not a door with names on it.
The app already knows who its experts are; what it does not have is a session
the browser carries, which is what would let Caddy check a person instead of a
shared secret. Worth doing if more than a handful of people ever need in.
