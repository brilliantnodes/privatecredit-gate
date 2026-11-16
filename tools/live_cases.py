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
NET = os.environ.get("PCG_NET", "studio")
BB = NET == "bradbury"
COMMIT = int(float(T[f"commitment_gen_{NET}"]) * G)
CAP = int(float(T[f"tranche_cap_gen_{NET}"]) * G)
UPG = T[f"units_per_gen_{NET}"]
SCALE = COMMIT // (10 * G) if COMMIT >= 10 * G else None  # draws are tenths of the commitment
GEN = lambda tenths_of_commitment: COMMIT * tenths_of_commitment // 10  # noqa: E731

# ---------------------------------------------------------------- Bradbury
# Bradbury runs through genlayer-js 2 (node), with two testnet wallets whose
# keys stay in files outside the repo. Each wallet sends one transaction at a
# time; payouts are external messages, so every write carries a fee budget for
# both parties. The method's return value is read back from the contract's
# views, not from the receipt.
BB_JS = Path(os.environ.get("BRADBURY_JS", "/home/claude/bradbury/js2"))
BB_KEYS = {"lender": "/home/claude/keys/bradbury_deployer.key", "borrower": "/home/claude/keys/bradbury_seller.key",
           "tester": "/home/claude/keys/bradbury_mr.key"}
BB_ADDR = {"lender": "0x77F1635B8F2eca3b7Eb46fB2534B7Fa18aCd2734", "borrower": "0xF5d92105174434618ae0f0E0C65D50Ae6d57eDb7",
           "tester": "0x6ce1cEE581B0057C0ff313d015eCa5936DEacD2B"}
KEY_LOCKS = {k: threading.Lock() for k in BB_KEYS}


def bb_free_role():
    """Anyone may run a covenant test. Bradbury reads take minutes, so the five
    stories' tests go to whichever of the three wallets is idle."""
    while True:
        for role in ("tester", "lender", "borrower"):
            if not KEY_LOCKS[role].locked():
                return role
        time.sleep(2)


def bb_node(role, *args):
    """A write is never sent twice: once it has a hash, a failure only means
    waiting longer for that same transaction."""
    env = {**os.environ, "BRADBURY_KEY_FILE": BB_KEYS[role]}
    for attempt in range(3):
        try:
            p = subprocess.run(["node", "gl2.mjs", *args], cwd=BB_JS, capture_output=True, text=True, timeout=1800, env=env)
            out = p.stdout
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        objs = [json.loads(ln) for ln in out.splitlines() if ln.startswith("{")]
        sent = next((o["sent"] for o in objs if "sent" in o), None)
        d = next((o for o in reversed(objs) if "ok" in o), {"ok": False, "error": "no result"})
        if d.get("ok"):
            return d
        if args[0] == "write" and (sent or d.get("hash")):
            return bb_wait(role, sent or d.get("hash"))
        time.sleep(15)
    return d


def bb_wait(role, h):
    env = {**os.environ, "BRADBURY_KEY_FILE": BB_KEYS[role]}
    for _ in range(120):
        p = subprocess.run(["node", "gl2.mjs", "tx", h], cwd=BB_JS, capture_output=True, text=True, timeout=300, env=env)
        objs = [json.loads(ln) for ln in p.stdout.splitlines() if ln.startswith("{")]
        raw = (objs[-1].get("raw") if objs else None) or {}
        if str(raw.get("statusName", "")) in ("ACCEPTED", "FINALIZED") or raw.get("resultName"):
            return {"ok": True, "hash": h, "raw": raw}
        time.sleep(15)
    return {"ok": False, "hash": h, "error": "still pending after 30 minutes"}


def bb_write(role, addr, fn, args, value=0):
    with KEY_LOCKS[role]:
        d = bb_node(role, "write", addr, fn, json.dumps(args, default=str), str(value), f"{BB_ADDR['lender']},{BB_ADDR['borrower']}")
    raw = d.get("raw") or {}
    return d.get("hash"), {"status": raw.get("resultName") or d.get("error"), "execution": raw.get("txExecutionResultName")}


def bb_read(addr, fn, args=None):
    d = bb_node("borrower", "read", addr, fn, json.dumps(args or [], default=str))
    if not d.get("ok"):
        raise RuntimeError(f"read {fn}: {d.get('error')}")
    return d["result"]


def log(name, msg):
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with LOCK:
        print(f"{stamp} [{name}] {msg}", flush=True)


def until(ts):
    while time.time() < ts:
        time.sleep(min(5, max(0.5, ts - time.time())))


class _Addr:
    def __init__(self, a):
        self.address = a


class Case:
    def __init__(self, slug, tag, e0, addr):
        self.slug, self.tag, self.e0, self.addr = slug, tag, e0, addr
        self.c = next(x for x in CASES["cases"] if x["slug"] == slug)
        self.rec = {"case": slug, "company": self.c["company"], "network": NET, "steps": []}
        if BB:
            self.cl, self.lender = None, _Addr(BB_ADDR["lender"])
            self.cb, self.borrower = None, _Addr(BB_ADDR["borrower"])
        else:
            self.cl, self.lender = client()
            self.cb, self.borrower = client()

    def bb_result(self, fn, args, value):
        """On Bradbury the outcome is read back from the views."""
        if fn == "create":
            n = bb_read(self.addr, "get_count")
            f = bb_read(self.addr, "get_facility", [str(n), 0])
            return {"ok": f["lender"].lower() == self.lender.address.lower(), "id": str(n), "dsra_required": f["terms"]["dsra_required"]}
        f = bb_read(self.addr, "get_facility", [self.fid, 0])
        out = {"ok": True, "status": f["status"]}
        if fn == "test_period":
            p = f["periods"][int(args[1])]
            last = p["attempts"][-1] if p["attempts"] else {}
            out.update(kind=last.get("kind"), reason=last.get("reason", ""), period=int(args[1]))
            if p["official"]:
                out["assessment"] = p["official"]["assessment"]
        return out

    def e(self, n):
        return self.e0 + n * P

    def step(self, label, who, fn, args, value=0, at=None, expect=None):
        if at:
            until(at)
        if BB:
            if fn == "create":
                with KEY_LOCKS["lender"]:
                    d = bb_node("lender", "write", self.addr, fn, json.dumps(args, default=str), str(value), f"{BB_ADDR['lender']},{BB_ADDR['borrower']}")
                    raw = d.get("raw") or {}
                    tx, r = d.get("hash"), {"status": raw.get("resultName") or d.get("error")}
                    res = self.bb_result(fn, args, value)
            else:
                tx, r = bb_write(who, self.addr, fn, args, value=value)
                res = self.bb_result(fn, args, value)
        else:
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
        if BB:
            return bb_read(self.addr, "get_facility", [self.fid, at])
        return read(self.cb, self.addr, "get_facility", [self.fid, at])

    def quote(self, n, at):
        if BB:
            return bb_read(self.addr, "quote_cure", [self.fid, n, at])
        return read(self.cb, self.addr, "quote_cure", [self.fid, n, at])

    def test(self, n, at, want="READ", retry_until=None):
        """Covenant test; a different kind than wanted is retried every two minutes."""
        until(at)
        while True:
            res = self.step(f"Test period {n}", bb_free_role() if BB else "borrower", "test_period", [self.fid, n])
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
        payoff = int(f["money"]["payoff"]) + COMMIT // 1000  # a small surplus comes back
        self.step("Repay in full at maturity", "borrower", "pay", [self.fid, 0], value=payoff,
                  expect=lambda r: r.get("ok") is True and r.get("status") == "CLOSED")

    def open(self):
        if not BB:
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
        if self.slug == "harbourline" and not BB:
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
        self.step("Draw tranche 1", "borrower", "draw", [self.fid, GEN(4)])
        self.step("Draw tranche 2", "borrower", "draw", [self.fid, GEN(4)])
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        self.step("Draw tranche 3", "borrower", "draw", [self.fid, GEN(2)])
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_quarrystone(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, GEN(4)])
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        self.step("Apply time after window close 1 (margin steps up)", "borrower", "apply_time", [self.fid], at=e(1) + R + 60)
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_brightwater(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw tranche 1", "borrower", "draw", [self.fid, GEN(4)])
        self.step("Draw tranche 2", "borrower", "draw", [self.fid, GEN(4)])
        self.pay_due(1, e(1) + 90)
        res = self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        if res.get("status") != "BREACH":
            raise RuntimeError(f"expected a breach at period 1: {res}")
        at = int(time.time()) + 240
        q = self.quote(1, at)
        self.rec["cure_quote"] = q
        log(self.slug, f"cure quote {q}")
        if not BB:
            small = int(q["wei"]) // 2
            self.step("Cure too small (refused, refunded)", "borrower", "cure", [self.fid, 1], value=small,
                      expect=lambda r: r.get("ok") is False and r.get("refunded") == str(small))
        until(at)
        self.step("Equity cure (quote plus a cushion that comes back)", "borrower", "cure", [self.fid, 1],
                  value=int(q["wei"]) + COMMIT // 100, expect=lambda r: r.get("ok") is True and r.get("status") == "ACTIVE")
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_northgate(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, GEN(4)])
        self.pay_due(1, e(1) + 90)
        res = self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        if res.get("status") != "BREACH":
            raise RuntimeError(f"expected a breach at period 1: {res}")
        q = self.quote(1, int(time.time()))
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
        self.step("Draw", "borrower", "draw", [self.fid, GEN(2)])
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
    ADDR = os.environ["PCG_ADDRESS"] if BB else address()
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
