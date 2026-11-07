# dev.to 续篇稿 · 对账单 PDF 转 CSV part 4（2026-11-07 02:40 轮）

发布者说明（不发布这部分）：
- 角度：part 4，选库决策（为什么只用 pdfplumber）＋ fixture 生成踩坑实录。承接 part 1（34 行全对）与 part 3（OCR 路径）；本篇不重复数字，只讲“为什么选这个库”和“测试夹具本身差点藏住真问题”。
- 事实全部取自已核实来源：converter/README.md（依赖／Fixture 说明／验证状态三节，2026-11-06 实测）＋ requirements.txt（pdfplumber==0.11.10 唯一运行时依赖）＋ 构建记录（GUI 打包、安装程序 run 号已在 part 2 核实，不重复引用）。
  - 运行时只有 pdfplumber==0.11.10；选它而不用 PyMuPDF/pypdf：按线表格抽取最适合银行对账单；纯 Python（基于 pdfminer.six），部署简单。PyMuPDF 只用于生成测试 fixture，不参与转换。
  - 4 个数字 fixture 合计 34 行逐字段比对全对：A 借方/贷方分列 2 页 12 行、 B 单列金额带 +/- 8 行、C 列顺序不同 MM-DD 8 行、D 无表格纯文本行兜底 6 行。扫描件 OCR 6/6 已在 part 3 讲过，本篇只提一句、不展开。
  - fixture 生成踩坑（README Fixture 说明原文）：reportlab + NotoSansCJK .ttc 嵌入后 CJK 提取出来全是 \x00；PyMuPDF + NotoSansCJK 会把 - 映射成 U+2011、个别汉字映射成兼容区码位；最终方案 PyMuPDF 分段渲染（CJK 用内置 china-s 字体、ASCII 用 Helvetica）。转换器对提取文本做 NFKC 归一化，兜住 U+2011 这类问题。
  - 设计决策：表提取优先、无表格时行解析兜底；按表头关键词认列，未见过的表头措辞跳过该表、宁可漏提不瞎提。
  - 未验证：真实银行 PDF（各家版式、表头措辞、汇总行、跨页续表）未测；加密 PDF、图片型 PDF 中混有文本层未测；不宣称 pdfplumber 普遍最优，只写“适合这项工作、通过了这些测试”。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、pdf、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 4: why pdfplumber, and the fixture bug that almost hid a real one

标签：python、pdf、showdev、tools

正文：

Parts 1 to 3 of this series covered what the converter does: 34 rows across four statement layouts, all fields correct, then a GUI, a Windows installer, and the scanned-PDF path through OCR. This post is about a decision underneath all of that — which PDF library to build on — and about the test fixtures, which nearly hid a real problem instead of catching one.

## The choice: one runtime dependency

The converter has exactly one runtime dependency: `pdfplumber==0.11.10`. It was picked over PyMuPDF and pypdf for two concrete reasons. First, its line-based table extraction fits bank statements, which are mostly ruled grids with debit and credit columns. Second, it is pure Python on top of pdfminer.six, which keeps deployment simple — one package, no system binary to install.

PyMuPDF is still in the project, but only on the test side: it generates the test fixtures. It does not take part in conversion. That split matters, because the fixture generator is where the interesting bug lived.

## The fixture bug

To test the converter I generate synthetic statements and compare every extracted row field by field against ground truth. The first attempt used reportlab with an embedded NotoSansCJK font. It looked fine on screen. Extracted text, though, came back as `\x00` for every Chinese character — the embedded font's encoding made the text unrecoverable.

The second attempt used PyMuPDF with the same font. Chinese characters extracted correctly this time, but something quieter went wrong: the hyphen `-` was mapped to U+2011 (non-breaking hyphen), and a few Chinese characters landed on compatibility code points. A converter tested only against those fixtures would have learned to handle U+2011 hyphens as if that were normal — or, worse, the fixtures would have passed while real PDFs with plain ASCII hyphens behaved differently.

The fix was to render fixtures in two parts: CJK text with PyMuPDF's built-in `china-s` font, ASCII with Helvetica. And the converter itself now runs NFKC normalisation over all extracted text before parsing, so a U+2011 hyphen from any PDF generator is folded back to a plain hyphen before it can break a match. The fixture bug surfaced a real class of problem — PDF generators do emit odd code points — and the normalisation step is the answer to it, not to any single fixture.

## What the fixtures actually proved

Four digital layouts, 34 rows, every field compared against ground truth:

- Two-column debit/credit, two pages, 12 rows: 12/12
- Single amount column with `+`/`-` signs, 8 rows: 8/8
- Reordered columns with MM-DD dates (year taken from the title), 8 rows: 8/8
- No table at all, plain text lines through the fallback parser, 6 rows: 6/6

The scanned path (6/6 through OCR) was covered in part 3. The point of listing the four layouts here is that they exercise different code paths: table extraction first, text-line parsing as a fallback when there is no table to extract.

## Two decisions that fell out of this

First, columns are recognised by header keywords — date, description, debit, credit, balance, amount, and their Chinese equivalents. If the parser meets header wording it has never seen, it skips that table instead of guessing. A missed table is a visible failure; invented numbers are not.

Second, I am not claiming pdfplumber is the best PDF library in general. It was the best fit for this job — ruled tables, one dependency, no system binary — and it passed these tests. A different document shape (say, statements with no ruling lines at all) might change the answer, and the text-line fallback exists precisely because the table path will not cover everything.

## What this does not prove

The same honest limits as before, restated because they still apply: no real bank statement has been tested yet — every fixture is synthetic, and banks differ in header wording, column order, summary rows, and multi-page tables. Encrypted PDFs and image PDFs that mix in a text layer are untested. The 34/34 result says the converter handles the four layouts I built; it says nothing about the fifth layout I have not seen.

The converter is open source: https://github.com/alapha888/bank-statement-presale

The presale page with the full status, scope and refund terms: https://alapha888.github.io/bank-statement-presale/
