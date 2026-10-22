# slothaudit

A local, offline audit agent for trading-strategy repos. Point it at a folder;
it runs deterministic checks over the source, then a local open-weight model
(via Ollama) writes the morning summary: what to fix first, in plain language.

Nothing leaves the machine. No API key, no upload, no account.

## Why

Most backtest bugs are boring and repetitive: a fill taken on the signal bar, a
ledger that never mentions fees, one market event counted as eleven samples, a
drawdown that resets its own peak. You find them when you already suspect them —
which is exactly when you don't need help.

slothaudit runs those checks every night instead of when you remember.

## Install

    pip install -e .
    ollama pull qwen2.5-coder:7b

## Run

    slothaudit audit samples/broken_lookahead

Writes report.md and exits 1 if any high-severity finding fired. `--no-llm`
runs the deterministic checks only (instant, useful in CI).

## Checks (v0)

| id | what it looks for | severity |
|---|---|---|
| LA-01 | signal and fill read the same bar | high |
| CO-01 | trades simulated with no fee/slippage term | high |
| SI-01 | entries without a cooldown (one event, many samples) | medium |
| MD-01 | drawdown computed from a reset peak | medium |
| NA-01 | NaN coerced to 0 by `where(x > 0, 0)` | medium |

These are heuristics over source, not proofs. A finding means "read this line",
not "this is wrong" — the report says so, every time.
