[Setup]
AppName=SmartTraffic AI
AppVersion=2.1.0
DefaultDirName={autopf}\SmartTraffic AI
DefaultGroupName=SmartTraffic AI
OutputBaseFilename=SmartTrafficInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SmartTraffic AI"; Filename: "wscript.exe"; Parameters: """{app}\launch_presentation.vbs"""; WorkingDir: "{app}"
Name: "{commondesktop}\SmartTraffic AI"; Filename: "wscript.exe"; Parameters: """{app}\launch_presentation.vbs"""; WorkingDir: "{app}"

[Run]
Filename: "wscript.exe"; Parameters: """{app}\launch_presentation.vbs"""; Description: "Launch SmartTraffic AI"; Flags: nowait postinstall skipifsilent
