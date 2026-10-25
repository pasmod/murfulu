"""The ground under a chain: built on something written, or built on air.

Measured on رفتن: 231 of its 476 two-step words are built on an intermediate
form nobody ever wrote, and three unwritten step-one forms carry over 150
step-two words between them. A form's own attestation cannot see that.

What is tested is the shape of the answer: one grounded route is enough, the
starting base never counts against a form, and *not checked* never comes back
looking like *not grounded*.
"""

from __future__ import annotations

from murfulu.engine.affix import Step
from murfulu.scoring.grounding import grounded, path_grounded, stored_grounded

WRITTEN = {"raft", "raftār"}


def _step(base: str) -> Step:
    return Step(rule_id="V-000", affix="-x", base_latin=base)


def test_a_one_step_path_is_grounded_by_definition():
    """Its base is a dictionary stem — what the generation started from."""
    assert path_grounded([_step("raft")], WRITTEN.__contains__) is True


def test_a_two_step_path_through_a_written_form_is_grounded():
    """Raft → raftār → raftāri: every intermediate was really written."""
    path = [_step("raft"), _step("raftār")]
    assert path_grounded(path, WRITTEN.__contains__) is True


def test_a_two_step_path_through_an_unwritten_form_is_not():
    """Raft → raftbān → došraftbān: the engine compounding its own guess."""
    path = [_step("raft"), _step("raftbān")]
    assert path_grounded(path, WRITTEN.__contains__) is False


def test_one_grounded_route_is_enough():
    """A form with one real route is grounded.

    Reachable through Raftār and through Raftbān means grounded: the first
    route is real, and the second does not make it less so.
    """
    through_written = (_step("raft"), _step("raftār"))
    through_air = (_step("raft"), _step("raftbān"))
    assert grounded([through_air, through_written], WRITTEN.__contains__) is True


def test_a_form_with_only_airborne_routes_is_not_grounded():
    assert grounded([(_step("raft"), _step("raftbān"))], WRITTEN.__contains__) is False


def test_the_starting_base_never_counts_against_a_form():
    """Step one's base is the stem itself, and is never judged.

    Judging it would judge the dictionary, not the chain — even when the
    lookup does not know it.
    """
    path = [_step("совершенно-unknown"), _step("raftār")]
    assert path_grounded(path, WRITTEN.__contains__) is True


# -- the same question of a stored record ------------------------------------


class _StoredPath:
    """What the index keeps of a path: the base of its **last** step."""

    def __init__(self, base_latin: str, depth: int) -> None:
        self.base_latin = base_latin
        self.depth = depth


def test_a_stored_one_step_path_is_grounded():
    assert stored_grounded([_StoredPath("raft", 1)], WRITTEN.__contains__) is True


def test_a_stored_two_step_path_reads_its_only_intermediate():
    """At two steps the base of the last step *is* the intermediate."""
    assert stored_grounded([_StoredPath("raftār", 2)], WRITTEN.__contains__) is True
    assert stored_grounded([_StoredPath("raftbān", 2)], WRITTEN.__contains__) is False


def test_one_grounded_stored_route_is_enough():
    paths = [_StoredPath("raftbān", 2), _StoredPath("raftār", 2)]
    assert stored_grounded(paths, WRITTEN.__contains__) is True


def test_a_stored_path_deeper_than_two_cannot_be_read_and_says_so():
    """Not established — never False, which would claim the corpus answered."""
    assert stored_grounded([_StoredPath("x", 3)], WRITTEN.__contains__) is None


def test_an_unreadable_route_beside_an_ungrounded_one_stays_unsettled():
    """The deep route might have been grounded. We cannot tell, so we do not say."""
    paths = [_StoredPath("raftbān", 2), _StoredPath("x", 3)]
    assert stored_grounded(paths, WRITTEN.__contains__) is None
