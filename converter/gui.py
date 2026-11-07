"""银行对账单转换器 — 图形界面（tkinter，标准库 only，无新增依赖）。

仅支持带文本层的数字 PDF（pdfplumber 路径）。
不支持扫描件 / 图片型 PDF（无 OCR）。

安装程序见 installer/；新版本检查为手动点按（不自动、不下载、不安装）。

转换逻辑在 bank_statement.py；本文件的 run_conversion() 是可独立测试
的后端入口（不需要显示器），界面只负责选文件、显示进度与结果。
"""

from __future__ import annotations

import re
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from bank_statement import CSV_COLUMNS, __version__, convert
from update_check import check_for_update

# 疑似交易行的启发式判断：行内出现日期（YYYY-MM-DD / MM-DD 等）。
# 用于估算"疑似漏提行数"：含日期的行数 − 已提取行数。
_DATE_LIKE = re.compile(r"20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}|\b\d{1,2}[-/]\d{1,2}\b")


@dataclass
class ConversionResult:
    ok: bool
    error: str = ""            # 失败时的人话错误说明；成功时为空
    rows: int = 0              # 提取到的交易行数
    output: str = ""           # 输出 CSV 路径
    skipped: int = 0           # 疑似漏提行数（启发式统计，见 _count_skipped）


def default_output_path(pdf_path: str | Path) -> str:
    """默认输出路径：与输入 PDF 同目录、同名 .csv。"""
    return str(Path(pdf_path).with_suffix(".csv"))


def _count_skipped(pdf_path: str | Path, extracted: int) -> int:
    """估算疑似漏提行数：含日期的文本行数 − 已提取行数（下限为 0）。

    只是提示性统计：表头日期、汇总行也可能含日期；它回答的是
    "有没有含日期的行没被转成交易"，不是精确的漏提计数。
    读不到文本层时返回 0（不瞎报数字）。
    """
    try:
        import pdfplumber

        date_lines = 0
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                for line in (page.extract_text() or "").splitlines():
                    if _DATE_LIKE.search(line):
                        date_lines += 1
        return max(0, date_lines - extracted)
    except Exception:
        return 0


def run_conversion(pdf_path: str | Path, csv_path: str | Path,
                   year: int | None = None) -> ConversionResult:
    """转换一发 PDF -> CSV（无界面依赖，供 GUI 与测试共用）。

    任何失败都以 ConversionResult(ok=False, error=人话说明) 返回，
    不抛异常、不崩溃。
    """
    pdf = Path(pdf_path)
    out = Path(csv_path)
    if not pdf.exists():
        return ConversionResult(False, f"找不到文件：{pdf}")
    if not pdf.is_file():
        return ConversionResult(False, f"不是文件：{pdf}")
    if pdf.suffix.lower() != ".pdf":
        return ConversionResult(False,
                                f"请选择 PDF 文件（当前是 {pdf.suffix or '无后缀'} 文件）")
    try:
        txns = convert(pdf, out, year)
    except Exception as exc:  # noqa: BLE001 - 任何读取/解析失败都转成人话
        return ConversionResult(
            False,
            "无法读取该 PDF：请确认它是带文本层的数字对账单 PDF。"
            "扫描件（图片型 PDF）暂不支持，也可能是文件已损坏或被加密。"
            f"（技术原因：{exc}）")
    return ConversionResult(
        ok=True,
        rows=len(txns),
        output=str(out),
        skipped=_count_skipped(pdf, len(txns)),
    )


def format_update_for_gui(result: dict) -> str:
    """把 update_check 的结果转成 GUI 里显示的中文说明（纯函数，无界面依赖）。

    只提示、不下载、不安装；检查失败时照实说原因，不谎报"已是最新"。
    """
    status = result.get("status")
    current = result.get("current", __version__)
    if status == "update-available":
        line = f"有新版本：{result.get('latest')}（当前版本 {current}）。"
        if result.get("url"):
            line += f"\n下载地址：{result['url']}"
        line += "\n本按钮只做提示，不会自动下载或安装。"
        return line
    if status == "up-to-date":
        return f"已是最新版本：{current}。"
    if status == "no-release":
        return (f"尚未发布任何正式版本（当前版本 {current}），"
                "无可比对的新版本。")
    return (f"新版本检查暂时不可用：{result.get('detail', '原因未知')}"
            f"（当前版本 {current}）。\n"
            "不影响转换功能；联网恢复后可再点一次。")


# ---- GUI -----------------------------------------------------------------

class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("银行对账单转换器")
        self.resizable(False, False)
        self._pdf_var = tk.StringVar()
        self._out_var = tk.StringVar()
        self._year_var = tk.StringVar()
        self._status_var = tk.StringVar(value="就绪：请选择对账单 PDF。")
        self._build_widgets()

    def _build_widgets(self) -> None:
        pad = {"padx": 8, "pady": 4}
        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frame, text="对账单 PDF：").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self._pdf_var, width=52).grid(
            row=0, column=1, **pad)
        ttk.Button(frame, text="选择…", command=self._pick_pdf).grid(
            row=0, column=2, **pad)

        ttk.Label(frame, text="输出 CSV：").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self._out_var, width=52).grid(
            row=1, column=1, **pad)
        ttk.Button(frame, text="另存为…", command=self._pick_output).grid(
            row=1, column=2, **pad)

        ttk.Label(frame, text="年份（可选）：").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(frame, textvariable=self._year_var, width=10).grid(
            row=2, column=1, sticky="w", **pad)
        ttk.Label(frame, text="只填 MM-DD 这类无年份日期时用；留空则自动推断。",
                  foreground="gray").grid(row=2, column=2, sticky="w", **pad)

        self._run_btn = ttk.Button(frame, text="开始转换",
                                   command=self._on_run)
        self._run_btn.grid(row=3, column=1, pady=10)

        self._update_btn = ttk.Button(frame, text="检查新版本",
                                      command=self._on_check_update)
        self._update_btn.grid(row=3, column=2, pady=10)

        ttk.Label(frame, textvariable=self._status_var,
                  wraplength=520, justify="left").grid(
            row=4, column=0, columnspan=3, sticky="w", **pad)

        self._result = tk.Text(frame, width=72, height=6, state="disabled",
                               wrap="word")
        self._result.grid(row=5, column=0, columnspan=3, **pad)

        ttk.Label(
            frame,
            text="说明：仅支持带文本层的数字 PDF；扫描件（图片型 PDF）暂不支持，"
                 "未含 OCR。\n新版本检查需手动点按，不自动联网、不自动下载安装；"
                 "转换只在本地进行，不上传。",
            foreground="gray", wraplength=520, justify="left").grid(
            row=6, column=0, columnspan=3, sticky="w", **pad)

    # -- 文件选择 -----------------------------------------------------------
    def _pick_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="选择对账单 PDF",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")])
        if not path:
            return
        self._pdf_var.set(path)
        if not self._out_var.get():
            self._out_var.set(default_output_path(path))

    def _pick_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="保存 CSV 到…",
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=Path(self._out_var.get()).name
            if self._out_var.get() else "对账单.csv")
        if path:
            self._out_var.set(path)

    # -- 转换 ---------------------------------------------------------------
    def _set_result_text(self, text: str) -> None:
        self._result.config(state="normal")
        self._result.delete("1.0", "end")
        self._result.insert("1.0", text)
        self._result.config(state="disabled")

    def _on_run(self) -> None:
        pdf = self._pdf_var.get().strip()
        out = self._out_var.get().strip() or (
            default_output_path(pdf) if pdf else "")
        year_text = self._year_var.get().strip()
        year: int | None = None
        if year_text:
            try:
                year = int(year_text)
            except ValueError:
                messagebox.showerror("年份不对", "年份请填 4 位数字，例如 2026；不需要填请留空。")
                return
            if not 1900 <= year <= 2100:
                messagebox.showerror("年份不对", "年份超出合理范围（1900–2100），请检查。")
                return
        if not pdf:
            messagebox.showerror("还没选文件", "请先选择要转换的对账单 PDF。")
            return
        if not out:
            messagebox.showerror("还没选输出", "请指定输出 CSV 的保存位置。")
            return
        self._out_var.set(out)
        self._run_btn.config(state="disabled")
        self._status_var.set("正在转换，请稍候…")
        self._set_result_text("")
        self.update_idletasks()
        threading.Thread(target=self._run_in_background,
                         args=(pdf, out, year), daemon=True).start()

    def _run_in_background(self, pdf: str, out: str, year: int | None) -> None:
        result = run_conversion(pdf, out, year)
        self.after(0, lambda: self._show_result(result))

    def _show_result(self, result: ConversionResult) -> None:
        self._run_btn.config(state="normal")
        if not result.ok:
            self._status_var.set("转换失败。")
            self._set_result_text(f"失败原因：{result.error}")
            return
        lines = [
            f"转换完成：共提取 {result.rows} 笔交易。",
            f"输出文件：{result.output}",
        ]
        if result.skipped:
            lines.append(
                f"提示：有 {result.skipped} 行含日期的文本未被转成交易"
                "（可能是汇总行或无法识别的版式，请打开 CSV 核对）。")
        else:
            lines.append("未发现疑似漏提的行。")
        lines.append("请打开 CSV 核对金额与日期后再使用。")
        self._status_var.set(f"完成：{result.rows} 笔交易已写入 CSV。")
        self._set_result_text("\n".join(lines))

    # -- 新版本检查 ---------------------------------------------------------
    def _on_check_update(self) -> None:
        """手动检查新版本：只提示，不下载、不安装；失败只报状态。"""
        self._update_btn.config(state="disabled")
        self._status_var.set("正在检查新版本…")
        self._set_result_text("")
        self.update_idletasks()
        threading.Thread(target=self._check_update_in_background,
                         daemon=True).start()

    def _check_update_in_background(self) -> None:
        result = check_for_update(__version__)
        self.after(0, lambda: self._show_update_result(result))

    def _show_update_result(self, result: dict) -> None:
        self._update_btn.config(state="normal")
        self._status_var.set("新版本检查完成。")
        self._set_result_text(format_update_for_gui(result))


def main() -> int:
    try:
        app = ConverterApp()
    except tk.TclError as exc:
        print(f"无法打开图形界面（没有可用的显示器）：{exc}")
        print("请改用命令行：python bank_statement.py 对账单.pdf 输出.csv")
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
