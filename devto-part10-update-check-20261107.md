# dev.to 续篇稿 · 对账单 PDF 转 CSV part 10（2026-11-07 08:40 轮）

发布者说明（不发布这部分）：
- 角度：part 10，关闭 part 6 缺口清单“无自动更新”的一半——做了一个显式的新版本提示（`--check-update`），并写明它故意不做的部分（不下载、不安装、不开机自查、不收集信息）。承接 part 6（清单写“自动更新（没有，升级靠重跑新安装程序）”）与 part 2（安装程序）；本篇只讲这一项，不重复 part 1–9 内容。
- 事实全部取自本轮实测：新增 converter/update_check.py（标准库 urllib，只做一次 GET 到 GitHub 最新 Release）＋ `__version__ = "0.1.0"` ＋ CLI `--check-update` 与 `--version` ＋ 11 项新增测试（全部 mock，不触网）＋本地全量套件 22 passed ＋ 真实 API 实测返回“no release published yet (you have 0.1.0)”退出 0 ＋ commit 2a2fb58 ＋ CI 两路 run 42320241535／42320241294 success、Pages 42320241062 success。
  - 状态机四值：update-available／up-to-date／no-release（404，仓库尚无 Release）／unavailable（网络或解析失败，只报状态不抛异常、不影响转换）。
  - 数字口径：22 passed = 11 项原有（转换器／GUI／边界）＋ 11 项新增（更新检查）；CI 三路全绿指本次提交触发的两路构建 run 与 Pages 各一。
  - 仍未做：自动下载／安装仍待做；图形界面入口待加（目前仅命令行）；仓库尚未发布任何 Release，第一个 Release 打出标签后该检查才有可比对象。
- 诚实口径：不写价格，只链一次预售页、一次仓库。
- 标签：python、windows、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 10: I added a version check — and what I deliberately did not build

标签：python、windows、showdev、tools

正文：

Part 6 ended with a list of things this converter had not proven. One item on that list was auto-update: the installer was verified, but once installed, the program had no way to tell you a newer version existed. Upgrading meant re-running a new installer, and nothing would ever prompt you to do it. This post closes half of that item — a version check — and I want to be exact about which half, because the half I did not build matters more than the half I did.

## What I built

A small module, `update_check.py`, using only the Python standard library. It does one GET to the GitHub API for the latest release tag of this repository and compares it with the local version, which is now stamped as `0.1.0`. The CLI gained two flags:

```
python bank_statement.py --check-update
python bank_statement.py --version
```

The check returns one of four statuses, and nothing else. `update-available` when a newer tag exists. `up-to-date` when the local version is at or above the latest tag. `no-release` when the repository has no release published yet — the API answers 404, and that is a fact about the repository, not an error. `unavailable` when the network fails, the response is malformed, or the tag cannot be parsed as a version. A failure is reported as a one-line status and the command still exits 0, because the check is advisory and must never break a conversion.

I ran the real check against the live API. The repository has no release published yet, so the honest output is:

```
no release published yet (you have 0.1.0) — nothing to compare against
```

That is the correct answer today. The first release has not been tagged, so there is nothing to compare against, and the tool says so instead of inventing a version or failing loudly. Once the first release is tagged, the same command will start comparing for real.

The tests are eleven new cases, all with the network faked — a newer tag, the same tag, an older tag, a tag without the `v` prefix, a 404, a 500, a network error, a non-numeric tag, a missing tag, malformed JSON, and a CLI run that checks and exits 0. The full suite is 22 passed locally, and the CI runs for this commit are green on all three workflows.

## What I deliberately did not build

No download. No install. No check at startup, and no check on every conversion — the converter stays offline by default, and this is the single exception, only when you ask for it. No telemetry of any kind: the request is a plain GET with no account, no file names, nothing about your statements. And no graphical button yet — the check is command-line only for now; the GUI entry is a separate, later piece of work.

The reason is scope, not laziness. An auto-updater that downloads and replaces a running executable is a different class of feature: it needs a safe replace-and-restart path on Windows, a rollback story for a bad download, and a signature or checksum story worth trusting. Building a quiet half-measure and calling it auto-update would be worse than saying plainly that it does not exist yet. So the honest statement is: you can now ask whether a newer version exists, in one command, and the answer is one line. Downloading and installing it is still your job, and the README says so in the same section.

## What this does not prove

Auto-update is still missing — this post closes the "does the program know a newer version exists" half, not the "does it install it" half. A real Windows machine install check is still missing. Chinese bank samples are still untested. Those stay on the list from part 6.

Links: the converter repository is at https://github.com/alapha888/bank-statement-presale, and the presale page is at https://alapha888.github.io/bank-statement-presale/.
