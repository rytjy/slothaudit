"""Deterministic source checks. Heuristics, not proofs."""
import os
import re

FINDINGS = []


def _add(fid, sev, path, line, title, detail):
    FINDINGS.append(dict(id=fid, severity=sev, path=path, line=line,
                         title=title, detail=detail))


def _py_files(root):
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "venv", "__pycache__", "node_modules"}]
        for n in names:
            if n.endswith(".py"):
                yield os.path.join(base, n)


def check_lookahead(path, src):
    lines = src.splitlines()
    fill = re.compile(r"\[\s*[\"']?(high|low|close|open)[\"']?\s*\]\s*\[\s*i\s*\]")
    for i, l in enumerate(lines):
        if not fill.search(l):
            continue
        window = "".join(lines[max(0, i - 20):i])
        if re.search(r"for\s+i\s+in\s+range", window):
            _add("LA-01", "high", path, i + 1,
                 "fill price read on the signal bar",
                 "A fill taken at index i while the signal is computed at i too is the classic same-bar leak. Check the fill uses i+1, or the next tick.")


def check_costs(path, src):
    if not re.search(r"\b(fee|fees|commission|slippage|spread|costs?)\b", src, re.I):
        if re.search(r"\b(profit|pnl|equity|trade)\b", src, re.I):
            _add("CO-01", "high", path, 1,
                 "no fee or slippage term in the ledger",
                 "This file records PnL but never mentions fee, commission, slippage or spread. At 4.5bps a side, high turnover can be negative before any edge.")


def check_sample_inflation(path, src):
    if re.search(r"for\s+i\s+in\s+range", src) and re.search(r"signal", src, re.I):
        if not re.search(r"cooldown|cool_down|debounce|last_entry", src, re.I):
            _add("SI-01", "medium", path, 1,
                 "entries without a cooldown",
                 "Consecutive bars can each open a position, so one market event counts as many samples and n is inflated.")


def check_drawdown(path, src):
    if re.search(r"drawdown|\bmdd\b|max_dd", src, re.I) and re.search(r"peak\s*=\s*(cap|start|initial)", src):
        _add("MD-01", "medium", path, 1,
             "peak reset inside the drawdown loop",
             "Resetting peak to a cap turns the reported MDD into the local drawdown since the last reset. Report capped and raw separately.")


def check_nan(path, src):
    for i, l in enumerate(src.splitlines()):
        if re.search(r"\.where\(\s*[^,]+>\s*0\s*,\s*0(\.0)?\s*\)", l):
            _add("NA-01", "medium", path, i + 1,
                 "NaN coerced to 0 by where(x > 0, 0)",
                 "NaN > 0 is False, so NaN silently becomes 0 here. clip(lower=0) keeps NaN as NaN.")


CHECKS = [check_lookahead, check_costs, check_sample_inflation, check_drawdown, check_nan]


def scan(root):
    FINDINGS.clear()
    for p in sorted(_py_files(root)):
        try:
            src = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for fn in CHECKS:
            fn(p, src)
    seen, out = set(), []
    for f in FINDINGS:
        key = (f["id"], f["path"])
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def summarize(findings):
    order = {"high": 0, "medium": 1, "low": 2}
    return sorted(findings, key=lambda f: (order.get(f["severity"], 9), f["path"], f["line"]))
