# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def check_progress():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        info = await page.evaluate("""() => {
            const pb = document.querySelector('[role="progressbar"], [aria-valuenow]');
            const textUploading = Array.from(document.querySelectorAll('div, span'))
                .find(el => el.innerText && el.innerText.includes('Đang tải file'));
            return {
                progressbar: pb ? { now: pb.getAttribute('aria-valuenow'), max: pb.getAttribute('aria-valuemax') } : null,
                uploadingText: textUploading ? textUploading.innerText.trim() : null
            };
        }""")
        print(info)

asyncio.run(check_progress())
