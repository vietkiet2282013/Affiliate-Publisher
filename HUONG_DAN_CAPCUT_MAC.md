# Hướng Dẫn Tối Ưu CapCut & Dọn Dẹp Cache Cho macOS (Apple Silicon / Intel)

Tài liệu này bao gồm **Prompt cho AI Agent** và **Script Shell cho macOS** để tắt hoàn toàn tính năng làm nét AI (`QualityEnhance`) và dọn dẹp hàng chục GB cache `videoAlg` của CapCut trên máy Mac.

---

## 🤖 1. PROMPT CHO AI AGENT (Copy dán cho AI trên máy Mac)

```markdown
Tôi đang chạy project tự động hóa video CapCut trên macOS. 
Nhiệm vụ của bạn:
1. Mở file script `auto_batch_capcut.py` (hoặc module tạo draft template CapCut):
   - Tìm đoạn gán thuộc tính `video_algorithm` vào `main_v` (video chính).
   - Xóa bỏ hoặc đặt `"video_algorithm": None` (hoặc `"algorithms": []`, xóa `"QualityEnhance"`, `"super_resolution"`, `"quality_enhance"`).
   - Mục đích: Ngăn chặn CapCut tự động render upscale video bằng AI, giúp project siêu nhẹ, mở tức thì và không bị giật lag trên macOS.
2. Kiểm tra đường dẫn CapCut Projects trên macOS:
   - Trên macOS, thư mục dự án mặc định nằm tại:
     `~/Movies/CapCut/User Data/Projects` hoặc 
     `~/Library/Containers/com.lemon.cuteditor/Data/Movies/CapCut/User Data/Projects`
   - Đảm bảo script tạo draft đúng đường dẫn trên macOS nếu chạy trên Mac.
3. Chạy script dọn dẹp cache `clean_capcut_cache_mac.sh` đi kèm để xóa toàn bộ các thư mục `videoAlg` và file cache rác đã chiếm dụng dung lượng ổ cứng.
```

---

## 💻 2. SCRIPT TỰ ĐỘNG DỌN DẸP CACHE CAPCUT TRÊN MACOS

Tệp script: `clean_capcut_cache_mac.sh`

### Cách chạy trên macOS Terminal:
```bash
chmod +x clean_capcut_cache_mac.sh
./clean_capcut_cache_mac.sh
```

Nội dung script tự động tìm và xóa tất cả cache `videoAlg`, `draft_content_temp`, `Cache`, `Proxy` của CapCut trên Mac để giải phóng hàng chục GB ổ cứng.
