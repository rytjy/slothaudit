# slothaudit report — samples/broken_lookahead

Generated 2026-10-22 23:04, offline.

## Morning summary

FIX FIRST: samples/broken_lookahead/strategy.py:1 — no fee or slippage term in the ledger
ALSO: samples/broken_lookahead/strategy.py:9 — fill price read on the signal bar
ALSO: samples/broken_lookahead/strategy.py:1 — entries without a cooldown

## Findings

### CO-01 [high] no fee or slippage term in the ledger

samples/broken_lookahead/strategy.py:1

This file records PnL but never mentions fee, commission, slippage or spread. At 4.5bps a side, high turnover can be negative before any edge.

Model check: gemma **NO**

### LA-01 [high] fill price read on the signal bar

samples/broken_lookahead/strategy.py:9

A fill taken at index i while the signal is computed at i too is the classic same-bar leak. Check the fill uses i+1, or the next tick.

Model check: gemma **YES** — the code fills on the bar that produced the signal.

### SI-01 [medium] entries without a cooldown

samples/broken_lookahead/strategy.py:1

Consecutive bars can each open a position, so one market event counts as many samples and n is inflated.

Model check: gemma **YES**

### MD-01 [medium] peak reset inside the drawdown loop

samples/broken_lookahead/strategy.py:1

Resetting peak to a cap turns the reported MDD into the local drawdown since the last reset. Report capped and raw separately.

Model check: gemma **YES** — the equity is updated with each new bar.


Blind spot: this tool does not run the strategy, does not see your data, and cannot tell you the edge is real.

---

These are source heuristics. A finding means read this line, not this is wrong.
The checker does not run the strategy, does not see the data, and cannot tell you the edge is real.