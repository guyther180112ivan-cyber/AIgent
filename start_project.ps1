Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList "/k cd /d C:\AIgent\IvanAgent && npm run dev"
Start-Process -WindowStyle Normal -FilePath "cmd.exe" -ArgumentList "/k cd /d C:\AIgent\IvanAgent\backend && py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
