; Inno Setup Script for YT Stream 24/7 — Reencoder
; This script creates a Windows installer with Start Menu shortcuts and uninstaller

#define AppName "YT Stream 24/7 — Reencoder"
#define AppShortcutName "YT Stream 247 — Reencoder"
#define AppGroupName "YT Stream 247 — Reencoder"
#define AppVersion "1.0.2"
#define AppPublisher "YTStream247"
#define AppURL ""
#define AppExeName "YTStream247Reencoder.exe"
#define AppDirName "YTStream247Reencoder"

[Setup]
; App information
AppId={{A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppDirName}
DefaultGroupName={#AppGroupName}
AllowNoIcons=yes
LicenseFile=
OutputDir=.
OutputBaseFilename=YTStream247Reencoder-Setup
SetupIconFile=..\..\assets\icons\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
DisableDirPage=no
VersionInfoVersion=1.0.2
VersionInfoCompany=YTStream247
VersionInfoDescription=YT Stream 24/7 — Reencoder Setup
VersionInfoProductName=YT Stream 24/7 — Reencoder
VersionInfoProductVersion=1.0.2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application executable (smaller size - FFmpeg not bundled)
Source: "..\..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; FFmpeg executables in separate folder (referenced by app)
Source: "..\..\ffmpeg-apps\ffmpeg.exe"; DestDir: "{app}\ffmpeg-apps"; Flags: ignoreversion
Source: "..\..\ffmpeg-apps\ffprobe.exe"; DestDir: "{app}\ffmpeg-apps"; Flags: ignoreversion

; Assets folder (language files)
Source: "..\..\assets\lang\*"; DestDir: "{app}\assets\lang"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppShortcutName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppShortcutName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppShortcutName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
