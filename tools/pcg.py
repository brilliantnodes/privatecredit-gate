#!/usr/bin/env python3
"""Small command-line client for PrivateCreditGate on GenLayer Studio.

Test GEN only. Keys are throwaway Studio keys funded from Studio's faucet.

  python tools/pcg.py deploy            # deploy contracts/privatecredit_gate.py, print the address
  python tools/pcg.py show <id> [at]    # print one facility (optionally projected to unix time `at`)
  python tools/pcg.py latest            # list recent facilities
  python tools/pcg.py rules             # print get_rules()

The address comes from PCG_ADDRESS or the "studio" entry in web/src/config.js.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.types import TransactionStatus

ROOT = Path(__file__).resolve().parents[1]
G = 10**18


def site_address() -> str:
    cfg = ROOT / "web" / "src" / "config.js"
    if cfg.exists():
        m = re.search(r'studio:\s*\{[^}]*?contract:\s*"(0x[0-9a-fA-F]{40})"', cfg.read_text(), re.S)
        if m:
            return m.group(1)
    return ""


def address() -> str:
    a = os.environ.get("PCG_ADDRESS") or site_address()
    if not a:
        raise SystemExit("set PCG_ADDRESS or put the Studio address in web/src/config.js")
    return a


def client(key=None):
    acct = create_account(key) if key else create_account()
    return create_client(chain=studionet, account=acct), acct


def fund(c, addr, gen=100):
    """Studio's built-in faucet (sim_fundAccount)."""
    return c.provider.make_request(method="sim_fundAccount", params=[addr, gen * G])


def wait(c, tx, status=TransactionStatus.ACCEPTED, retries=240):
    """Wait for a receipt; Studio's gateway sometimes answers 502 for a few seconds."""
    deadline = time.time() + retries * 3
    last = None
    while time.time() < deadline:
        try:
            return c.wait_for_transaction_receipt(transaction_hash=tx, status=status, interval=3000, retries=20)
        except Exception as e:
            last = e
            time.sleep(5)
    raise RuntimeError(f"no receipt for {tx}: {last}")


def receipt_result(r):
    lr = (r.get("consensus_data") or {}).get("leader_receipt")
    lr = lr[0] if isinstance(lr, list) and lr else lr
    lr = lr if isinstance(lr, dict) else {}
    res = lr.get("result") or {}
    payload = res.get("payload") if isinstance(res, dict) else None
    if isinstance(payload, dict) and "readable" in payload:
        try:
            payload = json.loads(payload["readable"])
        except Exception:
            payload = payload["readable"]
    return {"status": r.get("status_name"), "execution": lr.get("execution_result"), "result": payload}


def write(c, addr, fn, args, value=0):
    tx = None
    for attempt in range(3):
        try:
            tx = c.write_contract(address=addr, function_name=fn, args=args, value=value)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)
    return tx, receipt_result(wait(c, tx))


def read(c, addr, fn, args=None):
    return c.read_contract(address=addr, function_name=fn, args=args or [])


def deploy():
    c, acct = client(os.environ.get("PCG_KEY"))
    fund(c, acct.address, 10)
    code = (ROOT / "contracts" / "privatecredit_gate.py").read_text()
    tx = c.deploy_contract(code=code)
    r = wait(c, tx)
    addr = r.get("to_address") or r.get("recipient")
    print(json.dumps({"tx": tx, "address": addr, "status": r.get("status_name")}, indent=2))
    return addr


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "deploy":
        deploy()
        return
    c, _ = client()
    a = address()
    if cmd == "show":
        at = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        print(json.dumps(read(c, a, "get_facility", [sys.argv[2], at]), indent=2, default=str))
    elif cmd == "latest":
        for f in read(c, a, "get_latest", [20]):
            print(f["id"], f["status"], f["company_name"], f["principal"])
    elif cmd == "rules":
        print(json.dumps(read(c, a, "get_rules"), indent=2, default=str))


if __name__ == "__main__":
    main()
