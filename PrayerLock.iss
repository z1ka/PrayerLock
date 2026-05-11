#define MyAppName "PrayerLock"
#define MyAppVersion "1.0.0"
#define MyAppExeName "PrayerLock.exe"

[Setup]
AppId={{2DA5F8B1-82E5-4E5D-9B77-7C9D8B3D6F0B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PrayerLock
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=PrayerLock-Setup
OutputDir=installer
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
WizardStyle=modern
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts"

[Dirs]
Name: "{commonappdata}\PrayerLock"; Permissions: users-modify

[Files]
Source: "dist\PrayerLock\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PrayerLock"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall PrayerLock"; Filename: "{uninstallexe}"
Name: "{commondesktop}\PrayerLock"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PrayerLock"; ValueData: """{app}\{#MyAppExeName}"" --tray"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "PrayerLock"; Flags: deletevalue uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install-service"; Flags: runhidden waituntilterminated; StatusMsg: "Installing PrayerLock service..."
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PrayerLock"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/IM PrayerLock.exe /F"; Flags: runhidden; RunOnceId: "KillPrayerLock"
Filename: "sc.exe"; Parameters: "stop PrayerLockService"; Flags: runhidden; RunOnceId: "StopPrayerLockService"
Filename: "sc.exe"; Parameters: "delete PrayerLockService"; Flags: runhidden; RunOnceId: "DeletePrayerLockService"

[UninstallDelete]
Type: filesandordirs; Name: "{commonappdata}\PrayerLock"
