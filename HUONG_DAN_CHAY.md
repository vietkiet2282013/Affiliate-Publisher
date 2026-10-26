# 🚀 Hướng Dẫn Chạy Affiliate Dashboard

## Cách chạy nhanh nhất (1 click)

**Double-click file:** `CHAY_DASHBOARD.bat` trong thư mục `C:\Affiliate\post1\`

Sau đó mở trình duyệt vào: **http://localhost:5000**

---

## Cách chạy bằng lệnh (trong PowerShell / Terminal)

```powershell
& "C:\Affiliate\python311\python.exe" "C:\Affiliate\post1\app.py" --port 5000
```

---

## Khi có code mới (sửa file .py)

1. **Tắt server cũ**: Nhấn `Ctrl + C` ở cửa sổ đang chạy server
2. **Chạy lại**: Double-click `CHAY_DASHBOARD.bat` hoặc chạy lệnh ở trên

> ⚠️ Flask server không tự reload khi sửa code. Bạn **phải tắt rồi mở lại**.

---

## Cấu trúc quan trọng

| File / Thư mục | Mô tả |
|---|---|
| `C:\Affiliate\python311\` | Python 3.11 embedded (KHÔNG bị AppLocker chặn) |
| `C:\Affiliate\post1\app.py` | File chính của server Flask |
| `C:\Affiliate\post1\POST\config\brands.json` | Config 10 kênh + token vĩnh viễn |
| `C:\Affiliate\post1\POST\advanced_analytics.py` | Logic tính Ad Decision Score |
| `C:\Affiliate\post1\templates\index.html` | Giao diện Dashboard |
| `C:\Affiliate\post1\CHAY_DASHBOARD.bat` | File khởi động nhanh Dashboard |
| `C:\Affiliate\post1\CHAY_HEN_GIO_WORKER.bat` | Tiến trình chạy ngầm quét & xuất bản hẹn giờ (Instagram, Threads) |

---

## Cài thêm thư viện Python

```powershell
& "C:\Affiliate\python311\python.exe" -m pip install <tên-package>
```

> ❌ KHÔNG dùng `pip install` trực tiếp (bị AppLocker chặn)
> ✅ Luôn dùng `"C:\Affiliate\python311\python.exe" -m pip install ...`

---

## Khắc phục sự cố

| Lỗi | Cách sửa |
|---|---|
| Port 5000 đang bị chiếm | Đổi port: `--port 5001` |
| Token hết hạn | Token FB/IG hiện tại là **vĩnh viễn**, không hết hạn |
| `ModuleNotFoundError` | Cài module thiếu: `python.exe -m pip install <tên>` |
| AppLocker chặn | Dùng `C:\Affiliate\python311\python.exe` thay vì `.venv` |
