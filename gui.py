import asyncio
import os
import socket
import threading
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import messagebox, scrolledtext

from exam_helper import main as run_exam_helper
from license_codec import create_machine_binding, verify_license as verify_license_code, verify_machine_binding


class ExamGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Exam Helper")
        self.geometry("700x420")
        self.resizable(False, False)

        self.url_var = tk.StringVar(value="")
        self.verify_code_var = tk.StringVar(value="")
        self.validation_status_var = tk.StringVar(value="请先完成验证。")
        self._thread = None
        self._is_validated = False

        self._build_ui()
        self._restore_validation_state()

    def _build_ui(self):
        tk.Label(self, text="验证码:").pack(anchor="w", padx=12, pady=(12, 4))
        tk.Entry(self, textvariable=self.verify_code_var, width=90).pack(fill="x", padx=12, pady=4)

        verify_btn_frame = tk.Frame(self)
        verify_btn_frame.pack(fill="x", padx=12, pady=8)
        self.verify_button = tk.Button(verify_btn_frame, text="验证", width=12, command=self.verify_license)
        self.verify_button.pack(side="left")
        tk.Button(verify_btn_frame, text="删除验证", width=12, command=self.delete_binding).pack(side="left", padx=(8, 0))
        tk.Label(verify_btn_frame, textvariable=self.validation_status_var, fg="blue").pack(side="left", padx=(12, 0))

        tk.Label(self, text="考试 URL:").pack(anchor="w", padx=12, pady=(8, 4))
        tk.Entry(self, textvariable=self.url_var, width=90).pack(fill="x", padx=12, pady=4)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=12, pady=8)
        self.start_button = tk.Button(btn_frame, text="开始", width=12, command=self.start_run, state="disabled")
        self.start_button.pack(side="left")
        tk.Button(btn_frame, text="退出", width=12, command=self.destroy).pack(side="left", padx=(8, 0))

        tk.Label(self, text="日志:").pack(anchor="w", padx=12, pady=(8, 4))
        self.log_box = scrolledtext.ScrolledText(self, height=14, width=90, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=8)

    def _get_machine_id(self) -> str:
        return f"{socket.gethostname()}::{uuid.getnode()}"

    def _get_binding_path(self) -> Path:
        base = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        target = base / "ExamHelper"
        target.mkdir(parents=True, exist_ok=True)
        return target / "validation.bind"

    def _save_binding(self, token: str):
        self._get_binding_path().write_text(token, encoding="utf-8")

    def _load_binding(self) -> str:
        path = self._get_binding_path()
        if not path.exists():
            raise FileNotFoundError("未找到验证记录")
        return path.read_text(encoding="utf-8")

    def _update_validation_state(self, message: str, validated: bool):
        self.validation_status_var.set(message)
        self._is_validated = validated
        self.start_button.configure(state="normal" if validated else "disabled")

    def _restore_validation_state(self):
        try:
            binding_token = self._load_binding()
            payload = verify_machine_binding(binding_token, self._get_machine_id())
            code = payload.get("code", "")
            if code:
                self.verify_code_var.set(code)
                self._update_validation_state("验证完毕", True)
                self.append_log("已恢复上次验证状态。")
                return
        except Exception:
            pass
        self._update_validation_state("请先完成验证。", False)

    def delete_binding(self):
        path = self._get_binding_path()
        if not path.exists():
            messagebox.showinfo("提示", "未找到验证记录。")
            self._update_validation_state("请先完成验证。", False)
            return

        if not messagebox.askyesno("确认", "确定要删除本机的验证记录吗？"):
            return

        try:
            path.unlink()
            self.verify_code_var.set("")
            self._update_validation_state("请先完成验证。", False)
            self.append_log("已删除验证记录。")
            messagebox.showinfo("已删除", "验证记录已删除，状态已设为未验证。")
        except Exception as exc:
            messagebox.showerror("删除失败", str(exc))

    def verify_license(self):
        code = self.verify_code_var.get().strip()
        if not code:
            messagebox.showerror("错误", "请输入验证码")
            return

        try:
            verify_license_code(code)
            binding_token = create_machine_binding(self._get_machine_id(), code)
            self._save_binding(binding_token)
            self._update_validation_state("验证完毕", True)
            self.append_log("验证成功，已绑定当前机器。")
        except Exception as exc:
            self._update_validation_state("验证失败", False)
            self.append_log(f"验证失败: {exc}")
            messagebox.showerror("验证失败", str(exc))

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

        if not self._is_validated:
            try:
                self._restore_validation_state()
            except Exception:
                pass
            if not self._is_validated:
                messagebox.showerror("未验证", "请先点击验证按钮完成机器绑定验证。")
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
