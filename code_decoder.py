import tkinter as tk
from tkinter import messagebox, scrolledtext

from license_codec import verify_license


class CodeDecoderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("验证码验证器")
        self.geometry("520x360")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(frame, text="待验证文本：", font=(None, 11)).grid(row=0, column=0, sticky="nw", pady=(8, 0))
        self.token_text = scrolledtext.ScrolledText(frame, width=48, height=6)
        self.token_text.grid(row=0, column=1, sticky="w", pady=(8, 0))

        self.decode_button = tk.Button(frame, text="验证", width=14, command=self.decode_token)
        self.decode_button.grid(row=1, column=1, sticky="w", pady=12)

        tk.Label(frame, text="验证结果：", font=(None, 11)).grid(row=2, column=0, sticky="nw", pady=(6, 0))
        self.result_text = scrolledtext.ScrolledText(frame, width=48, height=8, state="disabled")
        self.result_text.grid(row=2, column=1, sticky="w", pady=(6, 0))

        self.status_label = tk.Label(frame, text="请输入验证码后点击验证。", fg="gray")
        self.status_label.grid(row=3, column=1, sticky="w", pady=(8, 0))

    def decode_token(self):
        token = self.token_text.get("1.0", tk.END).strip()
        if not token:
            messagebox.showwarning("提示", "请输入待验证的文本。")
            return

        try:
            payload = verify_license(token)
            self._show_result(payload)
            self.status_label.configure(text="验证成功。", fg="green")
        except Exception as exc:
            self._show_result({})
            self.status_label.configure(text="验证失败，请检查验证码是否正确。", fg="red")
            messagebox.showerror("验证失败", str(exc))

    def _show_result(self, payload):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tk.END)
        if payload:
            for key, value in payload.items():
                self.result_text.insert(tk.END, f"{key}: {value}\n")
        self.result_text.configure(state="disabled")


if __name__ == "__main__":
    app = CodeDecoderApp()
    app.mainloop()
