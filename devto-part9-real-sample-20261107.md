# dev.to 续篇稿 · 对账单 PDF 转 CSV part 9（2026-11-07 07:40 轮）

发布者说明（不发布这部分）：
- 角度：part 9，关闭 part 6 缺口清单“真实银行样本未测”的第一步——用一份能公开拿到的真实银行版式（英国 Starling Bank 公开样张）实测转换器在没见过的版式上的行为，并修掉一个真 bug（日期合法性校验）。承接 part 6 与 part 8（part 8 末尾仍写真实银行样本未测）；本篇只讲这一项，不重复 part 1–8 内容。
- 事实全部取自本轮实测：curl 下载的公开样张（4 页、212 行提取文本、151 行以 DD/MM/YYYY 日期开头、账期 01/10/2023–19/01/2024、表头 DATE/TYPE/TRANSACTION/IN/OUT/END OF DAY ACCOUNT BALANCE）＋ converter 默认运行 0 行 exit 0 ＋ --year 2023 修前 155 行、82 行不可能日期 ＋ 修复后 73 行、0 行不可能日期 ＋ 全量套件 11 passed ＋ commit bbdafd0。
  - 隐私红线：样张是公开托管的示例文件，但其中仍含开户人个人信息。本篇不写任何姓名、账号、IBAN、分行代码、交易对方与具体金额；只报告聚合计数与版式层面的模式。样本文件只存本地工作区，不提交进仓库。
  - 数字口径：151 是“以日期开头的行数”，不是交易笔数（部分行内含多笔交易拼接）；82/155 是修前 CSV 里月或日超出合法范围的行数（实测逐行计数）；23 行支出=2023.00 是年份碎片被当成金额；55 行摘要以 /2023 开头；44 行只有收入列；2 行标题行被提取。日期颠倒：03/10/2023 被读成 2023-03-10，实际是 2023-10-03；输出日期范围 2023-01-01–2023-12-12，而账期实际是 2023-10 至 2024-01。
  - 修复：bank_statement.py 的 parse_date 改走 _valid_date（datetime.date 校验），月/日不合法返回 None、该行跳过；新增回归测试 test_parse_date_rejects_impossible_dates（拒绝 60-83-71、31/10、2023-13-40、2023-02-30；合法日期不变）；./run_tests.sh 11 passed。
  - 仍未解决：73 行里的日期仍是 DD/MM 颠倒读法；23 行支出仍为年份碎片；55 行摘要仍带 /2023 残留；方向仍无法确定；2 行标题行仍在。中国银行真实样本仍未测——本次只证明了目标市场之外的真实版式的行为，缺口清单这一项不划掉。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、pdf、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 9: I finally ran it on a real bank statement — and found a bug

标签：python、pdf、showdev、tools

正文：

Part 6 ended with a list of things this converter had not proven. The first item on that list was the most important one: no real bank sample had ever been run through it. Every fixture so far was synthetic — invented payees, invented amounts, layouts I designed myself. This post takes the first step on that item, and it found a real bug.

One clarification up front, because the wording matters: this is not a Chinese bank sample. The converter is built for Chinese bank statements, and I still do not have a real Chinese sample — that can only come from a real account holder. What I found is a publicly hosted sample statement from a UK bank (Starling Bank), in English, with DD/MM/YYYY dates and separate IN/OUT amount columns. It is a real bank layout, outside the target market. The results below are about this sample only. I will not name the account holder or quote any account details from it; only aggregate counts and layout patterns.

## The sample

Four pages, 212 lines of extracted text, 151 lines starting with a DD/MM/YYYY date. The statement covers 01/10/2023 to 19/01/2024. The transaction table header reads DATE / TYPE / TRANSACTION / IN / OUT / END OF DAY ACCOUNT BALANCE. Three things differ from everything the converter was built for: English headers with no Chinese keywords, dates with the year last instead of first, and amounts with no sign — direction lives in the IN/OUT columns, not in the numbers.

## Default run: zero rows, no crash

```
python bank_statement.py statement.pdf out.csv
extracted 0 transactions -> out.csv
```

Exit code 0, empty CSV with just the header. The table path skipped the table because none of the header keywords matched, and the line parser skipped every line because no date in the document matched the supported formats and no statement year could be inferred. That is the design working as intended — the converter would rather extract nothing than guess. If a buyer feeds it an English statement by mistake, the default result is an empty CSV, not a wrong one.

## Forced run: 155 rows, 82 with impossible dates

Passing `--year 2023` forces the line parser to treat `MM/DD` fragments as dates. That produced 155 rows, and 82 of them had impossible dates — months like 60, days like 83. I counted them row by row in the output CSV.

The mechanism is simple and was entirely my code's fault. The line parser's date pattern matches any `NN/NN` fragment, and `parse_date` never checked whether the numbers could be a real date. A sort-code-like fragment and a DD/MM date with a day over 12 both sailed straight through as a "date". Worse, the dates that did pass the range check were still wrong: `03/10/2023` became 2023-03-10, when it is 3 October, not 10 March. The output's date range stretched from 2023-01-01 to 2023-12-12, while the statement actually covers October 2023 to January 2024.

The same run had more wrongness in the amount columns. Because the date match only consumed `03/10`, the leftover `/2023` stayed in the line, and the amount pattern then read `2023` as a sum of money — 23 rows came out with a debit of exactly 2023.00. 55 rows have descriptions starting with `/2023` for the same reason. And 44 rows landed entirely in the income column, because a single unsigned amount with no sign defaults to income; the IN/OUT distinction this layout uses is invisible to the line parser. Two header lines (the summary and statement title rows) were extracted as transactions too.

## The fix: validate the date

The fix is one function. `parse_date` now runs the numbers through `datetime.date` and returns nothing when they do not form a real calendar date, so that line is skipped instead of written out. A regression test pins the behaviour: it rejects a sort-code-like fragment, a DD/MM date, a month of 13, and 30 February, and leaves valid dates untouched. The full suite is 11 passed.

Re-running the same forced command after the fix:

```
extracted 73 transactions
```

Impossible dates: zero, down from 82. Rows dropped from 155 to 73 — the rejected rows were mostly the sort-code line and the DD/MM dates with a day over 12.

## What the fix does not do

I want to be exact about this, because the fix looks like a victory and it is only half of one. The remaining 73 rows still have their dates read month-first, so they are still systematically wrong. The 23 rows with the year fragment as a debit are still there. The 55 descriptions still start with `/2023`. Direction is still undetermined. The two header lines are still in the output. In other words, the validation removed the most obviously impossible dates, but this English layout as a whole is still not usable — and that is the correct conclusion for v1, which never claimed to support it. The `--year` flag is for Chinese MM-DD statements; forcing it onto an unsupported layout produces a CSV that looks normal and is wrong, and the README now says so explicitly.

## What this does not prove

Chinese bank samples are still untested — this post does not close that item, it only records the first real-layout behaviour. A real Windows machine install check and auto-update are still missing. Those stay on the list from part 6.

Links: the converter repository is at https://github.com/alapha888/bank-statement-presale, and the presale page is at https://alapha888.github.io/bank-statement-presale/.
