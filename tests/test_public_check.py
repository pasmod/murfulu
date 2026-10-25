"""The pre-commit check keeps the host, credentials and names out of the repository.

``tools/public_check.py`` is what stands between a working tree and a public
repository, so what it catches is pinned here. **The samples are assembled at
run time**, never written out: a test file holding a private address or a
name would itself be what the check refuses to commit.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "public_check", ROOT / "tools" / "public_check.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # A dataclass looks its module up by name, so the module must be known.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TOOL = _tool()
PRIVATE_IP = ".".join(["192", "168", "7", "21"])
TUNNEL_ID = "-".join(["1a2b3c4d", "0000", "4000", "8000", "123456789abc"])


def _rules(line: str, denylist: str = "") -> list[str]:
    denied = TOOL.denylist_patterns(denylist)
    return [f.rule for f in TOOL.check_line("x.md", 1, line, denied)]


@pytest.mark.parametrize(
    "line",
    [
        f"  HostName {PRIVATE_IP}",
        "ssh " + ".".join(["10", "0", "3", "4"]),
        "at " + ".".join(["172", "20", "1", "9"]) + ", inside",
        f"tunnel: {TUNNEL_ID}",
        f"credentials-file: /etc/cloudflared/{TUNNEL_ID}.json",
        "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
        "POSTGRES_PASSWORD=" + "s3cr3t-value-here",
        "token " + "ghp_" + "a" * 36,
        "code and data in " + "/root" + "/murfulu",
    ],
)
def test_a_generic_pattern_blocks_the_line(line: str) -> None:
    assert _rules(line)


@pytest.mark.parametrize(
    "line",
    [
        "  HostName 203.0.113.10",
        "version 10.2 of the lexicon, 172.3 MB",
        ".".join(["192", "168", "1", "1", "5"]) + " is not an address",
        "tunnel: <tunnel-id>",
        "POSTGRES_PASSWORD=change-me",
        "MURFULU_SITE_PASSWORD_HASH=$2a$14$replace-me",
        "MURFULU_SITE_PASSWORD_HASH=",
        "the SSH user's ~/murfulu",
    ],
)
def test_what_the_repository_already_says_passes(line: str) -> None:
    assert _rules(line) == []


def test_the_allow_marker_lifts_a_generic_pattern() -> None:
    assert _rules(f"RFC 1918 example {PRIVATE_IP}  # {TOOL.ALLOW}") == []


def test_a_name_matches_as_a_word_in_either_case() -> None:
    denylist = "# people\nTestname\n"
    assert _rules("asked by Testname on Monday", denylist)
    assert _rules("TESTNAME-stem-1", denylist)
    assert _rules("Testnames are many", denylist) == []


def test_the_allow_marker_never_lifts_the_denylist() -> None:
    assert _rules(f"Testname  # {TOOL.ALLOW}", "Testname")


def test_a_persian_name_matches_however_it_was_typed() -> None:
    denylist = "نیک‌نام\nعلی\n"
    assert _rules("از نیک‌نام پرسیدیم", denylist)
    assert _rules("از نیکنام پرسیدیم", denylist)
    assert _rules("از نیک نام پرسیدیم", denylist)
    assert _rules("گفتهٔ علي", denylist), "Arabic yeh is the same letter"
    assert _rules("گفتهٔ عَلی", denylist), "harakat do not hide a name"
    assert _rules("علی‌ها", denylist), "a ZWNJ ends the word"
    assert _rules("عالی", denylist) == []


def test_a_regular_expression_entry() -> None:
    assert _rules("hosted at Example Corp", r"re:\bexample (corp|inc)\b")


def test_a_local_file_is_refused_by_its_path() -> None:
    for path in ("deploy/ssh_config", "deploy/host.env", ".denylist", "web/.env"):
        assert list(TOOL.check_path(path, [])), path
    for path in ("deploy/ssh_config.example", ".env.example", "docs/DEPLOY.md"):
        assert list(TOOL.check_path(path, [])) == [], path


def test_a_name_in_a_file_name_is_refused() -> None:
    denied = TOOL.denylist_patterns("Testname")
    assert list(TOOL.check_path("rules/notes_testname.docx", denied))
    assert list(TOOL.check_path("Testname-notes.rtf", denied))
    assert _rules("RULE_ID = 'testname_stem_1'", "Testname")


def test_the_denylist_itself_is_never_committed() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/.denylist\n" in ignored
    assert (ROOT / ".denylist.example").is_file()
