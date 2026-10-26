# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def test_threads():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = await browser.contexts[0].new_page()
        await page.goto("https://www.threads.net/", timeout=60000)
        await asyncio.sleep(4)
        print("URL:", page.url)
        print("Title:", await page.title())
        
        # Check create button
        create_btn = page.locator('svg[aria-label="Tạo"], svg[aria-label="Create"], [aria-label="Tạo"], [aria-label="Create"]')
        count = await create_btn.count()
        print("Create button count:", count)
        
        # Find all buttons
        btns = await page.locator("button, [role='button']").all()
        for i, b in enumerate(btns[:30]):
            try:
                t = (await b.inner_text()).strip()
                a = await b.get_attribute("aria-label")
                if t or a:
                    print(f"Btn {i}: text={t!r}, aria={a!r}")
            except Exception:
                pass

asyncio.run(test_threads())
