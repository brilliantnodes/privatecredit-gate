"""Write a live run's facilities and transactions into the site config.

    python tools/fill_config.py studio studio-2 0x...      # contract address
    python tools/fill_config.py bradbury bradbury-2 0x...

Reads examples/live/<net>-<tag>.json and sets that network's contract,
example facilities, per-facility transactions and (Bradbury) withdrawals in
web/src/config.js.

Every covenant test is labelled with what it did. On Bradbury the label comes
from the chain's own outcome as recorded by the runner (consensus result and
execution result): a round where the validators disagreed stores nothing; a
test refused because the period already had its official reading is a
repeat sent after an early receipt.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "web/src/config.js"


def label_for(s, read_periods):
    label = s["label"]
    if s["fn"] != "test_period":
        return label
    res = s.get("result") or {}
    n = res.get("period")
    if s.get("status") in ("MAJORITY_DISAGREE", "UNDETERMINED", "NO_MAJORITY", "DISAGREE"):
        return label + " (validators disagreed: nothing stored, tested again)"
    if s.get("status") in ("LEADER_TIMEOUT", "VALIDATORS_TIMEOUT", "CANCELED", "MAJORITY_TIMEOUT", "TIMEOUT"):
        return label + f" ({s['status'].lower().replace('_', ' ')}: nothing stored, tested again)"
    if s.get("execution") == "FINISHED_WITH_ERROR" or res.get("reverted"):
        return label + (" (repeat, refused: already read)" if n in read_periods else " (refused)")
    kind, reason = res.get("kind"), res.get("reason") or ""
    if not kind:
        raise SystemExit(f"{label} {s['tx']}: no outcome recorded; check by hand")
    if kind == "READ":
        read_periods.add(n)
    return f"{label}: {kind}" + (f" {reason}" if reason else "")


def main():
    net, tag, contract = sys.argv[1], sys.argv[2], sys.argv[3]
    run = json.loads((ROOT / f"examples/live/{net}-{tag}.json").read_text())
    if run["address"].lower() != contract.lower():
        raise SystemExit(f"the record is for {run['address']}, not {contract}")
    txs, examples, withdrawals = {}, [], []
    for slug, c in run["cases"].items():
        if slug == "withdrawals":
            withdrawals = [[f"Withdraw credits ({w['role']}): {int(w['credited']) / 1e18:.6f} GEN", w["tx"]] for w in c if "tx" in w]
            continue
        fid = str(c["id"])
        examples.append({"id": fid, "slug": slug, "company": c["company"]})
        rows, read_periods = [], set()
        for s in c["steps"]:
            if s.get("tx"):
                rows.append([label_for(s, read_periods), s["tx"]])
        txs[fid] = rows
    src = CFG.read_text()
    start = src.index(f"  {net}: {{")
    end = src.index("\n  },", start)
    block = src[start:end]
    block = re.sub(r'contract: "[^"]*"', f'contract: "{contract}"', block)
    ex = "examples: [\n" + "".join(
        f'      {{ id: "{e["id"]}", slug: "{e["slug"]}", company: "{e["company"]}" }},\n' for e in examples) + "    ],"
    block = re.sub(r"examples: \[.*?\],", ex, block, flags=re.S)
    block = re.sub(r"    txs: \{.*?\},", "    txs: " + json.dumps(txs, indent=2).replace("\n", "\n    ") + ",", block, flags=re.S)
    if "withdrawals:" in block:
        block = re.sub(r"    withdrawals: \[.*?\],", "    withdrawals: " + json.dumps(withdrawals) + ",", block, flags=re.S)
    else:
        block = block.replace("    txs: ", "    withdrawals: " + json.dumps(withdrawals) + ",\n    txs: ", 1)
    CFG.write_text(src[:start] + block + src[end:])
    print(f"{net}: {len(examples)} facilities, {sum(len(v) for v in txs.values())} transactions, {len(withdrawals)} withdrawals")


if __name__ == "__main__":
    main()
