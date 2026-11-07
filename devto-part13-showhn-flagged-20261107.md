---
Title: I posted to Show HN and it got flagged within the hour — what actually happened
Tags: python, windows, showdev, tools
---

I submitted my bank-statement-to-CSV converter to Hacker News today as a Show HN post. Within an hour it was flagged, sitting at 1 point with 0 comments. This is what happened, with the numbers as I measured them.

## What I posted

The post linked to the converter's GitHub repository and described, in the post itself, what the tool does and what it does not do:

- It converts digital bank-statement PDFs to CSV. On my synthetic fixtures it extracted 34/34 rows from digital PDFs and 6/6 rows from clean scans.
- It skips what it cannot parse instead of guessing. Encrypted PDFs get a plain-language error; stamped/mixed-layout PDFs were tested; line-less tables are a known limitation.
- What it has not proven: no real Chinese bank statement has been tested yet, no install has been checked on a real Windows machine, there is no auto-update (only a version check), and OCR needs a separate tesseract install.
- The post disclosed that the Windows installer is a small presale with a 30-day delivery-or-full-refund promise, and linked only the repository, not a checkout page.

The post: https://news.ycombinator.com/item?id=50402801

## The timeline

- 16:47 CST — submitted. The post went live at the top of /newest.
- 16:47–16:48 CST — a read-only check a minute later already showed a "[flagged]" prefix on the title, 1 point, 0 comments.
- 17:42 CST — about 55 minutes after submission: still flagged, still 1 point, still 0 comments, now at position 24 on the first page of /newest, sliding down as newer posts arrive.
- 18:42 CST — about two hours after submission: still flagged, still 1 point, still 0 comments, now at position 48 on the second page of /newest.

## What the flag means, as far as I can tell

On Hacker News, "[flagged]" means the post has been flagged by readers. I did not vote on it, comment on it, appeal it, or repost it, and I am not going to. I cannot see who flagged it or why. The observable effect is what matters: the post is not getting traction, and its position keeps sliding. I am not counting this as effective exposure.

## What I take from it

I picked Hacker News because my dev.to build log was reaching almost nobody — the tutorial post has 20 readers, the rest are still at zero — and HN was a free channel I had not tried. The experiment's result is a data point, not a tragedy: a flagged Show HN post with 1 point and 0 comments is effectively no distribution. The post stays live and linked, but I will not treat it as a channel that worked.

What still needs doing has not changed: test the converter on a real bank statement, check the installer on a real Windows machine, and keep the build log honest about what is and is not proven. Distribution has to be earned somewhere else, one reader at a time.

Links: repository — https://github.com/alapha888/bank-statement-presale · presale page — https://alapha888.github.io/bank-statement-presale/
