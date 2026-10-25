"""Put the reviewed question wording into the store, and withdraw the rest.

    python tools/load_questions.py                    # dry run: say what would change
    python tools/load_questions.py --apply            # write it
    python tools/load_questions.py --markdown out.md  # the Persian, for proofreading

**The wording lives in ``rules/questions_fa.yaml``; the store stays the
record.** A question's wording is ours until the linguist answers it, and
wording is reviewed best as text in git — so it is written and proofread there,
and this puts it into whichever database ``MURFULU_DATABASE_URL`` names. The
rulings are never touched: they exist only in the store.

What it does, in that database:

* **adds** each question in the file that the store does not hold;
* **rewords** each one it holds that has never been answered — text, options,
  whether it blocks work — keeping the earlier Persian (see
  :func:`murfulu.db.rulings.reword`);
* **leaves alone** a question that has a ruling, and says so: after a ruling
  the wording is what the answer answered;
* **withdraws** every other question still waiting that does not block work,
  with the one-line Persian reason from the file. Never deletes.

**Dry run by default**, because the database it is pointed at may be
production. ``--apply`` writes, in one transaction.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from murfulu.db import rulings as store
from murfulu.db.session import session_scope

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "rules" / "questions_fa.yaml"


@dataclass
class Plan:
    """What a load would do, one line per question, in the order it acts."""

    lines: list[str] = field(default_factory=list)
    added: int = 0
    reworded: int = 0
    unchanged: int = 0
    kept: int = 0
    withdrawn: int = 0

    def say(self, line: str) -> None:
        """Add one line to the report."""
        self.lines.append(line)


def read(path: Path = QUESTIONS) -> dict[str, Any]:
    """The questions file, checked enough that a load cannot half-succeed."""
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    questions = data.get("questions") or []
    seen: set[str] = set()
    for one in questions:
        reference = one.get("reference")
        if not reference or reference in seen:
            raise ValueError(f"missing or repeated reference: {reference!r}")
        seen.add(reference)
        if not str(one.get("question_fa") or "").strip():
            raise ValueError(f"{reference} has no Persian")
        store.check_choices(one.get("choices") or [])
    for reference, why in (data.get("withdraw") or {}).items():
        if reference in seen:
            raise ValueError(f"{reference} is both asked and withdrawn")
        if not str(why or "").strip():
            raise ValueError(f"{reference} is withdrawn without a reason")
    return data


def load(session: Session, data: dict[str, Any], *, on: date | None = None) -> Plan:
    """Apply the file to the store in this session. The caller commits or not."""
    plan = Plan()
    asked: set[str] = set()

    for one in data.get("questions") or []:
        reference = one["reference"]
        asked.add(reference)
        question_fa = one["question_fa"].strip()
        extra = {"covers": one["covers"]} if one.get("covers") else {}
        try:
            row = store.by_reference(session, reference)
        except store.UnknownQuestionError:
            row = store.ask(
                session,
                reference=reference,
                question_fa=question_fa,
                question_en=one.get("question_en"),
                context={"choices": store.check_choices(one.get("choices") or [])}
                | extra,
                origin="app",
                blocks_work=bool(one.get("blocks_work", False)),
            )
            plan.added += 1
            plan.say(
                f"add       {reference}  ({len(one.get('choices') or [])} options)"
            )
            continue

        if store.rulings_on(session, row):
            plan.kept += 1
            plan.say(f"keep      {reference}  has a ruling; its wording is left alone")
            continue

        changed = store.reword(
            session,
            row,
            question_fa=question_fa,
            question_en=one.get("question_en"),
            choices=one.get("choices") or [],
            blocks_work=bool(one.get("blocks_work", False)),
            extra=extra,
            on=on,
        )
        if changed:
            plan.reworded += 1
            plan.say(
                f"reword    {reference}  ({len(one.get('choices') or [])} options)"
            )
        else:
            plan.unchanged += 1
            plan.say(f"same      {reference}")

    reasons: dict[str, str] = data.get("withdraw") or {}
    default = str(data.get("withdraw_default") or "").strip()
    for row in store.questions(session):
        if row.reference in asked or row.state not in ("open", "blocked"):
            continue
        if row.blocks_work:
            plan.say(f"blocking  {row.reference}  not in the file; left waiting")
            continue
        why = str(reasons.get(row.reference) or default).strip()
        if not why:
            plan.say(f"no reason {row.reference}  not withdrawn")
            continue
        store.withdraw(session, row, why=why)
        plan.withdrawn += 1
        plan.say(f"withdraw  {row.reference}  {why}")

    return plan


def markdown(data: dict[str, Any]) -> str:
    """Every question and its options, as Persian to proofread.

    Written for the person reviewing the wording, not for the linguist: the
    order is the file's, each question says whether it blocks work, and the
    withdrawal reasons follow at the end so they are proofread too.
    """
    lines = [
        "# پرسش‌های زبان‌شناس — متن برای بازخوانی",
        "",
        f"از `rules/questions_fa.yaml`، نوشته‌شده در {data.get('written', '')}، "
        f"سنجیده با {data.get('measured_against', '')}.",
        "در صفحه، کنار گزینه‌ها همیشه یک جعبهٔ متن هم هست.",
        "",
    ]
    for one in data.get("questions") or []:
        covers = one.get("covers")
        tail = f" (شامل {'، '.join(covers)})" if covers else ""
        lines += [f"## {one['reference']}{tail}", ""]
        if one.get("question_en"):
            lines += [f"*{one['question_en'].strip()}*", ""]
        for paragraph in one["question_fa"].strip().split("\n\n"):
            # Single line breaks are lists in the source; keep them as lines.
            lines += ["  \n".join(paragraph.strip().splitlines()), ""]
        lines += ["**گزینه‌ها**", ""]
        for at, choice in enumerate(one.get("choices") or [], start=1):
            marks = []
            if choice.get("suggested"):
                marks.append("پیشنهاد ما")
            if choice.get("settles") is False:
                marks.append("پرسش باز می‌ماند")
            mark = f" *({'، '.join(marks)})*" if marks else ""
            lines.append(f"{at}. {choice['text_fa'].strip()}{mark} `{choice['id']}`")
        lines += ["", "---", ""]
    reasons = data.get("withdraw") or {}
    if reasons:
        lines += [
            "## پرسش‌هایی که پس گرفته می‌شوند",
            "",
            "در صفحه به این شکل خوانده می‌شود: «پس گرفته شد، چون …».",
            "",
        ]
        lines += [f"- **{ref}** — {why.strip()}" for ref, why in reasons.items()]
        if data.get("withdraw_default"):
            lines += [f"- **دیگر پرسش‌ها** — {data['withdraw_default'].strip()}"]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    """Dry-run, apply, or write the proofreading export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=QUESTIONS)
    parser.add_argument(
        "--apply", action="store_true", help="write to the database (default: dry run)"
    )
    parser.add_argument(
        "--markdown", type=Path, help="write the Persian for proofreading here and stop"
    )
    arguments = parser.parse_args(argv)
    data = read(arguments.file)

    if arguments.markdown:
        arguments.markdown.write_text(markdown(data), encoding="utf-8")
        print(f"markdown  {arguments.markdown}")
        return 0

    with session_scope() as session:
        plan = load(session, data)
        for line in plan.lines:
            print(line)
        print(
            f"\n{plan.added} added, {plan.reworded} reworded, {plan.unchanged} "
            f"unchanged, {plan.kept} kept (answered), {plan.withdrawn} withdrawn"
        )
        if arguments.apply:
            session.commit()
            print("applied")
        else:
            session.rollback()
            print("dry run — nothing written; --apply to write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
