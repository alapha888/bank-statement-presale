# GUI 打包进 Windows exe — 构建记录（2026-11-06）

## 改了什么

- `.github/workflows/build-windows.yml`：
  - 新增构建步骤 `Build Windows GUI exe`：
    `pyinstaller --onefile --name bank-statement-converter-gui --console gui.py`
    （入口 `converter/gui.py`，tkinter 标准库，无新增依赖）。
  - CLI exe 构建原封不动：`pyinstaller --onefile --name bank-statement-converter --console bank_statement.py`，
    及其 fixture A 烟囱测试（12 行 → CSV 表头 + 12 行 = 13 行）未动。
  - 新增烟囱测试步骤 `Smoke-test the GUI exe (headless runner)`（设计见下）。
  - 新增 artifact 上传步骤：`bank-statement-converter-gui-windows`
   （`converter/dist/bank-statement-converter-gui.exe`，`if-no-files-found: error`）；
    CLI artifact `bank-statement-converter-windows` 未动。
  - 工作流头部注释同步：两个 exe 均为数字 PDF 路径（pdfplumber），无 OCR、
    无安装程序、无自动更新；两个 exe 均为 console 构建。
- `converter/README.md`“Windows 打包”小节：写明两个 exe（CLI + GUI）、
  各自的 artifact 名与烟囱测试、共同范围（数字 PDF only，OCR 不在 exe 内，
  无安装程序、无自动更新）、GUI exe 的 console 选择与代价。
  “仍待做”仍只有安装程序、自动更新。
  - 说明：README 的“仍待做”里本来就没有“GUI 打包进 Windows exe”这一项
    （GUI 落地时已从 README 的待做里去掉）；该项只留在
    `GUI-构建记录-20261106.md`“仍未做”里。本次构建完成后，该项即视为完成，
    旧记录是 dated 历史记录，不改；以本文件为准。
- 本文件（构建记录）新增；文件清单已补登记。

未动：`index.html`、仓库根 README、converter 核心逻辑（`bank_statement.py`、
`gui.py` 均未改）、预售页文案、价格与交付承诺。

## console / windowed 选择：`--console`

**决定：GUI exe 用 `--console`，不用 `--windowed`。**

理由：

1. `gui.py` 的无显示降级是 `print()` 到 stdout（“无法打开图形界面（没有可用的
   显示器）：…”+ 命令行提示），退出码 1。`--windowed` 构建会把 stdout/stderr
   重定向到空，提示信息在 CI 里不可见，烟囱测试也就无法断言它——等于把
   GUI 唯一的失败信号静默丢掉。
2. 只有 `--console`，CI 才能捕获并断言那条提示（见下）。

代价（已接受，记在这里）：双击 GUI exe 时，除了 GUI 窗口还会同时出现一个
黑色控制台窗口；关掉控制台会连带关掉 GUI。这是 presale v1 为可观测性付
出的 UX 成本。改回 `--windowed` 的前提（缺一不可）：① 错误有落盘方案
（例如写日志文件），失败不再静默；② 在真实 Windows 机器上做过点检
（双击打开、转换一次、关掉窗口）。

## 烟囱测试期望（CI，headless Windows runner）

关键适配：**Linux 的无显示行为不能直接搬到 Windows 上。**

- Linux 上 `tk.Tk()` 在无 `$DISPLAY` 时抛 `tk.TclError`，`gui.py` 捕获后打印
  提示、退出码 1、无 Traceback（本地已实测，见下）。
- Windows 的 tkinter 走 Win32 API，不用 `$DISPLAY`；GitHub 的 windows-latest
  runner 自带桌面会话，所以 `Tk()` **预期能成功**、进 `mainloop()` 后阻塞，
  不会快速退出。Linux 式“快速退出 1”在 runner 上是备用分支，不是期望分支。

因此烟囱测试接受且仅接受以下两种结果，每种都有严格断言——**不是
“任意退出码都算过”**：

- (a) 快速退出：退出码必须**恰好是 1**，stdout 必须含“无法打开图形界面”，
  stdout/stderr 均不得含 `Traceback`。（对应真正无显示的 Windows 会话。）
- (b) 15 秒后仍在运行：窗口已打开、`mainloop()` 存活，捕获到的输出中不得含
  `Traceback`；随后杀掉进程，通过。（runner 上的期望分支。）

其它一律失败：退出码非 1、退出 1 但没有提示信息、任何 `Traceback`、
退出码 0（`mainloop()` 不可能正常返回 0，说明流程异常）。

实现（pwsh）：`Start-Process -PassThru -RedirectStandardOutput/-RedirectStandardError`
起 exe，`WaitForExit(15000)` 分支判断；分支 (b) 用 `Stop-Process -Force` 杀掉。
输出重定向到文件是为了分支 (b) 也能检查 `Traceback`（直接读进程输出流在
进程未退出时会阻塞，故不用 `ReadToEnd`）。

## 本地验证结果（2026-11-06，Linux 本机，无显示器）

- `./run_tests.sh`（改动后重跑）：**6 passed，0 failed**（与改动前一致）：
  `test_converter.py::test_fixtures` + `test_gui.py` 5 个。
- 工作流 YAML 解析通过：`python3 -c "yaml.safe_load(...)"` 无报错。
- PyInstaller 本地可用（`pip install pyinstaller` 进 `.venv`，6.22.3；
  `.venv` 在 `.gitignore` 内，不影响仓库）。用与 CI 相同的参数本地构建 GUI 入口：
  `pyinstaller --onefile --name bank-statement-converter-gui --console gui.py`
  ——构建成功，无缺失 import 报错；产物 `dist/bank-statement-converter-gui`
  单文件 54,053,440 字节（约 51.5 MB）。
- 本地构建出的 GUI 二进制无显示运行：退出码 **1**，stdout 为
  “无法打开图形界面（没有可用的显示器）：no display name and no $DISPLAY
  environment variable”+ 命令行提示，stderr 为空，stdout/stderr 中
  `Traceback` 出现 **0 次**。与 `python gui.py` 的行为一致，说明 PyInstaller
  打包未丢东西（tkinter、pdfplumber 经 `bank_statement` 引入，均已收进包里）。
- 本地构建产物（`dist/`、`build/`、`*.spec`）验证后已清理，不进仓库；
  `.gitignore` 未覆盖这三者，CI 产物只存在于 runner 上，不提交。

## 仍未验证（需 parent / 真实 Windows 侧确认）

- **CI 首跑**：本机无 Windows，工作流改动尚未在 windows-latest 上跑过。
  需 push 后看 Actions：两个构建步骤、两个烟囱测试（尤其 GUI 的分支 (b)——
  窗口打开、15 秒存活、无 Traceback、杀掉后通过）、两个 artifact 上传。
  若 GUI 烟囱测试在 runner 上既不走 (a) 也不走 (b)（例如 `Start-Process`
  重定向参数在该 runner 的 pwsh 版本上有兼容问题），按报错原文修测试步骤，
  不要放宽断言。
- **真实 Windows 机器点检**：双击 GUI exe、选 fixture A 的 PDF、转换、核对
  CSV；确认控制台窗口伴随出现是否可接受；确认窗口布局与按钮在真实显示器
  上无问题。
- **安装程序、自动更新**：仍在 README“仍待做”里，不属于本单元。
- **真实银行 PDF 样本**：与转换器本体一致，仍未验证，只在合成 fixture 上验证。
