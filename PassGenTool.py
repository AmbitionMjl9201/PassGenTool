import customtkinter as ctk
from tkinter import messagebox, filedialog
import random
import string
import math
import json
import os
import re
from datetime import datetime

try:
    from zxcvbn import zxcvbn as zxcvbn_func
    ZXCVBN_AVAILABLE = True
except ImportError:
    ZXCVBN_AVAILABLE = False

HISTORY_FILE = "password_history.json"


class PasswordGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("随机密码生成器")
        self.geometry("700x700")
        self.minsize(600, 600)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.history = []
        self.load_history()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        title_label = ctk.CTkLabel(main_frame, text="随机密码生成器",
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(10, 20))

        settings_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        settings_frame.pack(padx=20, pady=(0, 10), fill="x")

        length_label = ctk.CTkLabel(settings_frame, text="密码长度：", font=ctk.CTkFont(size=14))
        length_label.grid(row=0, column=0, padx=(20, 10), pady=15, sticky="w")

        self.length_var = ctk.IntVar(value=16)
        self.length_slider = ctk.CTkSlider(settings_frame, from_=4, to=128,
                                           number_of_steps=124, variable=self.length_var,
                                           command=self.update_length_entry)
        self.length_slider.grid(row=0, column=1, padx=10, pady=15, sticky="ew")

        self.length_entry = ctk.CTkEntry(settings_frame, width=60, textvariable=self.length_var,
                                         justify="center")
        self.length_entry.grid(row=0, column=2, padx=(10, 20), pady=15)
        self.length_entry.bind("<Return>", self.update_length_slider)
        self.length_entry.bind("<FocusOut>", self.update_length_slider)

        settings_frame.columnconfigure(1, weight=1)

        options_frame = ctk.CTkFrame(settings_frame, corner_radius=8, fg_color="transparent")
        options_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 15), sticky="ew")

        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        chk_width = 180  

        self.upper_var = ctk.BooleanVar(value=True)
        self.lower_var = ctk.BooleanVar(value=True)
        self.digit_var = ctk.BooleanVar(value=True)
        self.special_var = ctk.BooleanVar(value=False)

        self.upper_check = ctk.CTkCheckBox(options_frame, text="大写字母 (A-Z)",
                                           variable=self.upper_var, width=chk_width)
        self.upper_check.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.lower_check = ctk.CTkCheckBox(options_frame, text="小写字母 (a-z)",
                                           variable=self.lower_var, width=chk_width)
        self.lower_check.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        self.digit_check = ctk.CTkCheckBox(options_frame, text="数字 (0-9)",
                                           variable=self.digit_var, width=chk_width)
        self.digit_check.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.special_check = ctk.CTkCheckBox(options_frame, text="特殊符号 (!@#...)",
                                             variable=self.special_var, width=chk_width)
        self.special_check.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        generate_btn = ctk.CTkButton(settings_frame, text="生成密码", command=self.generate_password,
                                     font=ctk.CTkFont(size=14, weight="bold"), height=36)
        generate_btn.grid(row=2, column=0, columnspan=3, pady=(5, 15))

        result_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        result_frame.pack(padx=20, pady=(0, 10), fill="x")

        result_label = ctk.CTkLabel(result_frame, text="生成的密码：", font=ctk.CTkFont(size=13))
        result_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")

        self.password_var = ctk.StringVar()
        password_entry = ctk.CTkEntry(result_frame, textvariable=self.password_var,
                                      font=ctk.CTkFont(size=16), state="readonly")
        password_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        copy_btn = ctk.CTkButton(result_frame, text="复制", width=60, command=self.copy_password)
        copy_btn.grid(row=0, column=2, padx=(10, 20), pady=10)

        result_frame.columnconfigure(1, weight=1)

        self.entropy_label_theory = ctk.CTkLabel(result_frame, text="理论熵：-- 比特", font=ctk.CTkFont(size=13))
        self.entropy_label_theory.grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 2), sticky="w")

        self.entropy_label_real = ctk.CTkLabel(result_frame, text="实际强度：-- 比特", font=ctk.CTkFont(size=13))
        self.entropy_label_real.grid(row=2, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="w")

        history_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        history_frame.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        history_label = ctk.CTkLabel(history_frame, text="历史记录：", font=ctk.CTkFont(size=14, weight="bold"))
        history_label.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        self.history_textbox = ctk.CTkTextbox(history_frame, height=150, corner_radius=6,
                                              font=ctk.CTkFont(size=13), activate_scrollbars=True)
        self.history_textbox.grid(row=1, column=0, columnspan=4, padx=20, pady=(0, 5), sticky="nsew")
        self.history_textbox.configure(state="disabled")

        btn_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=4, padx=20, pady=(5, 10), sticky="ew")

        copy_hist_btn = ctk.CTkButton(btn_frame, text="复制选中", width=90, command=self.copy_selected_history)
        copy_hist_btn.grid(row=0, column=0, padx=5, pady=5)

        delete_btn = ctk.CTkButton(btn_frame, text="删除选中", width=90, command=self.delete_selected_history)
        delete_btn.grid(row=0, column=1, padx=5, pady=5)

        clear_btn = ctk.CTkButton(btn_frame, text="清空历史", width=90, command=self.clear_history)
        clear_btn.grid(row=0, column=2, padx=5, pady=5)

        export_btn = ctk.CTkButton(btn_frame, text="导出", width=60, command=self.export_history)
        export_btn.grid(row=0, column=3, padx=5, pady=5)

        import_btn = ctk.CTkButton(btn_frame, text="导入", width=60, command=self.import_history)
        import_btn.grid(row=0, column=4, padx=5, pady=5)

        history_frame.rowconfigure(1, weight=1)
        history_frame.columnconfigure(3, weight=1)

        self.refresh_history_display()

    def update_length_entry(self, value):
        self.length_var.set(round(float(value)))

    def update_length_slider(self, event=None):
        try:
            val = int(self.length_var.get())
            val = max(4, min(128, val))
            self.length_var.set(val)
            self.length_slider.set(val)
        except ValueError:
            self.length_var.set(16)
            self.length_slider.set(16)

    def get_char_pool(self):
        pool = ""
        if self.upper_var.get():
            pool += string.ascii_uppercase
        if self.lower_var.get():
            pool += string.ascii_lowercase
        if self.digit_var.get():
            pool += string.digits
        if self.special_var.get():
            pool += "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
        return pool

    def calculate_entropy_theory(self, length, pool):
        if not pool or length <= 0:
            return 0.0
        return length * math.log2(len(pool))

    def estimate_entropy_real(self, password):
        """使用 zxcvbn 估算实际强度（bits），出错或不可用时返回 None"""
        if not ZXCVBN_AVAILABLE:
            return None
        try:
            result = zxcvbn_func(password)
            bits = result['guesses_log10'] / math.log10(2)
            return round(bits, 2)
        except Exception:
            return None

    def generate_password(self):
        pool = self.get_char_pool()
        if not pool:
            messagebox.showwarning("警告", "请至少选择一种字符类型！")
            return

        length = self.length_var.get()
        password = ''.join(random.choices(pool, k=length))

        entropy_theory = self.calculate_entropy_theory(length, pool)
        entropy_real = self.estimate_entropy_real(password)

        self.password_var.set(password)
        theory_text = f"理论熵：约 {entropy_theory:.2f} 比特 ({self.get_strength_label(entropy_theory)})"
        self.entropy_label_theory.configure(text=theory_text)

        if entropy_real is not None:
            real_text = f"实际强度：约 {entropy_real:.2f} 比特 ({self.get_strength_label(entropy_real)})"
        else:
            real_text = "实际强度：无法估算"
        self.entropy_label_real.configure(text=real_text)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history.append({
            "password": password,
            "entropy": round(entropy_theory, 2),
            "entropy_real": entropy_real if entropy_real is not None else None,
            "timestamp": timestamp
        })
        self.refresh_history_display()
        self.save_history()

    def get_strength_label(self, entropy):
        if entropy < 40:
            return "弱"
        elif entropy < 60:
            return "一般"
        elif entropy < 80:
            return "强"
        else:
            return "非常强"

    def copy_password(self):
        pwd = self.password_var.get()
        if pwd:
            self.clipboard_clear()
            self.clipboard_append(pwd)
            self.update()
            messagebox.showinfo("已复制", "密码已复制到剪贴板。")

    def copy_selected_history(self):
        idx = self.get_selected_history_index()
        if idx is not None and 0 <= idx < len(self.history):
            pwd = self.history[idx]["password"]
            self.clipboard_clear()
            self.clipboard_append(pwd)
            self.update()
            messagebox.showinfo("已复制", f"密码已复制：{pwd[:20]}...")
        else:
            messagebox.showwarning("未选择", "请先点击历史记录中的条目。")

    def refresh_history_display(self):
        self.history_textbox.configure(state="normal")
        self.history_textbox.delete("1.0", "end")
        for i, entry in enumerate(self.history):
            real_info = ""
            if entry.get("entropy_real") is not None:
                real_info = f", 实际: 约 {entry['entropy_real']} 比特"
            line = f"{i+1}. [{entry['timestamp']}] {entry['password']}  (理论熵: 约 {entry['entropy']} 比特{real_info})\n"
            self.history_textbox.insert("end", line)
        self.history_textbox.configure(state="disabled")
        self.history_textbox.see("end")

    def get_selected_history_index(self):
        try:
            sel = self.history_textbox.get("insert linestart", "insert lineend")
            dot_pos = sel.find(".")
            if dot_pos != -1:
                return int(sel[:dot_pos]) - 1
        except (ValueError, IndexError):
            pass
        return None

    def delete_selected_history(self):
        idx = self.get_selected_history_index()
        if idx is not None and 0 <= idx < len(self.history):
            del self.history[idx]
            self.refresh_history_display()
            self.save_history()
        else:
            messagebox.showwarning("未选择", "请先点击要删除的条目。")

    def clear_history(self):
        if messagebox.askyesno("确认清空", "确定要清空所有历史记录吗？"):
            self.history.clear()
            self.refresh_history_display()
            self.save_history()

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存失败: {e}")

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []

    def export_history(self):
        if not self.history:
            messagebox.showwarning("无数据", "没有历史记录可导出。")
            return

        filetypes = [
            ("文本文件", "*.txt"),
            ("JSON 文件", "*.json"),
        ]
        filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=filetypes,
                                                title="导出历史记录")
        if not filepath:
            return

        try:
            if filepath.endswith(".json"):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.history, f, indent=2, ensure_ascii=False)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    for entry in self.history:
                        real_info = ""
                        if entry.get("entropy_real") is not None:
                            real_info = f", 实际: 约 {entry['entropy_real']} 比特"
                        f.write(f"[{entry['timestamp']}] {entry['password']} (理论熵: 约 {entry['entropy']} 比特{real_info})\n")
            messagebox.showinfo("导出成功", f"历史记录已保存到：{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def import_history(self):
        filetypes = [
            ("文本文件", "*.txt"),
            ("JSON 文件", "*.json"),
            ("所有文件", "*.*")
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes,
                                              title="导入历史记录")
        if not filepath:
            return

        try:
            if filepath.endswith(".json"):
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("JSON 格式应为数组。")
                    for item in data:
                        if "password" not in item:
                            raise ValueError("缺少 password 字段。")
                    self.history.extend(data)
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        match = re.match(r'^\[(.+?)\]\s+(.+?)\s+\(.*?熵[：:]\s*约?\s*([\d.]+)\s*比特', line)
                        if match:
                            timestamp = match.group(1)
                            password = match.group(2)
                            entropy_theory = float(match.group(3))
                            entropy_real = None
                            real_match = re.search(r'实际[：:]\s*约?\s*([\d.]+)\s*比特', line)
                            if real_match:
                                entropy_real = float(real_match.group(1))
                            self.history.append({
                                "password": password,
                                "entropy": entropy_theory,
                                "entropy_real": entropy_real,
                                "timestamp": timestamp
                            })
                        else:
                            self.history.append({
                                "password": line,
                                "entropy": round(self.calculate_entropy_theory(len(line), string.printable), 2),
                                "entropy_real": None,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
            self.refresh_history_display()
            self.save_history()
            messagebox.showinfo("导入成功", f"已从 {filepath} 导入历史记录。")
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def on_closing(self):
        self.save_history()
        self.destroy()


if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()