# AutoLaTeX Web UI 使用指南

## 📋 目录
1. [环境准备](#环境准备)
2. [快速启动](#快速启动)
3. [功能说明](#功能说明)
4. [常见问题](#常见问题)
5. [API 接口](#api-接口)

---

## 环境准备

### 1. Python 环境要求
- Python >= 3.10 且 < 3.14
- 推荐使用 conda 或 venv 创建虚拟环境

### 2. 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或者使用 uv（如果已安装）
uv pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件（如果不存在），添加以下内容：

```env
MODEL=openai/deepseek-chat
OPENAI_API_KEY=你的API密钥
OPENAI_API_BASE=https://api.deepseek.com
```

**重要**：请将 `你的API密钥` 替换为实际的 DeepSeek API Key。

---

## 快速启动

### 方式一：一键启动（推荐）

使用 `start_services.py` 脚本同时启动后端和前端：

```bash
python start_services.py
```

**说明**：
- 脚本会自动启动 FastAPI 后端（端口 8000）
- 然后启动 Gradio Web UI（端口 7860）
- 两个服务会在后台同时运行

### 方式二：分别启动

如果需要分别启动服务：

#### 启动 FastAPI 后端

```bash
python run_api.py
```

后端服务地址：`http://localhost:8000`

#### 启动 Gradio Web UI

在另一个终端窗口运行：

```bash
python run_ui.py
```

Web UI 地址：`http://localhost:7860`

---

## 功能说明

### Web UI 主要功能

#### 1. 知识库搜索
- **功能**：搜索 LaTeX 模板信息
- **使用方法**：
  1. 在搜索框中输入期刊/模板名称（如 "BIThesis-Undergraduate", "NeurIPS", "IEEE" 等）
  2. 点击"搜索"按钮
  3. 查看返回的模板信息，包括：
     - 文档类（documentclass）
     - 关键宏包列表
     - 编译方式
     - 模板结构说明

#### 2. 论文转换
- **功能**：将 Word/Markdown/TXT 格式的论文转换为 LaTeX 格式
- **使用方法**：
  1. 上传论文文件（支持 .docx, .md, .txt 格式）
  2. 选择目标模板类型（如 "BIThesis-Graduate", "BIThesis-Undergraduate" 等）
  3. 点击"开始转换"按钮
  4. 等待处理完成，下载生成的 LaTeX 文件

#### 3. 使用说明
- 查看项目使用文档和 API 说明

---

## 访问地址

启动成功后，在浏览器中访问：

- **Web UI**: http://localhost:7860
- **API 文档**: http://localhost:8000/docs（Swagger UI）
- **API 健康检查**: http://localhost:8000/api/v1/health

---

## 常见问题

### 1. 端口被占用

**错误信息**：
```
Address already in use
```

**解决方法**：
- 关闭占用端口的程序
- 或修改 `run_api.py` 和 `run_ui.py` 中的端口号

### 2. 模块导入错误

**错误信息**：
```
ModuleNotFoundError: No module named 'xxx'
```

**解决方法**：
```bash
# 重新安装依赖
pip install -r requirements.txt
```

### 3. API Key 未配置

**错误信息**：
```
API key not found
```

**解决方法**：
- 检查 `.env` 文件是否存在
- 确认 `OPENAI_API_KEY` 已正确配置

### 4. 向量数据库初始化失败

**错误信息**：
```
知识库初始化失败
```

**解决方法**：
```bash
# 重新初始化数据库
python reinitialize_database.py
```

### 5. 服务启动后无法访问

**检查步骤**：
1. 确认服务已成功启动（查看终端输出）
2. 检查防火墙设置
3. 尝试访问 `http://127.0.0.1:7860` 而不是 `localhost`

---

## API 接口

### 主要 API 端点

#### 1. 健康检查
```
GET /api/v1/health
```

#### 2. 知识库搜索
```
POST /api/v1/knowledge/search
Content-Type: application/json

{
  "journal_name": "BIThesis-Undergraduate",
  "n_results": 3
}
```

#### 3. 获取所有可用模板
```
GET /api/v1/knowledge/journals
```

#### 4. 论文转换
```
POST /api/v1/paper/convert
Content-Type: multipart/form-data

file: <上传的文件>
template_type: "BIThesis-Graduate"
```

详细的 API 文档请访问：http://localhost:8000/docs

---

## 项目结构

```
AutoLatex/
├── start_services.py      # 一键启动脚本
├── run_api.py            # API 后端启动脚本
├── run_ui.py             # Web UI 启动脚本
├── .env                  # 环境变量配置
├── requirements.txt      # Python 依赖
├── src/
│   └── autolatex/
│       ├── api/
│       │   └── main.py   # FastAPI 后端
│       └── web_ui.py     # Gradio Web UI
└── data/
    └── vector_db/        # 向量数据库存储
```

---

## 停止服务

在运行服务的终端窗口中按 `Ctrl + C` 即可停止服务。

---

## 技术支持

如遇到问题，请：
1. 查看终端输出的错误信息
2. 检查 `output_log.txt` 日志文件
3. 联系项目维护者

---

## 更新日志

- **最新版本**：支持 BIThesis 研究生和本科生模板
- **向量数据库**：已包含 24 个模板信息
- **搜索功能**：支持精确匹配和语义搜索

---

**最后更新**：2024年

