# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_meta_details():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        cbs = await page.locator("input[type='checkbox']").all()
        print("Checkbox count:", len(cbs))
        for idx, cb in enumerate(cbs):
            chk = await cb.is_checked()
            txt = await cb.evaluate("e => e.closest('div, label, span').innerText.slice(0, 80)")
            print(f"CB {idx}: checked={chk}, text={txt!r}")

        date_inputs = await page.locator("input[placeholder='dd/mm/yyyy']").all()
        print("Date inputs count:", len(date_inputs))
        for idx, di in enumerate(date_inputs):
            val = await di.input_value()
            lbl = await di.evaluate("e => e.closest('div').innerText.slice(0, 80)")
            print(f"DateInput {idx}: val={val!r}, context={lbl!r}")

        # Check time inputs
        inputs = await page.locator("input").all()
        for idx, inp in enumerate(inputs):
            v = await inp.input_value()
            ph = await inp.get_attribute("placeholder")
            t = await inp.get_attribute("type")
            if v or ph:
                print(f"Input {idx}: type={t}, val={v!r}, ph={ph!r}")

asyncio.run(inspect_meta_details())
