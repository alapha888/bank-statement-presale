# dev.to 教程稿 · 对账单 PDF 转 CSV（2026-11-06）

发布者说明（不发布这部分）：
- 角度：实操教程，与 11-05 预售公告文（中文、产品说明）不同篇。
- 事实全部取自已核实来源：converter/README.md（pdfplumber 0.11.10、表格抽取＋纯文本行兜底、日期/金额格式、NFKC、CSV UTF-8 BOM）、18:40 轮 CI 实测（run 42204671398 全绿、exe 烟囱测试 fixture A 12 行准确、artifact 约 41 MB）、17:40 轮复测（合成数字样例 34/34、干净扫描样张 6/6）。
- 诚实口径：真实银行对账单与真实扫描件尚未用真实样本验证；exe 只含数字 PDF 路径，OCR 需另装 tesseract、不在 exe 内；无安装程序、无 GUI、无自动更新。文中不写价格，价格以预售页为准；只链一次预售页。
- 标签：python、pdf、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV with Python: what I built, what I actually tested

标签：python、pdf、showdev、tools

正文：

Every month the bank sends a PDF statement. The accounting software wants a CSV. In between there is usually a lot of retyping — slow, error-prone, and the file has to leave your machine if you use an online converter.

I built a small local tool that does the conversion on your own machine. This post is a walkthrough of how it works, and an honest account of what it has actually been tested on.

## How it works

The converter is Python, with one runtime dependency: `pdfplumber` (0.11.10). It tries the text layer first:

1. **Table extraction.** Most digital statements are tables. pdfplumber reads the ruling lines and pulls out rows with separate debit/credit columns, or a single amount column with `+`/`-` signs.
2. **Plain-text fallback.** Some statements have no real table, just lines of text. A line parser handles `date description amount [balance]` rows.
3. **OCR only for scans.** Scanned statements go through Tesseract. The OCR path needs Tesseract installed separately — it is not bundled in the Windows exe.

A few details that turned out to matter:

- **Dates** come in many shapes (`YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY年MM月DD日`, `MM-DD`, `MM/DD`). Everything is normalized to `YYYY-MM-DD`. A bare `MM-DD` takes its year from the document (a `YYYY年` heading or the first full date), or from a `--year` flag.
- **Amounts** handle thousands separators, `+`/`-` signs, and `(123.45)` parenthesised negatives.
- **NFKC normalization.** Some PDF generators write `-` as U+2011 or put a few CJK characters in the compatibility zone. Normalizing first makes the matching work.
- **CSV output** is UTF-8 with BOM, so Excel opens it without garbled characters. Columns are date, description, debit, credit, balance, and the raw source line for traceability.

## What I actually tested

Numbers first, because that is the part that matters:

- **Digital PDFs:** 4 synthetic layouts, 34 rows total, all fields accurate.
- **Clean scans:** 6 sample rows via OCR, all accurate.
- **Windows exe:** built in GitHub Actions (windows-latest, Python 3.12, PyInstaller `--onefile`), then smoke-tested on a 12-row fixture — the exe produced the expected 13-line CSV. The exe covers the digital-PDF path only.

## What I have not tested

- **Real bank statements from real banks.** The tests above use synthetic fixtures. Real statements have their own quirks, and I have not run the tool on real samples yet.
- **Degraded scans.** Heavily degraded scans are out of scope for the first version.

I am writing this down plainly because a conversion tool that silently gets a number wrong is worse than no tool at all. The raw source line is kept in the CSV so every converted row can be traced back to the original.

## The tool

The converter is open source: https://github.com/alapha888/bank-statement-presale

There is also a presale page with the full status, scope and refund terms: https://alapha888.github.io/bank-statement-presale/

No installer, no GUI, and no auto-update yet — those are still to do. If you try the converter on your own statements and it gets something wrong, that is exactly the kind of feedback I want to hear about.
