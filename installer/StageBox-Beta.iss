; Inno Setup installer for StageBox Beta
; Build this script after generating dist\StageBox-Beta.exe with PyInstaller.

#define MyAppName "StageBox"
#define MyAppVersion "0.1.0-beta"
#define MyAppPublisher "StageBox"
#define MyAppExeName "StageBox-Beta.exe"

[Setup]
AppId={{8A4D9D1D-5D37-4D9E-9F1B-4B5A5F1C2E91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\StageBox
DefaultGroupName={#MyAppName}
OutputDir=installer\output
OutputBaseFilename=StageBox-Beta-Setup
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
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
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent
