"""Merge a continuation record into a live-run record, as a new file.

    python tools/merge_continuation.py examples/live/bradbury-bradbury-2.json \
        examples/live/bradbury-bradbury-2-brenthollow-continued.json \
        examples/live/bradbury-bradbury-2-merged.json

Used once, for Brenthollow on Bradbury: the runner recorded its period-1 test
as a leader timeout, but after leader rotation the same transaction executed
and stored the official reading. A continuation script was started for that
facility while the runner was still retrying (the two overlapped for a few
minutes); it finished the story (cure, period 2, repayment) and the runner's
thread for that facility then stopped.

This keeps both input files unchanged and writes a third file in which:
  - the timed-out step carries the chain's final status and the reading the
    facility stored for it (read from get_facility), with the status the
    runner first saw kept under recorded_status / recorded_execution;
  - the later period-1 tests stay as they were (refused repeats);
  - the continuation's steps, cure quote and final state are appended.
The final status is checked against the chain by tools/verify_record.py.
"""
import json
import sys


def main():
    main_path, cont_path, out_path = sys.argv[1:4]
    rec = json.load(open(main_path))
    cont = json.load(open(cont_path))
    if rec["address"].lower() != cont["address"].lower() or rec["tag"] != cont["tag"]:
        raise SystemExit("the two records are for different runs")
    for slug, c in cont["cases"].items():
        m = rec["cases"][slug]
        off = c["period1_official"]
        hits = [i for i, s in enumerate(m["steps"])
                if s["fn"] == "test_period" and s.get("status") == "LEADER_TIMEOUT"
                and int(s.get("created", 0)) == int(off["at"])]
        if len(hits) != 1:
            raise SystemExit(f"{slug}: expected one timed-out test created at {off['at']}, found {hits}")
        s = m["steps"][hits[0]]
        s["recorded_status"], s["recorded_execution"] = s["status"], s.get("execution")
        s["status"], s["execution"] = "MAJORITY_AGREE", "FINISHED_WITH_RETURN"
        s["result"] = {"period": 1, "kind": "READ", "ok": True, "reason": "",
                       "status": "BREACH" if not off["assessment"]["compliant"] else "ACTIVE",
                       "assessment": off["assessment"], "figures": off.get("figures"),
                       "source": "get_facility: period 1, attempt 1 (stored at this transaction's time)"}
        s["note"] = ("The runner saw a leader timeout. After leader rotation the same transaction "
                     "executed and stored the official reading. Later tests of period 1 were "
                     "refused as repeats.")
        m.pop("error", None)
        m["steps"].extend(c["steps"])
        for k in ("cure_quote", "final", "period1_official"):
            if k in c:
                m[k] = c[k]
        m["note"] = "merged with " + cont_path.split("/")[-1] + ": " + c.get("note", "")
    rec["merged_from"] = [main_path.split("/")[-1], cont_path.split("/")[-1]]
    json.dump(rec, open(out_path, "w"), indent=1)
    n = sum(len(c["steps"]) for k, c in rec["cases"].items() if k != "withdrawals")
    print(f"wrote {out_path}: {n} steps")


if __name__ == "__main__":
    main()
