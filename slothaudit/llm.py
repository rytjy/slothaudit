"""Thin local-model client: llama.cpp first, Ollama only as a fallback. Localhost only."""
import glob
import json
import os
import subprocess
import urllib.request

HOST = "http://127.0.0.1:11434"
LLAMA_CLI = "/root/slothaudit/bin/llama/llama-b11804/llama-cli"
LLAMA_LIB = "/root/slothaudit/bin/llama/llama-b11804"
GGUF_DIR = "/root/slothaudit/models"

ALIASES = {
    "qwen": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    "qwen1.5b": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    "qwen2.5-coder-1.5b": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    "gemma": "gemma-2-2b-it-Q4_K_M.gguf",
    "gemma2b": "gemma-2-2b-it-Q4_K_M.gguf",
    "gemma-2-2b": "gemma-2-2b-it-Q4_K_M.gguf",
}


def resolve_gguf(model):
    """Map a short name to a local GGUF path, or None when that model is not on disk."""
    if model and model.endswith(".gguf"):
        return model if os.path.exists(model) else None
    key = (model or "").split(":")[0].lower()
    for alias, name in ALIASES.items():
        if key == alias:
            path = os.path.join(GGUF_DIR, name)
            if os.path.exists(path) and os.path.getsize(path) > 100 << 20:
                return path
            return None
    env = os.environ.get("SLOTHAUDIT_GGUF")
    if env and os.path.exists(env):
        return env
    files = sorted(p for p in glob.glob(os.path.join(GGUF_DIR, "*.gguf")) if os.path.getsize(p) > 100 << 20)
    return files[0] if files else None


def available(model="qwen"):
    if resolve_gguf(model) and os.path.exists(LLAMA_CLI):
        return True
    base = (model or "").split(":")[0]
    try:
        with urllib.request.urlopen(HOST + "/api/tags", timeout=3) as f:
            tags = json.load(f)
        return any(m.get("name", "").startswith(base) for m in tags.get("models", []))
    except Exception:
        return False


def _chat_llamacpp(prompt, gguf, timeout):
    env = dict(os.environ, LD_LIBRARY_PATH=LLAMA_LIB)
    cmd = [LLAMA_CLI, "-m", gguf, "-p", prompt, "-n", "600", "--temp", "0.2",
           "--no-display-prompt", "-st", "--no-show-timings"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if p.returncode != 0 and ("unknown argument" in p.stderr or "invalid argument" in p.stderr):
        cmd = [LLAMA_CLI, "-m", gguf, "-p", prompt, "-n", "600", "--temp", "0.2", "--no-display-prompt", "-st"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[-400:])
    lines = p.stdout.splitlines()
    cut = None
    for i, line in enumerate(lines):
        if line.strip().startswith(">"):
            cut = i
    if cut is not None:
        lines = lines[cut + 1:]
    keep = []
    for line in lines:
        s = line.strip()
        if not s or s == "Exiting..." or s.startswith("[ Prompt:"):
            continue
        keep.append(line.rstrip())
    plines = {l.strip() for l in prompt.splitlines() if l.strip()}
    k = 0
    while k < len(keep) and (keep[k].strip() in plines or keep[k].strip().endswith("(truncated)")):
        k += 1
    keep = keep[k:]
    out = "\n".join(keep).strip()
    probe = prompt.strip()[-60:]
    if probe and probe in out:
        out = out.split(probe, 1)[-1].strip()
    if prompt[:40] in out:
        out = out.split(prompt[:40], 1)[1].strip()
    return out


def chat(prompt, model="qwen", timeout=900):
    gguf = resolve_gguf(model)
    if gguf:
        return _chat_llamacpp(prompt, gguf, timeout)
    body = json.dumps({"model": model, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.2, "num_predict": 600}}).encode()
    req = urllib.request.Request(HOST + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return json.load(f).get("response", "").strip()
