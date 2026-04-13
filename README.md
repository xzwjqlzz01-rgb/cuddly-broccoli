# \# 📚 AI 阅读教练 · 第一性原理视角分析

# 

# 基于 FastAPI + LlamaIndex + 智谱 AI 的智能阅读工具，上传 PDF 即可获得结构化分析报告（元问题、概念还原、极致批判、实践指导、内化计划），并支持连续多轮对话追问，并支持苏格拉底式辩论与联网搜索。

# 

# \## 功能亮点

# \- 📄 支持文字版和扫描版 PDF（OCR）

# \- 🔍 洞察：元问题、概念还原、三大核心结论

# \- ⚡ 批判：未说出的假设、逻辑张力、被忽略的视角、反常识质疑

# \- 🚀 实践：情境迁移、24小时最小实验（强相关书中道理）、极端压力指令

# \- 🧠 内化：21天复习计划、模型类比、费曼解释

# \- 💬 双模式对话：
  - 普通模式：基于报告+原文回答，支持联网搜索
  - 辩论模式：苏格拉底式质疑，与你进行思想交锋

# 

# \## 技术栈

| 后端框架 | FastAPI + Uvicorn |
| AI 框架 | LlamaIndex |
| 大模型 | 智谱 AI (glm-4-flash + embedding-2) |
| 前端 | Streamlit |
| OCR | Tesseract + pdf2image + Poppler |
| 搜索 | DuckDuckGo Search (ddgs) |

# 

# \## 快速开始

# \## 环境变量配置（必读）

# 

# 本项目使用智谱AI的API，需要先获取免费的 API Key。

# 

# 1\. 访问 \[智谱AI开放平台](https://bigmodel.cn) 注册账号。

# 2\. 登录后进入 \[控制台 → API Keys](https://bigmodel.cn/usercenter/proj-mgmt/apikeys)，点击“创建新密钥”，复制生成的 Key（格式类似 `xxxxxx.xxxxxxxx`）。

# 3\. 在运行后端之前，设置环境变量：

# 

# &#x20;  \*\*Windows (PowerShell):\*\*

# &#x20;  ```powershell

# &#x20;  $env:ZHIPUAI\_API\_KEY="你的API Key"

# \# 克隆仓库

# git clone https://github.com/xzwjqlzz01-rgb/cuddly-broccoli.git

# cd cuddly-broccoli

# 

# \# 创建虚拟环境并安装依赖

# python -m venv venv

# source venv/bin/activate  # Linux/Mac

# \# 或 .\\venv\\Scripts\\activate (Windows)

# pip install -r requirements.txt

# 

# \# 设置智谱 API Key

# export ZHIPUAI\_API\_KEY="your\_key"  # Linux/Mac

# \# 或 $env:ZHIPUAI\_API\_KEY="your\_key" (Windows)

# 

# \# 启动后端

# uvicorn main:app --reload --port 8000

# 

# \# 新开终端，启动前端

# streamlit run app.py

