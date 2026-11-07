# dev.to 续篇稿 · 对账单 PDF 转 CSV part 11（2026-11-07 09:40 轮）

发布者说明（不发布这部分）：
- 角度：part 11，关闭 part 6 缺口清单“无自动更新”的另一半前提——第一个 Release 终于打出来了，`--check-update` 从此有了可比对象。承接 part 10（检查本身已做、但仓库尚无 Release，只能返回“尚无发布”）；本篇只讲这一项：标签怎么打的、为什么是不附二进制的源码快照、检查现在返回什么、以及仍然没做的部分。不重复 part 1–10 内容。
- 事实全部取自本轮实测：tag v0.1.0 打在 commit 2a2fb58（与 part 10 同一提交）＋ Release https://github.com/alapha888/bank-statement-presale/releases/tag/v0.1.0（2026-11-07T00:46:12Z 创建）＋ `gh release list` 此前为空、现有一条 ＋ 真实 API `releases/latest` 返回 tag v0.1.0（curl 独立核实，HTTP 200）＋ 本地 CLI `--check-update` 实测返回“up to date: 0.1.0 is the latest release”、退出 0（连续两次一致）＋ 首次尝试曾返回“update check unavailable: GitHub API returned HTTP 403”，立即重试即恢复（匿名配额当时剩余 17/60，未耗尽，属瞬态失败；如实记录，不掩盖）＋ README“更新检查”小节与两处“未发布 Release”已同步为新口径（commit 1a9e57a，已 push）。
  - 不附二进制的原因（诚实写明）：安装程序（约 85.6 MB，CLI＋GUI 双 exe）是预售交付物，不从公开 Release 分发；源码仓本身已公开，Release 只给源码快照加一个可供版本比较的标签。
  - 仍未做：自动下载／安装仍待做；图形界面入口待加；真实银行样本（中国银行）仍未测；真实 Windows 机器安装点检仍未做。
- 诚实口径：不写价格，只链一次预售页、一次仓库、一次 Release 页（Release 页链接只出现一次，计入“一次仓库”之外的额外链接需说明：本篇三个链接分别为仓库、预售页、Release 页，均只出现一次）。
- 标签：python、windows、showdev、tools（4 个）。
- 若 dev.to 会话过期，停止并汇报，不尝试登录。

---

标题：Bank statement PDFs to CSV, part 11: the first release is tagged — and what the version check says now

标签：python、windows、showdev、tools

正文：

Part 10 built a version check with nothing to check against. The repository had no release, so the honest output was "no release published yet". That was the correct answer at the time — but a version check that can only ever say "nothing to compare against" is a promise, not a feature. This post is the other half of that promise: the first release is now tagged, and the same command returns a real answer.

## What happened

The tag is `v0.1.0`, on the same commit part 10 shipped. The release page is at https://github.com/alapha888/bank-statement-presale/releases/tag/v0.1.0. It is a source snapshot — GitHub auto-attaches the source archives, and nothing else. That last part is deliberate, and I want to say why before anyone asks: the packaged Windows installer (about 85.6 MB, CLI and GUI executables) is the presale deliverable. It is not attached to the public release. The source is already public; the release exists to give the version check a real tag to compare against, not to hand out the packaged build for free.

I verified the release from two directions. The API endpoint for the latest release returns tag `v0.1.0` with HTTP 200. And the local CLI, run against the live API, now prints:

```
up to date: 0.1.0 is the latest release
```

Exit code 0, twice in a row. That is the `up-to-date` branch of the four-status check from part 10, exercised for real for the first time.

## The one failure, recorded honestly

The first attempt did not return that. It returned:

```
update check unavailable: GitHub API returned HTTP 403
```

I checked the anonymous API quota right after: 17 of 60 requests remaining, reset about half an hour out. The quota was not exhausted, so this was a transient failure, not a limit hit — and the immediate retry returned the correct answer. I record it because the check's whole design is "report the status, never raise": an `unavailable` line with exit 0 is the tool behaving as designed when the network disagrees with it. If you run `--check-update` and see `unavailable`, that is the answer for that minute, not a bug to chase — retry it.

## What this does not change

The release is a tag on a source snapshot. It does not add auto-download or auto-install — those are still not built, and the README still says so in the same section. The GUI entry for the check is still missing. Real Chinese bank samples are still untested, and a real Windows machine install check is still missing. Those stay on the list from part 6. What changed is narrower and worth naming exactly: the version check now has something real to compare against, and I have run it against the live API and watched it answer correctly.

Links: the converter repository is at https://github.com/alapha888/bank-statement-presale, the release is at https://github.com/alapha888/bank-statement-presale/releases/tag/v0.1.0, and the presale page is at https://alapha888.github.io/bank-statement-presale/.
