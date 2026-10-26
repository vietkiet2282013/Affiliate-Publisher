# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_time_groups():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        info = await page.evaluate("""() => {
            const inputs = Array.from(document.querySelectorAll('input'));
            function getContext(el) {
                let curr = el;
                for (let i = 0; i < 7; i++) {
                    if (!curr) break;
                    if (curr.innerText && (curr.innerText.includes('Facebook') || curr.innerText.includes('Instagram'))) {
                        return curr.innerText.replace(/\\s+/g, ' ').slice(0, 150);
                    }
                    curr = curr.parentElement;
                }
                return curr ? curr.innerText.replace(/\\s+/g, ' ').slice(0, 150) : '';
            }
            return {
                inp2_context: getContext(inputs[2]),
                inp5_context: getContext(inputs[5])
            };
        }""")
        print("Input 2 (Group 1):", info.get("inp2_context"))
        print("Input 5 (Group 2):", info.get("inp5_context"))

asyncio.run(inspect_time_groups())
