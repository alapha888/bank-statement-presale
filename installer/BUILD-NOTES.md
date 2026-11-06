# Installer build notes — bank-statement-converter v1.0.0

## What this is

Inno Setup installer (`bank-statement-converter.iss`) that packages the two
Windows exes built by the `build-exe` job into one setup file:
`bank-statement-converter-setup-1.0.0.exe`. Installs to
`{autopf}\Bank Statement Converter`, with Start Menu shortcuts for the GUI
and the CLI, an optional desktop shortcut for the GUI, and the converter
README installed alongside the exes.

## Honest scope (preserved — do not widen without evidence)

- Digital-PDF path only (pdfplumber). Scanned / image PDFs are NOT converted
  by these exes.
- OCR is NOT included; tesseract is NOT bundled. A scanned PDF needs a
  separate tesseract install, which this installer does not provide.
- No auto-update. Upgrades mean re-running a newer installer.
- Real bank samples have NOT yet been validated; a real-Windows spot check
  of the installed exes has NOT yet been done.

## Version

Single version constant in the .iss: `#define MyAppVersion "1.0.0"` (line 23).
Bump only that line for a new release; `AppVersion`, the setup filename,
and `VersionInfoVersion` all derive from it.

## Validated locally (2026-11-06, Linux — this environment has no Windows)

- `.github/workflows/build-windows.yml` parses as valid YAML (PyYAML).
- `build-installer` job exists, `needs: build-exe`, `runs-on: windows-latest`.
  (Note: the brief said `needs: build-windows`, but that is the workflow's
  name; the existing job id is `build-exe`. The dependency uses the real id.)
- Download-artifact names in the new job
  (`bank-statement-converter-windows`, `bank-statement-converter-gui-windows`)
  exactly match the upload-artifact names in the existing `build-exe` job.
- New upload-artifact name: `bank-statement-converter-installer-windows`,
  path glob `installer/bank-statement-converter-setup-*.exe`, `if-no-files-found: error`.
- `.iss` contains all required sections: `[Setup]`, `[Files]`, `[Icons]`,
  `[Tasks]`, `[Run]`.
- `.iss` references checked against the repo layout:
  - `..\converter\README.md` — exists; used as `LicenseFile` and installed
    as `{app}\README.md`.
  - `cli\bank-statement-converter.exe` and
    `gui\bank-statement-converter-gui.exe` — NOT in the repo and NOT present
    locally. This is expected: they are produced by the CI
    `download-artifact` steps into `installer/cli/` and `installer/gui/`.
    The compile step will fail loudly if either download is missing.
  - No other file references in the .iss.
- `.iss` contains no OCR-support claim and no tesseract bundling; the only
  mentions of OCR/tesseract are explicit "NOT included / NOT bundled"
  disclaimers in comments.
- Existing `build-exe` job untouched (same 10 steps); only two stale header
  comment lines were updated (they said "No installer" — now false).
- Push trigger now also includes `installer/**`, so installer-only changes
  run the workflow.
- Untouched as required: `index.html`, repo-root `README.md`, all
  `converter/` code. Nothing committed, nothing pushed.

## NOT validated (cannot be done on Linux)

- Inno Setup compile (`ISCC.exe`) — only runs on the Windows CI job.
  Possible first-run risks: the choco `innosetup` package's install path
  (`C:\Program Files (x86)\Inno Setup 6\ISCC.exe`), the `LicenseFile`
  pointing at a `.md` file, and the `{cm:CreateDesktopIcon}` message
  reference. Any of these failing will fail the CI job visibly — that is
  the intended check.
- Installing the resulting setup exe on a real Windows machine and
  double-clicking both installed shortcuts — still to be done after CI
  goes green (needs a real Windows machine; not available here).

## CI job to watch after push

Workflow `build-windows`, job **`build-installer`** (runs after
`build-exe`). On green, the installer is the Actions artifact
**`bank-statement-converter-installer-windows`**
(`bank-statement-converter-setup-1.0.0.exe`). Do NOT trigger CI from this
machine — push from the parent session, then watch that job.
