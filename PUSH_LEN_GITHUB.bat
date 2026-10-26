@echo off
chcp 65001 >nul 2>&1
title Push Affiliate-Publisher len GitHub
cd /d "C:\Affiliate\post1"

echo =======================================================
echo    DANG TIEN HANH PUSH CODE LEN GITHUB
echo =======================================================
echo Remote: https://github.com/vietkiet2282013/Affiliate-Publisher.git
echo Branch: main
echo.
echo * Trinh duyet se tu dong mo trang xac thuc GitHub.
echo   Ban chi can bam nut 'Authorize git-ecosystem' (hoac dang nhap neu duoc hoi).
echo =======================================================
echo.

git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo =======================================================
    echo [THANH CONG] DA PUSH TOAN BO CODE LEN GITHUB THANH CONG!
    echo =======================================================
) else (
    echo =======================================================
    echo [LOI] Khong the push. Vui long kiem tra lai thong bao ben tren!
    echo =======================================================
)
echo.
pause
