import asyncio
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from exam_helper import main as run_exam_helper


class ExamGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Exam Helper")
        self.geometry("700x420")
        self.resizable(False, False)

        self.url_var = tk.StringVar(value="")
        self._thread = None

        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="考试 URL:").pack(anchor="w", padx=12, pady=(12, 4))
        tk.Entry(self, textvariable=self.url_var, width=90).pack(fill="x", padx=12, pady=4)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=12, pady=8)
        tk.Button(btn_frame, text="开始", width=12, command=self.start_run).pack(side="left")
        tk.Button(btn_frame, text="退出", width=12, command=self.destroy).pack(side="left", padx=(8, 0))

        tk.Label(self, text="日志:").pack(anchor="w", padx=12, pady=(8, 4))
        self.log_box = scrolledtext.ScrolledText(self, height=18, width=90, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=8)

    def append_log(self, message: str):
        self.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    def start_run(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入考试 URL")
            return

        self.append_log("开始运行...")
        self._thread = threading.Thread(target=self._run_helper, args=(url,), daemon=True)
        self._thread.start()

    def _run_helper(self, url: str):
        try:
            asyncio.run(run_exam_helper(url, log_callback=self.append_log))
        except Exception as exc:
            self.append_log(f"运行失败: {exc}")
        finally:
            self.append_log("运行结束")


def launch_gui():
    app = ExamGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
