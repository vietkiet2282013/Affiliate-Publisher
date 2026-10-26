@echo off
chcp 65001 >nul 2>&1
title Affiliate Dashboard - Port 5000

echo ============================================
echo    AFFILIATE DASHBOARD - 10 Kenh x 4 Nen Tang
echo ============================================
echo.

REM Kiem tra embedded Python
if exist "C:\Affiliate\python311\python.exe" (
    echo [OK] Tim thay Python tai C:\Affiliate\python311\python.exe
) else (
    echo [LOI] Khong tim thay Python! Lien he ho tro.
    pause
    exit /b 1
)

echo.
echo Dang khoi dong Dashboard tren http://localhost:5000 ...
echo Nhan Ctrl+C de tat server.
echo.

"C:\Affiliate\python311\python.exe" "%~dp0app.py" --port 5000

pause
