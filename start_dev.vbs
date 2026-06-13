Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\AIgent\IvanAgent"
WshShell.Run "cmd /c npm run dev", 0, False
