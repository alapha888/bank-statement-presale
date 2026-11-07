# Show HN 草稿 · 银行对账单转换器（2026-11-07）

> 用途：提交到 Hacker News 的 Show HN 帖。标题＋URL＋正文逐字填入，不改写、不加价
> 格、不加额外链接。事实全部取自已核实来源（仓库 README、11-06/11-07 日志与 CI 实测）。

## Title

Show HN: Bank statement PDFs to CSV – a converter that skips what it can't parse

## URL

https://github.com/alapha888/bank-statement-presale

## Text

I built a small local desktop tool that turns bank statement PDFs into CSV
(6 columns: date / description / out / in / balance / raw line), for import
into QuickBooks or Excel. Files are processed on the machine only, nothing is
uploaded.

What it does, and what I verified so far:

- Digital text PDFs: 34/34 rows extracted correctly on synthetic fixtures
  (four layouts).
- Scanned PDFs: 6/6 rows via OCR (tesseract, chi_sim+eng; not bundled, you
  install it separately — the Windows install steps are CI-tested).
- Edge cases I actually ran: encrypted PDFs (clean error, exit 2), stamped
  pages (12/12), and statements with no table lines (a known limit: dates
  found, only 2/12 rows fully correct — documented, not hidden).
- Windows CLI and GUI exes plus an Inno Setup installer are built in CI;
  v0.1.0 is tagged. `--check-update` compares against the latest release
  (check only — no auto-download, no auto-install).

What it deliberately does not do: it skips rows and tables it cannot parse
instead of guessing, and the CSV keeps the raw source line so you can audit
every row. The tradeoff is missed rows rather than wrong numbers.

What it has not proven yet: no real Chinese bank sample has been tested
(a Starling Bank sample exposed a date-validation bug, which I fixed);
no install check on a real Windows machine; no auto-update.

Disclosure: the repo is free to read and the converter source is there. The
Windows installer is sold as a small presale (early bird ¥29 / ¥49, delivered
by DM within 30 days or fully refunded). I'm posting the repo, not the
checkout page.
