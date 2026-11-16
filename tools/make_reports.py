#!/usr/bin/env python3
"""Write the demo borrowers' compliance-report pages for one deployment.

    python tools/make_reports.py <deployment-tag> <first_period_end_unix> <period_seconds> [--only slug] [--variant slug:period:style]

Pages go to web/public/reports/<slug>/<tag>/period-<n>.html, so each
facility's frozen report_base_url is
https://privatecredit.brilliantnodes.com/reports/<slug>/<tag>/

Every company and figure is fictional. A page states the period end to the
minute, the currency code, the scale and the LTM labels, exactly as the
contract's reading expects. Styles:
  table          figures in a table under a heading such as "EUR thousands"
  prose          figures in sentences, each with its own scale
  units_missing  a table with no scale anywhere (a reading gives N2)
  not_published  a notice that the report is not yet published
"""
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "examples" / "demo_cases.json").read_text())


def fmt_time(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M")


def fmt_thousands(v):
    s = f"{abs(v):,}"
    return f"({s})" if v < 0 else s


def fmt_millions(v):
    m = abs(v) / 1000
    s = f"{m:,.1f}" if round(m, 1) == round(m, 3) else f"{m:,.2f}"
    return f"({s})" if v < 0 else s


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{company} - compliance certificate, period {n}</title>
<style>
body{{font-family:Georgia,'Times New Roman',serif;max-width:760px;margin:40px auto;padding:0 20px;color:#1d2330;background:#fbfaf7;line-height:1.55}}
header{{border-bottom:2px solid #1d2330;margin-bottom:24px}}
h1{{font-size:28px;margin:0}} h2{{font-size:19px;font-weight:normal;margin:6px 0 14px}}
table{{border-collapse:collapse;width:100%;margin:18px 0}} th,td{{padding:9px 10px;border-bottom:1px solid #d8d4ca;text-align:left}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}} .meta{{color:#555;font-size:15px}}
footer{{margin-top:40px;padding-top:12px;border-top:1px solid #d8d4ca;color:#777;font-size:13px}}
.notice{{padding:18px;border:1px solid #c9b98a;background:#fff8e3}}
</style>
</head>
<body>
<header>
<h1>{company}</h1>
<h2>Investor relations: covenant compliance certificate</h2>
</header>
{body}
<footer>{company} is a fictional company. This page is demo data for PrivateCreditGate, a GenLayer Intelligent Contract; it is not a real report.</footer>
</body>
</html>
"""


def body_table(c, n, f, end, with_scale=True):
    unit = f"{c['currency']} thousands" if with_scale else c["currency"]
    caption = (f"All figures in {c['currency']} thousands. EBITDA and net finance costs are for the last twelve months (LTM) to the period end."
               if with_scale else
               "EBITDA and net finance costs are for the last twelve months (LTM) to the period end.")
    rows = [
        ("LTM EBITDA", f["ltm_ebitda"]),
        ("LTM net finance costs", f["ltm_net_finance_costs"]),
        ("Total borrowings (total debt)", f["total_debt"]),
        ("Cash and cash equivalents", f["cash"]),
    ]
    trs = "\n".join(f"<tr><td>{html.escape(k)}</td><td class=\"num\">{fmt_thousands(v)}</td></tr>" for k, v in rows)
    return f"""<p class="meta">Test period {n}. Period ended: <strong>{fmt_time(end)} UTC</strong>. Reporting currency: {c['currency']}. Status: final.</p>
<p>{caption}</p>
<table>
<thead><tr><th>Measure</th><th class="num">{html.escape(unit)}</th></tr></thead>
<tbody>
{trs}
</tbody>
</table>
<p>The Chief Financial Officer confirms that these figures are final and have been prepared on the basis set out in the facility agreement.</p>"""


def body_prose(c, n, f, end):
    cur = c["currency"]
    return f"""<p class="meta">Test period {n}. Period ended: <strong>{fmt_time(end)} UTC</strong>. Reporting currency: {cur}. Status: final.</p>
<p>For the last twelve months (LTM) to {fmt_time(end)} UTC, {html.escape(c['company'])} recorded LTM EBITDA of {cur} {fmt_millions(f['ltm_ebitda'])} million and LTM net finance costs of {cur} {fmt_millions(f['ltm_net_finance_costs'])} million.</p>
<p>At the period end, total borrowings stood at {cur} {fmt_millions(f['total_debt'])} million, and cash and cash equivalents were {cur} {fmt_millions(f['cash'])} million.</p>
<p>The board confirms that these figures are final.</p>"""


def body_not_published(c, n, end):
    return f"""<div class="notice"><p><strong>Not yet published.</strong> The compliance certificate for test period {n} (period ended {fmt_time(end)} UTC) is not yet published. It will be posted on this page when it is available.</p></div>"""


def page(c, n, style, end):
    f = c["periods"][n] if n < len(c["periods"]) else None
    if style == "not_published" or f is None:
        body = body_not_published(c, n, end)
    elif style == "prose":
        body = body_prose(c, n, f, end)
    elif style == "units_missing":
        body = body_table(c, n, f, end, with_scale=False)
    else:
        body = body_table(c, n, f, end)
    return PAGE.format(company=html.escape(c["company"]), n=n, body=body)


def main(argv):
    tag, e0, p = argv[0], int(argv[1]), int(argv[2])
    only = None
    variants = {}
    i = 3
    while i < len(argv):
        if argv[i] == "--only":
            only = argv[i + 1]
            i += 2
        elif argv[i] == "--variant":
            slug, n, style = argv[i + 1].split(":")
            variants[(slug, int(n))] = style
            i += 2
        else:
            raise SystemExit("unknown argument " + argv[i])
    written = []
    for c in CASES["cases"]:
        if only and c["slug"] != only:
            continue
        out = ROOT / "web" / "public" / "reports" / c["slug"] / tag
        out.mkdir(parents=True, exist_ok=True)
        for n in range(CASES["num_periods"]):
            style = variants.get((c["slug"], n), c["styles"][n])
            path = out / f"period-{n}.html"
            path.write_text(page(c, n, style, e0 + n * p))
            written.append(str(path.relative_to(ROOT)))
    print("\n".join(written))


if __name__ == "__main__":
    main(sys.argv[1:])
