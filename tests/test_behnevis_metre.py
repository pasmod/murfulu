"""The metre as evidence for a word's Behnevis (an experiment, not served).

Every word and line here is written for the test or is a textbook example of
the metre named; no corpus text (NOTICE).
"""

import math

import pytest

from murfulu.behnevis.metre import (
    ROBAI,
    Licences,
    Metre,
    Option,
    Slot,
    Syllable,
    behaviour,
    fit,
    patterns,
    scans,
    shape,
    weights,
    with_ezafe,
)
from murfulu.behnevis.transcribe import Word

# -- 1. the weights of a reading ---------------------------------------------


@pytest.mark.parametrize(
    ("reading", "expected"),
    [
        ("del", "-"),  # a short vowel closed by one consonant: long
        ("Dal", "-"),  # the case of a noun changes nothing
        ("bovad", "U-"),
        ("Bud", "-U"),  # a long vowel closed: overlong
        ("dast", "-U"),  # a short vowel closed by two: overlong
        ("xāne", "-U"),  # the final -e is a short open syllable
        ("ke", "U"),
        ("jān", "-"),  # the n after a long vowel is not counted
        ("mānd", "-U"),  # …but the d after it is
        ("jāndār", "--U"),
        ("dāneš", "--"),  # an n before a vowel opens the next syllable
        ("ammā", "--"),  # a doubled letter closes one syllable, opens the next
        ("now", "-"),  # the diphthong: o closed by w
        ("owlād", "--U"),
        ("dastgāh", "-U-U"),  # overlong inside a word too
        ("ˈAli", "U-"),  # Behnevis's mark for ع is a consonant
        ("Nāāqāzruz", "---U-U"),  # two vowels side by side: two syllables
        ("siyāh", "U-U"),  # an i before an opening y is short
        ("miyān", "U-"),
        ("biyā", "U-"),
        ("pāyi", "--"),  # …a y after another vowel changes nothing
        ("ziyy", "-U"),  # …nor one that closes the syllable
    ],
)
def test_a_reading_weighs_its_syllables(reading: str, expected: str):
    assert weights(reading) == expected


@pytest.mark.parametrize("reading", ["baxšm", "st", "", "šxān"])
def test_a_reading_that_cannot_be_syllabled_has_no_weights(reading: str):
    # Three consonants closing a syllable, no vowel, or two opening one.
    assert shape(reading) is None


def test_a_reading_knows_how_it_starts_and_what_its_last_syllable_is():
    found = shape("andiše")
    assert found is not None
    assert found.vowel_first
    assert found.body == "--"
    assert found.last == Syllable(long=False, coda=0)
    assert not shape("del").vowel_first  # type: ignore[union-attr]
    # A glottal stop opens it, as one opens a word that starts with a vowel.
    assert shape("ˈAli").vowel_first  # type: ignore[union-attr]


def test_a_following_vowel_takes_the_last_consonant():
    # del az → de-laz; dast az → das-taz; dust az → dus-taz, still overlong;
    # jān az → jā-naz.
    assert shape("del").last.joined().weight() == "U"  # type: ignore[union-attr]
    assert shape("dast").last.joined().weight() == "-"  # type: ignore[union-attr]
    assert shape("dust").last.joined().weight() == "-U"  # type: ignore[union-attr]
    assert shape("jān").last.joined().weight() == "-"  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("reading", "spelling", "expected"),
    [
        ("aālam", "عالم", "--"),  # the a is the ع: ʔā-lam
        ("aāšeq", "عاشق", "--"),
        ("maalum", "معلوم", "--U"),  # maʔ-lum
        ("jaafari", "جعفری", "-U-"),
        ("neamat", "نعمت", "--"),
        ("šama", "شمع", "-U"),  # šamʔ: the final a is the ع
        ("samāa", "سماع", "U-U"),
        ("tabiat", "طبیعت", "U--"),  # ta-bi-ʔat: the ع unwritten between
        ("jamāat", "جماعت", "U--"),
        ("taaāli", "تعالی", "U--"),  # ta-ʔā-li
        ("moaāšarat", "معاشرت", "U-U-"),  # mo-ʔā-ša-rat
        ("āšofteaqli", "آشفته‌عقلی", "--U--"),  # āš-of-te-ʔaq-li: the vowel stays
        ("baad", "بعد", "-U"),  # baʔd
        ("moallem", "معلم", "U--"),  # mo-ʔal-lem: before a doubled letter
        ("bitāati", "بی‌طاعتی", "--U-"),  # bi-tā-ʔa-ti
        ("Ali", "علی", "U-"),  # an ع before one vowel is its onset already
        ("Jazāeri", "جزائری", "U-U-"),  # a hamza: the vowels stay
        ("čehreārāy", "چهره‌آرای", "-U--U"),  # two words joined, no ع
        ("hokumatgāe", "حکومت‌گاه", "U---U"),  # gāe is gāh
        ("hosain", "حسین", "U-U"),  # the diphthong: ho-sayn, not ho-sa-in
        ("faiz", "فیض", "-U"),
        ("aālam", "", "U--"),  # without the spelling, as written
    ],
)
def test_a_vowel_letter_for_ain_is_read_as_the_consonant(
    reading: str, spelling: str, expected: str
):
    assert weights(reading, spelling) == expected


def test_a_word_that_opens_on_ain_may_take_a_consonant_before_it():
    assert shape("aāšeq", "عاشق").vowel_first  # type: ignore[union-attr]
    assert shape("šama", "شمع", ezafe=True).alone() == "-U"  # type: ignore[union-attr]


def test_the_ezafe_is_e_after_a_consonant_and_ye_after_a_vowel():
    assert with_ezafe("Del") == "dele"
    assert with_ezafe("xāne") == "xāneye"
    assert with_ezafe("jā") == "jāye"
    assert weights(with_ezafe("del")) == "UU"
    assert weights(with_ezafe("xāne")) == "-UU"


# -- the metre's patterns ------------------------------------------------------


def test_a_label_gives_its_feet_pattern():
    assert patterns("مفاعیلن مفاعیلن فعولن (هزج مسدس محذوف یا وزن دوبیتی)") == {
        "U---U---U--"
    }
    assert patterns("فعولن فعولن فعولن فعل (متقارب مثمن محذوف یا وزن شاهنامه)") == {
        "U--U--U--U-"
    }


def test_a_label_carries_the_classical_variants():
    found = patterns("فعلاتن فعلاتن فعلاتن فعلن (رمل مثمن مخبون محذوف)")
    # The first foot may open long; the last فعلن may be فع لن.
    assert found == {
        "UU--UU--UU--UU-",
        "-U--UU--UU--UU-",
        "UU--UU--UU----",
        "-U--UU--UU----",
    }
    assert "U-U--U-U-UU--" in patterns(
        "مفتعلن فاعلات مفتعلن فع (منسرح مثمن مطوی منحور)"
    )


def test_the_robai_has_its_twelve_patterns():
    assert patterns("مفعول مفاعیل مفاعیل فعل (وزن رباعی)") == ROBAI
    # The 24 traditional forms, spelled out by their feet, give the twelve.
    first = ["مفعول مفاعیل", "مفعول مفاعلن", "مفعول مفاعیلن", "مفعولن مفعول"]
    first += ["مفعولن فاعلن", "مفعولن مفعولن"]
    second = {
        "مفعول مفاعیل": "مفاعیل",
        "مفعول مفاعلن": "مفاعیل",
        "مفعول مفاعیلن": "مفعول",
        "مفعولن مفعول": "مفاعیل",
        "مفعولن فاعلن": "مفاعیل",
        "مفعولن مفعولن": "مفعول",
    }
    forms = set()
    for opening in first:
        for third in (second[opening], second[opening] + "ن"):
            ending = ("فعل", "فعول") if not third.endswith("ن") else ("فع", "فاع")
            forms |= {f"{opening} {third} {end}" for end in ending}
    assert len(forms) == 24
    assert set().union(*(patterns(form) for form in forms)) == ROBAI


def test_the_catalogue_licences_where_they_apply():
    # متدارک: every فعلن may be فع لن.
    assert "--UU-UU---" in patterns("فعلن فعلن فعلن فعلن")
    # but elsewhere only the last: فعلاتن فعلاتن فعلن keeps its inner feet.
    assert "UU----UU-" not in patterns("فعلاتن فعلن فعلن")
    # قلب in the رجز of مفتعلن and مفاعلن, both ways.
    found = patterns("مفتعلن مفاعلن مفتعلن مفاعلن (رجز مثمن مطوی مخبون)")
    assert "U-U--UU-U-U--UU-" in found


def test_a_split_final_foot_and_an_unknown_foot():
    assert patterns("مفعول مفاعیل مفاعیلن فاع") == {"--UU--UU----"}
    assert patterns("مفاعیلن چیزی") == frozenset()
    assert patterns("") == frozenset()


# -- 2. a hemistich against its pattern ----------------------------------------


def slot(*readings: str, conjunction: bool = False, ast: bool = False) -> Slot:
    """A word offering these readings, each as written (no ezafe)."""
    options = []
    for reading in readings:
        found = shape(reading)
        options.append(
            Option(
                ((found, 0.0),) if found else (),
                conjunction=conjunction,
                ast=ast,
            )
        )
    return Slot(tuple(options), (1, 3))


def costs(slots: list[Slot], *pattern: str) -> list[list[float]]:
    return fit(slots, pattern, Licences())


#: The price of *some other reading* for one word: a fit that needs one is
#: a fit only because the model's readings were set aside.
OTHER = Licences().other


def test_the_metre_keeps_the_reading_whose_weights_it_holds():
    # که بود جان: *bovad* fills U-, the noun *Bud* (-U) cannot.
    line = [slot("ke"), slot("Bud", "bovad"), slot("jān")]
    found = costs(line, "UU--")
    assert found[1][1] == 0.0  # bovad
    # Bud fits only if another word is read as the model did not offer.
    assert found[1][0] >= OTHER
    assert scans(line, ["UU--"], Licences())
    assert not scans([slot("ke"), slot("Bud"), slot("jān")], ["UU--"], Licences())


def test_the_last_syllable_counts_long():
    assert costs([slot("del"), slot("ke")], "--")[1][0] == 0.0
    assert costs([slot("del"), slot("dast")], "--")[1][0] == 0.0  # not -U


def test_a_final_consonant_may_join_a_following_vowel():
    # del az: de-laz (vasl) or del ʔaz (the glottal stop kept).
    assert costs([slot("del"), slot("az")], "U-")[0][0] == 0.0
    assert costs([slot("del"), slot("az")], "--")[0][0] == 0.0
    # Before a consonant it cannot: del bar is always long-long.
    assert costs([slot("del"), slot("bar")], "U-")[1][0] >= OTHER


def test_the_conjunction_o_always_joins():
    # del o jān: de-lo-jān, never del-o-jān.
    line = [slot("del"), slot("o", conjunction=True), slot("jān")]
    assert costs(line, "UU-")[1][0] == 0.0
    assert costs(line, "-U-")[0][0] >= OTHER  # del cannot stay closed


def test_ast_after_a_vowel_may_lose_its_a():
    # xāne ast: xā-nest at the end of the line, or xā-ne ʔast.
    line = [slot("xāne"), slot("ast", ast=True)]
    assert costs(line, "--")[1][0] == 0.0
    assert costs(line, "-U-")[1][0] == 0.0


def test_the_licences_cost_what_they_are_set_to():
    licences = Licences()
    # ke counted long before a consonant: the lengthening.
    assert costs([slot("ke"), slot("del")], "--")[0][0] == licences.lengthen
    # tā counted short before a vowel: the shortening.
    assert costs([slot("tā"), slot("az")], "U-")[0][0] == licences.shorten
    # A reading the line cannot hold, with no neighbour to give way: none.
    assert costs([slot("Bud")], "U-")[0] == [math.inf, licences.other]


def test_an_ezafe_is_offered_by_the_metre_step_at_its_cost():
    metre = Metre()
    words = [
        Word("دل", "دل", "Del", 0.9, "bank", (("Del", 0.9),)),
        Word("من", "من", "man", 0.9, "function", (("man", 0.9),)),
    ]
    slots = metre.slots(words)
    # Del-e man: de-le-man, the ezafe at its cost; Del man: long-long, free.
    assert fit(slots, ["UU-"], metre.licences)[0][0] == metre.licences.ezafe
    assert fit(slots, ["--"], metre.licences)[0][0] == 0.0
    # No ezafe after the last word, or after a function word.
    assert len(slots[1].options[0].shapes) == 1


# -- 3. the words re-weighed ---------------------------------------------------


def test_the_metre_moves_a_word_to_the_reading_the_line_holds():
    metre = Metre()
    words = [
        Word("که", "که", "ke", 0.9, "function", (("ke", 0.9),)),
        Word("بود", "بود", "Bud", 0.6, "choice", (("Bud", 0.6), ("bovad", 0.3))),
        Word("جان", "جان", "jān", 0.9, "bank", (("jān", 0.9),)),
    ]
    weighed = metre.weigh(words, ["UU--"])
    moved = weighed[1].word
    assert moved.latin == "bovad"
    # bovad keeps its 0.3; Bud fits only with a neighbour read otherwise and
    # an ezafe (3.5), so it keeps 2 ** -3.5 of its 0.6; the 0.1 the model
    # left for readings it did not offer stays whole, as they might fit.
    bud = 0.6 * 2**-3.5
    assert moved.confidence == pytest.approx(0.3 / (0.3 + bud + 0.1))
    assert weighed[1].scanned
    assert weighed[1].extra == pytest.approx(3.5)
    assert moved.source == "choice"  # where the reading came from is kept


def test_a_reading_offered_without_a_number_takes_a_share_of_what_is_left():
    metre = Metre()
    words = [
        Word("دل", "دل", "del", 0.9, "bank", (("del", 0.9),)),
        Word(
            "بخشم",
            "بخشم",
            "baxšm",
            0.4,
            "inflected",
            (("baxšm", 0.4), ("baxšam", None)),
        ),
    ]
    weighed = metre.weigh(words, ["---"])  # del bax-šam; baxšm is no syllable
    moved = weighed[1].word
    assert moved.latin == "baxšam"
    # 0.6 left: half of it would be 0.3, but no more than baxšm's own 0.4 —
    # 0.3 then; the other 0.3 for readings not offered.
    assert moved.confidence == pytest.approx(0.3 / (0.3 + 0.3))


def test_without_the_metres_word_the_model_keeps_its_order():
    # Dal at 0.1, Del offered without a number: both fit equally, so nothing
    # moves — the unscored Del may not overtake the model's own reading.
    metre = Metre()
    words = [
        Word("دل", "دل", "Dal", 0.1, "inflected", (("Dal", 0.1), ("Del", None))),
        Word("من", "من", "man", 0.9, "function", (("man", 0.9),)),
    ]
    weighed = metre.weigh(words, ["--"])[0].word
    assert weighed.latin == "Dal"
    assert weighed.confidence == pytest.approx(0.1)


def test_the_metre_cannot_raise_a_word_with_no_rival():
    metre = Metre()
    words = [
        Word("دل", "دل", "Del", 0.8, "bank", (("Del", 0.8),)),
        Word("من", "من", "man", 0.9, "function", (("man", 0.9),)),
    ]
    weighed = metre.weigh(words, ["--"])
    assert weighed[0].word.confidence == pytest.approx(0.8)
    assert weighed[0].word.latin == "Del"


def test_same_weights_are_left_to_the_model():
    # Del and Dal weigh the same: the metre leaves their order and numbers.
    metre = Metre()
    words = [
        Word("دل", "دل", "Dal", 0.5, "choice", (("Dal", 0.5), ("Del", 0.4))),
        Word("من", "من", "man", 0.9, "function", (("man", 0.9),)),
    ]
    weighed = metre.weigh(words, ["--"])[0].word
    assert weighed.latin == "Dal"
    assert weighed.confidence == pytest.approx(0.5)


def test_without_a_pattern_nothing_changes():
    words = [Word("دل", "دل", "Dal", 0.5, "choice", (("Dal", 0.5), ("Del", 0.4)))]
    assert Metre().weigh(words, [])[0].word == words[0]


def test_the_fit_is_the_cheapest_of_every_path():
    # The forward and backward passes against every path enumerated.
    from murfulu.behnevis.metre import State, _finish, _steps

    licences = Licences()
    line = [
        slot("ke", "keh"),
        slot("Bud", "bovad"),
        slot("az"),
        slot("del", "Dal"),
        slot("o", conjunction=True),
        slot("jān", "jāne"),
    ]
    for pattern in ("UU-U-U-", "U-U--U-", "UU--UU-", "--U-U-"):
        best = [[math.inf] * (len(s.options) + 1) for s in line]

        def walk(
            i: int,
            state: State,
            cost: float,
            chosen: list[int],
            pattern: str = pattern,
            best: list[list[float]] = best,
        ) -> None:
            if i == len(line):
                total = cost + _finish(state, pattern)
                for j, index in enumerate(chosen):
                    best[j][index] = min(best[j][index], total)
                return
            for index, new, step in _steps(line[i], state, pattern, licences):
                walk(i + 1, new, cost + step, [*chosen, index])

        walk(0, (0, None), 0.0, [])
        assert fit(line, [pattern], licences) == best


def test_only_ast_itself_loses_its_a():
    # xāne-st: the reading ast (or st) may attach; a noun read Ost may not.
    st = Slot((Option((), ast=True),), (1, 2), enclitic=True)
    assert costs([slot("xāne"), st], "--")[1][0] == 0.0
    ost = slot("Ost")
    assert costs([slot("xāne"), ost], "--")[1][0] >= OTHER


def test_another_reading_may_end_open_before_ast():
    # An unknown word, then ast: *ke-st* is a fit at the price of the unknown.
    unknown = Slot((), (1, 1))
    found = costs([unknown, slot("ast", ast=True)], "-")
    assert found[0] == [OTHER]
    assert found[1][0] == OTHER


def test_a_word_the_line_cannot_hold_goes_to_a_person():
    # Bud, offered alone and as sure as can be, cannot fill U-: confidence 0.
    metre = Metre()
    words = [Word("بود", "بود", "Bud", 1.0, "bank", (("Bud", 1.0),))]
    weighed = metre.weigh(words, ["U-"])[0]
    assert weighed.word.confidence == 0.0
    assert weighed.word.latin == "Bud"


def test_numbers_past_one_are_read_as_shares():
    metre = Metre()
    words = [
        Word("بود", "بود", "Bud", 0.9, "choice", (("Bud", 0.9), ("bovad", 0.9))),
    ]
    weighed = metre.weigh(words, ["U-"])[0].word
    assert weighed.latin == "bovad"
    assert weighed.confidence == pytest.approx(1.0)  # 0.45 of 0.45 + 0.45 * 0


@pytest.mark.parametrize(
    ("first", "second", "spelling", "same"),
    [
        ("Del", "Dal", "دل", True),  # the vowel's quality: no metre sees it
        ("kenār", "kanār", "کنار", True),
        ("Jur", "Jowr", "جور", True),  # both overlong, both long when joined
        ("Bud", "bovad", "بود", False),
        ("ju", "Jav", "جو", False),  # before a vowel Jav may turn short
        ("ast", "Est", "است", False),  # only ast may lose its a
    ],
)
def test_what_a_metre_can_tell_apart(
    first: str, second: str, spelling: str, same: bool
):
    assert (behaviour(first, spelling) == behaviour(second, spelling)) is same


def test_the_cost_of_the_models_own_reading_is_unknown_when_it_is_not_offered():
    metre = Metre()
    words = [Word("دل", "دل", "other", 0.8, "bank", (("del", 0.2),))]
    assert math.isnan(metre.weigh(words, ["-"])[0].extra)
    words = [Word("دل", "دل", None, 0.0, "none", ())]
    assert math.isnan(metre.weigh(words, ["-"])[0].extra)


def _extractor():  # noqa: ANN202 (a tool, loaded from its file)
    import importlib.util
    import sys
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "tools" / "extract_metre_lines.py"
    spec = importlib.util.spec_from_file_location("extract_metre_lines", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["extract_metre_lines"] = module
    spec.loader.exec_module(module)
    return module


def test_a_poem_is_kept_only_when_every_section_has_the_one_metre(tmp_path):  # noqa: ANN001
    import gzip
    import json

    def section(rhythm: str | None) -> dict:  # type: ignore[type-arg]
        return {"ganjoorMetre": {"rhythm": rhythm} if rhythm else None}

    poems = [
        {"id": 1, "excerpt": "الف", "mainSections": [section("A"), section("A")]},
        {"id": 2, "excerpt": "ب", "mainSections": [section("A"), section(None)]},
        {"id": 3, "excerpt": "پ", "mainSections": [section("A"), section("B")]},
        {"id": 4, "excerpt": "ت", "mainSections": []},
    ]
    (tmp_path / "cat").mkdir()
    with gzip.open(tmp_path / "cat" / "1.json.gz", "wt", encoding="utf-8") as out:
        json.dump({"cat": {"poems": poems}}, out)
    assert _extractor().ganjoor_metres(tmp_path) == {1: ("A", "الف")}


def test_the_first_hemistich_is_compared_by_its_letters_alone():
    letters_only = _extractor().letters_only
    assert letters_only("برخیزْ بتا، بیا") == letters_only("برخیز  بتا بیا")
    assert letters_only("آب") == letters_only("اب")
    assert letters_only("برخیز") != letters_only("بنشین")
