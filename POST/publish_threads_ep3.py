# -*- coding: utf-8 -*-
import sys, os, time, requests, json
sys.stdout.reconfigure(encoding="utf-8")
POST_DIR = r"C:\Affiliate\post1\POST"
sys.path.insert(0, POST_DIR)

from uploaders import ThreadsAPIUploader

brands = json.load(open("C:/Affiliate/post1/POST/config/brands.json", encoding="utf-8"))
th_cfg = brands["yeu_da_hon_bo"]["threads"]
video_path = r"C:\Affiliate\Yêu Da Hơn Bồ\Video_việt_hóa\3.mp4"

th_caption = (
    "Ai bị nọng cằm với quầng thâm mắt mệt mỏi thì tham khảo ngay bộ đôi này! Mặt nạ định hình cằm V-line đeo 30p là cằm thon gọn thấy rõ, thêm mặt nạ mắt collagen mờ nhăn dưỡng ẩm sâu ✨\n\n"
    "🛒 Link sắm đồ dưỡng da chính hãng nè cả nhà:\n"
    "1. Mặt nạ V-Line thon gọn cằm: https://s.shopee.vn/7VGb8yx53d\n"
    "2. Mặt nạ mắt Lanbena Collagen: https://s.shopee.vn/AUuCiUlez0\n\n"
    "#yeudahonbo #skincare #vlinemask #eyecare"
)
th_comments = [
    "Link sản phẩm ở đây: https://s.shopee.vn/7VGb8yx53d",
    "Link sản phẩm: https://s.shopee.vn/3LR2BKCwVw",
    "Link sản phẩm ở đây nha mọi người: https://s.shopee.vn/4VczZT8V9H",
    "Link sản phẩm ở đây, mọi người ủng hộ nhé: https://s.shopee.vn/LnQboOMba",
    "Link xem và mua hàng ngay tại đây nè: https://s.shopee.vn/1VzNzxJvEv",
    "Link sản phẩm ở đây cho ai cần nha: https://s.shopee.vn/8AWHwCuXiK",
    "Mọi người xem chi tiết và đặt hàng tại link này nhé: https://s.shopee.vn/905OvjrN1b",
    "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: https://s.shopee.vn/AUuCiUlez0",
    "Mình để sẵn link mua hàng ở đây cho mọi người nè: https://s.shopee.vn/60RnME2n7F",
    "Bạn nào quan tâm thì bấm trực tiếp vào link này nha: https://s.shopee.vn/7VGb8yx54e",
    "Link sp mình mua ở đây nhé, mọi người tham khảo nha: https://s.shopee.vn/30oBmiEDCt"
]

print("🚀 BẮT ĐẦU ĐĂNG BÙ THREADS (TẬP 3)...", flush=True)
th = ThreadsAPIUploader(threads_user_id=th_cfg["user_id"], access_token=th_cfg["access_token"])
res_th = th.upload_video_thread(video_path=video_path, caption=th_caption, comment_link=None)
print("✅ Kết quả Threads:", res_th, flush=True)

if res_th and "id" in res_th:
    post_id = res_th["id"]
    print("💬 Đang reply link bình luận Threads...", flush=True)
    for idx, cmt in enumerate(th_comments, 1):
        time.sleep(2)
        r_c = requests.post(
            f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads",
            data={"media_type": "TEXT_POST", "text": cmt, "reply_to_id": post_id, "access_token": th_cfg["access_token"]},
            timeout=20
        ).json()
        if "id" in r_c:
            pub_c = requests.post(
                f"https://graph.threads.net/v1.0/{th_cfg['user_id']}/threads_publish",
                data={"creation_id": r_c["id"], "access_token": th_cfg["access_token"]},
                timeout=20
            ).json()
            print(f"  ✅ Reply Threads {idx}: {cmt[:45]}...", flush=True)
