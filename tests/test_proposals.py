"""Expert edits stored as proposals, exported to YAML, reviewed as a git diff.

The done test for PLAN 8.1 is the round trip: a proposal made over HTTP comes
back out as a change to the YAML that `git diff` can show, and nothing else in
the file moves.

What is checked here is mostly what must **not** happen — a proposal applied
on top of somebody else's change, a proposal that changes nothing, a reader
editing the grammar — because those are the ways a round trip like this
damages the thing it is meant to improve.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from murfulu.api.app import app
from murfulu.db import site
from murfulu.db.models import Base, RuleProposalDecision, RuleRow
from murfulu.db.rulesync import sync
from murfulu.rules.pack import loaded as loaded_pack
from murfulu.rules.proposals import PROPOSABLE_FIELDS, apply

TABLES = ("verb_stems", "nominals", "stem_rules")
PACK = Path(__file__).resolve().parents[1] / "rules"


@pytest.fixture
def accounts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[dict]:
    """A store with the real rule pack loaded.

    No accounts: there is one and it makes itself on first use — see
    murfulu.db.site.
    """
    url = f"sqlite:///{tmp_path / 'authored.sqlite'}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        # The rules have to be there: a proposal points at one.
        sync(session)
        session.commit()
    engine.dispose()
    monkeypatch.setenv("MURFULU_DATABASE_URL", url)
    yield {}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _as(_who: str = "") -> dict[str, str]:
    """No credential at all. Kept so call sites read unchanged.

    Every route behind the password wall is open as of 2026-08-17 —
    there is one account and no roles. See murfulu.db.site.
    """
    return {}


PROPOSAL = {
    "field": "explanation_fa",
    "proposed": "از کاربن یک با پسوند -ār کارنام ساخته می‌شود (بازنویسی)",
    "reason": "جملهٔ روشن‌تر",
}


# -- who may propose ---------------------------------------------------------


def test_an_expert_may_propose_a_change(client: TestClient, accounts: dict):
    made = client.post("/rules/V-010/proposals", json=PROPOSAL, headers=_as())
    assert made.status_code == 201, made.text
    body = made.json()
    assert body["rule_id"] == "V-010"
    assert body["field"] == "explanation_fa"
    # What the rule said at the time, taken from the pack and not from the
    # request: a caller cannot make a stale proposal look fresh.
    assert body["was"] == loaded_pack().by_id("V-010").explanation_fa
    assert body["rule_pack_version"] == loaded_pack().version


def test_the_permanent_id_cannot_be_proposed_against(
    client: TestClient, accounts: dict
):
    """Ids are appended, never inserted and never reused."""
    assert "id" not in PROPOSABLE_FIELDS
    refused = client.post(
        "/rules/V-010/proposals",
        json={"field": "id", "proposed": "V-999", "reason": "چرا نه"},
        headers=_as(),
    )
    assert refused.status_code == 400


def test_the_source_row_cannot_be_proposed_against(client: TestClient, accounts: dict):
    """Which row of the document a rule came from is a fact, not an opinion."""
    assert "source" not in PROPOSABLE_FIELDS
    refused = client.post(
        "/rules/V-010/proposals",
        json={"field": "source", "proposed": {}, "reason": "چرا نه"},
        headers=_as(),
    )
    assert refused.status_code == 400


def test_a_proposal_that_changes_nothing_is_refused(client: TestClient, accounts: dict):
    """A review queue full of no-ops is a review queue nobody reads."""
    unchanged = loaded_pack().by_id("V-010").explanation_fa
    refused = client.post(
        "/rules/V-010/proposals",
        json={"field": "explanation_fa", "proposed": unchanged, "reason": "همان"},
        headers=_as(),
    )
    assert refused.status_code == 403
    assert "already says" in refused.json()["detail"]


def test_a_proposal_has_to_say_why(client: TestClient, accounts: dict):
    refused = client.post(
        "/rules/V-010/proposals",
        json={**PROPOSAL, "reason": "   "},
        headers=_as(),
    )
    assert refused.status_code == 403


def test_a_proposal_against_a_rule_that_is_not_there_is_a_404(
    client: TestClient, accounts: dict
):
    refused = client.post("/rules/V-999/proposals", json=PROPOSAL, headers=_as())
    assert refused.status_code == 404


def test_a_glide_rule_is_not_proposed_against(client: TestClient, accounts: dict):
    """Seventeen vowel meetings, a closed table, a different kind of thing."""
    refused = client.post("/rules/G-04/proposals", json=PROPOSAL, headers=_as())
    assert refused.status_code == 400


def test_what_was_proposed_comes_back(client: TestClient, accounts: dict):
    client.post("/rules/V-010/proposals", json=PROPOSAL, headers=_as())
    read = client.get("/proposals", params={"rule_id": "V-010"}, headers=_as()).json()
    assert read["returned"] == 1
    assert read["proposals"][0]["reason"] == "جملهٔ روشن‌تر"


# -- applying them to the pack ------------------------------------------------


def _tables() -> dict[str, Any]:
    return {
        name: yaml.safe_load((PACK / f"{name}.yaml").read_text(encoding="utf-8"))
        for name in TABLES
    }


def _proposal(**fields: Any) -> dict[str, Any]:
    base = {
        "id": 1,
        "rule_id": "V-010",
        "field": "explanation_fa",
        "proposed": "تازه",
        "was": None,
        "reason": "چون",
    }
    return {**base, **fields}


def test_the_pack_round_trips_byte_for_byte():
    """The whole review method rests on this.

    An applied proposal has to show up as the one line it changed. If loading
    and dumping reformatted the file, every diff would be two thousand lines
    and nobody would read one.
    """
    for name in TABLES:
        path = PACK / f"{name}.yaml"
        original = path.read_text(encoding="utf-8")
        again = yaml.safe_dump(
            yaml.safe_load(original), allow_unicode=True, sort_keys=False, width=100
        )
        assert again == original, f"{name}.yaml does not round trip"


def test_a_proposal_is_applied_when_the_rule_still_says_what_it_said():
    tables = _tables()
    was = next(rule for rule in tables["verb_stems"]["rules"] if rule["id"] == "V-010")[
        "explanation_fa"
    ]
    result = apply(tables, [_proposal(was=was, proposed="نوشتهٔ تازه")])

    assert result.counted("applied") == 1
    assert result.changed_tables == ["verb_stems"]
    changed = next(
        rule for rule in result.tables["verb_stems"]["rules"] if rule["id"] == "V-010"
    )
    assert changed["explanation_fa"] == "نوشتهٔ تازه"


def test_the_original_tables_are_not_touched():
    tables = _tables()
    before = tables["verb_stems"]["rules"][9]["explanation_fa"]
    apply(tables, [_proposal(was=before, proposed="دیگر")])
    assert tables["verb_stems"]["rules"][9]["explanation_fa"] == before


def test_a_proposal_the_pack_already_agrees_with_is_not_applied_again():
    """Accepted last week, or two experts proposing the same thing."""
    tables = _tables()
    holds = next(
        rule for rule in tables["verb_stems"]["rules"] if rule["id"] == "V-010"
    )["explanation_fa"]
    result = apply(tables, [_proposal(was="چیزی دیگر", proposed=holds)])
    assert result.counted("already") == 1
    assert result.changed_tables == []


def test_a_proposal_is_skipped_when_the_rule_moved_underneath_it():
    """Applying it would silently revert whoever changed it since.

    This is the reason a proposal stores the old value at all.
    """
    tables = _tables()
    result = apply(
        tables, [_proposal(was="چیزی که آن زمان نوشته بود", proposed="تازه")]
    )
    assert result.counted("moved") == 1
    assert result.counted("applied") == 0
    assert result.changed_tables == []
    # And it says what the pack actually holds, so the disagreement is visible.
    assert result.outcomes[0].found is not None


def test_a_proposal_for_a_rule_that_is_not_in_the_pack_is_reported():
    result = apply(_tables(), [_proposal(rule_id="V-999")])
    assert result.counted("unknown") == 1


def test_proposals_are_applied_oldest_first():
    """Two experts, one field: the later one wins, and both are on record."""
    tables = _tables()
    was = next(rule for rule in tables["verb_stems"]["rules"] if rule["id"] == "V-010")[
        "explanation_fa"
    ]
    result = apply(
        tables,
        [
            _proposal(id=2, was="یکم", proposed="دوم"),
            _proposal(id=1, was=was, proposed="یکم"),
        ],
    )
    changed = next(
        rule for rule in result.tables["verb_stems"]["rules"] if rule["id"] == "V-010"
    )
    assert changed["explanation_fa"] == "دوم"
    assert result.counted("applied") == 2


# -- the whole round trip ----------------------------------------------------


def test_a_proposal_becomes_one_changed_line_in_the_yaml(
    client: TestClient, accounts: dict, tmp_path: Path
):
    """PLAN 8.1's done test: proposed in the app, reviewable as a git diff."""
    from tools.export_proposals import read_tables, write_table

    made = client.post("/rules/V-010/proposals", json=PROPOSAL, headers=_as()).json()

    # A copy of the pack, so the test never writes to the real one.
    for name in TABLES:
        (tmp_path / f"{name}.yaml").write_text(
            (PACK / f"{name}.yaml").read_text(encoding="utf-8"), encoding="utf-8"
        )

    result = apply(read_tables(tmp_path), [made])
    assert result.counted("applied") == 1
    for name in result.changed_tables:
        write_table(tmp_path, name, result.tables[name])

    before = (PACK / "verb_stems.yaml").read_text(encoding="utf-8").splitlines()
    after = (tmp_path / "verb_stems.yaml").read_text(encoding="utf-8").splitlines()
    assert len(before) == len(after)
    lines = enumerate(zip(before, after, strict=True))
    differing = [n for n, (a, b) in lines if a != b]
    assert len(differing) == 1, "a proposal must change exactly one line"
    assert PROPOSAL["proposed"] in after[differing[0]]


def test_nothing_writes_to_the_repository_from_a_request():
    """A request cannot reach the grammar files.

    A browser with a write path into the rule pack is a browser that can change
    it without anyone reading the change. The route stores a row; the command
    writes the file.
    """
    source = (
        Path(__file__).resolve().parents[1] / "src/murfulu/api/proposals.py"
    ).read_text(encoding="utf-8")
    assert "write_text" not in source
    assert "yaml" not in source


def test_the_rules_module_does_not_import_the_database():
    """``rules/`` loads and validates the pack. It knows nothing about a store."""
    source = (
        Path(__file__).resolve().parents[1] / "src/murfulu/rules/proposals.py"
    ).read_text(encoding="utf-8")
    assert "murfulu.db" not in source
    assert "sqlalchemy" not in source


def test_the_rule_table_and_the_pack_agree_on_what_may_be_proposed(
    accounts: dict, tmp_path: Path
):
    """One list, in the pack, enforced by the database."""
    from murfulu.db.models.proposals import PROPOSABLE_FIELDS as ENFORCED

    assert ENFORCED is PROPOSABLE_FIELDS
    # And every one of them is really a field of a rule.
    rule = loaded_pack().by_id("V-010")
    for name in PROPOSABLE_FIELDS:
        assert hasattr(rule, name), name


def test_the_rules_are_loaded_before_a_proposal_can_point_at_one(accounts: dict):
    """The foreign key is the guarantee; this proves the fixture provides it."""
    from murfulu.db.session import session_scope

    with session_scope() as session:
        assert session.get(RuleRow, "V-010") is not None


# -- a refused proposal does not come back -----------------------------------


def test_a_decided_proposal_is_not_exported_again(
    client: TestClient, accounts: dict
) -> None:
    """S5: refusing left no trace, so the loop never converged.

    Accepting a proposal is committing the diff the export wrote; refusing it
    is ``git checkout rules/``, which restores the file and says nothing. So
    the proposal stayed in the table, the next export applied it again, and the
    reviewer refused it again.

    The decision is a **row**, not a stamp on the proposal — the shape the
    feedback table and `linguist_rulings` already use, and the only one of the
    three candidates that keeps the history whole.
    """
    from murfulu.db import proposals as store
    from murfulu.db.session import session_scope

    made = client.post("/rules/V-010/proposals", json=PROPOSAL, headers=_as())
    assert made.status_code == 201
    proposal_id = made.json()["id"]

    with session_scope() as session:
        assert [one.id for one in store.undecided(session)] == [proposal_id]

        reviewer = site.account(session)
        store.decide(
            session,
            proposal_id=proposal_id,
            decided_by=reviewer.id,
            decision="refused",
            reason="جملهٔ کنونی روشن‌تر است",
            rule_pack_version="0.1.0",
        )

    with session_scope() as session:
        # Gone from what the export applies — but still in the table, with its
        # reason. Nothing is deleted and nothing is edited.
        assert store.undecided(session) == []
        assert len(store.all_proposals(session)) == 1
        standing = store.latest_decisions(session)[proposal_id]
        assert standing.decision == "refused"
        assert standing.reason == "جملهٔ کنونی روشن‌تر است"


def test_a_later_decision_reopens_a_refused_proposal(
    client: TestClient, accounts: dict
) -> None:
    """The latest row is the one that counts, so a reversal is possible.

    A proposal refused under one pack version may deserve a different answer
    under another. Deciding twice is allowed and the rows say how the answer
    changed — which is why this is appended rather than stamped.
    """
    from murfulu.db import proposals as store
    from murfulu.db.session import session_scope

    made = client.post("/rules/V-010/proposals", json=PROPOSAL, headers=_as())
    proposal_id = made.json()["id"]

    with session_scope() as session:
        reviewer = site.account(session)
        for decision, reason in (
            ("refused", "هنوز نه"),
            ("accepted", "پس از گفت‌وگو پذیرفته شد"),
        ):
            store.decide(
                session,
                proposal_id=proposal_id,
                decided_by=reviewer.id,
                decision=decision,
                reason=reason,
                rule_pack_version="0.1.0",
            )

    with session_scope() as session:
        standing = store.latest_decisions(session)[proposal_id]
        assert standing.decision == "accepted"
        # Both rows are still there: how it got here is the point of appending.
        assert len(list(session.scalars(select(RuleProposalDecision)))) == 2
