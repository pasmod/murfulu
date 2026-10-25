"""Say what a generated word means, from the tags along its derivation.

*namak* + *dān* is not just a string. The rule that built it carries the tag
*Jā* — "place" — whose gloss template is *جایی که {stem} در آن است*, so the
result can be handed to a reader as **جایی که نمک در آن است**, "the place where
salt is kept".

The templates are the linguist's to write. Most are still empty, and a word
whose tags have no template gets **no meaning** rather than a made-up one:
returning None is the honest answer, and the caller can see which tag is
missing.
"""

from __future__ import annotations

from dataclasses import dataclass

from murfulu.engine.affix import DerivedForm
from murfulu.rules.pack import RulePack


@dataclass(frozen=True)
class Meaning:
    """What a form means, and what is missing if it cannot be said."""

    text_fa: str | None = None
    text_en: str | None = None
    #: Tags on the path whose gloss template has not been written yet.
    missing_templates: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        """True when something can actually be shown to a reader."""
        return bool(self.text_fa)


def compose(pack: RulePack, form: DerivedForm) -> Meaning:
    """Build the meaning of one derived form from its semantic tags."""
    text_fa: str | None = None
    text_en: str | None = None
    missing: list[str] = []

    # The stem the gloss talks about is what the last step was applied to, in
    # Persian — the reader reads Persian, not the Latin working form.
    stem_fa = form.base_fa

    for label in form.semantic_tags:
        tag = pack.tag_for(label)
        if tag is None:
            missing.append(label)
            continue
        if tag.gloss_template_fa:
            text_fa = tag.gloss_template_fa.replace("{stem}", stem_fa)
            if tag.gloss_template_en:
                text_en = tag.gloss_template_en.replace("{stem}", form.base_latin)
        else:
            missing.append(label)

    return Meaning(text_fa=text_fa, text_en=text_en, missing_templates=tuple(missing))
