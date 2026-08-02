# Metrics Extraction Agent

**Status:** Implemented

Identifies metrics and builds structured, multi-period income statements, balance sheets,
and cash-flow statements with currency, units, periods, and source evidence.

The primary cross-company output is a stable Key Financial Facts pack rather than a forced
recreation of every source table. It maps company-specific labels such as `Net sales` into
canonical concepts such as `revenue`, while retaining the original label, periods, values,
units, page evidence, extraction method, and confidence. Metrics that are not separately
reported remain explicit `not_found` facts with reasons; they are never converted to zero or
invented by a model.

Complete statements remain available as an optional inspection and reconciliation view.
