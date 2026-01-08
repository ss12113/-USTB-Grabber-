# 🚀 USTB 抢课神器 (USTB Course Grabber)

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

专为北京科技大学（USTB）学子打造的跨平台抢课工具。基于 PySide6 开发，内置 Chromium 浏览器内核，支持 Windows 和 macOS 双端运行。

**主要功能：** 自动同步 Cookie、多课程类型支持（必修/素拓/专拓）、断点续传（自动保存课程数据）、高频自动请求。

## ✨ 功能特性

* **🌍 内置浏览器**：集成 QtWebEngine，直接在软件内登录教务系统，自动获取并同步 Cookie，无需手动抓包。
* **💾 数据持久化**：解析过的课程自动保存到本地 `courses_data.json`，软件关闭后数据不丢失，下次打开即用。
* **🎯 精准打击**：
    * 支持手动粘贴 `queryKxrw` 的 JSON 响应，批量导入课程。
    * **支持多种课程性质选择**：必修课 (`bx-b-b`)、素质拓展 (`sztzk-b-b`)、专业拓展 (`zytzk-b-b`)。
* **⚡ 高效抢课**：多线程循环请求，支持自定义请求间隔（毫秒级）。
* **🖥️ 跨平台**：完美支持 Windows 10/11 及 macOS (Intel/Apple Silicon)。

## 📦 如何使用 (普通用户)

### Windows 用户
1.  下载最新版本的压缩包 `USTB_Grabber_Win.zip`。
2.  解压整个文件夹（**不要**只把 exe 拖出来）。
3.  双击运行 `USTB抢课神器.exe`。
4.  **注意**：如果文件夹内包含 `courses_data.json`，则会自带预设课程；否则请自行登录添加。

### macOS 用户
1.  下载 `USTB_Grabber_Mac.zip` 并解压。
2.  双击 `选课.app` 运行。
3.  **⚠️ 常见问题**：
    * 如果提示“文件已损坏”或“无法验证开发者”：
        * 打开【系统设置】->【隐私与安全性】-> 点击【仍要打开】。
        * 或者在终端运行：`xattr -cr /Applications/选课.app` (假设你把它拖到了应用程序里)。

## 🛠️ 操作流程

1.  **登录**：在左侧浏览器窗口登录学校教务系统。
2.  **获取课程数据**：
    * 在浏览器中进入选课页面，打开开发者工具 (F12) -> Network。
    * 翻页或查询，找到 `queryKxrw` 请求。
    * 复制 Response 中的 JSON 内容，粘贴到软件右上方的输入框，点击 **“➕ 解析并保存”**。
3.  **配置抢课**：
    * 在中间列表选中你要抢的课。
    * **关键步骤**：在右侧下拉框选择正确的课程类型（如“素质拓展”）。
    * 设置请求间隔（建议 500ms - 1000ms）。
4.  **启动**：点击 **“🚀 启动循环”**，观察下方日志，抢到后软件会自动停止并弹窗提醒。

## 💻 开发与构建 (开发者)

如果你想修改代码或自行打包，请按照以下步骤操作。

### 1. 环境准备
确保安装 Python 3.8+。

```bash
# 安装依赖
pip install PySide6 requests urllib3 pyinstaller

### 2. 运行代码

```bash
python app.py

```

### 3. 打包指南

**Windows 打包 (生成 .exe):**

```bash
pyinstaller --noconsole --onedir --clean --name="USTB抢课神器" app.py

```

**macOS 打包 (生成 .app):**

```bash
pyinstaller --windowed --noconsole --onedir --clean --name="选课" app.py

```

> **注意**：打包完成后，如果想预置课程数据，请将生成的 `courses_data.json` 手动复制到 `dist/应用名/` 目录下（Mac 端需放入 `选课.app/Contents/MacOS/`）。

## ⚠️ 免责声明 (Disclaimer)

1. 本程序仅供编程学习与交流使用，**严禁用于商业用途**。
2. 请合理设置请求间隔，避免对教务系统服务器造成过大压力。
3. 使用本工具产生的任何后果（包括但不限于账号被封禁、选课失败等）由使用者自行承担。
4. 请遵守北京科技大学相关网络管理规定。

---

**Author:** Bear
**Last Update:** 2026-01

```

```
