"""Take karbon's lexicon out of a release wheel and store it as a snapshot.

    python tools/fetch_lexicon.py v1.3.2
    python tools/fetch_lexicon.py --wheel path/to/karbon_nlp-1.3.2-py3-none-any.whl

The lexicon murfulu reads is the SQLite file inside karbon's wheel
(``karbon/data/lexicon.sqlite``), as it was for 1.2.0 (data/README.md). The
snapshot is named after karbon's own build date, ``lexicon-YYYYMMDD.sqlite``,
in ``data/``, which git ignores: karbon's lexicon is not this repository's to
publish (NOTICE).

Without ``--wheel`` the wheel is downloaded with the GitHub CLI from karbon's
release page, which needs read access to karbon's repository. A file that
already exists under the target name is left alone if it is the same file and
refused if it is not — a snapshot id is a promise about its content.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "kp-multiverse/karbon"
MEMBER = "karbon/data/lexicon.sqlite"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def download(tag: str, into: Path) -> Path:
    """The release's wheel, downloaded with ``gh`` into ``into``."""
    subprocess.run(
        [
            "gh", "release", "download", tag, "-R", REPOSITORY,
            "-p", "karbon_nlp-*.whl", "-D", str(into), "--clobber",
        ],
        check=True,
    )  # fmt: skip
    wheels = sorted(into.glob("karbon_nlp-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected one wheel in release {tag}, found {len(wheels)}")
    return wheels[0]


def meta(path: Path) -> dict[str, str]:
    """Karbon's own description of the file: build date, entries, reviewed."""
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        return {
            str(k): str(v)
            for k, v in connection.execute("SELECT key, value FROM karbon_meta")
        }
    finally:
        connection.close()


def extract(wheel: Path, data_dir: Path) -> Path:
    """Write the wheel's lexicon to ``data_dir/lexicon-<build date>.sqlite``."""
    with tempfile.TemporaryDirectory() as scratch:
        with zipfile.ZipFile(wheel) as archive:
            if MEMBER not in archive.namelist():
                raise SystemExit(f"{wheel.name} has no {MEMBER}")
            unpacked = Path(archive.extract(MEMBER, scratch))
        described = meta(unpacked)
        build_date = described.get("build_date", "")
        if len(build_date) != 10:
            raise SystemExit(f"{wheel.name}: karbon_meta has no build_date")
        target = data_dir / f"lexicon-{build_date.replace('-', '')}.sqlite"
        if target.exists():
            if _sha256(target) != _sha256(unpacked):
                raise SystemExit(
                    f"{target} exists with other content; a snapshot name is "
                    f"never reused for a different file"
                )
            return target
        data_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(unpacked, target)
        return target


def main(argv: list[str] | None = None) -> int:
    """Fetch or unpack, store, and print the snapshot's id and counts."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("tag", nargs="?", help="karbon release tag, e.g. v1.3.2")
    parser.add_argument(
        "--wheel", type=Path, help="use this wheel instead of downloading"
    )
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    args = parser.parse_args(argv)
    if not args.wheel and not args.tag:
        parser.error("give a release tag or --wheel")

    with tempfile.TemporaryDirectory() as scratch:
        wheel = args.wheel or download(args.tag, Path(scratch))
        target = extract(wheel, args.data)

    described = meta(target)
    print(
        f"{target.relative_to(ROOT) if target.is_relative_to(ROOT) else target}  "
        f"sha256 {_sha256(target)[:12]}  build_date {described.get('build_date')}  "
        f"entries {described.get('entries', '?')}  "
        f"reviewed {described.get('reviewed', '?')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
