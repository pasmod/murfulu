"""Reading a score back, and placing it.

A figure with no spread beside it is not a measurement. These check the
placing, never the scoring: the cosines themselves come from a batch job.
"""

from murfulu.scoring import spread


class TestTypicalitySpread:
    """Placing one score among all of them.

    The cosine never leaves the middle on this corpus — 583,572 scored forms
    between 0.554 and 0.914, the middle half between 0.800 and 0.852 — so a
    bare percentage reads as a mark out of a hundred and is not one. See S15.
    """

    def _spread(self) -> "spread.Spread":
        # The v7 boundaries, measured by tools/measure_typicality_spread.py.
        return spread.from_document(
            {
                "corpus_version": "v7",
                "boundaries": [0.763, 0.807, 0.847, 0.870],
                "lowest": 0.554,
                "highest": 0.914,
                "median": 0.828,
                "counted": 583572,
            }
        )

    def test_the_median_reads_as_middle_not_as_a_good_mark(self):
        """0.828 is 83% and is the most ordinary word on the screen."""
        assert self._spread().band_for(0.828) == "middle"

    def test_the_bands_run_in_order(self):
        found = self._spread()
        assert found.band_for(0.60) == "lowest"
        assert found.band_for(0.79) == "low"
        assert found.band_for(0.86) == "high"
        assert found.band_for(0.91) == "highest"

    def test_nothing_measured_means_no_band_rather_than_a_guess(self):
        """An absent artefact is legitimate; the figure then stands alone."""
        assert spread.Spread().band_for(0.828) is None

    def test_a_malformed_file_is_treated_as_absent(self):
        """Wrong boundary count would place every band wrongly, in silence."""
        found = spread.from_document({"boundaries": [0.8, 0.9], "median": 0.83})
        assert found.band_for(0.828) is None
