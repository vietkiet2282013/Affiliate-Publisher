# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_time_inputs():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        info = await page.evaluate("""() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            return inputs.map((inp, idx) => ({
                idx,
                type: inp.type,
                val: inp.value,
                html: inp.outerHTML,
                parentText: inp.parentElement ? inp.parentElement.innerText.replace(/\\s+/g, ' ') : ''
            }));
        }""")
        for item in info:
            if any(k in item['parentText'] for k in ['00', '11', '12', 'Tháng', ':']):
                print(item)

asyncio.run(inspect_time_inputs())
