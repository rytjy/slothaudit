import os, sys, time, urllib.request, concurrent.futures as cf, threading

TOTAL = 1708582752
PARTS = 16
CHUNK = (TOTAL + PARTS - 1) // PARTS
URL = "https://hf-mirror.com/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf"
BASE = "/root/slothaudit/models/gemma-2-2b-it-Q4_K_M.gguf"
PARTS_DIR = BASE + ".parts"
RES = os.path.join(PARTS_DIR, ".res")
os.makedirs(RES, exist_ok=True)
lock = threading.Lock()
done_bytes = 0

def fetch_range(start, end, path):
    have = os.path.getsize(path) if os.path.exists(path) else 0
    if have >= end - start + 1:
        return 0
    s = start + have
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, headers={"Range": "bytes=%d-%d" % (s, end), "User-Agent": "slothaudit-resume"})
            with urllib.request.urlopen(req, timeout=40) as r:
                if r.status != 206:
                    raise RuntimeError("status %s" % r.status)
                with open(path, "ab") as f:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        f.write(b)
                        global done_bytes
                        with lock:
                            done_bytes += len(b)
            return 0
        except Exception as e:
            if attempt == 3:
                print("FAIL", path, e, flush=True)
                return -1
            time.sleep(2)

jobs = []
for i in range(PARTS):
    base = i * CHUNK
    end = min(TOTAL, base + CHUNK) - 1
    p = os.path.join(PARTS_DIR, "%03d" % i)
    have = os.path.getsize(p)
    start = base + have
    if start > end:
        continue
    # 2 MiB sub-ranges, so the remaining tail runs on many connections
    step = 2 << 20
    s = start
    while s <= end:
        e = min(end, s + step - 1)
        jobs.append((s, e, os.path.join(RES, "%03d_%d" % (i, s - base))))
        s = e + 1

print("jobs", len(jobs), flush=True)
remaining = sum(e - s + 1 for s, e, _ in jobs)
print("remaining bytes", remaining, flush=True)
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=48) as ex:
    futs = [ex.submit(fetch_range, s, e, p) for s, e, p in jobs]
    while any(not f.done() for f in futs):
        time.sleep(10)
        with lock:
            got = done_bytes
        el = max(1e-9, time.time() - t0)
        print("got %.1f/%.1f MiB  %.2f MiB/min" % (got / 1048576, remaining / 1048576, got / 1048576 / (el / 60)), flush=True)
    fails = sum(f.result() for f in futs)
print("fails", fails, flush=True)

# append sub-ranges back into each part, in order
for i in range(PARTS):
    p = os.path.join(PARTS_DIR, "%03d" % i)
    subs = sorted([x for x in os.listdir(RES) if x.startswith("%03d_" % i)], key=lambda x: int(x.split("_")[1]))
    with open(p, "ab") as out:
        for x in subs:
            q = os.path.join(RES, x)
            with open(q, "rb") as f:
                while True:
                    b = f.read(1 << 20)
                    if not b:
                        break
                    out.write(b)
            os.remove(q)
print("parts appended", flush=True)

with open(BASE, "wb") as out:
    for i in range(PARTS):
        p = os.path.join(PARTS_DIR, "%03d" % i)
        with open(p, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    break
                out.write(b)

size = os.path.getsize(BASE)
magic = open(BASE, "rb").read(4)
print("merged", size, magic, "OK" if size == TOTAL and magic == b"GGUF" else "BAD", flush=True)
