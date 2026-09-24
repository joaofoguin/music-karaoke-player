; Inno Setup installer for StageBox Beta
; Requer o executável gerado por:
;   pyinstaller --clean --noconfirm stagebox.spec

#define MyAppName "StageBox"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.0-beta"
#endif
#define MyAppPublisher "StageBox"
#define MyAppExeName "StageBox-Beta.exe"
#define MyAppIconName "StageBox.ico"
#define ProjectRoot AddBackslash(SourcePath) + ".."

[Setup]
AppId={{8A4D9D1D-5D37-4D9E-9F1B-4B5A5F1C2E91}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\StageBox
DefaultGroupName={#MyAppName}
OutputDir={#ProjectRoot}\installer\output
OutputBaseFilename=StageBox-Beta-Setup
SetupIconFile={#ProjectRoot}\assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppIconName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
DisableProgramGroupPage=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#ProjectRoot}\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\assets\logo.ico"; DestDir: "{app}"; DestName: "{#MyAppIconName}"; Flags: ignoreversion

[Icons]
; O atalho usa explicitamente o ICO instalado, em vez de depender do icone embutido no EXE.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; IconIndex: 0
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"; IconIndex: 0; Tasks: desktopicon

[Registry]
Root: HKCR; Subkey: "StageBox.AudioFile"; ValueType: string; ValueName: ""; ValueData: "StageBox Audio File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "StageBox.AudioFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppIconName},0"
Root: HKCR; Subkey: "StageBox.AudioFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

Root: HKCR; Subkey: ".mp3"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".wav"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".flac"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".ogg"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".opus"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".m4a"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".aac"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"
Root: HKCR; Subkey: ".wma"; ValueType: string; ValueName: ""; ValueData: "StageBox.AudioFile"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent
