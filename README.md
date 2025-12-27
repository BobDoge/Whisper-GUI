# **Whisper 本地字幕生成器 (Whisper GUI Subtitle Generator)**

这是一个基于 [OpenAI Whisper](https://github.com/openai/whisper) 模型的桌面应用程序，旨在为视频和音频文件自动生成高质量的 SRT 字幕。

本项目采用 Python 的 tkinter 库构建原生 GUI 界面，无需复杂的命令行操作，支持**批量处理**、**多语言识别**以及**实时进度显示**，完全在本地运行，保护隐私且无使用次数限制。

## **✨ 功能特性**

* **图形化界面**：简单直观的操作面板，无需编写代码。  
* **批量处理**：支持选择单个文件或整个文件夹，自动扫描并处理所有支持的媒体文件。  
* **多语言支持**：支持自动语言检测，也可以手动指定源语言（支持中文、英文、日文等多种语言）。  
* **模型选择**：提供 tiny 到 large 多种模型选择，平衡速度与精度。  
* **实时进度**：通过解析底层日志实现了精确的进度条显示。  
* **广泛格式支持**：支持 MP4, MP3, WAV, MKV, MOV, FLV, M4A, WEBM 等常见音视频格式。  
* **本地离线**：模型下载后即可离线运行，数据不上传云端。

## **🛠️ 环境要求**

在运行本程序之前，请确保您的系统满足以下要求：

1. **Python 3.8+**  
2. **FFmpeg**：Whisper 依赖 FFmpeg 进行音频提取和处理（**必须安装并配置到环境变量 PATH 中**）。  
3. **(可选) NVIDIA GPU**：虽然可以使用 CPU 运行，但强烈建议使用支持 CUDA 的 NVIDIA 显卡以获得几十倍的加速体验。

## **📦 安装指南**

### **1\. 安装 FFmpeg**

* **Windows**: 下载 FFmpeg (如 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/))，解压并将 bin 目录路径添加到系统的环境变量 PATH 中。  
* **macOS**: brew install ffmpeg  
* **Linux**: sudo apt install ffmpeg

### **2\. 安装 Python 依赖**

在项目目录下打开终端或命令提示符，运行以下命令：

\# 安装 OpenAI Whisper  
pip install openai-whisper

\# (可选) 如果 GUI 无法运行，可能需要安装 tkinter (Linux 环境)  
\# sudo apt-get install python3-tk

关于 GPU 加速:  
如果您希望使用 GPU 加速，请先根据您的 CUDA 版本安装 PyTorch，再安装 Whisper。请访问 PyTorch 官网 获取安装命令。

## **🚀 使用方法**

1. **启动程序**：  
   python whisper\_gui\_app.py

2. **选择文件**：  
   * 点击 **“选择文件”** 处理单个音视频。  
   * 点击 **“选择文件夹(批量)”** 自动处理该目录下所有支持的媒体文件。  
3. **配置选项**：  
   * **模型大小**：推荐使用 small 或 medium。large 精度最高但速度较慢且需要更多显存。  
   * **源语言**：默认为 Auto（自动检测）。如果已知视频语言（例如中文），手动选择 Chinese 通常能获得更好的效果。  
4. **开始生成**：  
   * 点击 **“开始生成字幕”**。  
   * 程序会自动加载模型（首次运行会自动下载模型文件）。  
   * 完成后，.srt 字幕文件将生成在原媒体文件的同一目录下。

## **🤖 模型说明**
|  Size  | Parameters | English-only model | Multilingual model | Required VRAM | Relative speed |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~10x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~7x       |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~4x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |
| turbo  |   809 M    |        N/A         |      `turbo`       |     ~6 GB     |      ~8x       |


*初次使用某个模型时，程序会自动从 OpenAI 服务器下载模型文件，请保持网络连接。*

## **❓ 常见问题 (FAQ)**

Q: 报错 FileNotFoundError: \[WinError 2\] The system cannot find the file specified  
A: 这通常是因为系统未找到 FFmpeg。请确认已安装 FFmpeg 并且将其 bin 文件夹路径添加到了系统的环境变量 Path 中，然后重启终端或电脑。  
Q: 进度条卡在 0% 或一直显示“正在分析音频”  
A: 程序正在使用 FFmpeg 读取音频流并计算总时长，对于长视频这可能需要几秒到几十秒。请耐心等待。  
Q: 报错 FP16 is not supported on CPU  
A: 如果没有 GPU，Whisper 会尝试使用 CPU 运行。通常库会自动处理此警告，如果程序崩溃，可能需要强制禁用 FP16（需修改源码 model.transcribe(..., fp16=False)）。

## **📝 许可证**


本项目代码基于 GNU GPL v3 许可证开源。Whisper 模型遵循 OpenAI 的开源协议。
