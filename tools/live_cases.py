#!/usr/bin/env python3
"""Run the five fictional borrowers live against a deployed PrivateCreditGate.

Every company and figure is fictional; only test GEN moves. On Studio each
case uses a fresh throwaway lender and borrower funded from Studio's faucet;
on Bradbury (PCG_NET=bradbury) two testnet wallets play lender and borrower
for all five. All five facilities share one schedule, so they run side by
side:

  period 0 ends at E0, period 1 at E0 + P, maturity (period 2) at E0 + 2P;
  report window 30 min after each period end, cure window 30 min after that.

  python tools/live_cases.py <tag> <E0_unix> [case ...]

The report pages must already be live at
https://privatecredit.brilliantnodes.com/reports/<slug>/<tag>/period-<n>.html
(tools/make_reports.py <tag> <E0> 3900 --variant tarrowmere:1:not_published).
Tarrowmere's period-1 page is replaced during its report window by a version
without units (see swap_tarrowmere), which this script commits and pushes.
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
P, R, K, GR = T["period_seconds"], T["report_seconds"], T["cure_seconds"], T["grace_seconds"]
NET = os.environ.get("PCG_NET", "studio")
BB = NET == "bradbury"
COMMIT = int(float(T[f"commitment_gen_{NET}"]) * G)
CAP = int(float(T[f"tranche_cap_gen_{NET}"]) * G)
UPG = T[f"units_per_gen_{NET}"]
SCALE = COMMIT // (10 * G) if COMMIT >= 10 * G else None  # draws are tenths of the commitment
GEN = lambda tenths_of_commitment: COMMIT * tenths_of_commitment // 10  # noqa: E731

# ---------------------------------------------------------------- Bradbury
# Bradbury runs through genlayer-js 2 (node), with testnet wallets whose keys
# stay in files outside the repo (paths from the environment). Each wallet
# sends one transaction at a time. Payouts are credits, so only withdraw()
# moves GEN out, and only that call carries a fee budget (for the caller's own
# address). Bradbury transactions carry no return value: every result recorded
# here is the chain's own outcome (consensus result and execution result of
# the transaction) plus what the contract's views show changed, including the
# facility's CREDIT log entries for refusals.
BB_JS = Path(os.environ.get("BRADBURY_JS", str(ROOT / "tools" / "bradbury")))
KEY_DIR = os.environ.get("BRADBURY_KEY_DIR", "/home/claude/keys")
BB_KEYS = {"lender": f"{KEY_DIR}/bradbury_deployer.key", "borrower": f"{KEY_DIR}/bradbury_seller.key",
           "tester": f"{KEY_DIR}/bradbury_mr.key"}
BB_ADDR = json.loads(os.environ.get("BRADBURY_ADDRS", "{}")) or {
    "lender": "0x77F1635B8F2eca3b7Eb46fB2534B7Fa18aCd2734", "borrower": "0xF5d92105174434618ae0f0E0C65D50Ae6d57eDb7",
    "tester": "0x6ce1cEE581B0057C0ff313d015eCa5936DEacD2B"}
KEY_LOCKS = {k: threading.Lock() for k in BB_KEYS}
CREATE_LOCK = threading.Lock()


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
            p = subprocess.run(["node", "gl.mjs", *args], cwd=BB_JS, capture_output=True, text=True, timeout=1800, env=env)
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


def bb_tx(h):
    p = subprocess.run(["node", "gl.mjs", "tx", h], cwd=BB_JS, capture_output=True, text=True, timeout=300,
                       env={**os.environ, "BRADBURY_KEY_FILE": BB_KEYS["tester"]})
    objs = [json.loads(ln) for ln in p.stdout.splitlines() if ln.startswith("{")]
    return (objs[-1].get("raw") if objs else None) or {}


NOTHING_STORED = ("UNDETERMINED", "LEADER_TIMEOUT", "VALIDATORS_TIMEOUT", "CANCELED")


def bb_decided(raw):
    """Decided: accepted or finalized with a consensus result, or ended with
    nothing stored (validators disagreed, a timeout, or cancelled)."""
    st = str(raw.get("statusName", ""))
    return st in NOTHING_STORED or (st in ("ACCEPTED", "FINALIZED") and raw.get("resultName") not in (None, "", "IDLE"))


def bb_wait(role, h, final=False):
    """Wait until the transaction is decided (a consensus result other than
    IDLE), or finalized if asked."""
    for _ in range(180):
        raw = bb_tx(h)
        if (str(raw.get("statusName")) == "FINALIZED") if final else bb_decided(raw):
            return {"ok": True, "hash": h, "raw": raw}
        time.sleep(10)
    return {"ok": False, "hash": h, "error": "not decided after 30 minutes", "raw": bb_tx(h)}


def bb_write(role, addr, fn, args, value=0, payees=""):
    with KEY_LOCKS[role]:
        d = bb_node(role, "write", addr, fn, json.dumps(args, default=str), str(value), payees)
    h = d.get("hash")
    if h and not bb_decided(d.get("raw") or {}):
        d = bb_wait(role, h)
    # A leader or validator timeout can still execute after the leader
    # rotates (seen on Bradbury on 17 Nov), so wait for the final outcome.
    if h and str((d.get("raw") or {}).get("statusName")) in ("LEADER_TIMEOUT", "VALIDATORS_TIMEOUT"):
        d = bb_wait(role, h, final=True)
    raw = d.get("raw") or {}
    st = str(raw.get("statusName", ""))
    status = st if st in NOTHING_STORED else (raw.get("resultName") or d.get("error"))
    return h, {"status": status, "execution": raw.get("txExecutionResultName"),
               "created": raw.get("createdTimestamp"), "from": BB_ADDR[role]}


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

    def bb_result(self, fn, args, before, r):
        """Bradbury: what this transaction did, from the chain's outcome and
        from what the views show changed since just before it."""
        if fn == "create":
            n = int(bb_read(self.addr, "get_count"))
            if not (r.get("status") == "MAJORITY_AGREE" and r.get("execution") == "FINISHED_WITH_RETURN"):
                return {"ok": False, "chain": r.get("status"), "execution": r.get("execution"), "count": n}
            # the new facility is the one created since `before` with this case's terms
            for i in range(int(before) + 1, n + 1):
                f = bb_read(self.addr, "get_facility", [str(i), 0])
                t = f["terms"]
                if (f["lender"].lower() == self.lender.address.lower() and t["company_name"] == self.c["company"]
                        and t["report_base_url"].endswith(f"/{self.slug}/{self.tag}/")):
                    return {"ok": True, "id": str(i), "dsra_required": t["dsra_required"]}
            return {"ok": False, "error": "no new facility with this case's terms", "count": n}
        f = bb_read(self.addr, "get_facility", [self.fid, 0])
        new = f["history"][len(before["history"]):] if before else []
        out = {"status": f["status"], "logged": [f"{x['what']}: {x['note']}" for x in new]}
        refused = [x for x in new if x["what"] == "CREDIT" and "(refused: " in x["note"]]
        if r.get("status") != "MAJORITY_AGREE" and r.get("status") != "AGREE":
            out.update(ok=False, chain=r.get("status"))
        elif r.get("execution") == "FINISHED_WITH_ERROR":
            out.update(ok=False, reverted=True)
        elif refused:
            note = refused[-1]["note"]
            out.update(ok=False, refunded=note.split(" wei", 1)[0], error=note.split("(refused: ", 1)[1].rsplit("); withdraw", 1)[0])
        else:
            out["ok"] = True
        if fn == "draw":
            out["principal"] = f["money"]["principal"]
        if fn == "test_period":
            n = int(args[1])
            pb, pa = before["periods"][n], f["periods"][n]
            out["period"] = n
            mine = [a for a in pa["attempts"] if r.get("created") and a["at"] == int(r["created"])]
            if pa["attempt_count"] > pb["attempt_count"] and (mine or not r.get("created")):
                last = mine[-1] if mine else pa["attempts"][-1]
                out.update(kind=last.get("kind"), reason=last.get("reason", ""))
                if pa["official"] and not pb["official"]:
                    out["assessment"] = pa["official"]["assessment"]
                    out["figures"] = pa["official"]["figures"]
            else:
                out.update(kind=None, reason="")
        return out

    def e(self, n):
        return self.e0 + n * P

    def step(self, label, who, fn, args, value=0, at=None, expect=None):
        if at:
            until(at)
        if BB:
            if fn == "create":
                with CREATE_LOCK:  # the new id is read back as get_count
                    count0 = bb_read(self.addr, "get_count")
                    tx, r = bb_write(who, self.addr, fn, args, value=value)
                    res = self.bb_result(fn, args, count0, r)
            else:
                before = self.view()
                tx, r = bb_write(who, self.addr, fn, args, value=value, payees=BB_ADDR[who] if fn == "withdraw" else "")
                res = self.bb_result(fn, args, before, r)
        else:
            c = self.cl if who == "lender" else self.cb
            tx, r = write(c, self.addr, fn, args, value=value)
            res = r["result"]
        self.rec["steps"].append({"label": label, "fn": fn, "tx": tx, "status": r["status"], "execution": r.get("execution"),
                                  "created": r.get("created"), "from": r.get("from"), "result": res, "at": int(time.time())})
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
            if want == "READ":
                p = self.view()["periods"][n]
                if p["official"]:  # an earlier test landed late and holds the official reading
                    log(self.slug, f"period {n} already has its official reading ({p['status']})")
                    return {"ok": True, "status": self.view()["status"], "period": n, "kind": "READ",
                            "assessment": p["official"]["assessment"], "note": "official reading from an earlier test"}
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
                CASES["num_periods"], R, K, GR, m, T["year_seconds"], T["base_bp"], T["grid"], T["fee_bp"], T["default_bp"],
                T["max_leverage_x100"], T["min_cover_x100"], T["min_cash"]]
        res = self.step("Offer the facility (commitment deposited)", "lender", "create", args, value=COMMIT,
                        expect=lambda r: r.get("ok") is True)
        self.fid = res["id"]
        self.rec["id"] = self.fid
        self.rec["lender"], self.rec["borrower"] = self.lender.address, self.borrower.address
        dsra = int(res["dsra_required"])
        if self.slug == "ashcarrow":
            # Evidence that a refused payable call refunds: the wrong DSRA comes straight back.
            self.step("Accept with the wrong DSRA (refused, credited back)", "borrower", "accept", [self.fid], value=dsra - 1,
                      expect=lambda r: r.get("ok") is False and r.get("refunded") == str(dsra - 1))
        self.step("Accept: fund the DSRA", "borrower", "accept", [self.fid], value=dsra,
                  expect=lambda r: r.get("ok") is True)

    def run(self):
        try:
            self.open()
            getattr(self, "story_" + self.slug)()
            if not BB:  # Bradbury's shared wallets withdraw once, at the end of the run
                for who in ("lender", "borrower"):
                    if int(read(self.cb, self.addr, "get_claimable", [getattr(self, who).address])) > 0:
                        self.step(f"Withdraw credits ({who})", who, "withdraw", [], expect=lambda r: r.get("ok") is True)
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

    def story_ashcarrow(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw tranche 1", "borrower", "draw", [self.fid, GEN(4)], expect=lambda r: r.get("ok") is True)
        self.step("Draw tranche 2", "borrower", "draw", [self.fid, GEN(4)], expect=lambda r: r.get("ok") is True)
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        self.step("Draw tranche 3", "borrower", "draw", [self.fid, GEN(2)], expect=lambda r: r.get("ok") is True)
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_quillstrand(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, GEN(4)], expect=lambda r: r.get("ok") is True)
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        self.step("Apply time after window close 1 (margin steps up)", "borrower", "apply_time", [self.fid], at=e(1) + R + 60)
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_brenthollow(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw tranche 1", "borrower", "draw", [self.fid, GEN(4)], expect=lambda r: r.get("ok") is True)
        self.step("Draw tranche 2", "borrower", "draw", [self.fid, GEN(4)], expect=lambda r: r.get("ok") is True)
        self.pay_due(1, e(1) + 90)
        res = self.test(1, e(1) + 150, retry_until=e(1) + R - 300)
        if res.get("status") != "BREACH":
            raise RuntimeError(f"expected a breach at period 1: {res}")
        at = int(time.time()) + 240
        q = self.quote(1, at)
        self.rec["cure_quote"] = q
        log(self.slug, f"cure quote {q}")
        small = int(q["wei"]) // 2
        self.step("Cure too small (refused, credited back)", "borrower", "cure", [self.fid, 1], value=small,
                  expect=lambda r: r.get("ok") is False and r.get("refunded") == str(small))
        until(at)
        self.step("Equity cure (quote plus a cushion that comes back)", "borrower", "cure", [self.fid, 1],
                  value=int(q["wei"]) + COMMIT // 100, expect=lambda r: r.get("ok") is True and r.get("status") == "ACTIVE")
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)

    def story_oskendale(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, GEN(4)], expect=lambda r: r.get("ok") is True)
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
        self.step("Accelerate after the grace period (undrawn credited back, DSRA applied)", "lender", "accelerate", [self.fid],
                  at=d1 + GR + 60, expect=lambda r: r.get("ok") is True)
        self.step("Close with a write-off", "lender", "close", [self.fid], at=d1 + GR + 240,
                  expect=lambda r: r.get("ok") is True)

    def story_tarrowmere(self):
        e = self.e
        self.test(0, e(0) + 60, retry_until=e(0) + R - 300)
        self.step("Draw", "borrower", "draw", [self.fid, GEN(2)], expect=lambda r: r.get("ok") is True)
        self.pay_due(1, e(1) + 90)
        self.test(1, e(1) + 150, want="NOT_PUBLISHED", retry_until=e(1) + 900)
        swap_tarrowmere(self.tag, self.e0)
        self.test(1, e(1) + 900, want="NO_READING", retry_until=e(1) + R - 120)
        d1 = e(1) + R + K
        self.step("Apply time at the cure deadline (E2 falls)", "lender", "apply_time", [self.fid], at=d1 + 30,
                  expect=lambda r: r.get("status") == "DEFAULT")
        self.step("Lender waives the covenant for period 1", "lender", "waive", [self.fid, 1, "covenant"], at=d1 + 120,
                  expect=lambda r: r.get("ok") is True and r.get("status") == "ACTIVE")
        self.test(2, e(2) + 60, retry_until=e(2) + R - 300)
        self.pay_off(e(2) + 240)


SWAP_LOCK = threading.Lock()


def swap_tarrowmere(tag, e0):
    """Publish Tarrowmere's period-1 report without units (replacing the
    not-yet-published notice), as a new commit, and wait for it to be live."""
    with SWAP_LOCK:
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_reports.py"), tag, str(e0), str(P), "--only", "tarrowmere"],
                       check=True, cwd=ROOT, capture_output=True)
        subprocess.run([sys.executable, str(ROOT / "tools" / "sync_reports.py")], check=True, cwd=ROOT, capture_output=True)
        subprocess.run(["git", "add", "-A", "web/public/reports", "docs/reports"], check=True, cwd=ROOT)
        subprocess.run(["git", "commit", "-q", "-m", f"Demo: Tarrowmere publishes its period-1 report ({tag}), without units"],
                       check=True, cwd=ROOT)
        subprocess.run(["git", "push", "-q", "origin", "main"], check=True, cwd=ROOT)
        log("tarrowmere", "period-1 page replaced (units missing); waiting for Pages")
        url = f"{SITE}/reports/tarrowmere/{tag}/period-1.html"
        for _ in range(60):
            try:
                out = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=30).stdout
                if ">Amount<" in out:
                    log("tarrowmere", "new page is live")
                    return
            except Exception:
                pass
            time.sleep(10)
        log("tarrowmere", "new page not seen yet; the test retries")


def bb_balance(a):
    d = bb_node("tester", "balance", a)
    return int(d["result"])


def bb_withdraw_all():
    """Bradbury: each wallet withdraws everything the five facilities
    credited to it, and the GEN is seen arriving after finalization."""
    out = []
    for role in ("lender", "borrower", "tester"):
        a = BB_ADDR[role]
        claim = int(bb_read(ADDR, "get_claimable", [a]))
        if claim <= 0:
            continue
        bal0 = bb_balance(a)
        tx, r = bb_write(role, ADDR, "withdraw", [], payees=a)
        fin = bb_wait(role, tx, final=True)
        time.sleep(30)
        rec = {"role": role, "address": a, "credited": str(claim), "tx": tx, "status": r["status"], "execution": r["execution"],
               "finalized": fin.get("ok"), "claimable_after": bb_read(ADDR, "get_claimable", [a]),
               "balance_change": str(bb_balance(a) - bal0), "note": "balance change = credit minus this transaction's fees"}
        log("main", f"withdraw {role}: {rec}")
        out.append(rec)
    out.append({"contract_balance": str(bb_balance(ADDR)), "locked": bb_read(ADDR, "get_locked"),
                "claims_total": bb_read(ADDR, "get_claims_total")})
    return out


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
    if BB:
        RESULTS["withdrawals"] = bb_withdraw_all()
    save()
    bad = [k for k, v in RESULTS.items() if "error" in v]
    log("main", "all cases done" + (f"; errors: {bad}" if bad else ""))
    sys.exit(1 if bad else 0)
