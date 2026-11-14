"""Automatic Behnevis: the letter model, the choice, and the two put together.

Every word here is written for the test; no corpus text (NOTICE).
"""

from pathlib import Path

import pytest

from murfulu.behnevis.choice import Answered, ChoiceModel, ranked
from murfulu.behnevis.letters import LetterModel, align, shape
from murfulu.behnevis.transcribe import (
    BANK,
    CHOICE,
    FUNCTION,
    LETTERS,
    Transcriber,
    bank_from,
)


@pytest.mark.parametrize(
    ("spelling", "latin", "pieces"),
    [
        ("ترک", "tork", ["to", "r", "k"]),
        ("خواب", "xāb", ["x", "", "ā", "b"]),  # the silent vav
        ("خانه", "xāne", ["x", "ā", "ne", ""]),  # the final he: the e is the n's
        ("مسئول", "masˈul", ["ma", "s", "ˈ", "u", "l"]),  # the mark for hamza
    ],
)
def test_each_letter_takes_its_piece_of_the_reading(
    spelling: str, latin: str, pieces: list[str]
):
    assert align(shape(spelling), latin) == pieces


def test_a_reading_the_letters_cannot_make_does_not_line_up():
    assert align(shape("دل"), "qal") is None
    assert align(("χ",), "x") is None


BANK_PAIRS = [
    ("دست", "Dast"),
    ("کار", "Kār"),
    ("بار", "Bār"),
    ("دار", "Dār"),
    ("داد", "Dād"),
    ("کام", "Kām"),
    ("بام", "Bām"),
]


def test_the_letter_model_guesses_from_the_surroundings_it_has_seen():
    model = LetterModel.train(BANK_PAIRS)
    latin, confidence = model.guess("دام") or ("", 0.0)
    assert latin == "dām"
    assert 0 < confidence <= 1
    assert model.guess("χ") is None
    assert model.guess("ژ") is None  # a letter it never saw


def test_one_hard_letter_lowers_the_whole_word():
    model = LetterModel.train(
        [("سرد", "sard"), ("سرو", "sarv"), ("گرد", "gerd"), ("گرگ", "gorg")]
    )
    _, sure = model.guess("سرد") or ("", 0.0)
    _, unsure = model.guess("گرد") or ("", 0.0)
    assert unsure <= 0.5 < sure


def test_the_letter_model_survives_a_round_trip():
    model = LetterModel.train(BANK_PAIRS)
    again = LetterModel.from_dict(model.to_dict())
    assert again.guess("دام") == model.guess("دام")


def test_a_function_word_starts_ahead_and_answers_move_the_choice():
    empty = ChoiceModel()
    probs = empty.probabilities("که", ["ke", "keh"], function_reading="ke")
    assert probs["ke"] == pytest.approx(0.9)

    two = ChoiceModel()
    assert two.probabilities("ترک", ["Tark", "tork"]) == {"Tark": 0.5, "tork": 0.5}

    taught = ChoiceModel.train(
        [Answered("ترک", "tork")] * 9 + [Answered("ترک", "Tark")]
    )
    probs = taught.probabilities("ترک", ["Tark", "tork"])
    assert probs["tork"] > 0.8


def test_a_neighbour_seen_often_enough_overrules_the_spelling_alone():
    answers = [Answered("ترک", "tork")] * 8 + [Answered("ترک", "Tark", before="از")] * 6
    model = ChoiceModel.train(answers)
    assert (
        max(model.probabilities("ترک", ["Tark", "tork"]).items(), key=lambda kv: kv[1])[
            0
        ]
        == "tork"
    )
    after_az = model.probabilities("ترک", ["Tark", "tork"], before="از")
    assert after_az["Tark"] > after_az["tork"]


def test_a_single_candidate_is_certain_before_coverage():
    assert ChoiceModel().probabilities("دست", ["Dast"]) == {"Dast": 1.0}


@pytest.fixture
def transcriber() -> Transcriber:
    pairs = [
        *BANK_PAIRS,
        ("که", "keh"),
        ("ترک", "Tark"),
        ("ترک", "tork"),
        ("بود", "Bud"),
    ]
    return Transcriber(
        bank=bank_from(pairs),
        letters=LetterModel.train(pairs),
        choice=ChoiceModel.train([Answered("ترک", "tork")] * 9),
        functions={"که": ("ke",)},
        covered={"بود": (1, 9)},
    )


def test_each_word_says_where_its_reading_came_from(transcriber: Transcriber):
    words = transcriber.line("که دست دام ترک")
    assert [(w.latin, w.source) for w in words] == [
        ("ke", FUNCTION),
        ("Dast", BANK),
        ("dām", LETTERS),
        ("tork", CHOICE),
    ]
    assert all(0 < w.confidence <= 1 for w in words)


def test_the_words_own_signs_settle_the_choice(transcriber: Transcriber):
    [marked] = transcriber.line("تَرک")
    assert marked.latin == "Tark"
    [unmarked] = transcriber.line("تَرک", use_signs=False)
    assert unmarked.latin == "tork"


def test_signs_that_fit_no_reading_send_the_word_to_a_person(transcriber: Transcriber):
    [word] = transcriber.line("بُوَد")
    assert word.confidence == 0.0


def test_a_spelling_the_corpus_often_contradicts_is_not_trusted(
    transcriber: Transcriber,
):
    [bud] = transcriber.line("بود")
    [dast] = transcriber.line("دست")
    assert bud.confidence < 0.3 < 0.85 < dast.confidence


def test_the_model_file_survives_a_round_trip(transcriber: Transcriber, tmp_path: Path):
    path = tmp_path / "model.json"
    transcriber.save(path, {"corpus_version": "test"})
    again = Transcriber.load(path, transcriber.bank)
    again.functions = transcriber.functions
    assert [w.as_dict() for w in again.line("که دست دام ترک بود")] == [
        w.as_dict() for w in transcriber.line("که دست دام ترک بود")
    ]


def test_a_guess_the_words_signs_rule_out_goes_to_a_person(transcriber: Transcriber):
    [plain] = transcriber.line("دام")
    [marked] = transcriber.line("دُام")  # a damma: the guess dām cannot stand
    assert plain.latin == marked.latin == "dām"
    assert plain.confidence > 0 and marked.confidence == 0.0


def test_a_reading_variant_is_a_candidate_too():
    pairs = [("رخ", "rex"), ("رخ", "rox")]
    model = Transcriber(
        bank=bank_from(pairs),
        letters=LetterModel.train(pairs),
        choice=ChoiceModel(),
        functions={},
    )
    [word] = model.line("رُخ")
    assert word.latin == "rox"


def test_a_reading_the_signs_cannot_judge_is_not_confirmed_by_them():
    model = Transcriber(
        bank={"باد": ("qqq",)},  # no letter of باد is spelled q: nothing to judge
        letters=LetterModel.train(BANK_PAIRS),
        choice=ChoiceModel(),
        functions={},
    )
    [word] = model.line("بَاد")
    assert word.latin == "qqq"
    assert word.confidence == pytest.approx(model.covered_prior)


def test_a_tie_goes_to_the_alphabetically_first_reading():
    assert ranked({"tork": 0.5, "Tark": 0.5})[0][0] == "Tark"


def test_a_function_word_keeps_its_prior_whatever_its_marked_places_say():
    model = ChoiceModel.train([Answered("به", "bah")] * 9)
    probs = model.probabilities("به", ["be", "bah"], function_reading="be")
    assert probs["be"] == pytest.approx(0.9)


def test_an_inflected_form_is_guessed_but_held_below_the_threshold():
    from murfulu.corpus.inflection import Analyser, Held

    pairs = [("بخش", "baxš"), ("چشم", "čašm"), ("خشم", "xašm"), ("پشم", "pašm")]
    model = Transcriber(
        bank=bank_from(pairs),
        letters=LetterModel.train(pairs),
        choice=ChoiceModel(),
        functions={},
        inflection=Analyser(Held.of([], [], ["بخش"])),
    )
    [word] = model.line("بخشم")
    assert word.source == "inflected"
    assert word.confidence <= model.inflected_cap


def test_an_inflected_form_with_a_half_space_is_held_too():
    from murfulu.corpus.inflection import Analyser, Held

    pairs = [("بی‌کس", "bikas"), ("کسان", "Kasān"), ("بیکس", "bikas")]
    model = Transcriber(
        bank={},
        letters=LetterModel.train(pairs),
        choice=ChoiceModel(),
        functions={},
        inflection=Analyser(Held.of(["بی‌کس"], [], [])),
    )
    [word] = model.line("بی‌کسان")
    assert word.source == "inflected"
    assert word.confidence <= model.inflected_cap


def test_the_lower_bound_is_the_exact_clopper_pearson_one():
    from murfulu.behnevis.stats import lower_bound, needed_without_error

    assert lower_bound(9, 10) == pytest.approx(0.6058, abs=1e-4)  # Beta(0.05; 9, 2)
    assert lower_bound(300, 300) == pytest.approx(0.05 ** (1 / 300))
    assert lower_bound(300, 300) < 0.991  # 300 of 300 proves only about 99 %
    assert lower_bound(0, 10) == 0.0
    assert needed_without_error(0.99) == 299


def test_poets_that_differ_widen_the_bound():
    from murfulu.behnevis.stats import cluster_lower_bound, lower_bound

    alike = [(9, 10)] * 20
    unlike = [(10, 10)] * 10 + [(8, 10)] * 10
    # alike poets: no wider than the answers taken one by one
    assert cluster_lower_bound(alike) == pytest.approx(lower_bound(180, 200))
    assert cluster_lower_bound(unlike) < 0.9
    # the same 180 of 200, as independent answers, claim more certainty
    assert cluster_lower_bound(unlike, 0.05) < lower_bound(180, 200, 0.05) + 0.02


def test_poets_without_a_single_error_do_not_prove_perfection():
    from murfulu.behnevis.stats import cluster_lower_bound

    assert cluster_lower_bound([(10, 10)] * 7, 0.001) == pytest.approx(0.001 ** (1 / 7))
