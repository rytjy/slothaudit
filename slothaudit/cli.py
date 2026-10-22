import argparse
import datetime
import sys

from . import checks, llm

PROMPT = """You are writing the morning summary of a code audit for a trading-strategy repo. A static checker produced the findings below. Do not invent findings, files, or line numbers.

FINDINGS (location is exact, copy it verbatim)
{findings}

CODE EXCERPTS
{excerpts}

Reply in exactly this shape, plain text, under 90 words:

FIX FIRST: <location copied verbatim from FINDINGS> — <one-line fix> — <the concrete dollar or sample-size consequence>
ALSO: <up to two lines, each starting with a location verbatim>
(Do not write a blind-spot sentence; the tool adds its own.)

No preamble. No praise. No headings. Never write "File:" or "line:" separately."""


def _excerpts(findings, width=6):
    out, seen = [], set()
    for f in findings[:3]:
        p = f["path"]
        if p in seen:
            continue
        seen.add(p)
        try:
            lines = open(p, encoding="utf-8", errors="ignore").read().splitlines()
        except OSError:
            continue
        a = max(0, f["line"] - 1 - width // 2)
        chunk = lines[a:a + width]
        out.append("%s:%d\n%s" % (p, a + 1, "\n".join("    " + l for l in chunk)))
    return "\n\n".join(out) or "(none)"


def render(repo, findings, summary):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = ["# slothaudit report — %s" % repo, "", "Generated %s, offline." % now, "",
           "## Morning summary", "", summary or "(deterministic findings only — no model available)", "",
           "## Findings", ""]
    if not findings:
        out.append("None of the v0 checks fired. That is not a clean bill of health.")
    for f in findings:
        out += ["### %s [%s] %s" % (f["id"], f["severity"], f["title"]), "",
                "%s:%d" % (f["path"], f["line"]), "", f["detail"], ""]
    out += ["", "Blind spot: this tool does not run the strategy, does not see your data, and cannot tell you the edge is real.", "", "---", "",
            "These are source heuristics. A finding means read this line, not this is wrong.",
            "The checker does not run the strategy, does not see the data, and cannot tell you the edge is real."]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="slothaudit")
    ap.add_argument("command", choices=["audit"])
    ap.add_argument("repo")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--model", default="qwen2.5-coder:7b")
    ap.add_argument("-o", "--out", default="report.md")
    args = ap.parse_args(argv)

    findings = checks.summarize(checks.scan(args.repo))
    summary = ""
    if not findings:
        summary = "No v0 check fired. That is not the same as clean: it means this run had nothing to point at, not that the strategy survives an audit."
    elif not args.no_llm:
        if llm.available(args.model):
            fl = "\n".join("- %s [%s] %s:%d %s" % (f["id"], f["severity"], f["path"], f["line"], f["title"]) for f in findings) or "(none)"
            try:
                summary = llm.chat(PROMPT.format(findings=fl, excerpts=_excerpts(findings)), model=args.model)
            except Exception as exc:
                summary = "(model call failed: %s)" % str(exc)[-160:]
        else:
            summary = "(model %s not available — run: ollama pull %s)" % (args.model, args.model)

    text = render(args.repo, findings, summary)
    open(args.out, "w", encoding="utf-8").write(text)
    print(text)
    print("\nwrote %s" % args.out)
    return 1 if any(f["severity"] == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
