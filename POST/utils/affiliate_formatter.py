# -*- coding: utf-8 -*-
"""
Helper định dạng link sản phẩm Affiliate và Comment theo đúng chuẩn SEO và format người dùng yêu cầu:

Format mẫu:
1. Link sản phẩm ở đây: <link>
2. Link xem và mua hàng ngay tại đây nè: <link>
3. Link sản phẩm ở đây nha mọi người: <link>
4. Link sản phẩm ở đây, mọi người ủng hộ nhé: <link>
5. Link sản phẩm: <link>
6. Link sản phẩm: <link>
"""
from typing import List

AFF_PREFIX_TEMPLATES = [
    "Link sản phẩm ở đây cho ai cần nha: ",
    "Link sp mình mua ở đây nhé, mọi người tham khảo nha: ",
    "Link săn deal/mua hàng chính hãng ở đây nha cả nhà: ",
    "Mình để sẵn link mua hàng ở đây cho mọi người nè: ",
    "Link sản phẩm ở đây: "
]

def format_affiliate_lines(links: List[str]) -> List[str]:
    """
    Định dạng danh sách link affiliate theo đúng thứ tự ưu tiên SEO.
    """
    formatted = []
    for idx, url in enumerate(links):
        prefix = AFF_PREFIX_TEMPLATES[idx % len(AFF_PREFIX_TEMPLATES)]
        formatted.append(f"{prefix}{url}")
    return formatted

def format_affiliate_caption(links: List[str]) -> str:
    """
    Trả về chuỗi text chứa danh sách link đã format.
    """
    return "\n".join(format_affiliate_lines(links))
