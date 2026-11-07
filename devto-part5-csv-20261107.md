# dev.to 续篇稿 · 对账单 PDF 转 CSV part 5（2026-11-07 03:40 轮）

发布者说明（不发布这部分）：
- 角度：part 5，输出物本身——CSV 长什么样、怎么在信任它之前先核对。承接 part 1–4（提取、GUI/安装程序、OCR、选库）；本篇不重复提取逻辑，只讲输出格式与核对方法。
- 事实全部取自已核实来源：converter/bank_statement.py（CSV_COLUMNS、write_csv、parse_amount、parse_date、_rows_from_table、_rows_from_text_lines，2026-11-07 03:40 实读）＋本轮实测（.venv pytest test_converter.py 1 passed；四 fixture 逐个转换计数 12+8+8+6=34 行）。
  - CSV 六列：日期、摘要、支出、收入、余额、原始行；写出为 UTF-8 带 BOM（utf-8-sig），Excel 直接打开中文不乱码。
  - 日期统一归一化为 YYYY-MM-DD；只有 MM-DD 的日期从对账单年份推断（文档内“YYYY年”提示或首个完整日期），或 --year 显式指定。
  - 金额统一为两位小数纯数字：千分位逗号去掉，(123.45) 括号形式作负数，前导 +/- 处理；单列“金额”时负数进支出、正数进收入。
  - 原始行：每行附带来源原文（表格行：各单元格以 " | " 连接；纯文本行：整行原文），可逐行回查 PDF。
  - 默认输出：与输入 PDF 同目录、同名 .csv。
  - 故意不进 CSV 的行：没有可解析日期的行跳过（小计行、页脚、续行）；表头既无日期列又无金额列的表整表跳过——宁可漏提不瞎提。后果：CSV 行数可能少于 PDF 里的行数，要数。
  - GUI 完成提示原文要求用户“打开 CSV 核对金额与日期后再使用”。
  - 数字：四数字 fixture 合计 34 行全部提取（A 12、B 8、C 8、D 6），test_converter.py 本轮实测 1 passed；扫描件 OCR 6/6 见 part 3。
  - 未验证：真实银行 PDF（各家版式、表头措辞、汇总行、跨页续表）未测；加密 PDF、图片型 PDF 中混有文本层未测。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、csv、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 5: what the CSV looks like, and how to check it before you trust it

标签：python、csv、showdev、tools

正文：

Parts 1 to 4 of this series covered extraction: 34 rows across four statement layouts, all fields correct, then a GUI, a Windows installer, the scanned-PDF path through OCR, and why pdfplumber was the library. This post is about the other end of the pipeline — the CSV file itself. It is the thing you actually open, and the thing you have to trust before it goes anywhere near a spreadsheet or a tax return.

## Six columns, and what each one holds

Every CSV the converter writes has the same header, in this order:

`日期, 摘要, 支出, 收入, 余额, 原始行`

- `日期` — the transaction date, normalised to `YYYY-MM-DD`.
- `摘要` — the description, as printed on the statement.
- `支出` — money out, a plain number with two decimals, or empty.
- `收入` — money in, same format, or empty.
- `余额` — the running balance when the statement prints one, or empty.
- `原始行` — the source text that row came from, kept verbatim.

The file is written as UTF-8 with a byte-order mark, so Excel opens it with the Chinese characters intact instead of mojibake. The default output path is next to the input PDF, same name, `.csv` extension.

## What normalisation does, and why

Two things are normalised on the way out, because bank PDFs are not consistent about either.

Dates: a statement can print `2026-03-04`, `2026/03/04`, `2026年3月4日`, or a bare `03-04`. Bare month-day dates take their year from the statement itself — a `YYYY年` hint in the document, or the first full date found — or from an explicit `--year` flag. Everything lands in the CSV as `YYYY-MM-DD`, so sorting and filtering work without reparsing.

Amounts: thousands commas are stripped, `(123.45)` in parentheses is read as a negative, and leading `+`/`-` signs are handled. A statement with a single signed `金额` column splits on sign: negative goes to `支出`, positive to `收入`. What lands in the CSV is a plain number with two decimals — no commas, no currency symbols, no parentheses — so a spreadsheet can sum the column directly.

The last column, `原始行`, is the audit trail. For a table row it is the row's cells joined with ` | `; for a plain-text statement it is the whole source line. Every converted row can be traced back to the exact text it came from, which is what makes the checks below possible.

## What is deliberately left out

Not every row in a PDF becomes a row in the CSV. Two rules decide that, and both err toward leaving things out rather than inventing them.

First, a row with no parseable date is skipped. That is how subtotal rows, footers, and continuation lines are dropped — they carry numbers but no date, so they are not transactions.

Second, a table whose header has no date column, or no amount column at all, is skipped whole. The parser recognises columns by header keywords; wording it has never seen means the table is passed over, not guessed at.

The consequence is honest but worth stating plainly: the CSV can have fewer rows than the statement appears to have. A missing row is a visible failure you can catch by counting. A wrong number silently copied into the wrong column is not, which is why the parser prefers the first failure mode.

## How to check a CSV before you trust it

The GUI says it on completion, and it is worth repeating here: open the CSV and check amounts and dates before using it. Four checks take about a minute:

1. Count the rows, and compare against the statement. If the PDF shows 40 transactions and the CSV has 34, find the six — they are probably in a table with unfamiliar header wording, and the `原始行` column will tell you nothing was invented in their place.
2. Spot-check `原始行` against the PDF for a few rows, especially the largest amounts. The source text is right there in the last column.
3. Sum the `支出` and `收入` columns and compare against the statement's own totals, if it prints them. A mismatch means something was misread or missed, and it is better to find that here than in a spreadsheet downstream.
4. Treat an empty `余额` as missing, not zero. Some layouts print no balance column at all, and an empty cell only means the statement did not supply one.

These checks exist because the converter has only ever been tested on synthetic statements: 34 rows across four digital layouts (12, 8, 8, and 6), all fields correct, plus 6/6 on the scanned path through OCR. No real bank statement has been tested yet, and banks differ in header wording, column order, summary rows, and multi-page tables. Encrypted PDFs and image PDFs with a partial text layer are untested too. The 34/34 result says the converter handles the four layouts I built; it says nothing about the fifth layout I have not seen.

The converter is open source: https://github.com/alapha888/bank-statement-presale

The presale page with the full status, scope and refund terms: https://alapha888.github.io/bank-statement-presale/
