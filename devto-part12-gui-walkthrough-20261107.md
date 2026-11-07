# Bank statement PDFs to CSV, part 12: using the GUI — pick a file, click convert, check the CSV

This is part 12 of a build log for a small converter that turns digital bank statement PDFs into CSV. Earlier parts covered the parser, the OCR path for scanned PDFs, edge cases, and the Windows installer. This part is the user-facing one: what the GUI actually looks like and what to do with it.

The GUI is a plain tkinter window (standard library only, no extra dependency). It ships in the Windows installer, and the same code runs from source with `python gui.py`.

## The window, field by field

There are three fields and one button:

1. **Statement PDF** — click "选择…" (Browse) and pick the PDF. The output path fills in automatically: same folder, same file name, `.csv` extension.
2. **Output CSV** — click "另存为…" (Save as) if you want the CSV somewhere else. Otherwise leave the default.
3. **Year (optional)** — only fill this in when your statement writes dates as MM-DD with no year. Leave it blank and the converter infers the year itself. If you do fill it, it must be a 4-digit year between 1900 and 2100; anything else gets a plain-language error and nothing runs.

Then click **开始转换** (Start conversion). The button disables itself while the conversion runs in a background thread, so the window stays responsive.

## What the result box tells you

When it finishes, the result area shows three things:

- How many transactions were extracted, e.g. "转换完成：共提取 34 笔交易。"
- The output file path.
- A missed-rows hint, or the all-clear line "未发现疑似漏提的行。"

The missed-rows hint is a heuristic, not a count: it counts text lines that look like they contain a date, subtracts the extracted rows, and reports the difference. Header dates and summary rows also contain dates, so a nonzero number does not prove rows were missed — it is a prompt to open the CSV and check. The last line of every successful run says exactly that: "请打开 CSV 核对金额与日期后再使用。" (Open the CSV and verify amounts and dates before using it.)

## What happens when it fails

Failures come back as plain-language messages, not tracebacks:

- No file selected, or the file does not exist: "找不到文件" / "还没选文件".
- Not a PDF: "请选择 PDF 文件".
- The PDF cannot be read — encrypted, damaged, or a scanned image PDF with no text layer: "无法读取该 PDF：请确认它是带文本层的数字对账单 PDF。扫描件（图片型 PDF）暂不支持，也可能是文件已损坏或被加密。" plus the technical reason in parentheses.

The GUI only handles digital PDFs with a text layer. Scanned PDFs need the OCR path (part 3 and part 7), which is a separate command-line flow, not in the GUI.

## What the GUI does not do

- No installer is needed to run it from source, and the window itself says so at the bottom: no OCR, no auto-update. Conversion happens locally; nothing is uploaded and nothing goes over the network. The only network call in the whole project is the optional `--check-update` flag on the command line (part 10), which the GUI does not expose.

## What this walkthrough does not prove

Two honest limits, same as the rest of the series:

- The GUI was smoke-tested in CI on a Windows runner (window opened, stayed up 15 seconds, no traceback — part 2). Nobody has yet clicked through it on a real person's Windows machine with a real bank statement.
- Real Chinese bank samples are still untested. The only real-bank run so far was a Starling Bank sample (part 9), which found a real date-validation bug — and that English layout still does not convert end to end.

If you try it on your own statement, the check that matters is the one in the result box: open the CSV, count the rows, spot-check the amounts against the PDF.

---

The converter is on GitHub: https://github.com/alapha888/bank-statement-presale

The Windows installer is a small presale: https://afa-kzz.onrender.com/bank-statement-presale/ — early-bird ¥29, regular ¥49, delivered by private message within 30 days or fully refunded.
