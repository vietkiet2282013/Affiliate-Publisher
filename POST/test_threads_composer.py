# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def test_threads_composer():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = browser.contexts[0].pages[-1]
        
        # Click "Thread mới" hoặc "Có gì mới?"
        btn = page.locator("text='Thread mới'").first
        if await btn.count() > 0:
            await btn.click()
            await asyncio.sleep(2)
        
        # Check inputs and buttons in modal
        inputs = await page.locator("input, [contenteditable='true']").all()
        print("Inputs in composer:", len(inputs))
        for idx, inp in enumerate(inputs):
            tag = await inp.evaluate("e => e.tagName")
            typ = await inp.get_attribute("type")
            ce = await inp.get_attribute("contenteditable")
            print(f"Input {idx}: tag={tag}, type={typ}, contenteditable={ce}")
            
        modal_btns = await page.locator("button, [role='button']").all()
        for idx, b in enumerate(modal_btns):
            t = (await b.inner_text()).strip()
            a = await b.get_attribute("aria-label")
            if t or a:
                print(f"Modal btn {idx}: text={t!r}, aria={a!r}")

asyncio.run(test_threads_composer())
