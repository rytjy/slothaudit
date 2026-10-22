#!/usr/bin/env bash
# A 40-second demo: one broken repo, one clean repo, both offline.
set -u
cd "$(dirname "$0")"

echo "## 1. A repo whose ledger never mentions costs"
echo "   $ slothaudit audit samples/broken_lookahead"
python3 -m slothaudit.cli audit samples/broken_lookahead -o /tmp/demo-broken.md | sed -n '1,16p'
echo
echo "## 2. A repo that pays fees, waits for the next bar, and has a cooldown"
echo "   $ slothaudit audit samples/clean_strategy"
python3 -m slothaudit.cli audit samples/clean_strategy -o /tmp/demo-clean.md | sed -n '5,12p'
echo
echo "Both runs used the same local model, no network:"
echo "   $(du -h models/*.gguf | cut -f1) GGUF, llama.cpp build b11804, on a laptop CPU"
