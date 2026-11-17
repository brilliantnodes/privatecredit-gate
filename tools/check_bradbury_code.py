"""Check that the contract deployed on Bradbury is the packed build in this repo.

    cd tools/bradbury && npm ci && cd ../..
    python tools/check_bradbury_code.py

Reads the deploy transaction from Bradbury and compares the code it carried,
byte for byte, with bradbury/build/privatecredit_gate.py. That file is the
source in contracts/ packed by tools/port_bradbury.py --pack, and a test in
tests/direct checks that it unpacks to the source. Reads only; a throwaway key
is used unless BRADBURY_READ_KEY names one.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_record import node  # noqa: E402

CONTRACT = "0x8c17b9742700539D3A2Ec97111073e5c93A6e1f0"
DEPLOY_TX = "0x021fd78789d9aa0f570a20199d1bbf139dd6fa4fed486f5566acfded682d748d"
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bradbury", "build", "privatecredit_gate.py")


def main():
    raw = node("tx", DEPLOY_TX)["raw"]
    dec = raw.get("txDataDecoded") or {}
    code = (dec.get("code") or "").encode()
    build = open(BUILD, "rb").read()
    print(f"deploy {DEPLOY_TX}: {raw.get('resultName')}, {raw.get('statusName')}, from {raw.get('sender')}")
    print(f"contract address in the deploy: {dec.get('contractAddress')}")
    print(f"deployed code sha256 {hashlib.sha256(code).hexdigest()} ({len(code)} bytes)")
    print(f"build         sha256 {hashlib.sha256(build).hexdigest()} ({len(build)} bytes)")
    same = code == build and str(dec.get("contractAddress", "")).lower() == CONTRACT.lower()
    print("identical" if same else "DIFFERENT")
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
