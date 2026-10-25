"""What `deploy/server.sh check` asks the API, from inside the api container.

Run as `compose exec -T api python - < deploy/check_api.py`, so it talks to
localhost:8000 and needs neither the password wall nor the tunnel. It answers
the questions a deploy has to answer before anyone else sees it: is the store
and the cluster up, which corpus version is served, does a generation work end
to end, and are the linguist's rulings there. Exits 1 if any of them is wrong.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:8000"
EXPECTED_FORMS = ("poridan", "porande")  # from پر, through both readings

# What the container was configured to serve, read from its own environment
# rather than written here: the corpus version is in the report's file name,
# the lexicon snapshot is the lexicon's. A version written into this file went
# stale at the first release after it.
_report = os.environ.get("MURFULU_CORPUS_REPORT_PATH", "")
_found = re.search(r"-(v\d+)\.json$", _report)
EXPECTED_VERSION = _found.group(1) if _found else "?"
EXPECTED_LEXICON = os.path.basename(os.environ.get("MURFULU_LEXICON_PATH", ""))
EXPECTED_LEXICON = EXPECTED_LEXICON.removesuffix(".sqlite")


def get(path: str) -> dict:
    """One API answer as JSON, or the HTTP error as a small dict."""
    try:
        with urllib.request.urlopen(BASE + path, timeout=300) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return {"_http": error.code, "_body": error.read().decode()[:300]}


def forms(node: object) -> set[str]:
    """Every `form_latin` anywhere in a generate answer."""
    found: set[str] = set()
    if isinstance(node, dict):
        if isinstance(node.get("form_latin"), str):
            found.add(node["form_latin"].lower())
        for value in node.values():
            found |= forms(value)
    elif isinstance(node, list):
        for value in node:
            found |= forms(value)
    return found


failures: list[str] = []

health = get("/health")
print("health     ", health.get("status"), health.get("checks"))
if health.get("status") != "ok":
    failures.append("health")

corpus = get("/corpus")
serving = corpus.get("serving", {})
matches = corpus.get("describes_the_served_version")
print("corpus     ", serving, "report matches:", matches)
if set(serving.values()) != {EXPECTED_VERSION}:
    failures.append("corpus version")

query = urllib.parse.urlencode({"word": "پر", "limit": 0, "worded": "false"})
generated = get(f"/generate?{query}")
built = forms(generated)
present = {form: form in built for form in EXPECTED_FORMS}
version = generated.get("corpus_version")
lexicon = generated.get("lexicon_snapshot_id") or ""
print("generate پر", f"{len(built)} forms,", present, "corpus", version)
print("lexicon    ", lexicon, "| expected", EXPECTED_LEXICON)
if not all(present.values()):
    failures.append("generate")
if not lexicon.startswith(EXPECTED_LEXICON + ":"):
    failures.append("lexicon snapshot")

# که is the conjunction 609,699 times and karbon reads it as the adjective
# *keh*. Since v14 the entry says "homograph of a function word" and carries no
# count (rules/function_words.yaml). Printed, not failed on: a rollback to v13
# is a legitimate state and shows the old count here.
keh = get("/word/" + urllib.parse.quote("که:keh") + "?index=word_types&citations=0")
entry = keh.get("word", {})
print(
    "که:keh     ",
    "function_word:",
    entry.get("function_word"),
    "| total_count:",
    entry.get("total_count"),
)

questions = get("/questions")
listed = questions.get("questions", [])
l16 = next((q for q in listed if q.get("reference") == "L16"), {})
count = questions.get("count")
print("questions  ", count, "| L16:", l16.get("state"), "rulings", l16.get("rulings"))
if l16.get("state") != "answered":
    failures.append("L16")

if failures:
    print("FAILED:", ", ".join(failures))
    sys.exit(1)
print("all checks passed")
