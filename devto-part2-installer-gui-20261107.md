# dev.to 续篇稿 · 对账单 PDF 转 CSV（2026-11-07 00:40 轮）

发布者说明（不发布这部分）：
- 角度：part 2 构建日志，承接 11-06 教程文（该文结尾写“无安装程序、无 GUI、无自动更新”；本篇更新其中两项）。
- 事实全部取自已核实来源：2026-11-06 日志 20:40/21:40/23:40 轮——GUI 构建记录、GUI exe CI 首跑 run 42228311551（2m58s 全绿、烟囱测试分支 b：窗口打开 15 秒仍运行、无 Traceback 后杀掉、artifact GUI exe 46,185,219 字节约 44.0 MB、CLI exe 43,154,989 字节约 41.2 MB）、安装程序 CI run 42246793629（3m20s 全绿、installer artifact 89,732,967 字节约 85.6 MB、首跑因 [Tasks] 段 Flags: checked 非法失败、commit 305def7 去掉该行修复）、run_tests.sh 6 passed。
- 诚实口径：真实 Windows 机器安装点检尚未做、自动更新尚未做、真实银行样本尚未验证、OCR 不在 exe 内。文中不写价格，价格以预售页为准；只链一次预售页、一次仓库。
- 标签：python、windows、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 2: a GUI and a Windows installer, and what CI caught

标签：python、windows、showdev、tools

正文：

Yesterday I wrote about a small local tool that converts bank statement PDFs to CSV, and ended the post with an honest list: no installer, no GUI, no auto-update yet. Since then I built the first two. This is a short build log — what shipped, what the CI caught, and what is still not done.

## The GUI

The converter now has a graphical interface, written with tkinter from the Python standard library — no extra dependency. It does one thing: pick a PDF, pick where the CSV goes, convert, and show the result.

The part I cared about most was the failure mode. A GUI that crashes on a machine without a display is worse than no GUI, so the no-display path is tested: with no display available the program exits with code 1, prints a plain message saying the interface cannot be opened, and produces no traceback. Six headless tests cover this, and they all pass locally.

## The Windows installer

Both executables — command-line and GUI — are now packaged into a Windows installer built with Inno Setup 6. The installer adds Start menu and desktop shortcuts and is versioned 1.0.0. It does not bundle Tesseract: scanned statements still need it installed separately, same as before.

The whole thing is built in GitHub Actions, and the build caught a real mistake before any user could. The first installer build failed with:

`Parameter "Flags" includes an unknown flag`

The `[Tasks]` section of the Inno Setup script had `Flags: checked` on the desktop-shortcut task. That flag is not accepted there — tasks are checked by default. The fix was deleting that one line. The rebuilt pipeline went fully green: command-line exe, GUI exe, installer, and both smoke tests, in about three and a half minutes.

The GUI smoke test itself was designed to accept exactly two outcomes: either the program exits quickly with code 1 and the no-display message and no traceback, or it is still running after 15 seconds, meaning the window opened. On the CI runner it took the second path — the window opened and stayed open, no traceback, and the test killed it afterwards.

## The numbers

- Command-line exe: about 41 MB
- GUI exe: about 44 MB
- Installer (both exes inside): about 86 MB

## What is still not done

- **Real Windows machine check.** The installer has only been built and smoke-tested on a CI runner. Nobody has installed it on a real Windows machine yet.
- **Auto-update.** Still to do.
- **Real bank statements.** The converter is still validated on synthetic fixtures only — 34 digital rows and 6 clean scan rows, all accurate, but no real samples yet.

The converter is open source: https://github.com/alapha888/bank-statement-presale

The presale page with the full status, scope and refund terms: https://alapha888.github.io/bank-statement-presale/

If you install it on a real machine and something breaks, that is exactly the kind of feedback I want to hear about.
