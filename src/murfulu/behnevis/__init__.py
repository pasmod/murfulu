"""Automatic Behnevis for running text: one reading per word, and how sure it is.

Persian script leaves the short vowels unwritten, and ا و ی ه each stand for
several sounds, so no set of rules turns a line of text into Behnevis. What
can be done (the project lead's choice of 2026-11-14) is to count: every word
gets the reading the evidence makes most likely, **and the probability that it
is right**, so a person checks only the words below a threshold.

Four sources, in order (:mod:`.transcribe`):

1. **A function word** (rules/function_word_readings.yaml): و, که, از … offer
   their function-word reading beside whatever the bank holds.
2. **The bank has one reading**: that reading.
3. **The bank has several**: the one the vowel-marked corpus chooses most
   often for this spelling, between these neighbours (:mod:`.choice`).
4. **The bank has none**: a guess letter by letter, from what the bank's
   letters do in the same surroundings (:mod:`.letters`).

None of the probabilities is a judgement: each is a count, measured on data
the model did not learn from (``tools/evaluate_behnevis.py``). What is not
measured is said where it is used.
"""
