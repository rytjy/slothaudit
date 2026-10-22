# slothaudit

A night-shift auditor for trading-strategy repos. It runs five deterministic
checks over the source, then a local 1.5B open-weight model reads the code each
finding points at and answers one narrow question: *is this actually true here?*

Nothing leaves the machine. No API key, no upload, no account, no telemetry.

## Why a night shift

Most backtest bugs are boring and repetitive: a fill taken on the signal bar, a
ledger that never mentions fees, one market event counted as eleven samples, a
drawdown that resets its own peak. You find them when you already suspect them —
which is exactly when you don't need help.

So the boring pass runs while you sleep, at sloth speed, on your own CPU.

## Run

    pip install -e .
    slothaudit audit samples/broken_lookahead      # ~13s on a laptop CPU

`--no-llm` runs the deterministic checks only (instant).

Model: any GGUF via llama.cpp (`SLOTHAUDIT_GGUF=/path/model.gguf`), or an
Ollama server on `127.0.0.1:11434`. Tested with Qwen2.5-Coder-1.5B-Instruct
Q4_K_M and llama.cpp build b11804.

## Output

    ## Morning summary

    FIX FIRST: samples/broken_lookahead/strategy.py:1 — no fee or slippage term in the ledger
    ALSO: samples/broken_lookahead/strategy.py:9 — fill price read on the signal bar
    ALSO: samples/broken_lookahead/strategy.py:1 — entries without a cooldown

    ## Findings

    ### CO-01 [high] no fee or slippage term in the ledger
    samples/broken_lookahead/strategy.py:1
    This file records PnL but never mentions fee, commission, slippage or spread.
    Model check: **YES**

A clean repo gets a deliberately un-reassuring answer:

    No v0 check fired. That is not the same as clean: it means this run had
    nothing to point at, not that the strategy survives an audit.

## Division of labour

- **Locations come from code, never from the model.** The report prints
  `path:line` from the checker; the model is never asked to name a file or line.
- **The model answers one yes/no/unsure question per finding**, with six lines of
  context. That is a task a 1.5B can do. Asking it to write a summary produced
  confident nonsense, so I stopped asking.
- **The blind spot is fixed text**, not generated: this tool does not run the
  strategy, does not see your data, and cannot tell you the edge is real.

## Checks (v0)

| id | what it looks for | severity |
|---|---|---|
| LA-01 | signal and fill read the same bar | high |
| CO-01 | trades simulated with no fee/slippage term | high |
| SI-01 | entries without a cooldown (one event, many samples) | medium |
| MD-01 | drawdown computed from a reset peak | medium |
| NA-01 | NaN coerced to 0 by `where(x > 0, 0)` | medium |

Heuristics over source, not proofs. A finding means *read this line*, not *this
is wrong*.

## License

MIT — see [LICENSE](LICENSE).

Built during the Hacktoberfest Week 3 window (Oct 19–25, 2026). Any commit made after the submission deadline will be noted here.
