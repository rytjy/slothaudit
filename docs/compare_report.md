# slothaudit report — samples/broken_lookahead

Generated 2026-10-23 12:30, offline.

## Morning summary

FIX FIRST: samples/broken_lookahead/strategy.py:10 — fill price read on the signal bar
ALSO: samples/broken_lookahead/strategy.py:12 — no fee or slippage term in the ledger
ALSO: samples/broken_lookahead/strategy.py:8 — entries without a cooldown

Two local models answered the same 4 findings: 4 agree, 0 disagree.

## Findings

### LA-01 [high] fill price read on the signal bar

samples/broken_lookahead/strategy.py:10

A fill taken at index i while the signal is computed at i too is the classic same-bar leak. Check the fill uses i+1, or the next tick.

Evidence:
    samples/broken_lookahead/strategy.py:10  entry = df["close"][i]          # fill on the bar that produced the signal

Model check: qwen **YES** · gemma **YES**

Agreement: yes

### CO-01 [high] no fee or slippage term in the ledger

samples/broken_lookahead/strategy.py:12

This file records PnL but never mentions fee, commission, slippage or spread. Searched 24 lines: 0 matches for fee|commission|slippage|spread|cost. At 4.5bps a side, high turnover can be negative before any edge.

Evidence:
    samples/broken_lookahead/strategy.py:12  pnl = (exit_ - entry) * 100

Model check: qwen **YES** · gemma **YES**

Agreement: yes

### SI-01 [medium] entries without a cooldown

samples/broken_lookahead/strategy.py:8

Consecutive bars can each open a position, so one market event counts as many samples and n is inflated. Searched 24 lines: no cooldown|cool_down|debounce|last_entry.

Evidence:
    samples/broken_lookahead/strategy.py:8  for i in range(2, len(df) - 1):

Model check: qwen **YES** · gemma **YES**

Agreement: yes

### MD-01 [medium] peak reset inside the drawdown loop

samples/broken_lookahead/strategy.py:20

Resetting peak to a cap turns the reported MDD into the local drawdown since the last reset. Report capped and raw separately.

Evidence:
    samples/broken_lookahead/strategy.py:20  peak = cap

Model check: qwen **YES** · gemma **YES** — This code calculates a running peak by adding the current P&L to the previous peak and then comparing the peak to the previous peak plus the current P&L.

Agreement: yes


Blind spot: this tool does not run the strategy, does not see your data, and cannot tell you the edge is real.

---

These are source heuristics. A finding means read this line, not this is wrong.
The checker does not run the strategy, does not see the data, and cannot tell you the edge is real.