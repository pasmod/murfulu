"""The tables. Importing this package registers every one on the metadata.

Alembic compares the models against the live database, so a table that is
never imported looks to it like a table that should be dropped. Everything is
therefore imported here, and this is the module both the migrations and the
application load.
"""

from murfulu.db.base import Base
from murfulu.db.models.corpus import CorpusVersion, CorpusVersionSource, Source
from murfulu.db.models.people import User
from murfulu.db.models.proposals import RuleProposal, RuleProposalDecision
from murfulu.db.models.review import (
    CATEGORIES,
    OWNERS,
    TARGET_TYPES,
    VERDICTS,
    ExpertFeedback,
)
from murfulu.db.models.rules import GlideRuleRow, RuleRow
from murfulu.db.models.rulings import (
    ORIGINS,
    STATES,
    LinguistQuestion,
    LinguistQuestionFile,
    LinguistRuling,
)
from murfulu.rules.proposals import PROPOSABLE_FIELDS

__all__ = [
    "CATEGORIES",
    "PROPOSABLE_FIELDS",
    "ORIGINS",
    "OWNERS",
    "STATES",
    "TARGET_TYPES",
    "VERDICTS",
    "Base",
    "CorpusVersion",
    "CorpusVersionSource",
    "ExpertFeedback",
    "GlideRuleRow",
    "LinguistQuestion",
    "LinguistQuestionFile",
    "LinguistRuling",
    "RuleProposal",
    "RuleProposalDecision",
    "RuleRow",
    "Source",
    "User",
]
