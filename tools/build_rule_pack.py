"""Turn the raw transcriptions into the YAML rule pack.

Reads ``rules/source_rows.json``, ``rules/rule_ids.json`` and the two authored
tables (``affix_spellings.yaml``, ``semantic_tags.yaml``) and writes
``verb_stems.yaml``, ``nominals.yaml`` and ``glides.yaml``.

**Nothing is invented.** Where a source cell cannot be resolved — an unknown
word class, an affix with no Persian spelling, an example that does not parse —
the rule is written out with ``needs_expert_check: true`` and a note saying
exactly what could not be read. Fields that would have to be guessed are left
null.

    python tools/build_rule_pack.py [-d rules]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from murfulu.rules.source_text import TYPE_FA, clean, parse_input, word_classes

KIND_FA = {"suffix": "پسوند", "prefix": "پیشوند", "infix": "میانوند"}

_BRACKETS = re.compile(r"\(.*?\)")
_SPLIT = re.compile(r"[\n/,]+")

#: One worked derivation: "row + eš = Raveš". A cell may hold several.
_WORKED = re.compile(r"\S+\s*\+\s*\S+\s*=\s*\S+")


def _affix_variants(cell: str) -> list[str]:
    """The affixes a row lists. Row 13 names four in one cell."""
    without_tags = _BRACKETS.sub("", cell)
    return [part.strip() for part in _SPLIT.split(without_tags) if part.strip()]


def _tags(cell: str) -> list[str]:
    found: list[str] = []
    for bracket in _BRACKETS.findall(cell):
        for part in bracket.strip("()").split(","):
            if part.strip():
                found.append(part.strip())
    return found


def _examples(cell: str) -> list[str]:
    """The example words a row gives, verbatim apart from separators.

    Kept exactly as written, typos included — a wrong example is a fact about
    the source and PLAN task 1.5 turns each one into a test, which is where a
    mistranscription should surface.
    """
    examples: list[str] = []
    for chunk in clean(cell).split("/"):
        stripped = chunk.strip(" ,،")
        if not stripped:
            continue
        # A worked derivation — "dānā + i = Dānāyi" — is one example even
        # though it contains spaces. Splitting on space would turn it into
        # three, and "+" and "=" would each become an "example".
        if "=" in stripped or "+" in stripped:
            # A cell can hold several: "row + am = ravam  šow + am = šavam".
            worked = _WORKED.findall(stripped)
            examples.extend(worked or [stripped])
        else:
            examples.extend(
                w.strip(" ,،") for w in stripped.split(" ") if w.strip(" ,،")
            )
    return examples


#: What the source writes in the affix column when a whole word fills the slot
#: rather than an affix being added.
SLOT_FA = {"Nām-": "نام", "Čonvāže-": "چون‌واژه"}

#: The letters that join the two halves of a compound, in Persian script.
#: Zadoxord is زدوخورد, Kešākeš is کشاکش, Budonabud is بودونبود.
# The Persian for each joiner a compounding pattern can name. **`na` is نا and
# not ن**: it is the negation, and V-021's pattern `{a} + o + na + {b}` built
# `{a}ون{b}` — the negation dropped — until it was corrected in the generated
# file on 2026-08-14 and not here, so the next rebuild undid it.
JOINER_FA = {"o": "و", "ā": "ا", "va": "و", "na": "نا"}


def _label_fa(input_types: list[str], affix: str, kind: str) -> str | None:
    """Build the rule's Persian label, the shape RULE_PACK.md shows."""
    if not input_types:
        return None
    names = " / ".join(TYPE_FA[t] for t in input_types)
    if kind == "none":
        return names
    if kind == "template":
        return " + ".join(TYPE_FA[t] for t in input_types)
    if kind == "slot":
        return f"{SLOT_FA.get(affix, affix)} + {names}"
    return f"{affix} + {names}" if kind == "prefix" else f"{names} + {affix}"


def _explanation_fa(
    input_types: list[str], output_types: list[str], affix: str, kind: str
) -> str | None:
    """Composed from the grammar's own Persian names, not written freehand."""
    if not input_types or not output_types:
        return None
    source = " یا ".join(TYPE_FA[t] for t in input_types)
    result = " یا ".join(TYPE_FA[t] for t in output_types)
    if kind in KIND_FA:
        return f"از {source} با {KIND_FA[kind]} {affix} {result} ساخته می‌شود"
    if kind == "none":
        # The base itself is the new word: Parhiz, Sāxt, Darxāst.
        return f"خودِ {source} {result} است"
    if kind == "template":
        joined = " و ".join(TYPE_FA[t] for t in input_types)
        return f"از پیوندِ {joined} {result} ساخته می‌شود"
    if kind == "slot":
        return f"از {SLOT_FA.get(affix, affix)} و {source} {result} ساخته می‌شود"
    return None


def _build_rule(
    entry: dict[str, Any],
    row: dict[str, Any],
    affixes: dict[str, dict[str, Any]],
    known_tags: set[str],
) -> dict[str, Any]:
    problems: list[str] = []
    affix_cell = row["affix"] or ""
    variants = _affix_variants(affix_cell)
    primary = variants[0] if variants else "‒"

    spelling = affixes.get(primary)
    # Where a ruling corrected the source's spelling, the pack carries the
    # corrected form and keeps the source form beside it.
    corrected = spelling.get("corrected_latin") if spelling else None
    if spelling is None:
        problems.append(f"no Persian spelling recorded for the affix {primary!r}")
    elif spelling.get("needs_expert_check"):
        problems.append(f"affix {primary!r}: {clean(spelling['note'])}")

    parsed = parse_input(row["attaches_to"] or "")
    input_types = parsed.types
    output_types, bad_output = word_classes(row["produces"] or "")
    if parsed.unresolved:
        problems.append(f"could not read part of the input: {parsed.unresolved}")
    if bad_output:
        problems.append(f"could not read the output type(s): {bad_output}")

    tags = _tags(affix_cell)
    for tag in tags:
        if tag not in known_tags:
            problems.append(f"semantic tag {tag!r} is not in semantic_tags.yaml")

    kind = (
        "template"
        if parsed.is_template
        else (spelling["kind"] if spelling else "unknown")
    )

    rule: dict[str, Any] = {
        "id": entry["id"],
        "source": {"table": entry["source"]["table"], "row": entry["source"]["row"]},
        "kind": kind,
        "affix": corrected or primary,
        "affix_source": primary,
        "affix_fa": spelling["fa"] if spelling else None,
        "affix_variants": variants[1:],
        "input": {
            "types": input_types,
            "condition_text": clean(row["attaches_to"] or "") or None,
        },
        "output": {"types": output_types},
        "semantic_tags": tags,
        # "mostly with -t and -d" is a tendency, not a rule that always
        # applies. Read from the source text, never assumed.
        "strength": "typical" if parsed.tendency else None,
        "examples": _examples(row["examples"] or ""),
        "label_fa": _label_fa(input_types, corrected or primary, kind),
        "explanation_fa": _explanation_fa(
            input_types, output_types, corrected or primary, kind
        ),
        "active": True,
    }
    if parsed.tendency:
        rule["input"]["tendency_text"] = parsed.tendency
    if parsed.is_template:
        rule["pattern"] = parsed.pattern
        # The Persian shape of the same pattern, so a compound can be built in
        # both scripts at once, exactly as an affix carries affix_fa.
        rule["pattern_fa"] = "".join(
            part if part.startswith("{") else JOINER_FA.get(part, part)
            for part in (parsed.pattern or "").split(" + ")
        )
        rule["slots"] = [
            {
                "name": slot.name,
                "type": slot.type,
                **({"constraint": slot.constraint} if slot.constraint else {}),
                **({"negated": True} if slot.negated else {}),
            }
            for slot in parsed.slots
        ]
    if entry["source"]["row"] is None:
        rule["source"]["follows_row"] = entry["source"].get("follows_row")
    if problems:
        rule["needs_expert_check"] = True
        rule["notes"] = problems
    return rule


def _decide(rule: dict[str, Any], rulings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Apply a ruling about one rule: retire it, or correct how it attaches.

    **This exists because the pack is generated and three rulings were not.**
    N-090 (the ezāfe) and N-099 (the indefinite enclitic) were retired by
    editing ``nominals.yaml`` directly, and V-021's Persian pattern was fixed
    the same way. Re-running this tool silently put all three back — measured
    2026-08-15, by running it. A ruling is a human decision about a source row,
    which is exactly what ``decisions.yaml`` is for, and glides already went
    through it. Nothing here deletes a rule: the id and the transcription stay.

    ``kind`` is corrected **per rule and not per affix**, because one spelling
    can be two affixes. The source writes ``-andar`` twice: V-052 is
    *-andar (darun)*, the preposition اندر, whose example *andarāmadan* puts it
    in front; N-038 is *-andar (nātani)*, the step-kin ending, whose example
    *Mādarandar* puts it on the end. Correcting the affix table would have
    moved both.
    """
    decision = rulings.get(rule["id"])
    if decision is None:
        return rule
    if decision.get("active") is False:
        return {
            **rule,
            "active": False,
            "retired_reason": clean(decision["reason"]),
            # The same reason in Persian. The rules screen is the canonical
            # published reference and it is Persian throughout, so a retirement
            # that can only say *why* in English tells a reader **that** the
            # rule no longer applies and not why — which for N-090 is the whole
            # of the interesting part. See S14. The interface may not invent
            # this: it is authored beside the ruling, here.
            "retired_reason_fa": clean(decision.get("reason_fa") or ""),
        }

    kind = decision.get("kind") or rule["kind"]
    affix = decision.get("affix") or rule["affix"]
    inputs = decision.get("input_types") or rule["input"]["types"]
    if (kind, affix, inputs) == (rule["kind"], rule["affix"], rule["input"]["types"]):
        return rule
    return {
        **rule,
        "kind": kind,
        "affix": affix,
        "input": {**rule["input"], "types": inputs},
        "label_fa": _label_fa(inputs, affix, kind),
        "explanation_fa": _explanation_fa(inputs, rule["output"]["types"], affix, kind),
        "corrected_by": clean(decision["reason"]),
    }


def build(directory: Path) -> dict[str, list[dict[str, Any]]]:
    """Build every rule file's contents."""
    source = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
    register = json.loads((directory / "rule_ids.json").read_text(encoding="utf-8"))
    affix_doc = yaml.safe_load(
        (directory / "affix_spellings.yaml").read_text(encoding="utf-8")
    )
    tag_doc = yaml.safe_load(
        (directory / "semantic_tags.yaml").read_text(encoding="utf-8")
    )

    affixes = {a["latin"]: a for a in affix_doc["affixes"]}
    known_tags = {label for tag in tag_doc["tags"] for label in tag["label_source"]}

    decisions_path = directory / "decisions.yaml"
    decisions = (
        yaml.safe_load(decisions_path.read_text(encoding="utf-8"))
        if decisions_path.exists()
        else {}
    )
    rulings = {d["id"]: d for d in (decisions.get("rules") or [])}

    built: dict[str, list[dict[str, Any]]] = {}
    for table in ("verb_stems", "nominals"):
        by_position = {
            r["docx_row_position"]: r for r in source["tables"][table] if not r["blank"]
        }
        rules = [
            _decide(
                _build_rule(
                    entry, by_position[entry["docx_row_position"]], affixes, known_tags
                ),
                rulings,
            )
            for entry in register["families"][table]
            if "reason" not in entry
        ]
        built[table] = sorted(rules, key=lambda r: r["id"])

    built["glides"] = _build_glides(source, register, decisions.get("glides") or [])
    built["stem_forms"] = list(decisions.get("stem_finals") or [])

    stem_path = directory / "stem_source_rows.json"
    if stem_path.exists():
        resolutions_path = directory / "stem_exception_resolutions.yaml"
        resolutions = (
            yaml.safe_load(resolutions_path.read_text(encoding="utf-8"))["resolutions"]
            if resolutions_path.exists()
            else []
        )
        built["stem_rules"] = _build_stem_rules(
            json.loads(stem_path.read_text(encoding="utf-8")),
            register,
            {r["infinitive_fa"]: r for r in resolutions},
        )
    return built


def _resolve(
    entry: dict[str, Any], resolution: dict[str, Any] | None
) -> dict[str, Any]:
    """Apply a settled second reading, keeping the source text visible."""
    if resolution is None or not resolution.get("settled"):
        return entry
    # Settled by a second reading of the same document. The flag comes off, but
    # read_by and resolution_note record that it was not read directly.
    settled = {
        k: v for k, v in entry.items() if k not in {"needs_expert_check", "note"}
    }
    return {
        **settled,
        "stems_fa": [resolution["past_stem_fa"], resolution["present_stem_fa"]],
        "stems_latin": [
            resolution["past_stem_latin"],
            resolution["present_stem_latin"],
        ],
        "source_text": resolution["source_text"],
        "read_by": resolution["read_by"],
        "resolution_note": clean(resolution["note"]),
    }


def _build_stem_rules(
    dump: dict[str, Any],
    register: dict[str, Any],
    resolutions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """The nine rules for getting from an infinitive to its two stems."""
    texts = {r["rule"]: r["text_fa"] for r in dump["rules"]}
    subs: dict[int, list[dict[str, Any]]] = {}
    for sub in dump["sub_rules"]:
        subs.setdefault(sub["parent_rule"], []).append(
            {"part": f"{sub['parent_rule']}-{sub['part']}", "text_fa": sub["text_fa"]}
        )

    rules = []
    for entry in register["families"]["stem_rules"]:
        number = int(entry["source"]["row"])
        exceptions = [e for e in dump["exceptions"] if e["rule"] == number]
        inputs = ["nabesudkarvaze"] if number == 1 else ["karbon_yek"]
        outputs = ["karbon_yek"] if number == 1 else ["karbon_do"]
        rule: dict[str, Any] = {
            "id": entry["id"],
            "source": {"table": "stem_rules", "row": entry["source"]["row"]},
            # Not affixation: a stem rule strips or changes sounds at the end
            # of a form. It has no affix and no Persian spelling for one.
            "kind": "stem",
            "label_fa": f"{TYPE_FA[outputs[0]]} از {TYPE_FA[inputs[0]]}",
            # Rule 1 makes stem 1 from the infinitive; 2-9 make stem 2 from
            # stem 1. Read from the rule number, which the document fixes.
            "input": {"types": inputs},
            "output": {"types": outputs},
            "explanation_fa": texts[number],
            "sub_rules": subs.get(number, []),
            "exceptions": [
                _resolve(
                    {
                        "infinitive_fa": e["infinitive_fa"],
                        "stems_fa": e["stems_fa"],
                        **(
                            {"needs_expert_check": True, "note": e["note"]}
                            if e.get("needs_expert_check")
                            else {}
                        ),
                    },
                    resolutions.get(e["infinitive_fa"]),
                )
                for e in exceptions
            ],
            "active": True,
        }
        unreadable = [
            e
            for e in exceptions
            if e.get("needs_expert_check")
            and not resolutions.get(e["infinitive_fa"], {}).get("settled")
        ]
        if unreadable:
            rule["needs_expert_check"] = True
            rule["notes"] = [f"{e['infinitive_fa']}: {e['note']}" for e in unreadable]
        rules.append(rule)
    return rules


def _build_glides(
    source: dict[str, Any],
    register: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_position = {
        r["docx_row_position"]: r for r in source["tables"]["glides"] if not r["blank"]
    }
    ruling = {d["id"]: d for d in decisions}

    glides = []
    for entry in register["families"]["glides"]:
        row = by_position[entry["docx_row_position"]]
        left, right, result = row["left_vowel"], row["right_vowel"], row["result"]
        decision = ruling.get(entry["id"], {})
        glides.append(
            {
                "id": entry["id"],
                "source": {"table": "glides", "row": entry["source"]["row"]},
                "left": left,
                "right": right,
                "result": result,
                "examples": _examples(row["examples"] or ""),
                "explanation_fa": (
                    f"هنگام برخورد {left} و {right} واج‌میانجی می‌آید و {result} "
                    f"ساخته می‌شود"
                ),
                "active": bool(decision.get("active", True)),
                **(
                    {
                        "retired_reason": clean(decision["reason"]),
                        "retired_reason_fa": clean(decision.get("reason_fa") or ""),
                    }
                    if decision.get("active") is False
                    else {}
                ),
            }
        )

    # An example the document filed under the wrong rule moves to the right one.
    # Done after every glide exists, so the destination is always there.
    by_id = {g["id"]: g for g in glides}
    for decision in decisions:
        destination = decision.get("move_examples_to")
        if not destination:
            continue
        moved = by_id[decision["id"]]["examples"]
        by_id[destination]["examples"] = sorted(
            {*by_id[destination]["examples"], *moved}
        )
        by_id[decision["id"]]["examples"] = []

    return sorted(glides, key=lambda g: g["id"])


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--directory", type=Path, default=Path("rules"))
    args = parser.parse_args(argv)

    built = build(args.directory)
    for table, rules in built.items():
        path = args.directory / f"{table}.yaml"
        path.write_text(
            yaml.safe_dump(
                {"version": "0.1.0", "rules": rules},
                allow_unicode=True,
                sort_keys=False,
                width=100,
            ),
            encoding="utf-8",
        )
        flagged = sum(1 for r in rules if r.get("needs_expert_check"))
        print(f"{table}: {len(rules)} rules, {flagged} flagged → {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
