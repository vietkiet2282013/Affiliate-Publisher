$action = New-ScheduledTaskAction -Execute "C:\Affiliate\post1\.venv\Scripts\python.exe" -Argument "C:\Affiliate\post1\POST\run_publish_instagram_threads.py" -WorkingDirectory "C:\Affiliate\post1\POST"
$trigger = New-ScheduledTaskTrigger -Once -At 12:00
Register-ScheduledTask -TaskName "Affiliate_GocTapLuyen_Instagram_Threads_12h" -Action $action -Trigger $trigger -Description "Dang video 4 goc tap luyen len Instagram va Threads vao 12h00 26-09-2026" -Force
