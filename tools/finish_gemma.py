import os, urllib.request, concurrent.futures as cf, time
TOTAL = 1708582752
PARTS = 16
CHUNK = TOTAL // PARTS + 1
URL = "https://hf-mirror.com/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf"
BASE = "/root/slothaudit/models/gemma-2-2b-it-Q4_K_M.gguf"
PD = BASE + ".parts"
TMP = os.path.join(PD, ".fin")
os.makedirs(TMP, exist_ok=True)
jobs = []
for i in (11, 12):
    start = i * CHUNK
    end = min(TOTAL, start + CHUNK) - 1
    p = os.path.join(PD, "%03d" % i)
    have = os.path.getsize(p)
    s = start + have
    while s <= end:
        e = min(end, s + (256 << 10) - 1)
        jobs.append((i, s, e))
        s = e + 1
print("jobs", len(jobs), "bytes", sum(e - s + 1 for _, s, e in jobs), flush=True)

def fetch(job):
    i, s, e = job
    path = os.path.join(TMP, "%03d_%d" % (i, s))
    if os.path.exists(path) and os.path.getsize(path) == e - s + 1:
        return 0
    for a in range(4):
        try:
            req = urllib.request.Request(URL, headers={"Range": "bytes=%d-%d" % (s, e), "User-Agent": "x"})
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status != 206:
                    raise RuntimeError(r.status)
                data = r.read()
            if len(data) != e - s + 1:
                raise RuntimeError("short %d" % len(data))
            open(path, "wb").write(data)
            return 0
        except Exception as ex:
            if a == 3:
                print("FAIL", i, s, ex, flush=True)
                return -1
            time.sleep(1)

with cf.ThreadPoolExecutor(max_workers=24) as ex:
    fails = sum(ex.map(fetch, jobs))
print("fails", fails, flush=True)
for i in (11, 12):
    p = os.path.join(PD, "%03d" % i)
    starts = sorted(s for (ii, s, e) in jobs if ii == i)
    with open(p, "ab") as out:
        for s in starts:
            q = os.path.join(TMP, "%03d_%d" % (i, s))
            out.write(open(q, "rb").read())
            os.remove(q)
print("parts done", flush=True)
with open(BASE, "wb") as out:
    for i in range(PARTS):
        with open(os.path.join(PD, "%03d" % i), "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    break
                out.write(b)
size = os.path.getsize(BASE)
magic = open(BASE, "rb").read(4)
print("merged", size, magic, "OK" if size == TOTAL and magic == b"GGUF" else "BAD", flush=True)
