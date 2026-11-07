# dev.to 续篇稿 · 对账单 PDF 转 CSV part 8（2026-11-07 06:40 轮）

发布者说明（不发布这部分）：
- 角度：part 8，关闭 part 6 缺口清单“加密／图文混排／重度劣化 PDF 未测”一项的实证篇——三个边界形态合成样张的实测结果，含一个真实局限（E3 借方/贷方判反）。承接 part 6（该篇明确写了这三类形态未测）；本篇只讲这一项的验证过程与结果，不重复 part 1–7 内容。
- 事实全部取自已核实来源：本地 `./run_tests.sh` 全绿（10 passed，含新增 test_edge_cases.py 4 项）＋ converter 66f897a commit＋实读代码（bank_statement.py 的 PasswordProtectedError 处理）＋实读 fixture 生成脚本（fixtures/generate_edge_fixtures.py）。
  - E1 加密：fixture A 内容，PyMuPDF AES-256 加密，用户口令 test123（合成样张专用口令，公开写明无妨）。实测前：pdfplumber 抛空消息的 PdfminerException（内层为 pdfminer 的 PDFPasswordIncorrect），CLI 直接打 traceback。实测后：extract_transactions 抛 PasswordProtectedError（人话消息），CLI 退出码 2、无 traceback、无 CSV 写出；GUI 本来就把一切异常转成人话提示，现技术原因栏也不再是空消息。
  - E2 图文混排：fixture A 同 12 行、两页，页 1 右上角嵌一张 PyMuPDF 渲染的“某某银行 业务专用章”光栅图，文本层不动。结果 12/12 行全字段正确（100%），与 fixture A 逐字段一致。
  - E3 无表格线：同 12 行、同列位置，但一张表格线都不画，pdfplumber 找不到表格，走行解析兜底。结果：12/12 行找到、12/12 日期正确，但只有 2 行（两笔收入）全字段正确；10 笔支出因金额无正负号、行解析又拿不到列信息，借方/贷方判反。已锁定为特征测试（test_e3_no_ruling_lines_characterisation），修法是行解析改用 extract_words 的 x 坐标认列，超出预售 v1 范围，留待后续。
  - 仍未证明：真实银行样本上的同类形态、真实银行样本本身、真实 Windows 机器安装点检、无自动更新。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、pdf、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 8: encrypted, stamped, and line-less — three edge cases I finally tested

标签：python、pdf、showdev、tools

正文：

Part 6 ended with a list of things this converter had not proven. One item on that list was three PDF shapes I had never tested: encrypted PDFs, image PDFs that still have a text layer, and statements with no table ruling lines at all. This post closes that item. Two of the three went fine. The third found a real limitation, and that is the most useful part.

The test setup is the same as the rest of the series: synthetic fixtures, invented payees and amounts, ground truth written down before the converter runs. The new fixtures are E1, E2 and E3 in the repository, all built from the same 12-row statement as fixture A, so the results compare directly.

## E1: the encrypted PDF

I took fixture A and re-saved it with AES-256 encryption (user password `test123` — a synthetic fixture, nothing secret in it). Before this round, the converter's answer was bad: pdfplumber raised a `PdfminerException` with an empty message, wrapping pdfminer's `PDFPasswordIncorrect`, and the CLI printed a bare traceback. A user would have learned nothing from that output.

The fix is small and now tested: `extract_transactions` translates that specific failure into a `PasswordProtectedError` with a plain message — the PDF is password-protected, decrypt it first, then convert — and the CLI exits with code 2, no traceback, and writes no CSV. The GUI already turned every failure into a human message; its technical-reason line is no longer empty for this case either. The converter still cannot open an encrypted PDF. What changed is that it now says so clearly instead of crashing obscurely.

## E2: a stamp image on the same page

Real statements often carry a raster stamp or logo on the same page as the transaction table. I embedded a small raster stamp image ("business seal") in the top-right corner of page 1, leaving the text layer untouched, and ran the same 12 rows through.

Result: 12/12 rows, every field correct, identical to fixture A. An embedded image does not disturb table extraction, because pdfplumber reads the text layer and the image is simply not text. This was the expected outcome; it is worth having as a test rather than an assumption, since the converter will meet stamped statements in the real world.

## E3: no ruling lines at all — the honest failure

This is the interesting one. I drew the same 12 rows at the same column positions, with the same header, but no table lines whatsoever. Without lines, pdfplumber finds no table, and the converter falls back to its line parser, which reads each row as a line of text: date, description, then the numbers.

Result: 12/12 rows found, 12/12 dates correct — but only 2 of the 12 rows are fully correct. The 10 spending rows came back with debit and credit swapped.

The reason is structural, not a typo. In this fixture the debit and credit are separate columns with unsigned amounts — `328.50` in the debit column, no minus sign. The line parser sees two trailing numbers (amount, balance) and, with no sign to go on, assigns the amount to income. The table path never has this problem, because the header tells it which column is which; the line fallback has no column information at all.

I locked this in as a characterisation test — it asserts the measured behaviour, 2 fully correct out of 12, with the 10 swaps — so the limitation is on the record and any future fix has to update the test deliberately. The fix would be to give the fallback column positions, for example by reading word x-coordinates instead of plain text lines. That is real work and out of scope for presale v1, so for now the honest statement is: statements without ruling lines extract, but spending and income may be swapped. The two income rows were correct, which is consistent with the mechanism, not luck.

## What this does not prove

The three shapes were tested on synthetic fixtures, not real bank PDFs — real statements with the same shapes are still untested, as are real bank samples in general. The Windows installer still has no real-machine install check, and there is still no auto-update. Those items stay on the list from part 6.

Links: the converter repository is at https://github.com/alapha888/bank-statement-presale, and the presale page is at https://alapha888.github.io/bank-statement-presale/.
