"""Refuse a commit that would publish what must stay private.

    python tools/public_check.py          # the staged changes — what the hook runs
    python tools/public_check.py --all    # every tracked file

**The repository is public**, and three kinds of thing must never reach it:
the production host's specifics (docs/DEPLOY.md §0), credentials, and the
names of the people who work on the project — the docs refer to them by role.
``tools/hooks/pre-commit`` runs this before every commit; ``make hooks``
installs it.

Two sets of rules.

**Generic patterns**, here in the code because they reveal nothing: a private
IPv4 address, a real tunnel id or credentials file in a cloudflared config,
private keys and access tokens, a filled-in secret on an env-style line, a
path in the root user's home on a host, and the local files that hold the
host's specifics being staged at all.

**The denylist**, ``.denylist`` at the repository root — gitignored and never
committed, because its entries are exactly what must not be published: the
host name, its address, the tunnel id, people's names in Latin and in Persian
script. ``.denylist.example`` shows the format. Without the file only the
generic patterns run, and the check says so.

The staged mode reads only the lines a commit adds and the paths it adds, so
text already in the repository is not judged again on every commit. A line may
opt out of a generic pattern with ``public-check: allow``; nothing opts out of
the denylist.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

#: The local file of terms that must not be published, at the repository root.
DENYLIST = ".denylist"

#: A line carrying this is exempt from the generic patterns, never the denylist.
ALLOW = "public-check: allow"

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

#: Patterns that reveal nothing themselves, so they can live in the repository.
GENERIC: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "a private IPv4 address",
        re.compile(
            r"(?<![\d.])(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)"
            r"\.\d{1,3}\.\d{1,3}(?!\.?\d)"
        ),
    ),
    ("a tunnel id in a cloudflared config", re.compile(rf"^\s*tunnel:\s*{_UUID}")),
    ("a tunnel credentials file", re.compile(rf"credentials-file:.*{_UUID}")),
    ("tunnel credentials", re.compile(r'"(?:TunnelSecret|AccountTag)"')),
    ("a private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "an access token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_\w{40,}|AKIA[0-9A-Z]{16}"
            r"|xox[abposr]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9_-]{20,})"
        ),
    ),
    ("a bcrypt hash", re.compile(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}")),
    (
        "a secret filled in",
        re.compile(
            r"^\s*(?:export\s+)?[A-Z][A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY)"
            r"[A-Z0-9_]*\s*=\s*(?!.*(?:change-me|replace-me|\$\{))\S{8,}"
        ),
    ),
    # Split so that this source line does not match its own pattern.
    ("a host path under /root", re.compile(r"(?<![\w~.-])/" + "root/")),
)

#: Files that hold the host's specifics or secrets: never staged, whatever
#: they contain (docs/DEPLOY.md §0).
PRIVATE_PATHS = re.compile(
    r"^(?:\.denylist|deploy/host\.env|deploy/ssh_config|deploy/cloudflared/config\.yml"
    r"|deploy/cloudflared/[^/]+\.json|(?:.*/)?\.env)$"
)

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

#: Arabic letters a Persian name may be typed with, and the Persian ones they
#: stand for — so «علي» and «علی» are one name.
_PERSIAN = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه"})

#: Harakat, the dagger alif and the tatweel: marks that can sit inside a name
#: without changing it.
_MARKS = re.compile(r"[ً-ٰٟـ]")


@dataclass(frozen=True)
class Finding:
    """One thing that must not be committed, and where it is."""

    path: str
    line: int
    rule: str

    def __str__(self) -> str:
        """Render as ``path:line: rule``, the shape editors jump to."""
        where = f"{self.path}:{self.line}" if self.line else self.path
        return f"{where}: {self.rule}"


def normalise(text: str) -> str:
    """Fold the spellings a name can hide behind into one form.

    An underscore counts as a space, so a name between underscores — in a file
    name or an identifier — is still a word of its own.
    """
    folded = unicodedata.normalize("NFC", text).translate(_PERSIAN)
    return _MARKS.sub("", folded).replace("_", " ")


def denylist_patterns(text: str) -> list[tuple[str, re.Pattern[str]]]:
    """Parse a denylist: one term per line, ``re:`` for a regular expression.

    A plain term matches as a whole word, ignoring case, in either script.
    Blank lines and lines starting with ``#`` are skipped.
    """
    patterns = []
    for raw in text.splitlines():
        term = raw.strip()
        if not term or term.startswith("#"):
            continue
        if term.startswith("re:"):
            source = term[3:]
        else:
            # A space may be any run of spaces, and a ZWNJ may be typed as
            # nothing or a space: «نیک‌نام», «نیکنام» and «نیک نام» are one name.
            body = re.escape(normalise(term)).replace("\\ ", r"\s+")
            body = body.replace("\u200c", "[\u200c ]?")
            source = rf"(?<!\w){body}(?!\w)"
        patterns.append((term, re.compile(source, re.IGNORECASE)))
    return patterns


def check_line(
    path: str, number: int, line: str, denied: list[tuple[str, re.Pattern[str]]]
) -> Iterator[Finding]:
    """Yield what one line must not carry."""
    if ALLOW not in line:
        for rule, pattern in GENERIC:
            if pattern.search(line):
                yield Finding(path, number, rule)
    folded = normalise(line)
    for term, pattern in denied:
        if pattern.search(folded):
            yield Finding(path, number, f"denylist entry «{term}»")


def check_path(
    path: str, denied: list[tuple[str, re.Pattern[str]]]
) -> Iterator[Finding]:
    """Yield what a path must not be or contain — a file name is published too."""
    if PRIVATE_PATHS.match(path):
        yield Finding(
            path, 0, "a local file that holds the host's specifics or a secret"
        )
    folded = normalise(path)
    for term, pattern in denied:
        if pattern.search(folded):
            yield Finding(path, 0, f"denylist entry «{term}» in the file name")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def staged() -> tuple[list[str], list[tuple[str, int, str]]]:
    """The paths a commit adds or changes, and the lines it adds, numbered."""
    paths = [
        p
        for p in _git(
            "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"
        ).split("\0")
        if p
    ]
    added: list[tuple[str, int, str]] = []
    path, number = "", 0
    diff = _git(
        "diff", "--cached", "-U0", "--no-color", "--no-ext-diff", "--diff-filter=ACMR"
    )
    for raw in diff.split("\n"):
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else ""
        elif raw.startswith("@@"):
            hunk = _HUNK.match(raw)
            number = int(hunk.group(1)) if hunk else 0
        elif raw.startswith("+") and path:
            added.append((path, number, raw[1:]))
            number += 1
    return paths, added


def tracked(root: Path) -> tuple[list[str], list[tuple[str, int, str]]]:
    """Every tracked path and every line of every tracked text file."""
    paths = [p for p in _git("ls-files", "-z").split("\0") if p]
    lines: list[tuple[str, int, str]] = []
    for path in paths:
        data = (root / path).read_bytes() if (root / path).is_file() else b""
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        lines.extend(
            (path, n, line) for n, line in enumerate(text.split("\n"), start=1)
        )
    return paths, lines


def check(
    paths: Iterable[str],
    lines: Iterable[tuple[str, int, str]],
    denied: list[tuple[str, re.Pattern[str]]],
) -> list[Finding]:
    """Every finding over these paths and lines."""
    findings = [f for path in paths for f in check_path(path, denied)]
    findings.extend(
        f for path, n, line in lines for f in check_line(path, n, line, denied)
    )
    return findings


def main(argv: list[str] | None = None) -> int:
    """Check the staged changes (or every tracked file) and say what blocks them."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true", help="check every tracked file")
    arguments = parser.parse_args(argv)

    root = Path(_git("rev-parse", "--show-toplevel").strip())
    denylist = root / DENYLIST
    if denylist.is_file():
        denied = denylist_patterns(denylist.read_text(encoding="utf-8"))
    else:
        denied = []
        print(
            f"public-check: no {DENYLIST} — generic patterns only "
            f"(copy {DENYLIST}.example and fill it in)",
            file=sys.stderr,
        )

    paths, lines = tracked(root) if arguments.all else staged()
    findings = check(paths, lines, denied)
    for finding in findings:
        print(f"public-check: {finding}", file=sys.stderr)
    if findings:
        outcome = "in tracked files" if arguments.all else "— not committed"
        print(
            f"public-check: {len(findings)} finding(s) {outcome}. Remove them; "
            f"a generic pattern that is a false alarm takes «{ALLOW}» on its line.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
