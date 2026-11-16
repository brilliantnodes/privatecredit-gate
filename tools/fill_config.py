"""Write the live runs' transactions into the site config.

    python tools/fill_config.py studio studio-1
    python tools/fill_config.py bradbury bradbury-1 0x4170...

Reads examples/live/<net>-<tag>.json and fills that network's `txs` (and, for
Bradbury, its contract and example facilities) in web/src/config.js.

On Bradbury a receipt can come back before the result is applied; the runner
then tested again. Each Bradbury test is labelled from its outcome on chain: a
repeat refused because the period already had its official reading, or a round
where the validators disagreed and nothing was stored.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "web/src/config.js"


def execution(h):
    """The execution result of a Bradbury transaction, from the chain."""
    p = subprocess.run(["node", "gl2.mjs", "tx", h], cwd="/home/claude/bradbury/js2", capture_output=True, text=True, timeout=120,
                       env={**os.environ, "BRADBURY_KEY_FILE": "/home/claude/keys/bradbury_mr.key"})
    raw = json.loads(p.stdout.strip().splitlines()[-1])["raw"]
    return raw.get("resultName"), raw.get("txExecutionResultName")


def main():
    net, tag = sys.argv[1], sys.argv[2]
    run = json.loads((ROOT / f"examples/live/{net}-{tag}.json").read_text())
    txs, examples = {}, []
    for slug, c in run["cases"].items():
        if not isinstance(c, dict) or "fid" not in c and not c.get("steps"):
            continue
        fid = str(c.get("fid") or next(s["result"]["id"] for s in c["steps"] if s["fn"] == "create" and s["result"].get("ok")))
        examples.append({"id": fid, "slug": slug, "company": c["company"]})
        rows, seen = [], set()
        steps = c["steps"]
        for i, s in enumerate(steps):
            if not s.get("tx"):
                continue
            label = s["label"]
            if s["fn"] == "test_period":
                # the outcome this test stored; on Bradbury an early receipt
                # leaves it to the next read-back of the same period
                kind = (s["result"] or {}).get("kind") or next(
                    (x["result"].get("kind") for x in steps[i + 1:] if x["label"] == label and x["result"].get("kind")), None)
                reason = (s["result"] or {}).get("reason") or ""
                outcome = f": {kind}" + (f" {reason}" if reason else "") if kind else ""
            if net == "bradbury" and s["fn"] == "test_period":
                result, ex = execution(s["tx"])
                if result == "MAJORITY_DISAGREE":
                    label += " (validators disagreed: nothing stored, tested again)"
                elif ex == "FINISHED_WITH_ERROR":
                    if label not in seen:
                        raise SystemExit(f"{slug}: first test {s['tx']} was refused; check by hand")
                    label += " (repeat, refused: already read)"
                elif s["fn"] == "test_period":
                    label += outcome
            elif s["fn"] == "test_period":
                label += outcome
            seen.add(s["label"])
            rows.append([label, s["tx"]])
        # a refused offer or accept belongs to the facility that follows
        txs[fid] = rows
    src = CFG.read_text()
    start = src.index(f"  {net}: {{")
    end = src.index("\n  },", start)
    block = src[start:end]
    block = re.sub(r"    txs: \{.*?\},", "    txs: " + json.dumps(txs, indent=2).replace("\n", "\n    ") + ",", block, flags=re.S)
    if net == "bradbury":
        block = re.sub(r'contract: "[^"]*"', f'contract: "{sys.argv[3]}"', block)
        ex = "examples: [\n" + "".join(
            f'      {{ id: "{e["id"]}", slug: "{e["slug"]}", company: "{e["company"]}" }},\n' for e in examples) + "    ],"
        block = re.sub(r"examples: \[.*?\],", ex, block, flags=re.S)
    CFG.write_text(src[:start] + block + src[end:])
    print(f"{net}: {len(examples)} facilities, {sum(len(v) for v in txs.values())} transactions")


if __name__ == "__main__":
    main()
