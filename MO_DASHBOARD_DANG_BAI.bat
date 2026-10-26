@echo off
title Khoi Dong Affiliate Video Dashboard

echo ======================================================================
echo 🚀 DANG KHOI DONG AFFILIATE VIDEO PUBLISHER DASHBOARD...
echo 🌐 Dia chi truy cap: http://localhost:5000
echo ======================================================================
echo.

cd /d "c:\Affiliate\post1"

:: Mo trinh duyet tu dong
start http://localhost:5000

:: Chay server Flask
"c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py"

pause
