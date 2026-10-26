@echo off
chcp 65001 > nul
cd /d C:\Affiliate\post1\POST
uv run python C:\Affiliate\post1\POST\task_ig_threads_dong_ho.py >> C:\Affiliate\post1\POST\config\task_ig_threads_dong_ho.log 2>&1
