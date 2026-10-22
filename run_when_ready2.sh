#!/bin/bash
cd /root/slothaudit || exit 1
echo "start $(date -Is)"
for i in $(seq 1 600); do
  f=$(ls models/*.gguf 2>/dev/null | head -1)
  if [ -n "$f" ]; then
    sz=$(stat -c %s "$f")
    echo "found $f size=$sz at $(date -Is)"
    if [ "$sz" -ge 1117320768 ]; then break; fi
  fi
  sleep 5
done
f=$(ls models/*.gguf 2>/dev/null | head -1)
if [ -z "$f" ]; then echo "TIMEOUT no gguf"; exit 2; fi
export SLOTHAUDIT_GGUF="$f"
t0=$(date +%s)
timeout 1800 python3 -m slothaudit.cli audit samples/broken_lookahead > /tmp/audit_run.log 2>&1
rc=$?
t1=$(date +%s)
echo "audit rc=$rc elapsed=$((t1-t0))s size=$(stat -c %s \"$f\")"
cp report.md /tmp/audit_report.md 2>/dev/null
echo "DONE $(date -Is)"

