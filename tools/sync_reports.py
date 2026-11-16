#!/usr/bin/env python3
"""Copy the report pages from web/public/reports to docs/reports, so a page
change goes live on GitHub Pages without rebuilding the whole site."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src, dst = ROOT / "web" / "public" / "reports", ROOT / "docs" / "reports"
for f in src.rglob("*.html"):
    out = dst / f.relative_to(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() or out.read_bytes() != f.read_bytes():
        shutil.copyfile(f, out)
print("synced")
