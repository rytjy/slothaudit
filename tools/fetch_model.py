"""Resumable multi-connection downloader for a single file."""
import os
import sys
import threading
import time
import urllib.request

URL = sys.argv[1]
OUT = sys.argv[2]
TOTAL = int(sys.argv[3])
PARTS = int(sys.argv[4]) if len(sys.argv) > 4 else 16
CHUNK = TOTAL // PARTS + 1

os.makedirs(OUT + ".parts", exist_ok=True)


def fetch(idx):
    start = idx * CHUNK
    end = min(TOTAL, start + CHUNK) - 1
    path = os.path.join(OUT + ".parts", "%03d" % idx)
    have = os.path.getsize(path) if os.path.exists(path) else 0
    if have > end - start:
        return
    pos = start + have
    for attempt in range(40):
        try:
            req = urllib.request.Request(URL, headers={"Range": "bytes=%d-%d" % (pos, end)})
            with urllib.request.urlopen(req, timeout=60) as r, open(path, "ab") as f:
                while pos <= end:
                    b = r.read(65536)
                    if not b:
                        break
                    f.write(b)
                    pos += len(b)
            if pos > end:
                return
        except Exception as e:
            time.sleep(2 + attempt)
            have = os.path.getsize(path) if os.path.exists(path) else 0
            pos = start + have


def reporter():
    while True:
        time.sleep(30)
        got = sum(os.path.getsize(os.path.join(OUT + ".parts", p)) for p in os.listdir(OUT + ".parts"))
        print("%.1f%% %.1f MB" % (100.0 * got / TOTAL, got / 1e6), flush=True)


threads = [threading.Thread(target=fetch, args=(i,), daemon=True) for i in range(PARTS)]
threading.Thread(target=reporter, daemon=True).start()
for t in threads:
    t.start()
for t in threads:
    t.join()

with open(OUT, "wb") as out:
    for i in range(PARTS):
        p = os.path.join(OUT + ".parts", "%03d" % i)
        with open(p, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    break
                out.write(b)
print("done", os.path.getsize(OUT), flush=True)
