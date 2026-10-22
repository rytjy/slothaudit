import time
from slothaudit import checks, llm, cli

findings = checks.summarize(checks.scan("samples/broken_lookahead"))
for f in findings:
    f["question"] = cli.QUESTIONS.get(f["id"], "Does the code do what the finding says?")
print("findings:", [f["id"] for f in findings], flush=True)
for m in ("gemma", "qwen"):
    print("MODEL %s available=%s" % (m, llm.available(m)), flush=True)
    for f in findings[:4]:
        t0 = time.time()
        try:
            ans = llm.chat(cli.PROMPT.format(question=f["question"], excerpts=cli._excerpts([f])), model=m)
            v, why = cli._verdict(ans)
        except Exception as exc:
            v, why = "ERROR", str(exc)[:160]
        dt = time.time() - t0
        print("RESULT %s %s %s %.1fs %s" % (m, f["id"], v, dt, " ".join(why.split())[:160]), flush=True)
