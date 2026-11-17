#!/usr/bin/env python3
"""Mutation check: break the contract on purpose, one change at a time, and
confirm that the direct-mode tests catch every break.

    PYTHONPATH=. python tools/mutate.py            # all mutants
    PYTHONPATH=. python tools/mutate.py 12 40      # only mutants 12 and 40

Each mutant is written to a temporary file and the tests are pointed at it
with PCG_CONTRACT; contracts/privatecredit_gate.py itself is never modified.

Left out on purpose (equivalent mutants, so no test can catch them):
- the leader-result checks for a figure off the resolution grid, a bool, a
  negative debt or an over-size figure: the validator also compares the
  leader's figures with its own reading, which never has such values;
- the second size cap in _to_units, which the first cap already covers;
- the final money-adds-up check in _commit, a safety net that no correct
  path can trip;
- the closing call at the end of get_facility's projection: _advance
  already closes after every step, and only payments or steps can make a
  facility closable;
- the leader's reason-code check: validators now compare the reason with
  their own, which is always a valid code, so a bad code is refused anyway.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "contracts" / "privatecredit_gate.py").read_text()

MUTANTS = [
    # --- agreement and leader checks
    ("figures not compared", 'return a["figures"] == b["figures"]', "return True"),
    ("figures within 1 percent", 'return a["figures"] == b["figures"]', 'return all(abs(a["figures"][k] - b["figures"][k]) * 100 <= abs(b["figures"][k]) for k in FIGURES)'),
    ("kind not compared", 'if a["kind"] != b["kind"]:\n        return False\n    if a["kind"] == "READ":', 'if False:\n        return False\n    if a["kind"] == "READ":'),
    ("extra keys from the leader accepted", "sorted(figs.keys()) != sorted(FIGURES)", "not all(k in figs for k in FIGURES)"),
    # --- interpretation of the copied form
    ("any company accepted", ' or name not in _words(ans.get("company_name_on_page")):', ":"),
    ("draft accepted", 'if _yes(ans.get("marked_draft")):', "if False:"),
    ("period not checked", 'if not _period_matches(ans.get("period_end_on_page"), _period_end(t, n)):', "if False:"),
    ("currency not checked", '    if not _currency_matches(ans.get("currency_on_page"), t["currency"]):\n        return {"kind": "NO_READING", "reason": "N2_CURRENCY"}', '    if False:\n        return {"kind": "NO_READING", "reason": "N2_CURRENCY"}'),
    ("conflicting figure accepted", 'if _yes(f.get("conflicting")):', "if False:"),
    ("LTM label not required", 'if key in LTM_FIGURES and not _yes(f.get("ltm_labelled")):', "if False:"),
    ("LTM label required for every figure", 'if key in LTM_FIGURES and not _yes(f.get("ltm_labelled")):', 'if not _yes(f.get("ltm_labelled")):'),
    ("missing scale read as units", 'mult = SCALES.get(str(f.get("scale", "")).strip().lower())', 'mult = SCALES.get(str(f.get("scale", "")).strip().lower(), 1)'),
    ("missing figure read as zero", 'if not isinstance(f, dict) or f.get("value") is None or str(f.get("value")).strip() == "":', 'if not isinstance(f, dict):'),
    ("negative debt or cash accepted", 'if out["total_debt"] < 0 or out["cash"] < 0:\n        return {"kind": "NO_READING", "reason": "N2_FORMAT"}', 'if False:\n        return {"kind": "NO_READING", "reason": "N2_FORMAT"}'),
    ("rounding floors negatives", "return (abs(v) // res) * res * (-1 if v < 0 else 1)", "return (v // res) * res"),
    ("debt rounded down", 'ROUND_UP = ("ltm_net_finance_costs", "total_debt")', 'ROUND_UP = ("ltm_net_finance_costs",)'),
    ("finance costs rounded down", 'ROUND_UP = ("ltm_net_finance_costs", "total_debt")', 'ROUND_UP = ("total_debt",)'),
    ("brackets read as positive", "neg, s = True, _strip_code(s[1:-1], currency)", "neg, s = False, _strip_code(s[1:-1], currency)"),
    ("minus read as positive", "neg, s = True, _strip_code(s[1:], currency)", "neg, s = False, _strip_code(s[1:], currency)"),
    ("decimal comma read as thousands", 'if "," in frac or not (groups[0] != "" and groups[0][0] != "0" and all(c in DIGITS for c in groups[0]) and len(groups[0]) <= 3 and all(len(g) == 3 and all(c in DIGITS for c in g) for g in groups[1:])):\n            return None', 'if "," in frac:\n            return None'),
    ("leading-zero comma group read as thousands", 'groups[0] != "" and groups[0][0] != "0" and all(', 'groups[0] != "" and all('),
    ("JSON decimals parsed as floats", 'out = json.loads(s, parse_float=str)', "out = json.loads(s)"),
    ("floats accepted", '    if value is None or isinstance(value, bool) or isinstance(value, float):\n        return None\n    s = str(value)', '    if value is None or isinstance(value, bool):\n        return None\n    s = repr(value) if isinstance(value, float) else str(value)'),
    ("currency code not stripped", '    s = _strip_code(s.replace("\u2212", "-"), currency)', '    s = s.replace("\u2212", "-")'),
    ("date-only matches the end day", "day == datetime.fromtimestamp(end_ts - 1, timezone.utc).date().isoformat()", "day == datetime.fromtimestamp(end_ts, timezone.utc).date().isoformat()"),
    ("period end within a minute", "return ts == end_ts", "return abs(ts - end_ts) <= 60"),
    # --- covenants and bands
    ("leverage edge exclusive", 'lev_ok = e > 0 and adj * RATIO <= t["max_leverage_x100"] * e', 'lev_ok = e > 0 and adj * RATIO < t["max_leverage_x100"] * e'),
    ("zero EBITDA passes leverage", 'lev_ok = e > 0 and adj', 'lev_ok = e >= 0 and adj'),
    ("leverage in basis points", 'lev_ok = e > 0 and adj * RATIO <= t["max_leverage_x100"] * e', 'lev_ok = e > 0 and adj * BP <= t["max_leverage_x100"] * e'),
    ("cover edge exclusive", 'cover_ok = fc <= 0 or e * RATIO >= t["min_cover_x100"] * fc', 'cover_ok = fc <= 0 or e * RATIO > t["min_cover_x100"] * fc'),
    ("zero finance cost tested", 'cover_ok = fc <= 0 or', 'cover_ok = fc < 0 or'),
    ("cash edge exclusive", 'cash_ok = cash >= t["min_cash"]', 'cash_ok = cash > t["min_cash"]'),
    ("band edge exclusive", "if net * RATIO <= upper * ebitda:", "if net * RATIO < upper * ebitda:"),
    ("band ignores EBITDA sign", "    if ebitda <= 0:\n        return _top(t)", "    if False:\n        return _top(t)"),
    ("band from cured leverage", "band = _band(t, net, e)  # a cure fixes the covenant, not the price", "band = _band(t, adj, e)"),
    ("cure units ignored", "adj = net - cure_units", "adj = net"),
    ("cure quote one short", "return max(0, net - allowed)", "return max(0, net - allowed - 1)"),
    ("cure wei rounded down", 'return _ceil_div(units * WEI, t["units_per_gen"])', 'return units * WEI // t["units_per_gen"]'),
    # --- draws
    ("no period-0 condition precedent", '    if n < 0:\n        return "no draws before', '    if False:\n        return "no draws before'),
    ("no draw stop", '    if not _period_ok(s["periods"][n]):\n        return f"draw stop', '    if False:\n        return f"draw stop'),
    ("draws after availability end", '    if now >= t["availability_end"]:\n        return "the availability', '    if False:\n        return "the availability'),
    ("draws in breach or default", '    if st != "ACTIVE":\n        return f"draws need status', '    if st == "CLOSED":\n        return f"draws need status'),
    ("tranche cap ignored", 'amount > t["tranche_cap"] or ', ""),
    ("anyone may draw", 'if gl.message.sender_address.as_hex.lower() != f.borrower.lower():\n            raise gl.vm.UserError("only the borrower can draw")', 'if False:\n            raise gl.vm.UserError("only the borrower can draw")'),
    ("waiver does not lift the draw stop", '    if p["waived_at"]:\n        return True\n    o = p["official"]', '    if False:\n        return True\n    o = p["official"]'),
    ("cure does not lift the draw stop", 'return o is not None and (o["assessment"]["compliant"] or p["cure"] is not None)', 'return o is not None and o["assessment"]["compliant"]'),
    # --- set dates and the engine
    ("any reading sets the margin at once", "            if n == 0:\n                # Nothing", "            if True:\n                # Nothing"),
    ("margin not changed at window close", '            s["band"], s["margin_bp"] = a["band"], a["margin_bp"]\n            _log(s, at, "WINDOW_CLOSE"', '            pass\n            _log(s, at, "WINDOW_CLOSE"'),
    ("missing report keeps the margin", '            p["missing"] = True\n            s["band"], s["margin_bp"] = _top(t), t["grid"][-1][1]', '            p["missing"] = True'),
    ("missing report never flagged", '            p["missing"] = True\n', "            pass\n"),
    ("E3 never", '        if s["paid_fee"] + s["paid_interest"] < p["due_through"]:\n            _add_event(s, "E3", n, at)', '        if False:\n            _add_event(s, "E3", n, at)'),
    ("E3 against what has accrued since", 's["paid_fee"] + s["paid_interest"] < p["due_through"]:', 's["paid_fee"] + s["paid_interest"] < sum(_accrued(t, s)):'),
    ("E1 never", '        if _breach_open(p):\n            _add_event(s, "E1", n, at)', '        if False:\n            _add_event(s, "E1", n, at)'),
    ("E2 never", '        elif p["missing"] and not p["waived_at"]:\n            _add_event(s, "E2", n, at)', '        elif False:\n            _add_event(s, "E2", n, at)'),
    ("E2 despite a waiver", '        elif p["missing"] and not p["waived_at"]:\n            _add_event(s, "E2", n, at)', '        elif p["missing"]:\n            _add_event(s, "E2", n, at)'),
    ("E4 never", '        if s["principal"] > 0:\n            _add_event(s, "E4", -1, at)', '        if False:\n            _add_event(s, "E4", -1, at)'),
    ("period 0 is a payment date", "if n >= 1:  # payment dates", "if n >= 0:  # payment dates"),
    ("interest due with no grace", 'out.append((e + t["cure_seconds"], _ORDER["DUE"], "DUE", n))', 'out.append((e, _ORDER["DUE"], "DUE", n))'),
    ("cure deadline at window close", 'return _window_close(t, n) + t["cure_seconds"]', "return _window_close(t, n)"),
    ("maturity default with no grace", 'out.append((_maturity(t) + t["cure_seconds"], _ORDER["MATURITY"], "MATURITY", -1))', 'out.append((_maturity(t), _ORDER["MATURITY"], "MATURITY", -1))'),
    ("default interest never", 'return s["state"] == "ACCELERATED" or bool(_open_events(s))', 'return s["state"] == "ACCELERATED"'),
    ("waived events still open", 'return [e for e in s["events"] if not e["waived_at"] and not e["remedied_at"]]', 'return [e for e in s["events"] if not e["remedied_at"]]'),
    ("remedied events still open", 'return [e for e in s["events"] if not e["waived_at"] and not e["remedied_at"]]', 'return [e for e in s["events"] if not e["waived_at"]]'),
    ("default add-on not charged", ' + (t["default_bp"] if _default_on(s) else 0)', ""),
    ("fee on the whole commitment", 's["fee_num"] += s["commitment_held"] * t["fee_bp"] * dt', 's["fee_num"] += t["commitment"] * t["fee_bp"] * dt'),
    ("interest rounded at every step", 's["interest_num"] += s["principal"] * _rate_bp(t, s) * dt', 's["interest_num"] += (s["principal"] * _rate_bp(t, s) * dt) // (BP * t["year_seconds"]) * (BP * t["year_seconds"])'),
    ("offer never expires", '        if now >= t["first_period_end"]:\n            pays.append((t["lender"], s["commitment_held"], "offer not accepted', '        if False:\n            pays.append((t["lender"], s["commitment_held"], "offer not accepted'),
    ("undrawn kept at availability end", '        if s["commitment_held"] > 0:\n            pays.append((t["lender"], s["commitment_held"], "undrawn commitment back at availability end"))', '        if False:\n            pays.append((t["lender"], s["commitment_held"], "undrawn commitment back at availability end"))'),
    ("DSRA to the lender at closing", 'pays.append((t["borrower"], s["dsra_held"], "DSRA back to the borrower at closing"))', 'pays.append((t["lender"], s["dsra_held"], "DSRA back to the borrower at closing"))'),
    ("closes with undrawn still available", ' or _owed(t, s) != (0, 0) or s["commitment_held"] != 0:', ' or _owed(t, s) != (0, 0):'),
    ("closes with fees still owed", ' or s["principal"] != 0 or _owed(t, s) != (0, 0) or', ' or s["principal"] != 0 or'),
    # --- money
    ("interest before fees", "    pf = min(amount, fee_owed)\n    amount -= pf\n    pi = min(amount, int_owed)\n    amount -= pi", "    pi = min(amount, int_owed)\n    amount -= pi\n    pf = min(amount, fee_owed)\n    amount -= pf"),
    ("principal before interest", "    pi = min(amount, int_owed)\n    amount -= pi\n    pp", "    pi = 0\n    pp"),
    ("payment excess kept", 'pays.append((t["borrower"], excess, "payment excess back"))', "pass"),
    ("refused value kept", 'pays = pays + [(gl.message.sender_address.as_hex, value, "refused: " + error)]', "pays = pays"),
    ("DSRA amount not exact", "if value != need:", "if value < need:"),
    ("DSRA rounded down", 'return _ceil_div(t["commitment"] * rate * t["period_seconds"], BP * t["year_seconds"])', 'return t["commitment"] * rate * t["period_seconds"] // (BP * t["year_seconds"])'),
    ("DSRA at the first band", 'rate = t["base_bp"] + t["grid"][-1][1]', 'rate = t["base_bp"] + t["grid"][0][1]'),
    ("undrawn kept on acceleration", '        if s["commitment_held"] > 0:\n            pays.append((t["lender"], s["commitment_held"], "undrawn commitment back on acceleration"))', '        if False:\n            pays.append((t["lender"], s["commitment_held"], "undrawn commitment back on acceleration"))'),
    ("DSRA leftover to the lender", 'pays.append((t["borrower"], excess, "DSRA left over after acceleration"))', 'pays.append((t["lender"], excess, "DSRA left over after acceleration"))'),
    ("accelerate without default", 'if _status(s) != "DEFAULT":', 'if _status(s) == "CLOSED":'),
    ("anyone may accelerate", 'if gl.message.sender_address.as_hex.lower() != f.lender.lower():\n            raise gl.vm.UserError("only the lender can accelerate")', 'if False:\n            raise gl.vm.UserError("only the lender can accelerate")'),
    ("close before acceleration", 'if s["state"] != "ACCELERATED":\n            raise gl.vm.UserError("the lender can close only', 'if s["state"] == "CLOSED":\n            raise gl.vm.UserError("the lender can close only'),
    ("locked not updated", "self.locked = u256(int(self.locked) + held_after - held_before)", "self.locked = u256(int(self.locked))"),
    ("anyone may pay", 'return self._refund(f, s, held, pays, "only the borrower can pay")', 'pass'),
    ("anyone may accept", 'return self._refund(f, s, held, pays, "only the borrower can accept")', 'pass'),
    ("expired offer accepted", 'if s["state"] != "OFFERED":\n            return self._refund(f, s, held, pays, "this facility is not an open offer', 'if s["state"] not in ("OFFERED", "CANCELLED"):\n            return self._refund(f, s, held, pays, "this facility is not an open offer'),
    # --- cure
    ("cure after the deadline", '    if now >= _cure_deadline(t, n):\n        return f"the cure deadline', '    if False:\n        return f"the cure deadline'),
    ("unlimited cures", 'if len(s["cures_used"]) >= MAX_CURES:', 'if len(s["cures_used"]) >= 99:'),
    ("consecutive cures", 'if n - 1 in s["cures_used"] or n + 1 in s["cures_used"]:', "if False:"),
    ("cure fixes interest cover", 'if not (a["cover_ok"] and a["cash_ok"]):', 'if not a["cash_ok"]:'),
    ("cure counts fees and interest too", 'units = pp * t["units_per_gen"] // WEI', 'units = (pf + pi + pp) * t["units_per_gen"] // WEI'),
    ("cure counts the refunded excess", 'units = pp * t["units_per_gen"] // WEI', 'units = value * t["units_per_gen"] // WEI'),
    ("anyone may cure", 'return self._refund(f, s, held, pays, "only the borrower can cure")', "pass"),
    # --- the covenant test
    ("debt check off", 'if outcome["kind"] == "READ" and outcome["figures"]["total_debt"] < _drawn_units(t, p["principal_at_end"]):', "if False:"),
    ("debt check on today's principal", '_drawn_units(t, p["principal_at_end"])', '_drawn_units(t, s["principal"])'),
    ("second reading accepted", '        if p["official"] is not None:\n            raise gl.vm.UserError(f"period {n} already', '        if False:\n            raise gl.vm.UserError(f"period {n} already'),
    ("test after the window", "if now >= _window_close(t, n):", "if now > _window_close(t, n):"),
    ("test before the period end", "        if now < _period_end(t, n):\n            raise gl.vm.UserError(f\"period {n} ends at", "        if now < _period_end(t, n) - 60:\n            raise gl.vm.UserError(f\"period {n} ends at"),
    ("attempt log unbounded", 'if len(p["attempts"]) < MAX_ATTEMPTS_KEPT:', "if True:"),
    # --- waiver
    ("anyone may waive", 'if gl.message.sender_address.as_hex.lower() != f.lender.lower():\n            raise gl.vm.UserError("only the lender can waive")', 'if False:\n            raise gl.vm.UserError("only the lender can waive")'),
    ("waiver covers every period", 'if e["period"] == n and e["code"] in codes', 'if e["code"] in codes + ("E4",)'),
    ("waiver after acceleration", 'if s["state"] != "ACTIVE":\n            raise gl.vm.UserError("nothing to waive', 'if s["state"] == "CLOSED":\n            raise gl.vm.UserError("nothing to waive'),
    # --- review fixes (16 Nov)
    ("no-reading reason not compared", '    return a.get("reason", "") == b.get("reason", "")', "    return True"),
    ("finance label ignored", '            v = _finance_cost(f.get("line_label"), v)\n            if v is None:', '            v = v\n            if v is None:'),
    ("unclear finance label accepted", '            if v is None:\n                return {"kind": "NO_READING", "reason": "N2_FINANCE_LABEL"}', '            if v is None:\n                v = 0'),
    ("apostrophe read as a scale word", '    10**3: ("thousands", "thousand", "k"),', '    10**3: ("thousands", "thousand", "k", "\'000", "000s"),'),
    ("dot thousands read as a decimal", "        return None  # '12.450' is 12,450", "        pass  # '12.450' is 12,450"),
    ("other time zones read as UTC", '    if rest not in ("", ":00") and not', '    if False and not'),
    ("remedy after acceleration", '    if s["state"] != "ACTIVE":\n        return\n    for e in s["events"]:', '    for e in s["events"]:'),
    ("cure sweeps the cushion into principal", "_waterfall(t, s, value, need)  # prepays", '_waterfall(t, s, value, s["principal"])  # prepays'),
    ("bad prepay reverts", '        try:\n            prepay = int(prepay)\n        except Exception:\n            return self._refund(f, s, held, pays, "prepay must be a whole number of wei")', '        prepay = int(prepay)'),
    ("bad cure period reverts", '        try:\n            n = int(period)\n        except Exception:\n            return self._refund(f, s, held, pays, "period must be a whole number")', '        n = int(period)'),
    ("unicode digits in a host", 'all(lab != "" and all(c in DIGITS for c in lab) and str(int(lab)) == lab', 'all(lab.isdigit() and str(int(lab)) == lab'),
    ("times off the minute accepted", 'if any(t[k] % 60 != 0 for k in ("first_period_end", "period_seconds", "report_seconds", "cure_seconds", "grace_seconds")):', "if False:"),
    ("availability before window close 0", 'if not _window_close(t, 0) < t["availability_end"] <= _maturity(t):', 'if not t["first_period_end"] < t["availability_end"] <= _maturity(t):'),
    ("cure quote ignores what is drawn", '    if _wei_for_units(t, need) > s["principal"]:\n        return "a cure prepays', '    if False:\n        return "a cure prepays'),
    ("cure quote leaves out what is owed", '    return fee_owed + int_owed + _wei_for_units(t, _cure_needed_units(t, s["periods"][n]["official"]["figures"]))', '    return _wei_for_units(t, _cure_needed_units(t, s["periods"][n]["official"]["figures"]))'),
    ("cure quote ignores cover failures", '    if not (a["cover_ok"] and a["cash_ok"]):\n        return "a cure counts', '    if False:\n        return "a cure counts'),
    ("E3 never remedied", '            if s["paid_fee"] + s["paid_interest"] >= s["periods"][e["period"]]["due_through"]:\n                e["remedied_at"] = at', '            if False:\n                e["remedied_at"] = at'),
    ("E3 remedied by a partial payment", 'if s["paid_fee"] + s["paid_interest"] >= s["periods"][e["period"]]["due_through"]:', 'if s["paid_fee"] + s["paid_interest"] > 0:'),
    ("payment never remedies", '        _log(s, now, "PAYMENT", f"fees {pf} wei, interest {pi} wei, principal {pp} wei; excess {excess} wei back")\n        _remedy(s, now)', '        _log(s, now, "PAYMENT", f"fees {pf} wei, interest {pi} wei, principal {pp} wei; excess {excess} wei back")'),
    ("surplus prepays without asking", '_waterfall(t, s, value, _principal_due(t, s, now) + prepay)', '_waterfall(t, s, value, s["principal"])'),
    ("prepay ignored", '_waterfall(t, s, value, _principal_due(t, s, now) + prepay)', '_waterfall(t, s, value, _principal_due(t, s, now))'),
    ("principal never due at maturity", '    return s["principal"] if s["state"] == "ACCELERATED" or now >= _maturity(t) else 0', '    return s["principal"] if s["state"] == "ACCELERATED" else 0'),
    ("negative prepay accepted", '        if prepay < 0:\n            return self._refund', '        if False:\n            return self._refund'),
    ("anyone may cancel the undrawn", 'raise gl.vm.UserError("only the borrower can cancel the undrawn commitment")', "pass"),
    ("clock may run backwards", 'now = max(self._now(), s["t"])', "now = self._now()"),
    ("leverage text rounded down", 'x = _ceil_div(n, den) if up else n // den', "x = n // den"),
    ("cover text rounded up", 'x = _ceil_div(n, den) if up else n // den', "x = _ceil_div(n, den)"),
    ("date-only at any time of day", '    if day is None or end_ts % 86400 != 0:\n        return False', '    if day is None:\n        return False'),
    ("scale word not stripped", '    s = _strip_scale_word(s, mult)\n    if s is None:\n        return None', '    pass'),
    ("contradicting scale word accepted", '                return head if m == mult else None', '                return head'),
    ("currency symbol not stripped", '    for mark in (code, CURRENCY_SYMBOLS.get(code, code)):', '    for mark in (code,):'),
    ("unknown facility reverts a payment", '        if not isinstance(facility_id, str) or facility_id not in self.facilities:\n            return None\n        return self._start(facility_id)', '        return self._start(facility_id)'),
    ("non-string facility id reverts a payment", 'if not isinstance(facility_id, str) or facility_id not in self.facilities:', "if facility_id not in self.facilities:"),
    ("borrower indexed before accepting", '        self._index(borrower_hex, new_id, offers=True)', '        self._index(borrower_hex, new_id)'),
    ("time loop continues after closing", '        if s["state"] != "ACTIVE":\n            return pays\n    _accrue(t, s, now)', '        pass\n    _accrue(t, s, now)'),
    ("cure after acceleration", '    if s["state"] != "ACTIVE" or not 0 <= n < t["num_periods"]:\n        return "no breach to cure', '    if s["state"] not in ("ACTIVE", "ACCELERATED") or not 0 <= n < t["num_periods"]:\n        return "no breach to cure'),
    ("test after acceleration", 'if st not in ("ACTIVE", "BREACH", "DEFAULT"):', 'if st not in ("ACTIVE", "BREACH", "DEFAULT", "ACCELERATED"):'),
    ("waiver covers remedied events", 'e["code"] in codes and not e["waived_at"] and not e["remedied_at"]:', 'e["code"] in codes and not e["waived_at"]:'),
    # --- fourth review fixes (16 Nov)
    ("a second currency code accepted", '        if x.startswith(code) or (x in ISO_CODES and x != code):\n            return False', '        if False:\n            return False'),
    ("code-shaped words accepted", 'if x.startswith(code) or (x in ISO_CODES and x != code):', 'if x in ISO_CODES and x != code:'),
    ("other currencies' symbols accepted", '    if any(sym in raw and sym != own for sym in SYMBOLS):\n        return False', '    if False:\n        return False'),
    ("currency needs no exact token", '    if not any(x in allowed for x in toks):\n        return False', '    if False:\n        return False'),
    ("decimal mark fails open", 'if str(ans.get("decimal_mark", "")).strip().lower() not in (".", "none"):', 'if str(ans.get("decimal_mark", "")).strip() == ",":'),
    ("page not scanned for decimal commas", '    if _decimal_comma_page(page):\n        return {"kind": "NO_READING", "reason": "N2_FORMAT"}', '    if False:\n        return {"kind": "NO_READING", "reason": "N2_FORMAT"}'),
    ("scan misses comma decimals", '            if 1 <= len(tail) <= 2 and all(c in DIGITS for c in tail):\n                return True', '            if False:\n                return True'),
    ("scan misses dot-thousands groups", '        if len(parts) >= 3 and all(len(x) == 3 and all(c in DIGITS for c in x) for x in parts[1:]):\n            return True', '        if False:\n            return True'),
    ("scan misses 1.234,5", '            if "." in r and r.index(".") < r.rindex(","):\n                return True', '            if False:\n                return True'),
    ("no rounding to the resolution", 'out[key] = _round_figure(key, v, t["resolution"], d)', 'out[key] = v // d'),
    ("truncated before rounding", 'out[key] = _round_figure(key, v, t["resolution"], d)', 'out[key] = _round_figure(key, (abs(v) // d) * (-1 if v < 0 else 1), t["resolution"])'),
    ("figures rounded toward zero", 'out[key] = _round_figure(key, v, t["resolution"], d)', 'out[key] = _toward_zero((abs(v) // d) * (-1 if v < 0 else 1), t["resolution"])'),
    ("exponents read", '    whole, dot, frac = s.partition(".")\n    if "." in frac or (whole == "" and frac == ""):\n        return None\n    if any(c not in DIGITS for c in whole + frac):\n        return None\n    num = int((whole or "0") + frac)\n    scale = len(frac)', '    exp = 0\n    if "e" in s:\n        s, e = s.split("e", 1)\n        exp = int(e) if e.lstrip("+-").isdigit() else 0\n    whole, dot, frac = s.partition(".")\n    if "." in frac or (whole == "" and frac == ""):\n        return None\n    if any(c not in DIGITS for c in whole + frac):\n        return None\n    num = int((whole or "0") + frac)\n    scale = len(frac) - exp\n    if scale < 0:\n        num, scale = num * 10 ** (-scale), 0'),
    ("no digit cap", "    if len(s) > 60:\n        return None\n    whole, dot, frac = s.partition(\".\")\n    if \".\" in frac or (whole == \"\" and frac == \"\"):", "    whole, dot, frac = s.partition(\".\")\n    if \".\" in frac or (whole == \"\" and frac == \"\"):"),
    ("float conversion back", "    return sign * num * mult, 10**scale", "    return int(sign * num / 10**scale * mult), 1"),
    ("bracketed income word ignored", '        if bracket_income:\n            return v', '        if bracket_income:\n            return abs(v)'),
    ("bracketed cost word ignored", '        if bracket_cost:\n            return -v', '        if bracket_cost:\n            return abs(v)'),
    ("both sides bracketed accepted", '        if bracket_income and bracket_cost:\n            return None', '        if bracket_income and bracket_cost:\n            return abs(v)'),
    ("slash label accepted", '    if "/" in lab:\n        return None\n    if has_cost:', '    if False:\n        return None\n    if has_cost:'),
    ("mixed words without brackets accepted", '            return -v\n        return None\n    if "/" in lab:', '            return -v\n        return abs(v)\n    if "/" in lab:'),
    ("negative cost line refused", '    if has_cost:\n        return abs(v)', '    if has_cost:\n        return abs(v) if v >= 0 else None'),
    ("cost line keeps its brackets", '    if has_cost:\n        return abs(v)\n    # ', '    if has_cost:\n        return v\n    # '),
    ("gross income line accepted", '    net_line = any(w == "net" and (i + 1 == len(words) or words[i + 1] != "of") for i, w in enumerate(words))', '    net_line = True'),
    ("income line ignores the sign", 'any(w in FINANCE_WORDS for w in words):\n        return -v', 'any(w in FINANCE_WORDS for w in words):\n        return -abs(v)'),
    # --- terms and URLs
    ("grid margins may fall", "        if out and m < out[-1][1]:\n            return None", "        if False:\n            return None"),
    ("grid edges may tie", "(out and u <= out[-1][0])", "(out and u < out[-1][0])"),
    ("windows may overlap", 'if not t["report_seconds"] + t["cure_seconds"] < t["period_seconds"] <= MAX_PERIOD_SECONDS:', 'if not t["report_seconds"] < t["period_seconds"] <= MAX_PERIOD_SECONDS:'),
    ("short windows allowed", "MIN_WINDOW_SECONDS = 1800", "MIN_WINDOW_SECONDS = 60"),
    ("availability past maturity", 't["availability_end"] <= _maturity(t):', 't["availability_end"] <= _maturity(t) + 10**9:'),
    ("metadata range allowed", "or (a == 169 and b == 254)", ""),
    ("user info allowed", 'if "@" in authority:', "if False:"),
    ("query in the base address", 'if "?" in url or "#" in url:', "if False:"),
    ("base address without a slash", 'if not url.endswith("/") or url.count("/") < 3:', 'if url.count("/") < 3:'),
    ("history unbounded", "MAX_HISTORY = 150", "MAX_HISTORY = 10**6"),
    # --- final review fixes (17 Nov): credits, grace, scoped waivers
    ("payouts pushed, not credited", "        for a, v, _n in pays:\n            self._credit(a, v)", "        for a, v, _n in pays:\n            self._send(a, v)"),
    ("withdraw keeps the claim", "        self.claims[k] = u256(have - amount)\n", "        self.claims[k] = u256(have)\n"),
    ("withdraw leaves the total", "        self.claims_total = u256(int(self.claims_total) - amount)\n", ""),
    ("credit missing from the total", "            self.claims_total = u256(int(self.claims_total) + amount)\n", ""),
    ("refund without a facility lost", "            self._credit(gl.message.sender_address.as_hex, value)", "            pass"),
    ("credit not logged", '            if v > 0 and a.lower() in (f.lender.lower(), f.borrower.lower()):\n                _log(s, at, "CREDIT"', '            if False:\n                _log(s, at, "CREDIT"'),
    ("no grace before acceleration", 'if now < since + t["grace_seconds"]:', "if False:"),
    ("grace from the latest event", 'since = min(e["at"] for e in _open_events(s))', 'since = max(e["at"] for e in _open_events(s))'),
    ("grace may be short", "MIN_GRACE_SECONDS = 600", "MIN_GRACE_SECONDS = 0"),
    ("grace may exceed the cure window", 'if not MIN_GRACE_SECONDS <= t["grace_seconds"] <= t["cure_seconds"]:', 'if not MIN_GRACE_SECONDS <= t["grace_seconds"]:'),
    ("waiver scope ignored", '        codes = {"covenant": ("E1", "E2"), "payment": ("E3",), "all": ("E1", "E2", "E3")}[scope]', '        codes = ("E1", "E2", "E3")'),
    ("payment waiver covers the breach", '        if scope != "payment":', "        if True:"),
    ("covenant waiver covers payment", '{"covenant": ("E1", "E2"),', '{"covenant": ("E1", "E2", "E3"),'),
    ("pay with nothing sent goes on", '        if value <= 0:\n            return self._refund(f, s, held, pays, "send GEN with pay', '        if False:\n            return self._refund(f, s, held, pays, "send GEN with pay'),
    ("closed facility shows open windows", '    if s["state"] in ("CLOSED", "CANCELLED", "ACCELERATED"):\n        return "NOT_TESTED"', '    if s["state"] in ("CLOSED", "CANCELLED"):\n        return "NOT_TESTED"'),
    # --- second review of the fixes (17 Nov)
    ("lone bracketed cost word read as income", "    if has_cost and has_income:\n        if bracket_income and bracket_cost:", "    if True:\n        if bracket_income and bracket_cost:"),
    ("strangers' refunds logged", "            if v > 0 and a.lower() in (f.lender.lower(), f.borrower.lower()):", "            if v > 0:"),
    ("credit logged at the stored time", "        at = max(s[\"t\"], self._now())", "        at = s[\"t\"]"),
    ("withdraw more than credited", "        if not 0 < amount <= have:", "        if not 0 < amount:"),
    ("withdraw of 0 takes nothing", "        if amount == 0:\n            amount = have", "        if False:\n            amount = have"),
    ("income line without a finance word accepted", " and not bracket_income and any(w in FINANCE_WORDS for w in words):", " and not bracket_income:"),
    ("bracketed income word on an income line accepted", "if has_income and net_line and not bracket_income and", "if has_income and net_line and"),
    ("net of tax counts as net", 'words[i + 1] != "of")', 'True)'),
]


def main() -> int:
    only = {int(a) for a in sys.argv[1:]}
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    caught = total = 0
    missed = []
    tmp = Path(tempfile.mkdtemp(prefix="pcg-mutants-"))
    for i, (name, old, new) in enumerate(MUTANTS, 1):
        n = SRC.count(old)
        if n != 1:
            print(f"SETUP ERROR  {i} {name}: pattern found {n} times")
            return 2
        if only and i not in only:
            continue
        total += 1
        path = tmp / f"mutant_{i:03d}.py"
        path.write_text(SRC.replace(old, new))
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/direct", "-q", "-x", "-p", "no:cacheprovider"],
                           cwd=ROOT, env={**env, "PCG_CONTRACT": str(path)}, capture_output=True, text=True)
        ok = r.returncode != 0
        caught += ok
        if not ok:
            missed.append(i)
        print(f"{'caught ' if ok else 'MISSED '} {i:3d} {name}", flush=True)
    print(f"\n{caught} of {total} mutants caught" + (f"; missed: {missed}" if missed else ""))
    return 0 if caught == total else 1


if __name__ == "__main__":
    sys.exit(main())
