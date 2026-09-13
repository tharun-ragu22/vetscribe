; Inno Setup script for VetScribe Assistant.
;
; Prerequisite: build the PyInstaller --onedir output first, so that
; dist\VetScribe\VetScribe.exe (and its supporting files) exist:
;   uv run pyinstaller build_spec/vetscribe.spec --distpath dist --workpath build
;
; Then compile this script (e.g. with the Inno Setup Compiler or
; `iscc build_spec/installer.iss`) to produce dist\installer\VetScribeSetup.exe.

#define MyAppName "VetScribe Assistant"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "VetScribe"
#define MyAppExeName "VetScribe.exe"

[Setup]
AppId={{B6C2E9B0-6F5E-4A7B-9E9B-1A2B3C4D5E6F}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\VetScribe
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=VetScribeSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\VetScribe\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
