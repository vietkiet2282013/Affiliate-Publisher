# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_destinations():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        info = await page.evaluate("""() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            return inputs.map((inp, idx) => {
                let p = inp;
                let text = '';
                for (let i = 0; i < 5; i++) {
                    if (!p) break;
                    if (p.innerText && p.innerText.trim()) {
                        text = p.innerText.trim().replace(/\\s+/g, ' ');
                        break;
                    }
                    p = p.parentElement;
                }
                return { idx, type: inp.type, val: inp.value, checked: inp.checked, text: text.slice(0, 80) };
            });
        }""")
        for item in info:
            print(item)

asyncio.run(inspect_destinations())
