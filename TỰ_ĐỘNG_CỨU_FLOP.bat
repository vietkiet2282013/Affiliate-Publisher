@echo off
chcp 65001 >nul
title TỰ ĐỘNG CỨU FLOP VIDEO YOUTUBE VÀ FACEBOOK
color 0A

echo =======================================================================
echo          HỆ THỐNG TỰ ĐỘNG CỨU FLOP VIDEO BẰNG AI (GEMINI)
echo                Áp dụng: YouTube Shorts & Facebook Reels
echo =======================================================================
echo.
echo [1/3] Đang kiểm tra môi trường...
cd /d "C:\Affiliate"
if not exist "C:\Affiliate\python311\python.exe" (
    color 0C
    echo [LỖI] Không tìm thấy Python 3.11 tại C:\Affiliate\python311\python.exe!
    pause
    exit /b 1
)

echo [2/3] Đang khởi chạy tiến trình quét video và tối ưu bằng AI...
echo -----------------------------------------------------------------------
"C:\Affiliate\python311\python.exe" "C:\Affiliate\auto_rescue_flop.py"
set EXIT_CODE=%ERRORLEVEL%
echo -----------------------------------------------------------------------

echo [3/3] Tiến trình hoàn tất (Mã thoát: %EXIT_CODE%).
echo Log chi tiết được lưu tại: C:\Affiliate\post1\logs\auto_flop_rescue.log
echo.
echo Đã tích hợp Windows Task Scheduler: Tự động chạy 2 lần/ngày (09:00 và 21:00).
echo Bấm phím bất kỳ để đóng cửa sổ này...
pause >nul
exit /b %EXIT_CODE%
