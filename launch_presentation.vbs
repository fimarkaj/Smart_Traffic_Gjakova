Set shell = CreateObject("WScript.Shell")
base = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
backend = "cmd /c call ""C:\ProgramData\anaconda3\Scripts\activate.bat"" ""D:\Yolov11\STAI\conda_envs\smarttraffic"" && cd /d """ & base & "\api"" && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
frontend = "cmd /c call ""C:\ProgramData\anaconda3\Scripts\activate.bat"" ""D:\Yolov11\STAI\conda_envs\smarttraffic"" && cd /d """ & base & """ && python frontend_server.py"
shell.Run backend, 0, False
WScript.Sleep 4000
shell.Run frontend, 0, False
WScript.Sleep 3000
shell.Run "http://localhost:5173", 1, False
