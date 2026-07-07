import tkinter as tk
from tkinter import messagebox

from license_codec import create_license, validate_date


ADMIN_PASSWORD = "adm123xyz789"


class CodeGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("验证码生成器")
        self.geometry("520x360")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(frame, text="管理员密码：", font=(None, 11)).grid(row=0, column=0, sticky="w")
        self.password_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.password_var, show="*", width=32).grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(frame, text="日期（YYYYMMDD）：", font=(None, 11)).grid(row=1, column=0, sticky="w")
        self.date_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.date_var, width=32).grid(row=1, column=1, sticky="w", pady=4)

        self.generate_button = tk.Button(frame, text="生成验证码", width=14, command=self.generate_code)
        self.generate_button.grid(row=2, column=1, sticky="w", pady=16)

        self.status_label = tk.Label(frame, text="请输入密码和日期后生成。", fg="gray")
        self.status_label.grid(row=3, column=1, sticky="w")

        tk.Label(frame, text="生成的码：", font=(None, 11)).grid(row=4, column=0, sticky="nw", pady=(12, 0))
        self.code_var = tk.StringVar(value="------")
        self.code_entry = tk.Entry(frame, textvariable=self.code_var, font=(None, 14, "bold"), fg="#1a73e8", justify="center", state="readonly", readonlybackground="#f0f0f0", width=34)
        self.code_entry.grid(row=4, column=1, sticky="w", pady=(12, 0))

    def generate_code(self):
        password = self.password_var.get().strip()
        if password != ADMIN_PASSWORD:
            messagebox.showerror("错误", "管理员密码错误。")
            self.status_label.configure(text="密码错误，请重新输入。", fg="red")
            return

        date_str = self.date_var.get().strip()
        if not validate_date(date_str):
            messagebox.showerror("错误", "日期格式应为 YYYYMMDD。")
            self.status_label.configure(text="日期格式无效。", fg="red")
            return

        try:
            code = create_license(date_str)
            self.code_var.set(code)
            self.status_label.configure(text="验证码已生成，可复制使用。", fg="green")
        except Exception as exc:
            messagebox.showerror("生成失败", str(exc))
            self.status_label.configure(text="生成失败，请检查输入。", fg="red")


if __name__ == "__main__":
    app = CodeGeneratorApp()
    app.mainloop()
