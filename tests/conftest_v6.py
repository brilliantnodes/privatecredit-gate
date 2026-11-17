"""Shared helpers for direct mode tests, GenVM v0.6 (genlayer-test 0.30.0rc2)."""


def to_hex(addr_bytes):
    if hasattr(addr_bytes, "as_hex"):
        return addr_bytes.as_hex
    from genlayer.types import Address

    return Address(addr_bytes).as_hex


# genlayer-test 0.30.0rc2: VMContext.warp() updates its own clock, but
# _refresh_gl_message() only syncs sender, origin, value and chain id, so a
# contract reading gl.message.raw["datetime"] keeps the deploy time. Copy the
# clock across (same fix as the v0.2 conftest, for the v0.6 module layout).
def _patch_warp():
    from gltest.direct import vm as _vm

    original = _vm.VMContext._refresh_gl_message
    if getattr(original, "_patterns_patched", False):
        return

    def refresh(self):
        original(self)
        import sys as _sys

        m = _sys.modules.get("genlayer.message")
        raw = getattr(m, "raw", None) if m is not None else None
        if isinstance(raw, dict):
            raw["datetime"] = self._datetime
            raw["value"] = self._value
        if m is not None and hasattr(m, "datetime") and not callable(getattr(m, "datetime")):
            try:
                m.datetime = self._datetime
            except Exception:
                pass

    refresh._patterns_patched = True
    _vm.VMContext._refresh_gl_message = refresh


_patch_warp()
