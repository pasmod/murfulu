"""Readings people picked on the reading screen, as answers the model learns.

``deploy/server.sh proposals`` fetches what readers picked or typed into
``data/behnevis-proposals.jsonl``; ``tools/build_behnevis.py`` learns the picks
among the bank's readings from it, and ``tools/evaluate_behnevis.py`` holds
them out by poet like every other answer (DECISIONS 2026-11-14, *a pick
teaches the model*).
"""

from __future__ import annotations

import json
from pathlib import Path

from murfulu.behnevis.choice import Answered
from murfulu.behnevis.transcribe import key


def picks_from(
    path: Path,
    bank: dict[str, tuple[str, ...]],
    functions: dict[str, tuple[str, ...]],
) -> list[Answered]:
    """The readings people picked among the current bank's, as answers.

    Checked against the bank being built, not the flag saved with the pick:
    a reading karbon added since is learned, one it removed is not. The
    author comes from the text's heading, so a held-out poet stays held out.
    """
    found: list[Answered] = []
    for line in path.open(encoding="utf-8"):
        one = json.loads(line)
        spelling = key(one.get("spelling_fa") or "")
        latin = one.get("latin") or ""
        known = (*functions.get(spelling, ()), *bank.get(spelling, ()))
        if not spelling or latin not in known:
            continue
        found.append(
            Answered(
                spelling,
                latin,
                key(one["before"]) if one.get("before") else None,
                key(one["after"]) if one.get("after") else None,
                (one.get("heading") or "").split(" · ")[0],
                by_person=True,
            )
        )
    return found
