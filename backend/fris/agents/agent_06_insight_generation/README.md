# Insight Generation Agent

**Status:** Implemented

Converts validated latest-period movements and risk findings into ranked management insights.
Each insight explains what changed, why the movement matters, what should be investigated,
which risks and metrics it relates to, and which source evidence supports it.

The agent is deterministic and deliberately avoids invented causal claims. Possible drivers are
presented as investigation prompts until report notes or management commentary establish them.

An optional Ollama augmentation layer uses `phi3:mini` by default on the 8 GB M2 to consolidate
the deterministic items into connected management themes. `llama3.1:8b` remains selectable,
but is substantially slower on this hardware. The structured response is accepted only when
Python verifies every figure, metric, risk code, evidence page, and causal-language guardrail.
Invalid or unavailable model output falls back to the deterministic insights.
