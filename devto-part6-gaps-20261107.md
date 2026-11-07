# dev.to 续篇稿 · 对账单 PDF 转 CSV part 6（2026-11-07 04:40 轮）

发布者说明（不发布这部分）：
- 角度：part 6，系列收束篇——诚实缺口清单：这台转换器还没证明过什么。承接 part 1–5（提取、GUI/安装程序、OCR、选库、CSV）；本篇不重复已讲内容，只列未验证项、每项意味着什么、以及什么证据能关闭它。
- 事实全部取自已核实来源：installer/BUILD-NOTES.md（安装程序构成与未验证清单）＋2026-11-06/07 日志已核实数字（CLI exe 43,154,989 字节约 41.2 MB、GUI exe 46,185,219 字节约 44.0 MB、安装程序 89,732,967 字节约 85.6 MB、CI run 42246793629 3m20s 全绿、GUI 烟囱分支 b 窗口开 15 秒无 Traceback、run_tests.sh 6 passed、数字 fixture 34/34、扫描 OCR 6/6、tesseract 5.3.4 chi_sim+eng 300 dpi）。
  - 安装程序构成：Inno Setup 打包双 exe，装到 {autopf}\Bank Statement Converter，开始菜单给 GUI 与 CLI 建快捷方式、GUI 可选桌面快捷方式、README 随 exe 一起装。
  - 未验证：真实银行样本；真实 Windows 机器上的安装＋双击快捷方式点检；Windows 上装 tesseract 的步骤；加密 PDF、图文混排 PDF、重度劣化扫描件；自动更新（没有，升级靠重跑新安装程序）；跨页续表、汇总行、各家表头措辞。
  - 已验证：数字 PDF 34/34（四版式 12+8+8+6）、干净扫描 OCR 6/6（Linux 上 tesseract 5.3.4）、GUI 窗口在 CI runner 上能打开、安装程序在 CI 上能编译出 85.6 MB 的 setup exe。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、windows、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 6: what this converter has not proven yet

标签：python、windows、showdev、tools

正文：

Parts 1 to 5 of this series built the case for a small converter: 34 rows across four statement layouts, all fields correct; a GUI and a Windows installer; a scanned-PDF path through OCR; a CSV output with an audit trail. This post is the other half of that case — everything the converter has not proven yet. If you are deciding whether to trust it with a real statement, this is the list that matters more than the first five posts.

## 1. No real bank statement has been tested

Every number so far comes from statements I built myself: four digital layouts (12, 8, 8, and 6 rows) and six clean synthetic scan pages. The parser recognises columns by header keywords, and banks differ in header wording, column order, summary rows, and multi-page tables. A layout whose wording the parser has never seen is skipped, not guessed at — that is the safe failure mode, but it is still a failure for that statement. The 34/34 result says the converter handles the four layouts I built. It says nothing about the fifth layout I have not seen. What would close this: converting real statements from several banks and reporting the row counts, misses included.

## 2. No real Windows machine has run the installer

The installer is real — Inno Setup, about 85.6 MB, bundling the CLI exe (about 41.2 MB) and the GUI exe (about 44.0 MB), installing to `Bank Statement Converter` with Start Menu shortcuts for both and an optional desktop shortcut for the GUI. It compiled clean on CI (run 42246793629, 3 minutes 20 seconds) after one first-run failure: a `Flags: checked` line in the `[Tasks]` section that Inno Setup 6.7.1 rejects, fixed by removing it. But "compiles on CI" is not "installs on a machine". The GUI window was opened once on a CI runner and left running for 15 seconds with no traceback — that is a smoke test, not a spot check. Nobody has yet downloaded the setup file on a real Windows machine, run it, and double-clicked both installed shortcuts. What would close this: that exact check, on a real machine, with the result reported.

## 3. The scanned path is unproven on Windows

OCR works on Linux in my tests: tesseract 5.3.4, Chinese plus English, 300 dpi synthetic scan pages, 6/6 rows with all fields correct. None of that transfers to Windows automatically. Tesseract is not bundled in the installer and not in either exe — a scanned PDF needs a separate tesseract install, which the installer does not provide, and the steps for installing tesseract on Windows have not been tested here. A user with a scanned statement on Windows currently has a documented gap, not a working path. What would close this: installing tesseract on Windows, running a scanned statement through the installed GUI, and reporting what broke.

## 4. Encrypted PDFs, mixed PDFs, and bad scans are untested

Three inputs the converter has never seen: encrypted PDFs, image PDFs with a partial text layer, and heavily degraded scans. The first version's stated scope is digital PDFs and ordinary scanned statements; badly degraded scans are explicitly out of scope. But "out of scope" is a design decision, and the boundary has not been probed — I do not know where ordinary ends and degraded begins. What would close this: a small set of awkward inputs, run through the converter, with the failure modes written down instead of assumed.

## 5. There is no auto-update

Upgrades mean re-running a newer installer. That is a deliberate choice for a first version, not an oversight, but it has a consequence worth stating: a user who installs 1.0.0 will not be told 1.0.1 exists. For a tool that handles financial documents, a silent old version is a real risk, and the fix is either an update check or a clear statement at install time. What would close this: either a minimal update check or an explicit note in the installer that none exists.

## What this list is for

None of these gaps makes the five earlier posts wrong. The extraction logic, the GUI, the installer build, the OCR path on Linux, and the CSV format are all as described, with the numbers to back them. But a tool is not done when its happy path works; it is done when its failure modes are known. This list is the work between "built" and "done", and it is also the reason the series pauses here — the next post worth writing is one that closes an item on this list with evidence, not another post about what already works.

The converter is open source: https://github.com/alapha888/bank-statement-presale

The presale page with the full status, scope and refund terms: https://alapha888.github.io/bank-statement-presale/
