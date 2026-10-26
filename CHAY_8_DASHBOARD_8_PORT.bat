@echo off
title Khoi Dong 8 Dashboard Cho 8 Kenh Dang Dong Thoi

echo ======================================================================
echo 🚀 DANG KHOI DONG 8 PORT CHO DASHBOARD NHO:
echo    - Port 5000: http://localhost:5000 (Tab 1)
echo    - Port 5001: http://localhost:5001 (Tab 2)
echo    - Port 5002: http://localhost:5002 (Tab 3)
echo    - Port 5003: http://localhost:5003 (Tab 4)
echo    - Port 5004: http://localhost:5004 (Tab 5)
echo    - Port 5005: http://localhost:5005 (Tab 6)
echo    - Port 5006: http://localhost:5006 (Tab 7)
echo    - Port 5007: http://localhost:5007 (Tab 8)
echo ======================================================================

cd /d "c:\Affiliate\post1"

:: Chay cac server Flask tren 8 ports
start "Dashboard Port 5000" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5000
start "Dashboard Port 5001" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5001
start "Dashboard Port 5002" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5002
start "Dashboard Port 5003" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5003
start "Dashboard Port 5004" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5004
start "Dashboard Port 5005" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5005
start "Dashboard Port 5006" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5006
start "Dashboard Port 5007" /B "c:\Affiliate\post1\.venv\Scripts\python.exe" "c:\Affiliate\post1\app.py" --port 5007

timeout /t 2 /nobreak >nul

:: Mo cac tab trinh duyet
start http://localhost:5000
start http://localhost:5001
start http://localhost:5002
start http://localhost:5003
start http://localhost:5004
start http://localhost:5005
start http://localhost:5006
start http://localhost:5007

echo Da khoi dong thanh cong 8 port! Ban co the bat dau dang video song song.
pause
