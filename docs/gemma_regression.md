# Gemma 2B vs Qwen 1.5B regression on samples/broken_lookahead
Date: 2026-10-22 22:24 +08. Model: models/gemma-2-2b-it-Q4_K_M.gguf, 1,708,582,752 bytes, magic GGUF verified. llama.cpp b11804, CPU only.

## Per-check verdicts (--compare, same prompt)
| id | Qwen 1.5B | Gemma 2B |
|---|---|---|
| CO-01 no fee/slippage | YES | NO |
| LA-01 fill on signal bar | YES | YES |
| SI-01 no cooldown | YES | YES |
| MD-01 peak reset in DD loop | YES | YES |
Agreement 3/4. Compare run: 154s for 8 calls.

## Timing (one finding per call, model reloaded each call)
| model | CO-01 | LA-01 | SI-01 | MD-01 | total | avg |
|---|---|---|---|---|---|---|
| Gemma 2B | 19.7s | 19.2s | 17.6s | 18.2s | 74.7s | 18.7s |
| Qwen 1.5B | 13.6s | 12.5s | 10.6s | 10.8s | 47.5s | 11.9s |
Gemma ~57% slower per finding on this machine.

## Notes
- Gemma MD-01 answered YES while its sentence said the peak is never reset: internally contradictory.
- Gemma CO-01 returned no reason sentence after the verdict.
- CO-01 question is polarity-flipped versus the other three (YES there means a fee exists, i.e. the finding is false). Worth fixing in cli.QUESTIONS.
- Scope: one sample repo, four findings, CPU-only WSL2. Not a general model ranking.
