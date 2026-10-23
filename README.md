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
    slothaudit audit samples/broken_lookahead      # ~50s on a laptop CPU (4 model checks)
    slothaudit audit samples/broken_lookahead --compare   # both models, one report

`--no-llm` runs the deterministic checks only (instant).

Models: `--model qwen` (Qwen2.5-Coder-1.5B-Instruct Q4_K_M) or
`--model gemma` (Gemma 2 2B IT Q4_K_M), both loaded with llama.cpp build
b11804. Any other GGUF works via `--model /path/model.gguf` or
`SLOTHAUDIT_GGUF`. An Ollama server on `127.0.0.1:11434` is used only when
the named model is not on disk.

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
- **Two models are a confidence signal, not a vote.** `--compare` asks the same
  question of Qwen 1.5B and Gemma 2B independently and prints both answers.
  Agreement means neither model disputed the checker; disagreement means the
  finding is worth reading yourself. There is no ground truth in the report —
  only who said what.

  On the bundled broken sample, two runs of the same audit gave **3 of 4** and
  then **4 of 4** agreement. The code changed between them (the context window
  moved to the evidence line), so the difference is not clean sampling variance
  — and asking Gemma the cost question again in isolation returned NO in both
  variants. At 2B the verdict is **not a stable measurement**, which is why the
  report leads with the checker's evidence line and treats agreement as a hint.
  Both runs are committed: [2026-10-22](docs/compare_report_1022.md) and
  [2026-10-23](docs/compare_report.md).
- **Every finding prints its own evidence line.** The checker already knows which
  source line it matched, so the report shows that line verbatim under
  `Evidence:` — the model's prose is never the reason to read a finding. For
  absence checks (no fee term, no cooldown) it prints the ledger line and the
  number of lines searched instead of pretending there is a match.
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
