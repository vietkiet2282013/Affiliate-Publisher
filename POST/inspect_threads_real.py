# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_threads():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "threads.com" in pg.url or "threads.net" in pg.url:
                page = pg
                break
        
        print("Threads page:", page.url)
        # Click compose box
        compose_trigger = page.locator("text='Có gì mới?'").first
        if await compose_trigger.count() > 0:
            print("Found trigger 'Có gì mới?' -> clicking")
            await compose_trigger.click()
            await asyncio.sleep(2)
        
        inputs = await page.locator("input, [contenteditable='true']").all()
        print("Inputs in Threads:", len(inputs))
        for idx, inp in enumerate(inputs):
            tag = await inp.evaluate("e => e.tagName")
            typ = await inp.get_attribute("type")
            ce = await inp.get_attribute("contenteditable")
            print(f"Input {idx}: tag={tag}, type={typ}, contenteditable={ce}")

        btns = await page.locator("button, [role='button']").all()
        for idx, b in enumerate(btns[:40]):
            t = (await b.inner_text()).strip()
            a = await b.get_attribute("aria-label")
            if t or a:
                print(f"Btn {idx}: text={t!r}, aria={a!r}")

asyncio.run(inspect_threads())
