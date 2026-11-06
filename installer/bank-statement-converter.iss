; Bank Statement Converter — Inno Setup installer script (v1)
;
; Installs the two Windows exes built by .github/workflows/build-windows.yml:
;   bank-statement-converter.exe      (CLI, digital-PDF path only)
;   bank-statement-converter-gui.exe  (GUI, digital-PDF path only)
;
; Honest scope (do not widen in this script):
;   - Digital-PDF path only (pdfplumber). Scanned / image PDFs are NOT
;     converted by these exes; OCR is NOT included and tesseract is NOT
;     bundled — a scanned PDF needs a separate tesseract install, which
;     this installer does not provide.
;   - No auto-update. The user re-runs a newer installer to upgrade.
;   - Real bank samples have NOT yet been validated; real-Windows spot
;     check of the installed exes has NOT yet been done.
;
; Build: the `build-installer` job in build-windows.yml downloads both exe
; artifacts into installer\cli\ and installer\gui\ and compiles this file
; with Inno Setup 6 (choco `innosetup`). The .iss is NOT compiled on Linux.

; ============================================================================
; VERSION — single version constant. Bump ONLY this line for a new release.
; ============================================================================
#define MyAppVersion "1.0.0"

#define MyAppName "Bank Statement Converter"
#define MyAppPublisher "Muse"
#define MyAppExeName "bank-statement-converter-gui.exe"
#define MyAppCliExeName "bank-statement-converter.exe"

[Setup]
AppId={{8F3A2C1E-4B7D-4A9E-9C2F-1A5B6D7E8F01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Bank Statement Converter
DefaultGroupName=Bank Statement Converter
DisableProgramGroupPage=yes
LicenseFile=..\converter\README.md
; The README is the honest-scope reference: it states the digital-PDF-only
; range, the no-OCR / no-tesseract position, and what is still unvalidated.
OutputDir=.
OutputBaseFilename=bank-statement-converter-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName} {#MyAppVersion}
VersionInfoVersion={#MyAppVersion}.0

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
; NOTE: no Flags here — tasks are checked by default in Inno Setup, and
; `Flags: checked` is not a valid [Tasks] flag (CI 2026-11-06: "Parameter
; "Flags" includes an unknown flag" on this line). Default = checked/opt-out.

[Files]
; Both exes come from the CI artifacts (see build-windows.yml):
;   bank-statement-converter-windows     -> installer\cli\
;   bank-statement-converter-gui-windows -> installer\gui\
; They are NOT committed to the repo and are NOT present in a local checkout.
Source: "cli\{#MyAppCliExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "gui\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\converter\README.md"; DestDir: "{app}"; DestName: "README.md"; Flags: ignoreversion

[Icons]
Name: "{group}\Bank Statement Converter"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Bank Statement Converter (Command Line)"; Filename: "{app}\{#MyAppCliExeName}"
Name: "{group}\README"; Filename: "{app}\README.md"
Name: "{userdesktop}\Bank Statement Converter"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
