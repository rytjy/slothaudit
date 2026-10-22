import argparse
import datetime
import sys

from . import checks, llm

PROMPT = """You check one finding against real code. Answer about THIS code, never restate the template.

Worked example (different code):
QUESTION: Does the fill price come from a later bar than the signal?
CODE: for i in range(n): sig = close[i]; entry = close[i]
ANSWER: NO — the signal and the fill both read index i, so the fill is not later.

Now the real one:
QUESTION: {question}
CODE
{excerpts}

Answer on one line: yes, no, or unsure; then a dash; then one short sentence about this code. Start with the word."""


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


QUESTIONS = {
    "LA-01": "Is the fill price taken from the same bar that produced the signal, or from a later bar?",
    "CO-01": "Does the code charge any fee, commission, slippage or spread anywhere?",
    "SI-01": "Can two consecutive bars both open a position, with no cooldown between them?",
    "MD-01": "Is the running peak ever reset to something other than the highest equity seen so far?",
    "NA-01": "Does this expression turn NaN into 0 instead of keeping it as NaN?",
}


def _verdict(ans):
    text = " ".join(ans.split())
    low = text.lower()
    v = "UNSURE"
    for word in ("yes", "no", "unsure"):
        if low.startswith(word):
            v = word.upper()
            break
    for sep in ("—", "-", ":"):
        if sep in text:
            text = text.split(sep, 1)[1].strip()
            break
    else:
        text = ""
    why = text.strip()[:200]
    if why.lower().startswith(v.lower()):
        why = why[len(v):].lstrip(" -—:")
    return v, why


def headline(findings):
    if not findings:
        return ""
    lines = ["FIX FIRST: %s:%d — %s" % (findings[0]["path"], findings[0]["line"], findings[0]["title"])]
    for f in findings[1:3]:
        lines.append("ALSO: %s:%d — %s" % (f["path"], f["line"], f["title"]))
    return "\n".join(lines)


def render(repo, findings, summary):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    out = ["# slothaudit report — %s" % repo, "", "Generated %s, offline." % now, "",
           "## Morning summary", ""]
    head = headline(findings)
    if head:
        out += [head, ""]
    if summary:
        out += [summary, ""]
    elif not any(f.get("verdict") for f in findings):
        out += ["(deterministic findings only — no model available)", ""]
    out += ["## Findings", ""]
    if not findings:
        out.append("None of the v0 checks fired. That is not a clean bill of health.")
    for f in findings:
        out += ["### %s [%s] %s" % (f["id"], f["severity"], f["title"]), "",
                "%s:%d" % (f["path"], f["line"]), "", f["detail"]]
        if f.get("verdict"):
            why = f["verdict"][1]
            out += ["", "Model check: **%s**%s" % (f["verdict"][0], (" — " + why) if why else "")]
        out += [""]
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
    for f in findings:
        f["question"] = QUESTIONS.get(f["id"], "Does the code do what the finding says?")
    summary = ""
    if not findings:
        summary = "No v0 check fired. That is not the same as clean: it means this run had nothing to point at, not that the strategy survives an audit."
    elif not args.no_llm:
        if llm.available(args.model):
            for f in findings[:2]:
                try:
                    ans = llm.chat(PROMPT.format(question=f["question"], excerpts=_excerpts([f])), model=args.model)
                    f["verdict"] = _verdict(ans)
                except Exception as exc:
                    f["verdict"] = ("UNSURE", "model failed: %s" % str(exc)[-80:])
        else:
            summary = "(model %s not available — run: ollama pull %s)" % (args.model, args.model)

    text = render(args.repo, findings, summary)
    open(args.out, "w", encoding="utf-8").write(text)
    print(text)
    print("\nwrote %s" % args.out)
    return 1 if any(f["severity"] == "high" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
