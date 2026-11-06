# 银行对账单转换器 (converter) — 核心转换逻辑

把带文本层的银行对账单 PDF 转成可导入 QuickBooks / Excel 的 CSV。
本地运行，不联网；文件只在本地处理。

> 本目录是预售产品的**核心转换逻辑单元**（命令行 + 图形界面 + 可导入模块）。
> Windows exe 与安装程序已由 GitHub Actions 打包验证（见“Windows 打包”）；自动更新仍待做。

## 用法

```bash
# 首次使用：创建虚拟环境并安装依赖（约 30 秒）
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # 含 fixture 生成与测试工具
# 仅运行时依赖：
.venv/bin/pip install -r requirements.txt

# 转换
.venv/bin/python bank_statement.py 对账单.pdf 输出.csv
.venv/bin/python bank_statement.py 对账单.pdf 输出.csv --year 2026  # 指定 MM-DD 日期的年份

# 在 Python 里用
from bank_statement import extract_transactions, convert
txns = extract_transactions("对账单.pdf")
convert("对账单.pdf", "输出.csv")
```

## 图形界面

```bash
.venv/bin/python gui.py
```

打开窗口后：选对账单 PDF → 确认输出 CSV 位置（默认与 PDF 同目录、同名
`.csv`）→ 需要时填年份（只影响 `MM-DD` 这类无年份日期，留空自动推断）
→ 点“开始转换”。完成后窗口显示提取到的交易笔数、输出路径，以及
“疑似漏提行数”（含日期但未被转成交易的行数，启发式统计——汇总行也可能
被计入，仅作核对提示）。

诚实范围：图形界面只包数字 PDF 路径（pdfplumber），**不支持扫描件 /
图片型 PDF，未含 OCR**；安装程序已在 CI 打包验证（见“Windows 打包”），无自动更新；转换只在本地进行，
不联网、不上传。界面用 tkinter（Python 标准库），不新增任何依赖。

## CSV 格式

| 列 | 说明 |
|---|---|
| 日期 | 统一为 `YYYY-MM-DD`（`MM-DD` 按对账单年份推断，见下） |
| 摘要 | 交易说明 / 对方户名（原文） |
| 支出 | 借方金额，无千分位、保留 2 位小数；无则为空 |
| 收入 | 贷方金额，同上 |
| 余额 | 余额，同上；无则为空 |
| 原始行 | 该行各单元格原文以 ` \| ` 连接（可追溯） |

CSV 以 UTF-8（含 BOM）写入，Excel 直接打开不乱码。

## 支持的版式（v1）

- 表格型对账单（pdfplumber 表格抽取）：分开的借方/贷方列，或单列带 `+`/`-` 的金额列。
- 无表格的纯文本行（行解析兜底）：`日期 摘要 金额 [余额]`。
- 日期：`YYYY-MM-DD`、`YYYY/MM/DD`、`YYYY年MM月DD日`、`MM-DD`、`MM/DD`。
  `MM-DD` 的年份先从文档中推断（`YYYY年` 标题或首个完整日期），
  推断不到时可用 `--year` 指定。
- 金额：千分位逗号、`+`/`-` 号、`(123.45)` 括号负数。
- 多页对账单（每页重复表头也可）。
- 对提取文本做 NFKC 归一化：某些 PDF 生成器会把 `-` 写成 U+2011、
  把个别汉字写成兼容区码位，归一化后才能正常匹配。

## 依赖

- 运行时只有 `pdfplumber==0.11.10`（见 `requirements.txt`）。
  选 pdfplumber 而不用 PyMuPDF/pypdf：它的按线表格抽取最适合银行对账单；
  且它是纯 Python（基于 pdfminer.six），部署简单。
  PyMuPDF 只用于生成测试 fixture，不参与转换。
- 开发/测试另需 `requirements-dev.txt`（PyMuPDF、fonttools、pytest）。

## 测试（一条命令）

```bash
./run_tests.sh
```

该脚本创建虚拟环境（如没有）、安装依赖、重新生成全部 fixture、
再跑 pytest。2026-11-06 实测：**1 passed**。

OCR 另有一条独立脚本（需要系统安装 tesseract，见下）：

```bash
.venv/bin/python test_ocr.py
```

## 验证状态（2026-11-06 实测，合成 fixture）

数字 PDF（文本层），逐字段与 ground truth 比对
（日期/摘要/支出/收入/余额五项全对才算一行正确）：

| Fixture | 版式 | 行数 | 正确 | 准确率 |
|---|---|---|---|---|
| fixture-a-two-col-two-page.pdf | 借方/贷方分列，YYYY-MM-DD，2 页 12 行 | 12 | 12 | 100% |
| fixture-b-single-amount.pdf | 单列金额带 +/−，YYYY/MM/DD | 8 | 8 | 100% |
| fixture-c-mmdd-reordered.pdf | 列顺序不同，MM-DD（年份在标题中） | 8 | 8 | 100% |
| fixture-d-text-lines.pdf | 无表格纯文本行（行解析兜底） | 6 | 6 | 100% |
| **合计** | | **34** | **34** | **100%** |

扫描件 / OCR：

| 检查 | 结果 |
|---|---|
| tesseract | 本机原本未安装；本次通过 apt 安装 5.3.4，含 chi_sim + eng 语言数据 |
| ocrmypdf | 本机未安装，未使用 |
| fixture-s1-scanned.pdf（fixture D 渲染成的 300 dpi 纯图片 PDF，无文本层） | tesseract `chi_sim+eng --psm 6` 识别后经行解析：**6/6 行全字段正确（100%）** |

OCR 结论：**干净的 300 dpi 合成扫描页可以走通**。这不等于“常规扫描对账单”
已验证——真实扫描件常有倾斜、噪点、低分辨率、印章遮挡，本次没有这类样本。

## 未验证 / 不属于本单元

- **真实银行 PDF**：工作区内没有任何真实银行对账单样本；各家银行的版式
  （表头措辞、列顺序、汇总行、跨页续表）只能等到拿到真实样本后再测。
  转换器按表头关键词（日期/摘要/支出/收入/余额/金额/借方/贷方等）认列，
  遇到未见过的表头措辞会跳过该表——宁可漏提，不瞎提。
- **重度破损扫描件**：超出预售 v1 范围；本次只验证了干净渲染页。
- **非数字 PDF 的其余形态**：加密 PDF、图片型 PDF 中混有文本层等未测。

## Windows 打包

- **已验证（2026-11-06，CI 首跑全绿，1m30s）**：`.github/workflows/build-windows.yml`
  在 windows-latest 上用 PyInstaller `--onefile` 打出两个 exe：
  - `bank-statement-converter.exe`（命令行，`--console`）——对 fixture A
    烟囱测试（12 行准确，CSV 表头 + 12 行 = 13 行），上传为 Actions artifact
    `bank-statement-converter-windows`（约 41 MB，未发布 Release）。
  - `bank-statement-converter-gui.exe`（图形界面，入口 `gui.py`，`--console`）——
    已接线进同一工作流，CI 首跑已验证（2026-11-06，run 42228311551，2m58s 全绿）：
    GUI 烟囱测试走分支 (b)，窗口在 runner 上打开、15 秒仍运行、无 Traceback 后杀掉；
    上传为 artifact `bank-statement-converter-gui-windows`（46,185,219 字节，约 44.0 MB，
    未过期，未发布 Release）。本地 Linux 构建亦验证能打出单文件（约 51.5 MB）且无显示时
    优雅退出（exit 1、有提示、无 Traceback）。
  流程为数字 fixture 全量验证（pytest）→ 两个 exe 各自烟囱测试 → 上传 artifact。
  每次改动 converter/** 或工作流本身都会重跑。
- **范围**：两个 exe 都只含数字 PDF 路径（pdfplumber）；OCR 路径需另装 tesseract，
  不在 exe 内；安装程序见下；无自动更新。
- **安装程序（2026-11-06，CI 已验证，run 42246793629，3m20s 全绿）**：
  `installer/bank-statement-converter.iss`（Inno Setup 6）把两个 exe 打成一个
  安装包 `bank-statement-converter-setup-1.0.0.exe`（89,732,967 字节，约 85.6 MB），
  上传为 artifact `bank-statement-converter-installer-windows`（未过期，未发布
  Release）。安装时装两个 exe 到同一目录、开始菜单两个快捷方式、桌面快捷方式
  （默认勾选、可取消）、附 converter/README.md 作说明。首跑曾因 [Tasks] 段写了
  非法 `Flags: checked` 编译失败，已去掉该 flag 后重跑全绿（见
  installer/BUILD-NOTES.md）。范围诚实：安装程序不捆 tesseract、不含 OCR；
  真实 Windows 机器上的安装与双击点检尚未做。
- **GUI exe 的 console 选择**：有意用 `--console` 而不用 `--windowed`，因为
  `gui.py` 的无显示提示（“无法打开图形界面…”）是打印到 stdout 的，
  `--windowed` 会把它吞掉、CI 也就无法断言它。代价是双击 GUI exe 时会同时
  出现一个黑色控制台窗口；等有真实 Windows 点检与错误落盘方案后再考虑
  `--windowed`。GUI 烟囱测试的期望见构建记录。
- **仍待做**：自动更新不在本单元内。

## Fixture 说明

- `fixtures/generate_fixtures.py`：生成 4 个数字 PDF fixture + `ground_truth.json`
  （余额为自期初余额起的连续计算值，内部一致）。
  生成工具为 PyMuPDF：CJK 用内置 `china-s` 字体、ASCII 用 Helvetica
  分段渲染——因为本机上 reportlab + NotoSansCJK .ttc 嵌入后 CJK 提取出来全是
  `\x00`，而 PyMuPDF + NotoSansCJK 会把 `-` 映射成 U+2011、个别汉字映射成
  兼容区码位；混合字体方案提取结果才是标准码位。
  （转换器本身的 NFKC 归一化也能兜住后一类问题，见上。）
- `fixtures/make_scanned_fixture.py`：把 fixture D 渲染成 300 dpi 纯图片 PDF/PNG。
- `test_converter.py`：数字 fixture 验证（也是 pytest 入口）。
- `test_ocr.py`：扫描 fixture 的 OCR 端到端验证；缺 tesseract 时退出码为 2
  并打印安装指引，不谎报通过。

## 文件清单

- `bank_statement.py` — 转换器（CLI + 模块）
- `gui.py` — 图形界面（tkinter 标准库；后端 `run_conversion` 可无显示器测试）
- `test_gui.py` — GUI 后端测试（不需要显示器）
- `GUI-构建记录-20261106.md` — 本次 GUI 构建记录
- `构建记录-GUI打包.md` — GUI 打进 Windows exe 的构建记录（console 选择、烟囱测试设计）
- `requirements.txt` / `requirements-dev.txt` — 依赖 pin
- `run_tests.sh` — 一条命令跑全量数字测试
- `test_converter.py` — 数字 fixture 验证
- `test_ocr.py` — OCR 端到端验证
- `fixtures/` — 4 个数字 PDF + 1 个扫描 PDF/PNG + ground truth + 两个生成脚本
