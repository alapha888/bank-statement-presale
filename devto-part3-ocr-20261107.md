# dev.to 续篇稿 · 对账单 PDF 转 CSV part 3（2026-11-07 01:40 轮）

发布者说明（不发布这部分）：
- 角度：part 3，扫描件 OCR 路径实测。承接 part 1（数字 PDF 34 行全对）与 part 2（GUI＋安装程序）；本篇只讲扫描件这一条线：它怎么跑通、为什么不在 exe 里、哪些没验证。
- 事实全部取自已核实来源：converter/README.md“扫描件 / OCR”小节（2026-11-06 实测）＋ test_ocr.py 源码（已读）＋ 17:40 轮独立复跑记录（OCR test_ocr.py 复测 6/6，tesseract 5.3.4 在位）。
  - tesseract 本机原本未安装，本次 apt 安装 5.3.4，含 chi_sim + eng 语言数据；ocrmypdf 本机未安装、未使用。
  - fixture-s1-scanned.pdf：fixture D 渲染成的 300 dpi 纯图片 PDF，无文本层；tesseract `chi_sim+eng --psm 6` 识别后经行解析：6/6 行全字段正确（100%）。
  - test_ocr.py 缺 tesseract 时退出码 2 并打印安装指引，不谎报通过。
  - exe 只含数字 PDF 路径（pdfplumber）；OCR 路径需另装 tesseract，不在 exe 内；安装程序不捆 tesseract。
  - 未验证：真实扫描件（倾斜、噪点、低分辨率、印章遮挡）未测；真实银行样本未测；加密 PDF、图片型 PDF 中混有文本层未测。列识别按表头关键词（日期/摘要/支出/收入/余额/金额/借方/贷方），未见过的表头措辞会跳过该表、宁可漏提不瞎提。
  - Windows 上安装 tesseract 的步骤未经我们实测（实测只在 Linux apt），文中如实写明，不写未经验证的 Windows 安装步骤。
- 诚实口径：只写已测的干净合成扫描页 6/6；不写价格，只链一次预售页、一次仓库。
- 标签：python、ocr、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 3: the scanned-PDF path — what OCR actually did, and what it didn't

标签：python、ocr、showdev、tools

正文：

Parts 1 and 2 of this series covered the digital-PDF path: 34 rows across four statement layouts, all fields correct, then a GUI and a Windows installer. But plenty of bank statements arrive as scans — image-only PDFs with no text layer at all. This post is about that path: how I tested it, what the result was, and why OCR is deliberately not inside the executables.

## The setup

The OCR path is a standalone script, not part of the main converter. It shells out to the `tesseract` binary, which has to be installed on the system first. On this machine Tesseract was not installed at all, so the first step was installing it — version 5.3.4, with Simplified Chinese (`chi_sim`) and English language data.

Two things worth stating plainly. First, `ocrmypdf` was not installed and not used; the pipeline is Tesseract straight to the same line parser the digital path uses. Second, the check script refuses to fake a pass: if Tesseract is missing, it exits with code 2 and prints installation instructions instead of reporting anything as validated.

## The test

The test fixture is a clean 300 dpi image-only PDF, rendered from one of the digital fixtures, with no text layer. The command is:

`tesseract fixture-s1-scanned.png stdout -l chi_sim+eng --psm 6`

Tesseract's output goes through the same row parser as the digital path, and each row is compared field by field against ground truth — date, description, debit, credit, and balance all have to match for a row to count.

Result: 6 out of 6 rows fully correct.

## Why OCR is not in the exe

The Windows executables and the installer contain only the digital-PDF path. Tesseract is a separate system binary with its own language data files, not a Python package you can bundle the same way, so the installer does not include it. If you work with scanned statements, you install Tesseract separately and use the OCR script; the digital path keeps working without it.

## What this does not prove

The 6/6 result is on a clean synthetic render. It says nothing about real-world scans, and I am not going to pretend otherwise:

- **Real scans are untested.** Skew, noise, low resolution, stamps covering text — none of that was in the sample.
- **Real bank statements are untested.** Every fixture so far is synthetic. Different banks use different header wording, column orders, summary rows, and multi-page tables.
- **Two PDF shapes are untested.** Encrypted PDFs, and image PDFs that mix in a text layer, have not been tried.

One design choice is relevant here: the parser recognises columns by header keywords (date, description, debit, credit, balance, amount, and their Chinese equivalents). If it meets header wording it has never seen, it skips that table rather than guessing. Missing a table is a visible failure; inventing numbers is not.

The Windows side of the OCR setup is also untested by me — the install above ran on Linux. If you set Tesseract up on Windows and it works, or breaks, that is exactly the kind of feedback I want to hear about.

The converter is open source: https://github.com/alapha888/bank-statement-presale

The presale page with the full status, scope and refund terms: https://alapha888.github.io/bank-statement-presale/
