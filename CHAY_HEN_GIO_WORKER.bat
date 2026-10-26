@echo off
chcp 65001 >nul 2>&1
title Affiliate Scheduler Worker - Background Job
echo ======================================================
echo    AFFILIATE SCHEDULER WORKER (HEN GIO DANG BAI)
echo ======================================================
echo.

if exist "C:\Affiliate\python311\python.exe" (
    echo [OK] Tim thay Python tai C:\Affiliate\python311\python.exe
) else (
    echo [LOI] Khong tim thay Python!
    pause
    exit /b 1
)

echo.
echo Dang khoi dong Tien trinh quet lich hen gio (Worker)...
echo Chuong trinh se tu dong quet file schedule_queue.json va dang bai dung gio.
echo Nhan Ctrl+C de dung.
echo.

"C:\Affiliate\python311\python.exe" "%~dp0POST\scheduler.py" --worker

pause
