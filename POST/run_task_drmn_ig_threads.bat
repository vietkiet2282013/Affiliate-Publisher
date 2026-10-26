@echo off
chcp 65001 > nul
cd /d C:\Affiliate\post1\POST
C:\Users\ADMIN\.local\bin\uv.exe run --with requests --with openpyxl python C:\Affiliate\post1\POST\task_drmn_ig_threads.py >> C:\Affiliate\post1\POST\config\task_ig_threads_drmn.log 2>&1
