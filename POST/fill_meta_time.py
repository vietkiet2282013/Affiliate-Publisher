# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def fill_spinbuttons():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        spinbuttons = await page.locator("input[role='spinbutton']").all()
        print("Spinbuttons found:", len(spinbuttons))
        
        # spinbuttons[0]: FB Gio -> 12
        # spinbuttons[1]: FB Phut -> 01
        # spinbuttons[2]: IG Gio -> 11
        # spinbuttons[3]: IG Phut -> 55
        
        targets = [("12", spinbuttons[0]), ("01", spinbuttons[1]), ("11", spinbuttons[2]), ("55", spinbuttons[3])]
        
        for val, sb in targets:
            await sb.click()
            await page.keyboard.press("Control+A")
            for digit in val:
                await page.keyboard.press(digit)
                await asyncio.sleep(0.1)
            await page.keyboard.press("Tab")
            await asyncio.sleep(0.5)
            
        await asyncio.sleep(2)
        await page.screenshot(path=r"C:\Affiliate\post1\POST\meta_time_filled.png")
        print("Saved meta_time_filled.png")

asyncio.run(fill_spinbuttons())
