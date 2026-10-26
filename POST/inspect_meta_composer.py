# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_meta_composer():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        if not page:
            print("Meta composer page not found!")
            return
            
        print("Page URL:", page.url)
        print("Title:", await page.title())
        
        # Check inputs and buttons
        inputs = await page.locator("input, [contenteditable='true']").all()
        print("Inputs in Meta composer:", len(inputs))
        for idx, inp in enumerate(inputs[:15]):
            tag = await inp.evaluate("e => e.tagName")
            typ = await inp.get_attribute("type")
            ce = await inp.get_attribute("contenteditable")
            ph = await inp.get_attribute("placeholder")
            print(f"Input {idx}: tag={tag}, type={typ}, contenteditable={ce}, placeholder={ph!r}")

        btns = await page.locator("button, [role='button']").all()
        for idx, b in enumerate(btns[:30]):
            t = (await b.inner_text()).strip()
            a = await b.get_attribute("aria-label")
            if t or a:
                print(f"Btn {idx}: text={t!r}, aria={a!r}")

asyncio.run(inspect_meta_composer())
