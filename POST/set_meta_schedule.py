# -*- coding: utf-8 -*-
import asyncio
import sys
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAPTION_FB = """Thách thức thái đậu phụ non thành lụa và cái kết! Chiếc bàn nạo rau củ chân ái cho hội sợ dao kéo: thái lát mỏng, nạo sợi gừng tỏi đều tăm tắp, có khay thoát nước rửa trực tiếp cực sạch.

🛒 Link mua hàng chính hãng giá ưu đãi: https://s.shopee.vn/8AWQEzTQ4q

#noithatdungthat #reviewthat #bannaodanang #dungcubep #meovathay #giadungtienich #reviewhangtieudung"""

CAPTION_IG = """Tưởng không ngon mà ngon không tưởng! Test thử bàn nạo đa năng thái từ gừng, tỏi đến cả đậu phụ non mà mịn tưng. Quan trọng nhất là có khung kẹp bảo vệ tay, thái nhanh cỡ nào cũng không lo bay móng tay nhé!

🔗 Link mua sắm chuẩn xịn: https://s.shopee.vn/8AWQEzTQ4q

#reelsvn #noithatdungthat #bannaoraucu #reviewdogiadung #giadungthongminh #dogiadungtienich #nhabepxinh #foryou"""

async def set_meta():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:49958")
        page = None
        for pg in browser.contexts[0].pages:
            if "business.facebook.com" in pg.url:
                page = pg
                break
        
        # 1. Điền caption Facebook
        print("1. Chọn tab Facebook...")
        fb_tab = page.locator("div[role='tab']:has-text('Facebook'), div:has-text('Facebook')").filter(has_text="Facebook").last
        # Thử tìm nút chuyển tab Facebook / Instagram
        tab_buttons = await page.locator("div[role='button'], button").all()
        for b in tab_buttons:
            t = (await b.inner_text()).strip()
            if t == "Facebook":
                await b.click()
                print("Clicked Facebook tab button!")
                break
        await asyncio.sleep(1)

        # Tìm textarea hoặc contenteditable cho Facebook
        editor = page.locator("div[contenteditable='true']").first
        if await editor.count() > 0:
            await editor.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.insert_text(CAPTION_FB)
            print("Đã điền caption Facebook!")
        await asyncio.sleep(1)

        # 2. Điền caption Instagram
        print("2. Chọn tab Instagram...")
        for b in tab_buttons:
            t = (await b.inner_text()).strip()
            if t == "Instagram":
                await b.click()
                print("Clicked Instagram tab button!")
                break
        await asyncio.sleep(1)

        editor = page.locator("div[contenteditable='true']").first
        if await editor.count() > 0:
            await editor.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await page.keyboard.insert_text(CAPTION_IG)
            print("Đã điền caption Instagram!")
        await asyncio.sleep(1)

        # 3. Cài đặt giờ hẹn Facebook: 12:01 ngày 28/09/2026
        # Input 3 là giờ Facebook, Input 4 là phút Facebook
        # Input 6 là giờ Instagram, Input 7 là phút Instagram
        inputs = await page.locator("input").all()
        print("3. Điền giờ hẹn Facebook (12:01)...")
        # Giờ FB (inp 3)
        await inputs[3].click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await inputs[3].fill("12")
        await asyncio.sleep(0.5)

        # Phút FB (inp 4)
        await inputs[4].click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await inputs[4].fill("01")
        await asyncio.sleep(0.5)

        # 4. Cài đặt giờ hẹn Instagram: 11:55 ngày 28/09/2026
        print("4. Điền giờ hẹn Instagram (11:55)...")
        # Giờ IG (inp 6)
        await inputs[6].click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await inputs[6].fill("11")
        await asyncio.sleep(0.5)

        # Phút IG (inp 7)
        await inputs[7].click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await inputs[7].fill("55")
        await asyncio.sleep(0.5)

        print("Hoàn tất cập nhật Caption và Giờ hẹn Meta!")

asyncio.run(set_meta())
