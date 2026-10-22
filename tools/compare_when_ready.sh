#!/usr/bin/env bash
# Wait for the merged Gemma GGUF, then run the two-model comparison on both samples.
set -u
cd /root/slothaudit
GGUF=models/gemma-2-2b-it-Q4_K_M.gguf
TOTAL=1708582752
for i in $(seq 1 240); do
  if [ -f "$GGUF" ] && [ "$(stat -c%s "$GGUF" 2>/dev/null)" = "$TOTAL" ]; then
    break
  fi
  sleep 15
done
if [ ! -f "$GGUF" ] || [ "$(stat -c%s "$GGUF" 2>/dev/null)" != "$TOTAL" ]; then
  echo "TIMEOUT at $(date -Is)" > docs/compare_status.txt
  exit 1
fi
sleep 3
head -c 4 "$GGUF" > /tmp/gguf_magic
echo "gguf size=$(stat -c%s "$GGUF") magic=$(cat /tmp/gguf_magic)" > docs/compare_status.txt
python3 -m slothaudit.cli audit samples/broken_lookahead --compare -o docs/compare_report.md > /tmp/compare_broken.log 2>&1
echo "broken rc=$? at $(date -Is)" >> docs/compare_status.txt
python3 -m slothaudit.cli audit samples/clean_strategy --compare -o docs/compare_clean.md > /tmp/compare_clean.log 2>&1
echo "clean rc=$? at $(date -Is)" >> docs/compare_status.txt
echo DONE >> docs/compare_status.txt
