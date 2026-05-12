#define MyAppName "PrayerLock"
#define MyAppVersion "1.0.1"
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

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install-service"; Flags: runhidden waituntilterminated; StatusMsg: "Installing PrayerLock service..."
Filename: "{app}\{#MyAppExeName}"; Description: "Launch PrayerLock"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/IM PrayerLock.exe /F"; Flags: runhidden; RunOnceId: "KillPrayerLock"
Filename: "sc.exe"; Parameters: "stop PrayerLockService"; Flags: runhidden; RunOnceId: "StopPrayerLockService"
Filename: "sc.exe"; Parameters: "delete PrayerLockService"; Flags: runhidden; RunOnceId: "DeletePrayerLockService"

[UninstallDelete]
Type: filesandordirs; Name: "{commonappdata}\PrayerLock"

[Code]
function VerifyUninstallPassword(Password: String): Boolean;
var
  ResultCode: Integer;
  PasswordFile: String;
  AppExe: String;
begin
  Result := False;
  AppExe := ExpandConstant('{app}\{#MyAppExeName}');
  if not FileExists(AppExe) then
  begin
    MsgBox('PrayerLock could not verify the password because the app file is missing.', mbError, MB_OK);
    Exit;
  end;

  PasswordFile := ExpandConstant('{tmp}\prayerlock_uninstall_password.txt');
  if not SaveStringToFile(PasswordFile, Password, False) then
  begin
    MsgBox('PrayerLock could not prepare password verification.', mbError, MB_OK);
    Exit;
  end;

  try
    Result :=
      Exec(
        AppExe,
        '--verify-password-file "' + PasswordFile + '"',
        '',
        SW_HIDE,
        ewWaitUntilTerminated,
        ResultCode
      ) and (ResultCode = 0);
  finally
    DeleteFile(PasswordFile);
  end;
end;

function PromptForUninstallPassword(var Password: String): Boolean;
var
  Form: TSetupForm;
  PromptLabel: TLabel;
  PasswordEdit: TPasswordEdit;
  OKButton: TButton;
  CancelButton: TButton;
begin
  Result := False;
  Password := '';

  Form := CreateCustomForm();
  try
    Form.Caption := 'PrayerLock';
    Form.ClientWidth := ScaleX(380);
    Form.ClientHeight := ScaleY(135);
    Form.Position := poScreenCenter;
    Form.BorderStyle := bsDialog;

    PromptLabel := TLabel.Create(Form);
    PromptLabel.Parent := Form;
    PromptLabel.Left := ScaleX(16);
    PromptLabel.Top := ScaleY(16);
    PromptLabel.Width := ScaleX(348);
    PromptLabel.Caption := 'Enter the master password to uninstall PrayerLock:';

    PasswordEdit := TPasswordEdit.Create(Form);
    PasswordEdit.Parent := Form;
    PasswordEdit.Left := ScaleX(16);
    PasswordEdit.Top := ScaleY(44);
    PasswordEdit.Width := ScaleX(348);

    OKButton := TButton.Create(Form);
    OKButton.Parent := Form;
    OKButton.Caption := 'OK';
    OKButton.Left := ScaleX(204);
    OKButton.Top := ScaleY(92);
    OKButton.Width := ScaleX(76);
    OKButton.ModalResult := mrOk;
    OKButton.Default := True;

    CancelButton := TButton.Create(Form);
    CancelButton.Parent := Form;
    CancelButton.Caption := 'Cancel';
    CancelButton.Left := ScaleX(288);
    CancelButton.Top := ScaleY(92);
    CancelButton.Width := ScaleX(76);
    CancelButton.ModalResult := mrCancel;
    CancelButton.Cancel := True;

    Form.ActiveControl := PasswordEdit;

    if Form.ShowModal() = mrOk then
    begin
      Password := PasswordEdit.Text;
      Result := True;
    end;
  finally
    Form.Free();
  end;
end;

function InitializeUninstall(): Boolean;
var
  Password: String;
  Attempt: Integer;
begin
  Result := False;
  for Attempt := 1 to 3 do
  begin
    if not PromptForUninstallPassword(Password) then
      Exit;

    if VerifyUninstallPassword(Password) then
    begin
      Result := True;
      Exit;
    end;

    MsgBox('Incorrect password.', mbError, MB_OK);
  end;
end;
