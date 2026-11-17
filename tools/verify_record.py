"""Check a Bradbury live-run record against the chain.

    python tools/verify_record.py examples/live/bradbury-<tag>.json

For every recorded transaction: fetch it from Bradbury and compare its
consensus result, execution result and sender with the record. For every
covenant test: check that the outcome recorded for it is the attempt the
facility stored at that transaction's time (or that nothing was stored, for
a refused repeat or a round where the validators disagreed). Reads only.
Exit code 1 on any mismatch.
"""
import atexit
import json
import os
import secrets
import subprocess
import sys
import tempfile

def _throwaway_key():
    fd, path = tempfile.mkstemp(suffix=".key")
    os.write(fd, ("0x" + secrets.token_hex(32)).encode())
    os.close(fd)
    atexit.register(os.remove, path)
    return path


JS = os.environ.get("BRADBURY_JS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "bradbury"))
# Reads need an account object but sign nothing. Without BRADBURY_READ_KEY a throwaway key is made
# for this run and deleted afterwards (run `npm ci` in tools/bradbury first).
KEY = os.environ.get("BRADBURY_READ_KEY") or _throwaway_key()
NOTHING_STORED = ("UNDETERMINED", "LEADER_TIMEOUT", "VALIDATORS_TIMEOUT", "CANCELED")


def node(*a):
    p = subprocess.run(["node", "gl.mjs", *a], cwd=JS, capture_output=True, text=True, timeout=300,
                       env={**os.environ, "BRADBURY_KEY_FILE": KEY})
    return json.loads([ln for ln in p.stdout.splitlines() if ln.startswith("{")][-1])


def main():
    rec = json.load(open(sys.argv[1]))
    addr, bad, n = rec["address"], [], 0
    for slug, c in rec["cases"].items():
        if slug == "withdrawals":
            continue
        f = node("read", addr, "get_facility", json.dumps([str(c["id"]), 0]))["result"]
        for s in c["steps"]:
            if not s.get("tx"):
                continue
            n += 1
            raw = node("tx", s["tx"])["raw"]
            got = (raw.get("resultName"), raw.get("txExecutionResultName"), str(raw.get("sender", "")).lower())
            want = (s.get("status"), s.get("execution"), str(s.get("from", "")).lower())
            if s.get("status") in NOTHING_STORED and got[0] != "MAJORITY_AGREE" and got[2] == want[2]:
                pass  # recorded while undetermined or timed out; nothing was stored either way
            elif got != want:
                bad.append(f"{slug} {s['label']} {s['tx']}: chain {got}, record {want}")
            if s["fn"] == "test_period":
                p = f["periods"][s["result"]["period"]]
                stored = [a for a in p["attempts"] if a["at"] == int(raw.get("createdTimestamp", 0))]
                kind = s["result"].get("kind")
                if kind and not any(a["kind"] == kind for a in stored):
                    bad.append(f"{slug} {s['label']} {s['tx']}: recorded {kind}, stored {stored}")
                if not kind and stored and got[0] == "MAJORITY_AGREE" and got[1] == "FINISHED_WITH_RETURN":
                    bad.append(f"{slug} {s['label']} {s['tx']}: recorded nothing, stored {stored}")
    for w in rec["cases"].get("withdrawals", []):
        if "tx" in w:
            n += 1
            raw = node("tx", w["tx"])["raw"]
            if w["status"] in NOTHING_STORED and raw.get("resultName") != "MAJORITY_AGREE":
                continue
            if (raw.get("resultName"), raw.get("txExecutionResultName")) != (w["status"], w["execution"]):
                bad.append(f"withdraw {w['role']} {w['tx']}: chain {raw.get('resultName')}/{raw.get('txExecutionResultName')}")
    print(f"{n} transactions checked against the chain; {len(bad)} mismatches")
    for b in bad:
        print("  " + b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
