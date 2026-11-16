#!/usr/bin/env python3
"""Run the five fictional borrowers live against a deployed PrivateCreditGate.

Every company and figure is fictional; only test GEN moves. Each case uses a
fresh throwaway lender and borrower funded from Studio's faucet. All five
facilities share one schedule, so they run side by side:

  period 0 ends at E0, period 1 at E0 + P, maturity (period 2) at E0 + 2P;
  report window 30 min after each period end, cure window 30 min after that.

  python tools/live_cases.py <tag> <E0_unix> [case ...]

The report pages must already be live at
https://privatecredit.brilliantnodes.com/reports/<slug>/<tag>/period-<n>.html
(tools/make_reports.py <tag> <E0> 3900 --variant fenwick:1:not_published).
Fenwick's period-1 page is replaced during its report window by a version
without units (see swap_fenwick), which this script commits and pushes.
"""
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcg import G, address, client, fund, read, write  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "examples" / "demo_cases.json").read_text())
T = CASES["terms"]
SITE = os.environ.get("PCG_SITE", "https://privatecredit.brilliantnodes.com")
LOCK = threading.Lock()
RESULTS = {}
P, R, K = T["period_seconds"], T["report_seconds"], T["cure_seconds"]
COMMIT = int(float(T["commitment_gen_studio"]) * G)
CAP = int(float(T["tranche_cap_gen_studio"]) * G)
UPG = T["units_per_gen_studio"]


def log(name, msg):
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with LOCK:
        print(f"{stamp} [{name}] {msg}", flush=True)


def until(ts):
    while time.time() < ts:
        time.sleep(min(5, max(0.5, ts - time.time())))


class Case:
    def __init__(self, slug, tag, e0, addr):
        self.slug, self.tag, self.e0, self.addr = slug, tag, e0, addr
        self.c = next(x for x in CASES["cases"] if x["slug"] == slug)
        self.rec = {"case": slug, "company": self.c["company"], "steps": []}
        self.cl, self.lender = client()
        self.cb, self.borrower = client()

    def e(self, n):
        return self.e0 + n * P

    def step(self, label, who, fn, args, value=0, at=None, expect=None):
        if at:
            until(at)
        c = self.cl if who == "lender" else self.cb
        tx, r = write(c, self.addr, fn, args, value=value)
        res = r["result"]
        self.rec["steps"].append({"label": label, "fn": fn, "tx": tx, "status": r["status"], "result": res,
                                  "at": int(time.time())})
        log(self.slug, f"{label}: {r['status']} {json.dumps(res, default=str)[:300]}")
        with LOCK:
            RESULTS[self.slug] = self.rec
            save()
        if expect is not None and not expect(res):
            raise RuntimeError(f"{label}: unexpected result {res}")
        return res

    def view(self, at=0):
        return read(self.cb, self.addr, "get_facility", [self.fid, at])

    def test(self, n, at, want="READ", retry_until=None):
        """Covenant test; a different kind than wanted is retried every two minutes."""
        until(at)
        while True:
            res = self.step(f"Test period {n}", "borrower", "test_period", [self.fid, n])
            if isinstance(res, dict) and res.get("kind") == want:
                return res
            if retry_until is None or time.time() + 120 > retry_until:
                raise RuntimeError(f"test {n}: wanted {want}, got {res}")
            time.sleep(120)

    def pay_due(self, n, at):
        until(at)
        self.step("Apply time", "borrower", "apply_time", [self.fid])
        f = self.view()
        due = int(f["periods"][n]["due_through"]) - int(f["money"]["paid_fees"]) - int(f["money"]["paid_interest"])
        if due > 0:
            self.step(f"Pay interest and fees due at period {n}", "borrower", "pay", [self.fid, 0], value=due,
                      expect=lambda r: r.get("ok") is True)

    def pay_off(self, at):
        until(at)
        f = self.view(int(time.time()) + 180)
        payoff = int(f["money"]["payoff"]) + G // 100  # a small surplus comes back
        self.step("Repay in full at maturity", "borrower", "pay", [self.fid, 0], value=payoff,
                  expect=lambda r: r.get("ok") is True and r.get("status") == "CLOSED")

    def open(self):
        fund(self.cl, self.lender.address, 60)
        fund(self.cb, self.borrower.address, 60)
        time.sleep(3)
        base = f"{SITE}/reports/{self.slug}/{self.tag}/"
        m = self.e(CASES["num_periods"] - 1)
        args = [self.borrower.address, self.c["company"], T["currency"], base, UPG, T["resolution"], CAP, self.e0, P,
                CASES["num_periods"], R, K, m, T["year_seconds"], T["base_bp"], T["grid"], T["fee_bp"], T["default_bp"],
                T["max_leverage_x100"], T["min_cover_x100"], T["min_cash"]]
        res = self.step("Offer the facility (commitment deposited)", "lender", "create", args, value=COMMIT,
                        expect=lambda r: r.get("ok") is True)
        self.fid = res["id"]
        self.rec["id"] = self.fid
        self.rec["lender"], self.rec["borrower"] = self.lender.address, self.borrower.address
        dsra = int(res["dsra_required"])
        if self.slug == "harbourline":
            # Evidence that a refused payable call refunds: the wrong DSRA comes straight back.
            self.step("Accept with the wrong DSRA (refused, refunded)", "borrower", "accept", [self.fid], value=dsra - 1,
                      expect=lambda r: r.get("ok") is False and r.get("refunded") == str(dsra - 1))
        self.step("Accept: fund the DSRA", "borrower", "accept", [self.fid], value=dsra,
                  expect=lambda r: r.get("ok") is True)

    def run(self):
        try:
            self.open()
            getattr(self, "story_" + self.slug)()
            f = self.view()
            self.rec["final"] = {"status": f["status"], "closed_reason": f["closed_reason"], "money": f["money"],
                                 "events": f["events"], "periods": [p["status"] for p in f["periods"]],
                                 "written_off": f["written_off"]}
            log(self.slug, f"DONE {f['status']} {f['closed_reason']}")
        except Exception as ex:
            self.rec["error"] = str(ex)
            log(self.slug, f"ERROR {ex}")
        with LOCK:
            RESULTS[self.slug] = self.rec
            save()

    # ------------------------------------------------------------ stories

    def story_harbourline(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw tranche 1", "borrower", "draw", [self.fid, 4 * G])
        self.step("Draw tranche 2", "borrower", "draw", [self.fid, 4 * G])
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        self.step("Draw tranche 3", "borrower", "draw", [self.fid, 2 * G])
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_quarrystone(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, 4 * G])
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        self.step("Apply time after window close 1 (margin steps up)", "borrower", "apply_time", [self.fid], at=e(1) + R + 60)
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_brightwater(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw tranche 1", "borrower", "draw", [self.fid, 4 * G])
        self.step("Draw tranche 2", "borrower", "draw", [self.fid, 4 * G])
        self.pay_due(1, e(1) + 90)
        res = self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        if res.get("status") != "BREACH":
            raise RuntimeError(f"expected a breach at period 1: {res}")
        at = int(time.time()) + 240
        q = read(self.cb, self.addr, "quote_cure", [self.fid, 1, at])
        self.rec["cure_quote"] = q
        log(self.slug, f"cure quote {q}")
        small = int(q["wei"]) // 2
        self.step("Cure too small (refused, refunded)", "borrower", "cure", [self.fid, 1], value=small,
                  expect=lambda r: r.get("ok") is False and r.get("refunded") == str(small))
        until(at)
        self.step("Equity cure (quote plus a cushion that comes back)", "borrower", "cure", [self.fid, 1],
                  value=int(q["wei"]) + G // 10, expect=lambda r: r.get("ok") is True and r.get("status") == "ACTIVE")
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_northgate(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, 4 * G])
        self.pay_due(1, e(1) + 90)
        res = self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        if res.get("status") != "BREACH":
            raise RuntimeError(f"expected a breach at period 1: {res}")
        q = read(self.cb, self.addr, "quote_cure", [self.fid, 1, int(time.time())])
        self.rec["cure_quote"] = q
        log(self.slug, f"cure quote {q}")
        d1 = e(1) + R + K
        self.step("Apply time at the cure deadline (E1 falls)", "lender", "apply_time", [self.fid], at=d1 + 30,
                  expect=lambda r: r.get("status") == "DEFAULT")
        self.step("Accelerate (undrawn back, DSRA applied)", "lender", "accelerate", [self.fid], at=d1 + 120,
                  expect=lambda r: r.get("ok") is True)
        self.step("Close with a write-off", "lender", "close", [self.fid], at=d1 + 300,
                  expect=lambda r: r.get("ok") is True)

    def story_fenwick(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, 2 * G])
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, want="NOT_PUBLISHED", retry_until=e(1) + 900)
        swap_fenwick(self.tag, self.e0)
        self.test(1, e(1) + 900, want="NO_READING", retry_until=e(1) + R - 120)
        d1 = e(1) + R + K
        self.step("Apply time at the cure deadline (E2 falls)", "lender", "apply_time", [self.fid], at=d1 + 30,
                  expect=lambda r: r.get("status") == "DEFAULT")
        self.step("Lender waives period 1", "lender", "waive", [self.fid, 1], at=d1 + 120,
                  expect=lambda r: r.get("ok") is True and r.get("status") == "ACTIVE")
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)


SWAP_LOCK = threading.Lock()


def swap_fenwick(tag, e0):
    """Publish Fenwick's period-1 report without units (replacing the
    not-yet-published notice), as a new commit, and wait for it to be live."""
    with SWAP_LOCK:
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_reports.py"), tag, str(e0), str(P), "--only", "fenwick"],
                       check=True, cwd=ROOT, capture_output=True)
        subprocess.run([sys.executable, str(ROOT / "tools" / "sync_reports.py")], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(["git", "add", "-A", "web/public/reports", "docs/reports"], check=True, cwd=ROOT)
        subprocess.run(["git", "commit", "-q", "-m", f"Demo: Fenwick publishes its period-1 report ({tag}), without units"],
                       check=True, cwd=ROOT)
        subprocess.run(["git", "push", "-q", "origin", "main"], check=True, cwd=ROOT)
        log("fenwick", "period-1 page replaced (units missing); waiting for Pages")
        url = f"{SITE}/reports/fenwick/{tag}/period-1.html"
        for _ in range(60):
            try:
                out = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=30).stdout
                if ">Amount<" in out:
                    log("fenwick", "new page is live")
                    return
            except Exception:
                pass
            time.sleep(10)
        log("fenwick", "new page not seen yet; the test retries")


def save():
    out = ROOT / "examples" / "live" / f"{os.environ.get('PCG_NET', 'studio')}-{TAG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"address": ADDR, "tag": TAG, "e0": E0, "cases": RESULTS}, indent=2, default=str))


if __name__ == "__main__":
    TAG, E0 = sys.argv[1], int(sys.argv[2])
    names = sys.argv[3:] or [c["slug"] for c in CASES["cases"]]
    ADDR = address()
    log("main", f"contract {ADDR}, tag {TAG}, E0 {datetime.fromtimestamp(E0, timezone.utc):%Y-%m-%d %H:%M} UTC")
    threads = [threading.Thread(target=Case(n, TAG, E0, ADDR).run) for n in names]
    for th in threads:
        th.start()
        time.sleep(2)
    for th in threads:
        th.join()
    save()
    bad = [k for k, v in RESULTS.items() if "error" in v]
    log("main", "all cases done" + (f"; errors: {bad}" if bad else ""))
    sys.exit(1 if bad else 0)
