#!/usr/bin/env bash
# A 40-second demo: one broken repo, one clean repo, both offline.
set -u
cd "$(dirname "$0")"

echo "→ broken repo: no cost term, fill on the signal bar"
echo "$ slothaudit audit samples/broken_lookahead"
python3 -m slothaudit.cli audit samples/broken_lookahead -o /tmp/demo-broken.md | sed -n '1,16p'
echo
echo "→ clean repo: fees, next-bar fill, 24-bar cooldown"
echo "$ slothaudit audit samples/clean_strategy"
python3 -m slothaudit.cli audit samples/clean_strategy -o /tmp/demo-clean.md | sed -n '5,9p'
echo
echo "→ both runs: 1.1G GGUF, llama.cpp b11804, no network, ~13s each"
