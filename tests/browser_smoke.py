"""Headless browser smoke test for the dependency-free static grading UI.

Run: python -m pip install playwright && python -m playwright install chromium
Then: python tests/browser_smoke.py
"""
import csv
from io import StringIO
from pathlib import Path

from playwright.sync_api import sync_playwright


def smoke_browser():
    page_markup = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_text(
        encoding="utf-8"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height in ((1300, 860), (390, 844)):
                context = browser.new_context(
                    viewport={"width": width, "height": height}, accept_downloads=True
                )
                try:
                    page = context.new_page()
                    failures = []
                    requests = []
                    page.on("pageerror", lambda exc: failures.append(str(exc)))
                    page.on("console", lambda msg: failures.append(msg.text) if msg.type == "error" else None)
                    page.on("request", lambda request: requests.append(request.url))
                    page.set_content(page_markup, wait_until="load")

                    page.get_by_role("button", name="Describe grades").click()
                    assert "Select at least one observed grade" in page.locator("#error").inner_text()

                    page.locator("#mallampati").select_option("2")
                    page.locator("#cormack").select_option("3")
                    page.locator("#tmd").fill("6.5")
                    page.get_by_role("button", name="Describe grades").click()
                    result = page.locator("#results").inner_text()
                    assert "Soft palate, fauces and uvula visible" in result
                    assert "Epiglottis visible, but glottis not seen" in result
                    assert "6.5 cm" in result

                    with page.expect_download() as pending:
                        page.get_by_role("button", name="Export CSV").click()
                    data = Path(pending.value.path()).read_text(encoding="utf-8")
                    rows = list(csv.DictReader(StringIO(data)))
                    assert len(rows) == 1
                    assert rows[0]["mallampati"] == "2"
                    assert rows[0]["cormack_lehane"] == "3"

                    page.get_by_role("button", name="Clear").click()
                    assert page.locator("#export").is_disabled()
                    assert "Select at least one observed grade" in page.locator("#results").inner_text()

                    page.locator("#mallampati").select_option("1")
                    page.locator("#tmd").fill("-1")
                    page.get_by_role("button", name="Describe grades").click()
                    assert "positive finite" in page.locator("#error").inner_text()
                    assert page.locator("#export").is_disabled()
                    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                    assert not failures, failures
                    assert not requests, requests
                    print(f"Browser smoke passed at {width}px")
                finally:
                    context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    smoke_browser()
