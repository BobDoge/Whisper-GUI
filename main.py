import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import os
import datetime
import sys
import re

# 尝试导入 whisper，如果未安装则稍后在 GUI 中提示
try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class StdoutRedirector:
    """用于捕获 Whisper 的 verbose 输出并更新进度条"""

    def __init__(self, callback):
        self.callback = callback
        self.original_stdout = sys.stdout

    def write(self, text):
        # 仍然输出到控制台（可选）
        # self.original_stdout.write(text)
        # 调用回调函数解析进度
        if text.strip():
            self.callback(text)

    def flush(self):
        self.original_stdout.flush()


class SubtitleGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper 字幕生成器 (支持批量)")
        self.root.geometry("700x600")
        self.root.resizable(False, False)

        # 变量初始化
        self.file_path = tk.StringVar()
        self.model_size = tk.StringVar(value="small")
        self.language_var = tk.StringVar(value="Auto")  # 新增语言变量
        self.output_format = tk.StringVar(value="srt")
        self.status_msg = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0)  # 进度条变量
        self.progress_text = tk.StringVar(value="0%")  # 进度百分比文字
        self.is_running = False

        # 支持的媒体格式
        self.supported_exts = ('.mp4', '.mp3', '.wav', '.mkv', '.mov', '.flv', '.m4a', '.webm')

        # 创建 UI 组件
        self.create_widgets()

        # 检查依赖
        self.check_dependencies()

    def create_widgets(self):
        # 1. 文件选择区域
        file_frame = tk.LabelFrame(self.root, text="文件/文件夹选择", padx=10, pady=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        tk.Entry(file_frame, textvariable=self.file_path, width=40, state="readonly").pack(side=tk.LEFT, padx=5)
        tk.Button(file_frame, text="选择文件", command=self.select_file).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="选择文件夹(批量)", command=self.select_directory).pack(side=tk.LEFT, padx=2)

        # 2. 配置区域
        config_frame = tk.LabelFrame(self.root, text="配置选项", padx=10, pady=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # 模型选择
        tk.Label(config_frame, text="模型大小:").grid(row=0, column=0, sticky="w", padx=5)
        models = ["tiny", "base", "small", "medium", "large","turbo"]
        model_menu = ttk.Combobox(config_frame, textvariable=self.model_size, values=models, state="readonly", width=8)
        model_menu.grid(row=0, column=1, padx=5)

        # 语言选择 (新增)
        tk.Label(config_frame, text="源语言:").grid(row=0, column=2, sticky="w", padx=5)
        # 常用语言列表，Whisper 支持更多，这里列出主要的
        languages = ["Auto", "Chinese", "English", "Japanese", "Korean", "French", "German", "Spanish", "Russian",
                     "Italian", "Portuguese"]
        lang_menu = ttk.Combobox(config_frame, textvariable=self.language_var, values=languages, state="readonly",
                                 width=10)
        lang_menu.grid(row=0, column=3, padx=5)

        # 说明标签
        tk.Label(config_frame, text="(模型越大精度越高)", fg="gray").grid(row=0, column=4, sticky="w", padx=5)

        # 3. 操作区域
        action_frame = tk.Frame(self.root, padx=10, pady=10)
        action_frame.pack(fill="x", padx=10)

        self.start_btn = tk.Button(action_frame, text="开始生成字幕", command=self.start_thread, bg="#4CAF50",
                                   fg="white", font=("TkFixedFont", 12, "bold"))
        self.start_btn.pack(fill="x", pady=5)

        # 进度条区域
        progress_frame = tk.Frame(action_frame)
        progress_frame.pack(fill="x", pady=5)

        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate",
                                        variable=self.progress_var)
        self.progress.pack(side=tk.LEFT, fill="x", expand=True)

        self.percent_label = tk.Label(progress_frame, textvariable=self.progress_text, width=6)
        self.percent_label.pack(side=tk.RIGHT, padx=5)

        # 4. 日志输出区域
        log_frame = tk.LabelFrame(self.root, text="运行日志", padx=10, pady=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=12, state="disabled", font=("TkFixedFont", 9))
        self.log_area.pack(fill="both", expand=True)

        # 状态栏
        status_bar = tk.Label(self.root, textvariable=self.status_msg, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, message):
        """向日志区域添加信息"""
        self.root.after(0, self._log_impl, message)

    def _log_impl(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def check_dependencies(self):
        """检查 FFmpeg 和 Whisper 是否可用"""
        if not WHISPER_AVAILABLE:
            self.log("错误: 未检测到 'openai-whisper' 库。请参考说明安装。")
            self.start_btn.config(state="disabled")
            return

        # 简单的 FFmpeg 检查
        if os.system("ffmpeg -version >nul 2>&1") != 0 and os.system("ffmpeg -version >/dev/null 2>&1") != 0:
            self.log("警告: 未检测到系统 PATH 中的 FFmpeg。")
            self.log("请确保已安装 FFmpeg 并将其添加到环境变量中。")
        else:
            self.log("系统检查: FFmpeg 已就绪。")
            self.log("系统检查: Whisper 库已加载。")

    def select_file(self):
        filetypes = (("媒体文件", " ".join([f"*{ext}" for ext in self.supported_exts])), ("所有文件", "*.*"))
        filename = filedialog.askopenfilename(title="选择视频或音频文件", filetypes=filetypes)
        if filename:
            self.file_path.set(filename)
            self.log(f"已选择单文件: {os.path.basename(filename)}")
            self.reset_progress()

    def select_directory(self):
        directory = filedialog.askdirectory(title="选择包含媒体文件的文件夹")
        if directory:
            self.file_path.set(directory)
            self.log(f"已选择文件夹: {directory}")
            self.reset_progress()

    def reset_progress(self):
        self.progress_var.set(0)
        self.progress_text.set("0%")
        self.status_msg.set("就绪")

    def start_thread(self):
        if not self.file_path.get():
            messagebox.showwarning("提示", "请先选择一个文件或文件夹！")
            return

        if self.is_running:
            return

        self.is_running = True
        self.start_btn.config(state="disabled", text="正在处理中...")

        thread = threading.Thread(target=self.run_transcription, daemon=True)
        thread.start()

    def format_timestamp(self, seconds):
        """将秒数转换为 SRT 时间戳格式 00:00:00,000"""
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def parse_time_str(self, time_str):
        """解析 Whisper 输出的时间字符串"""
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                m, s = parts
                h = 0
            elif len(parts) == 3:
                h, m, s = parts
            else:
                return 0.0
            return int(h) * 3600 + int(m) * 60 + float(s)
        except ValueError:
            return 0.0

    def write_srt(self, segments, input_file):
        """将转录片段写入 SRT 文件"""
        base_name = os.path.splitext(input_file)[0]
        srt_filename = f"{base_name}.srt"

        with open(srt_filename, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start_time = self.format_timestamp(segment['start'])
                end_time = self.format_timestamp(segment['end'])
                text = segment['text'].strip()

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

        return srt_filename

    def progress_parser(self, text, total_duration):
        """解析控制台输出并更新进度条"""
        match = re.search(r"\[([0-9:.]+) --> ([0-9:.]+)\]", text)
        if match and total_duration > 0:
            end_time_str = match.group(2)
            current_seconds = self.parse_time_str(end_time_str)
            progress = (current_seconds / total_duration) * 100
            progress = min(progress, 99.9)

            self.root.after(0, self.update_progress_ui, progress)

    def update_progress_ui(self, value):
        self.progress_var.set(value)
        self.progress_text.set(f"{value:.1f}%")

    def process_one_file(self, model, input_file, index, total_files):
        """处理单个文件的核心逻辑"""
        filename = os.path.basename(input_file)
        self.log(f"[{index}/{total_files}] 正在加载音频: {filename}")

        # UI 更新：重置进度条
        self.root.after(0, lambda: self.status_msg.set(f"[{index}/{total_files}] 正在分析音频: {filename}..."))
        self.root.after(0, lambda: self.progress_var.set(0))
        self.root.after(0, lambda: self.progress_text.set("0%"))

        # 确定语言参数
        selected_lang = self.language_var.get()
        language = None if selected_lang == "Auto" else selected_lang

        # 加载音频获取时长
        audio = whisper.load_audio(input_file)
        total_duration = len(audio) / whisper.audio.SAMPLE_RATE

        lang_msg = f"语言: {selected_lang}" if selected_lang != "Auto" else "语言: 自动检测"
        self.log(f"[{index}/{total_files}] 开始转录 ({lang_msg}, 时长: {total_duration:.1f}s)...")
        self.root.after(0, lambda: self.status_msg.set(f"[{index}/{total_files}] 正在转录: {filename}"))

        # 准备重定向
        original_stdout = sys.stdout
        redirector = StdoutRedirector(lambda text: self.progress_parser(text, total_duration))
        sys.stdout = redirector

        try:
            # 执行转录，传入 language 参数
            result = model.transcribe(audio, verbose=True, language=language)
        finally:
            # 恢复标准输出
            sys.stdout = original_stdout

        # 生成字幕
        srt_path = self.write_srt(result['segments'], input_file)
        self.log(f"[{index}/{total_files}] 完成! 字幕已保存至: {os.path.basename(srt_path)}")
        return srt_path

    def run_transcription(self):
        path = self.file_path.get()
        model_name = self.model_size.get()

        # 1. 确定要处理的文件列表
        files_to_process = []
        if os.path.isdir(path):
            self.log(f"扫描目录: {path} ...")
            try:
                for f in os.listdir(path):
                    full_path = os.path.join(path, f)
                    if os.path.isfile(full_path) and f.lower().endswith(self.supported_exts):
                        files_to_process.append(full_path)
            except Exception as e:
                self.log(f"扫描目录出错: {e}")
                self.reset_ui()
                return
        elif os.path.isfile(path):
            files_to_process.append(path)

        if not files_to_process:
            self.log("错误: 未找到支持的媒体文件！")
            messagebox.showwarning("提示", "未找到支持的媒体文件 (.mp4, .mp3, .wav 等)")
            self.reset_ui()
            return

        total_files = len(files_to_process)
        self.log(f"共找到 {total_files} 个文件待处理，正在加载模型 '{model_name}'...")
        self.status_msg.set("正在加载模型 (可能需要一些时间)...")

        # 切换进度条到不确定模式（加载模型期间）
        self.root.after(0, lambda: self.progress.config(mode="indeterminate"))
        self.root.after(0, lambda: self.progress.start(10))

        try:
            # 2. 加载模型 (只需加载一次)
            model = whisper.load_model(model_name)

            # 切换回确定模式准备处理文件
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.config(mode="determinate", maximum=100))

            success_count = 0

            # 3. 循环处理
            for idx, file_path in enumerate(files_to_process, 1):
                try:
                    self.process_one_file(model, file_path, idx, total_files)
                    success_count += 1
                except Exception as e:
                    self.log(f"错误: 处理文件 {os.path.basename(file_path)} 失败 - {str(e)}")

            self.log("---------------")
            self.log(f"所有任务结束。成功: {success_count} / {total_files}")

            # 只有在全部成功且文件数>0时才弹窗，避免打断
            self.root.after(0, lambda: messagebox.showinfo("完成",
                                                           f"批量处理完成！\n成功: {success_count}\n总数: {total_files}"))

        except Exception as e:
            self.log(f"严重错误: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"程序发生错误:\n{str(e)}"))
        finally:
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.is_running = False
        self.start_btn.config(state="normal", text="开始生成字幕")
        self.status_msg.set("就绪")
        self.progress.stop()
        self.progress.config(mode="determinate")
        self.progress_var.set(100)
        self.progress_text.set("完成")


if __name__ == "__main__":
    root = tk.Tk()
    app = SubtitleGeneratorApp(root)
    root.mainloop()