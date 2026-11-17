#!/usr/bin/env bash
# Run the direct-mode tests on GenVM v0.6 against the packed Bradbury build.
#
#   pip install --pre genlayer-test==0.30.0rc2     # in a separate virtualenv
#   tools/test_v6.sh /path/to/that/venv
#
# The test files are the same as for Studio (GenVM v0.2); only the shared
# helpers differ, so a scratch copy of the repo swaps in tests/conftest_v6.py.
set -euo pipefail
VENV="${1:?path to a virtualenv with genlayer-test 0.30.0rc2}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
(cd "$ROOT" && git ls-files -co --exclude-standard -- contracts tests tools bradbury examples gltest.config.yaml | grep -v '^docs/' | tar -cf - -T -) | tar -xf - -C "$TMP"
cp "$TMP/tests/conftest_v6.py" "$TMP/tests/direct/conftest.py"
cd "$TMP"
GENVM_VERSION="${GENVM_VERSION:-v0.6.0-rc10}" PCG_CONTRACT=bradbury/build/privatecredit_gate.py PYTHONPATH=. \
  "$VENV/bin/python" -m pytest tests/direct -q -p no:cacheprovider
