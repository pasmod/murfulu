# Deploying Murfulu to a server

The whole system in Docker, behind one password, with automatic HTTPS. Written
2026-08-17 for `murfulu.mosaic-hub.de`, following the pattern mosaic-studio
already uses on the same domain.

**Read [What this publishes](#7-what-this-publishes) before opening it to
anyone.** Murfulu's own licence is settled and deliberately does not reach the
corpus; Ganjoor's terms are settled too, and they settle *against* publishing.
The password is not a placeholder.

---

## 0. Where production runs (since 2026-10-27)

**On a rented VPS shared with Sokhan, since 2026-10-27.** Ubuntu 24.04 →
Docker Engine; compose project **`murfulu`** from `docker-compose.prod.yml` +
`docker-compose.server.yml`, code and data in the SSH user's `~/murfulu`. The
tunnel connector runs there as the container `murfulu_cloudflared` — the same
tunnel as before, so the hostname needed no DNS change. Sokhan's stack on the
same machine is compose project `mana`; nothing in this repository touches it,
and nothing here publishes a host port. The host's base (user, firewall,
updates, swap, Docker) is Sokhan's set-up and is not repeated here.

**The fallback is the previous host** that served production from 2026-10-17
to 2026-10-27 (Ubuntu in WSL, Docker Engine, the same compose project). Its
stack keeps running with corpus v12–v14 and its connector `murfulu_cloudflared`
**stopped, not removed**, so a rollback is one command. Before that, from
2026-08-17, the Mac served the site; its stack is still there and is the
fallback only when no fallback host is configured.

**Which machines those are stays out of the repository.** Three local files,
each copied from the `*.example` beside it and gitignored, hold everything
specific to the hosts:

| file | holds |
|---|---|
| `deploy/host.env` | `MURFULU_SSH_HOST`, the production `Host` in `deploy/ssh_config`; `MURFULU_REMOTE_DIR`, the checkout there (default `murfulu`, relative to the SSH user's home); and `MURFULU_FALLBACK_SSH_HOST` / `MURFULU_FALLBACK_REMOTE_DIR`, the machine that served before. Unset, the fallback is the Mac. |
| `deploy/ssh_config` | each host's address, user and port |
| `deploy/cloudflared/config.yml` | the tunnel id and the name of its credentials file. `deploy` carries it to the server; `tunnel` copies the credentials JSON from `~/.cloudflared/` |

A fresh clone has none of them, and `deploy/server.sh` names the one that is
missing rather than guessing. `deploy/host.previous.env` (also gitignored)
keeps the settings from when the previous host was production, with no fallback.

Everything is `deploy/server.sh`, run on the Mac from the repo root, over SSH,
from a network that reaches both hosts (the previous one only over a VPN):

| | |
|---|---|
| `deploy` | rsync the working tree, rebuild and restart the app — **the normal deploy**. Never starts the tunnel. Never carries `.denylist` or the host files. |
| `check` | on the server, not public: health, served corpus version, `generate پر`, L16, Caddy's 401. Exits 1 on any failure. |
| `counts` | ES document counts and Postgres rows + per-table checksum, fallback vs server |
| `corpus vN` | snapshot of `passages` + the three `*-vN` indices on the fallback into a repository of its own (`/snapshots/release-vN`), streamed through the Mac into the server's `es_snapshots` volume and restored, aliases set, counts compared. How v14 reached the VPS. A *new* version is built on the server instead (ENGINEERING). |
| `release v14 [lexicon-20261012]` | serve a corpus version already on the server: all three aliases in one request, the version paths (and the lexicon) in the server `.env`, the api recreated. |
| `data` | rsync exactly the files `deploy/server.env.example` names (`MURFULU_*_PATH`) from the Mac — keep it in step with the server `.env` |
| `env`, `tunnel` | once: the server `.env` (Postgres password generated there; the site login copied unread from the fallback's `.env`, so the same password works) and the tunnel credentials |
| `db`, `db-back` | copy the Postgres database fallback → server, or back, and compare |
| `cutover` / `rollback` | switch which machine serves the site, below |
| `migrate`, `ps`, `logs` | as named |

**The move to the VPS, 2026-10-27, as run:** `env`, `tunnel`, `data`,
`deploy` (3 min 21 s, images built there), `corpus v14` (below), `db`,
`check`, `counts`, `cutover`. The fallback's `.env` and the server's differ
only in the generated Postgres password. The code deployed was `main`, which
differed from the previous host's only in docs and one anonymised file name.

**`corpus` over a remote link is a copy, and it is timed by the slowest hop.**
v14 on 2026-10-27, previous host → Mac (VPN) → VPS: snapshot 72 s on the previous host,
2.8 GB copied at **~3.7 MB/s** (the VPN; Mac → VPS measured ~6.5 MB/s), restore
under a minute — **14 min 14 s in all**, with the previous host serving throughout.
v12 on 2026-10-17, Mac → previous host: ~2.9 GB in ~55 minutes at ~0.8 MB/s. While
`docker cp` runs, `docker exec` into the server's Elasticsearch container
blocks, so watch progress from the host: `sudo du -sh
/var/lib/docker/volumes/murfulu_es_snapshots/_data`. **Counts after the move,
previous host = VPS:** passages 1,427,460 (`_count`; 19,556,734 Lucene docs with
the nested ones), documents 133,148, word_types 411,190, derivations 1,844,043;
Postgres identical row for row and by checksum (195 rules, 26 questions, one
ruling, 10 feedback). **Building v14 on the VPS instead was not the faster
path:** it still needs `passages` (2 GB) copied, plus a 15-minute build and a
comparison to show the rebuild equals what is served; the snapshot is that
equality by construction.

**Memory: murfulu stays under 5 GB on a 16 GB machine Sokhan also uses.**
Every service has a `mem_limit` in `docker-compose.server.yml` (Elasticsearch
3 GB, api 1 GB, db 512 MB, web, caddy and cloudflared 128 MB each: 4.9 GB in
all). Elasticsearch's heap is **1 GB, not 2**: after 9.6 days serving v14 on
the previous host the 1 GB heap was 28% used with no old-generation collection,
and a 2 GB heap tried on the VPS left 2.5 GiB anonymous memory and only
~0.5 GB of the 3 GB for Lucene's page cache over a 2 GB `passages`. Measured
after the cutover (`docker stats`): murfulu ~1.9 GiB (Elasticsearch 1.54 GiB,
api 266 MiB, the rest under 50 MiB each), Sokhan ~6.9 GiB (Qdrant 5.8 GiB of
it), `free`: 3.5 GB used, 12.2 GB available, no swap in use, no OOM kill.

**Only one connector at a time.** Two connectors on one tunnel are load-balanced
by Cloudflare, which here would mean two databases answering in turn.
`cutover` runs `check` first and stops unless it passes, then stops the
fallback's connector (`compose stop cloudflared` on the fallback host; with the
Mac as fallback it parks the LaunchAgent `com.cloudflared.murfulu` in
`~/Library/LaunchAgents/disabled/`), copies the database once more now that
nothing can write there, and starts `murfulu_cloudflared` on the server. The
2026-10-27 cutover took 32 s; `cloudflared tunnel info murfulu` afterwards
listed exactly one connector, from the VPS.

**Rollback is one command: `deploy/server.sh rollback`** — stops the server's
connector and starts the previous host's again (`compose start cloudflared`; with
the Mac as fallback, moves the LaunchAgent back). Rulings, feedback or
proposals written on the server since the cutover exist only there:
`deploy/server.sh db-back` copies the database back to the fallback (run it
before or right after the rollback). To make the previous host production again in
the script's eyes as well, `cp deploy/host.previous.env deploy/host.env`.

**Autostart.** On the VPS systemd starts Docker, and Docker starts every
container with a restart policy — `restart: always` for the app,
`unless-stopped` for the connector, so a connector stopped by `rollback` or
`cutover` stays stopped across a reboot. The previous host's stack depends on
Sokhan's Windows task «Sokhan WSL», which boots WSL at startup and logon with
the user's stored Windows password; after a password change it fails until
the password is re-entered (`Set-ScheduledTask -TaskName 'Sokhan WSL' -User
<user> -Password <new>`, admin), and until then the fallback only comes back
after a login.

**Corpus versions are built on the server since v13** (2026-10-18, ENGINEERING
"Building a corpus version"): 16 minutes in a one-shot container, against
v12's 58 minutes of copying. **Serving v14 since 2026-10-18** (v13 plus the
function-word rule, `data/compare-v13-v14.md`) with karbon 1.2.0's lexicon
(`lexicon-20261012`). **The VPS holds v14 only** (and `passages`); v12 and v13
stay on the previous host with their `.env` backups (`~/murfulu/.env.bak-v13-20261018`,
`.env.bak-v12-20261018`), so returning to an earlier corpus version is a
rollback to the previous host followed by `release v13 lexicon-20261012` there (with
`deploy/host.previous.env` as `host.env`) — the code keeps applying the
function-word list to live lookups, so a full return to v13 also needs the code
reverted and `deploy`. **A build on the VPS must fit the shared memory**: the
7 GB cap the previous host's builds ran with does not (OPEN_QUESTIONS).
`docker compose -f docker-compose.prod.yml` on the Mac still targets the Mac's
stack, which has not been production since 2026-10-17.

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
