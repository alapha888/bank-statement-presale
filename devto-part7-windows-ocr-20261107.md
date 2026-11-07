# dev.to 续篇稿 · 对账单 PDF 转 CSV part 7（2026-11-07 05:40 轮）

发布者说明（不发布这部分）：
- 角度：part 7，关闭 part 6 缺口清单第 3 项的实证篇——Windows 上装 tesseract 的步骤，CI 实测。承接 part 6（该篇明确写了"the steps for installing tesseract on Windows have not been tested here"）；本篇只讲这一项的验证过程与结果，不重复 part 1–5 内容。
- 事实全部取自已核实来源：GitHub Actions run 42299707395（1m24s 全绿）日志实读＋.github/workflows/ocr-windows.yml＋converter/test_ocr.py 两次修复 commit（293446a、76f3afb）。
  - 安装：Chocolatey v2.7.5，`choco install tesseract` 装上 tesseract v5.5.3.20260724，位于 C:\Program Files\Tesseract-OCR。
  - 中文数据：choco 装完后 tessdata 里没有 chi_sim，从 tesseract-ocr/tessdata_fast 下载 chi_sim.traineddata 放入 tessdata 目录，`tesseract --list-langs` 输出确认 chi_sim 在列。
  - 结果：同一扫描 fixture（fixture D 渲染成的 300 dpi 纯图片 PDF）上，`chi_sim+eng --psm 6` 识别后经行解析：6/6 行全字段正确（100%），extracted 6 rows。
  - 两次失败先行：首跑 run 42299116293 与第二跑 run 42299429085 均失败在 OCR 验证步，都是 test_ocr.py 自身的 Windows 编码 bug，不是 OCR 质量问题——①`text=True` 未指定编码，Windows 下按 cp1252 解码 tesseract 的 UTF-8 中文输出，UnicodeDecodeError（byte 0x90），stdout 变 None 后 AttributeError；②解码修好后 `print(ocr_text)` 又在 cp1252 控制台 stdout 上 UnicodeEncodeError。修复：`encoding="utf-8-sig", errors="replace"`＋`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`。Linux 下无行为变化。
  - 仍未证明：仍是同一张合成干净扫描页（非真实银行扫描件）；tesseract 仍不在 exe 与安装程序内（用户仍需另装）；真实 Windows 机器上的安装＋双击点检仍未做；加密／图文混排／重度劣化 PDF 仍未测；无自动更新。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、windows、ocr、showdev（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 7: installing tesseract on Windows, tested in CI

标签：python、windows、ocr、showdev

正文：

Part 6 ended with a list of things this converter had not proven. Item 3 on that list was the scanned-PDF path on Windows: OCR worked on Linux (tesseract 5.3.4, 6/6 rows on a clean synthetic scan), but tesseract is not bundled in the installer or in either exe, and the steps for installing it on Windows had never been tested. This post closes that item — with the two failures it took to get there, because those failures are part of the result.

## What the test does

A new CI job, `ocr-windows`, runs on every change to the converter: install tesseract with Chocolatey, add Simplified Chinese language data, install the Python dependencies, regenerate the fixtures, and run `test_ocr.py` against the same scanned fixture part 3 used — a 300 dpi image-only PDF rendered from fixture D, six rows of ground truth. The job passes only if all six rows come back with every field correct.

## The install steps, as run

Chocolatey installed tesseract 5.5.3.20260724 at `C:\Program Files\Tesseract-OCR`. The Chocolatey package did not include Chinese language data, so the job downloads `chi_sim.traineddata` from tesseract-ocr/tessdata_fast into the tessdata directory and then asserts that `tesseract --list-langs` actually lists `chi_sim` before proceeding. That assertion matters: without it, a silent missing-language failure would look like a parser failure later.

## The result

The run passed in 1 minute 24 seconds (run 42299707395): tesseract with `chi_sim+eng --psm 6` recognised the scanned fixture, and the row parser extracted **6/6 rows with all fields correct (100%)**. The Windows install steps are now tested, not assumed.

## The two failures before it

The first run failed in the OCR step, and the second run failed in the same step at a new position. Both were bugs in `test_ocr.py` itself — bugs that only exist on Windows, which is exactly why the job runs on Windows:

1. The script called `subprocess.run` with `text=True` and no encoding. On Windows that decodes with cp1252, which cannot decode tesseract's UTF-8 Chinese output — `UnicodeDecodeError` on byte 0x90 — and `proc.stdout` came back as `None`, crashing the row comparison with an `AttributeError`. Fixed by decoding explicitly with `encoding="utf-8-sig", errors="replace"`.
2. With decoding fixed, `print(ocr_text)` crashed instead: the Windows console stdout is also cp1252 and cannot encode Chinese characters. Fixed by reconfiguring stdout to UTF-8 at the start of `main()`.

Neither failure was an OCR quality problem. A script that passes on Linux and crashes on Windows is the kind of thing a Windows CI job is for, and it found two of them in two runs.

## What this does not prove

The same limits from part 6 still apply to the scanned path. The fixture is still one clean synthetic scan page, not a real bank scan with skew, noise, low resolution, or stamps. Tesseract is still a separate install — the exe and the installer do not bundle it, and the installer does not install it. Nobody has yet run the installer on a real Windows machine and double-clicked the installed shortcuts. Encrypted PDFs, mixed image-and-text PDFs, and heavily degraded scans are still untested. The next post in this series will be evidence closing one of those items, not a repeat of this one.

Links: the converter repository is at https://github.com/alapha888/bank-statement-presale, and the presale page is at https://alapha888.github.io/bank-statement-presale/.
