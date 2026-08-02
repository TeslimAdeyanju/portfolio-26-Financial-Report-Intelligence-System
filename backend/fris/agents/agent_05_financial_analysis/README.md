# Financial Analysis Agent

**Status:** Implemented

Analyses every available adjacent reporting period across canonical financial facts and
calculated ratios. Each movement records current and prior values, absolute and percentage
variance, direction, performance assessment, rationale, units, and source evidence.

The agent uses deterministic policies rather than an LLM. It distinguishes ordinary increases
and decreases from profit turnarounds, loss deteriorations, immaterial movements below 1%, and
context-dependent items such as capital expenditure. This output becomes the validated input
for the separate Insight, Risk, and Narrative agents.
