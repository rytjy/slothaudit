#!/usr/bin/env bash
set -u
cd /root/slothaudit || exit 1
GGUF=models/gemma-2-2b-it-Q4_K_M.gguf
TOTAL=1708582752
STATUS=docs/gemma_regression_status.txt
: > "$STATUS"
echo "start $(date -Is)" >> "$STATUS"
for i in $(seq 1 1200); do
  s=$(stat -c%s "$GGUF" 2>/dev/null || echo 0)
  if [ "$s" = "$TOTAL" ]; then break; fi
  sleep 5
done
s=$(stat -c%s "$GGUF" 2>/dev/null || echo 0)
if [ "$s" != "$TOTAL" ]; then
  echo "TIMEOUT waiting model size=$s at $(date -Is)" >> "$STATUS"; exit 1
fi
sleep 2
echo "model size=$s magic=$(head -c 4 "$GGUF" | od -An -c | tr -d ' \n') at $(date -Is)" >> "$STATUS"
t0=$(date +%s)
PYTHONPATH=. python3 tools/time_models.py > docs/timing.txt 2>&1
echo "timing rc=$? elapsed=$(( $(date +%s) - t0 ))s at $(date -Is)" >> "$STATUS"
t0=$(date +%s)
python3 -m slothaudit.cli audit samples/broken_lookahead --compare -o docs/compare_report.md > /tmp/compare_broken.log 2>&1
echo "compare rc=$? elapsed=$(( $(date +%s) - t0 ))s at $(date -Is)" >> "$STATUS"
t0=$(date +%s)
python3 -m slothaudit.cli audit samples/clean_strategy --compare -o docs/compare_clean.md > /tmp/compare_clean.log 2>&1
echo "compare_clean rc=$? elapsed=$(( $(date +%s) - t0 ))s at $(date -Is)" >> "$STATUS"
echo "DONE at $(date -Is)" >> "$STATUS"
