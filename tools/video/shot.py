"""Screenshots of the live site for the demo video.

    python3 shot.py            # Bradbury facility #3 (Brenthollow) and the front page
"""
import os
from playwright.sync_api import sync_playwright

SITE = "https://privatecredit.brilliantnodes.com"
proxy = {"server": os.environ["HTTPS_PROXY"]} if os.environ.get("HTTPS_PROXY") else None
with sync_playwright() as p:
    b = p.chromium.launch(proxy=proxy) if proxy else p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 1400}, device_scale_factor=1.5, ignore_https_errors=True)
    pg.goto(f"{SITE}/?net=bradbury&id=3", wait_until="domcontentloaded", timeout=90000)
    pg.locator("#fac-periods tbody tr").first.wait_for(timeout=120000)
    pg.add_style_tag(content=".top { position: static !important; }")
    pg.wait_for_timeout(1500)
    el = pg.locator("#fac")
    el.screenshot(path="shot_facility.jpg", type="jpeg", quality=92)
    box = el.bounding_box()
    print("shot_facility.jpg", box["width"], box["height"], round(box["height"] / box["width"], 4))
    pg.locator("#demo").screenshot(path="shot_cards.jpg", type="jpeg", quality=92)
    box = pg.locator("#demo").bounding_box()
    print("shot_cards.jpg", box["width"], box["height"], round(box["height"] / box["width"], 4))
    pg.close()
    pg = b.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=1.5)
    pg.goto("file:///home/claude/privatecredit-gate/docs/reports/brenthollow/bradbury-1/period-1.html")
    pg.wait_for_timeout(500)
    pg.screenshot(path="shot_report.jpg", type="jpeg", quality=92, full_page=True)
    print("shot_report.jpg", pg.evaluate("[document.body.scrollWidth, document.body.scrollHeight]"))
    b.close()
