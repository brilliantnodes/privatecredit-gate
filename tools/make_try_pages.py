#!/usr/bin/env python3
"""Report pages for visitors who open their own facility on the site.

Two fictional borrowers, one page set per hourly slot (period 0 ends on the
hour, UTC), for the next DAYS days:
  kelvardine  Kelvardine Shipping Ltd: compliant every period
  pellingrove  Pellingrove Foods plc: period-1 leverage 3.73x, a curable breach

    python tools/make_try_pages.py [days]

Pages go to web/public/reports/try/<slug>/s<E0>/period-<n>.html; a slot's
pages never change once written. Old slots are left in place.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_reports as mr  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
P = mr.CASES["terms"]["period_seconds"]
TRY = [
    {"slug": "kelvardine", "company": "Kelvardine Shipping Ltd", "currency": "EUR", "styles": ["table"] * 3,
     "periods": [{"ltm_ebitda": 16200, "ltm_net_finance_costs": 1900, "total_debt": 36800, "cash": 7100},
                 {"ltm_ebitda": 16500, "ltm_net_finance_costs": 1950, "total_debt": 37900, "cash": 7300},
                 {"ltm_ebitda": 16900, "ltm_net_finance_costs": 2000, "total_debt": 36500, "cash": 7900}]},
    {"slug": "pellingrove", "company": "Pellingrove Foods plc", "currency": "EUR", "styles": ["table"] * 3,
     "periods": [{"ltm_ebitda": 13800, "ltm_net_finance_costs": 1800, "total_debt": 42500, "cash": 5100},
                 {"ltm_ebitda": 13100, "ltm_net_finance_costs": 1900, "total_debt": 54000, "cash": 5100},
                 {"ltm_ebitda": 13600, "ltm_net_finance_costs": 1900, "total_debt": 47000, "cash": 5400}]},
]


def main(days=10):
    now = int(time.time())
    first = (now // 3600 + 1) * 3600
    n_written = 0
    for c in TRY:
        for e0 in range(first, first + days * 86400, 3600):
            out = ROOT / "web" / "public" / "reports" / "try" / c["slug"] / f"s{e0}"
            if out.exists():
                continue
            out.mkdir(parents=True)
            for n in range(3):
                (out / f"period-{n}.html").write_text(mr.page(c, n, "table", e0 + n * P))
                n_written += 1
    print(f"{n_written} pages written")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
