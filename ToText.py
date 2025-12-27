import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import re


class SrtToTxtConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("SRT 字幕转纯文本工具")
        self.root.geometry("600x450")

        # 存储选中的文件路径
        self.file_paths = []

        # --- 界面布局 ---

        # 1. 顶部按钮区
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill=tk.X)

        self.btn_add = tk.Button(top_frame, text="添加 SRT 文件", command=self.add_files, bg="#e1f5fe", width=15)
        self.btn_add.pack(side=tk.LEFT, padx=10)

        self.btn_clear = tk.Button(top_frame, text="清空列表", command=self.clear_list, width=15)
        self.btn_clear.pack(side=tk.LEFT, padx=10)

        # 2. 中间列表区
        list_frame = tk.Frame(root, padx=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_list = tk.Label(list_frame, text="待处理文件列表:")
        self.lbl_list.pack(anchor=tk.W)

        # 滚动条与列表框
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # 3. 底部操作区
        bottom_frame = tk.Frame(root, pady=15, padx=10)
        bottom_frame.pack(fill=tk.X)

        # 进度条
        self.progress = ttk.Progressbar(bottom_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        # 转换按钮
        self.btn_convert = tk.Button(bottom_frame, text="开始转换", command=self.start_conversion, bg="#4caf50",
                                     fg="white", font=("Arial", 10, "bold"), height=2)
        self.btn_convert.pack(fill=tk.X)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.lbl_status = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

    def add_files(self):
        """打开文件选择对话框"""
        files = filedialog.askopenfilenames(
            title="选择 SRT 文件",
            filetypes=[("SRT Subtitles", "*.srt"), ("All Files", "*.*")]
        )
        if files:
            for f in files:
                if f not in self.file_paths:
                    self.file_paths.append(f)
                    self.listbox.insert(tk.END, f)
            self.status_var.set(f"已添加 {len(files)} 个文件")

    def clear_list(self):
        """清空列表"""
        self.file_paths = []
        self.listbox.delete(0, tk.END)
        self.status_var.set("列表已清空")
        self.progress['value'] = 0

    def clean_srt_content(self, content):
        """
        核心逻辑：清洗 SRT 内容
        1. 去除 HTML 标签
        2. 识别并去除时间轴行 (00:00:00 --> 00:00:00)
        3. 识别并去除纯数字的索引行
        """
        lines = content.splitlines()
        cleaned_lines = []

        # 时间轴的正则匹配 (00:00:00,000 --> ...)
        time_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}')

        for i, line in enumerate(lines):
            line = line.strip()

            # 1. 跳过空行
            if not line:
                continue

            # 2. 跳过时间轴行
            if time_pattern.search(line):
                continue

            # 3. 跳过纯数字索引行
            # 逻辑：如果当前行是数字，且下一行包含 "-->"，则判定为索引行
            if line.isdigit():
                if i + 1 < len(lines) and time_pattern.search(lines[i + 1]):
                    continue

            # 4. 去除 HTML 标签 (如 <font color="..."> 或 <i>)
            line = re.sub(r'<[^>]+>', '', line)

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def start_conversion(self):
        """执行转换任务"""
        if not self.file_paths:
            messagebox.showwarning("提示", "请先添加 SRT 文件！")
            return

        total = len(self.file_paths)
        self.progress['maximum'] = total
        success_count = 0

        self.btn_convert.config(state=tk.DISABLED)  # 禁用按钮防止重复点击

        for index, srt_path in enumerate(self.file_paths):
            try:
                # 更新状态
                self.status_var.set(f"正在处理: {os.path.basename(srt_path)}...")
                self.root.update_idletasks()  # 强制刷新界面

                # 读取文件 (尝试 utf-8，失败则尝试 gbk)
                try:
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(srt_path, 'r', encoding='gbk') as f:
                        content = f.read()

                # 清洗内容
                txt_content = self.clean_srt_content(content)

                # 生成输出路径 (同目录下，后缀改为 .txt)
                txt_path = os.path.splitext(srt_path)[0] + ".txt"

                # 写入文件
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(txt_content)

                success_count += 1
                self.progress['value'] = index + 1

            except Exception as e:
                print(f"Error converting {srt_path}: {e}")

        self.btn_convert.config(state=tk.NORMAL)
        self.status_var.set("转换完成")
        messagebox.showinfo("完成", f"成功转换 {success_count}/{total} 个文件。\n文本文件已保存在原目录下。")


if __name__ == "__main__":
    root = tk.Tk()
    app = SrtToTxtConverter(root)
    root.mainloop()