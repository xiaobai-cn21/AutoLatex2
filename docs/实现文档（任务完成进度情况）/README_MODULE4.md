# 模块四：记忆与交互层 - 实现文档

## 概述

本模块实现了 AutoLaTeX 系统的记忆与交互层，包括：
1. 向量数据库部署和知识库搜索功能
2. FastAPI 后端服务
3. Gradio Web UI 界面
4. API 通信协议定义

## 实现内容

### 1. 向量数据库实现

**文件位置**:
- `src/autolatex/tools/vector_db.py` - 向量数据库管理类
- `src/autolatex/tools/knowledge_base.py` - 知识库初始化和搜索功能

**技术栈**:
- **ChromaDB**: 轻量级向量数据库，支持持久化存储
- **嵌入模型**: ChromaDB 内置的默认嵌入模型（可扩展为自定义模型）

**功能特性**:
- 自动初始化知识库数据（8个常见期刊/会议的模板信息）
- 支持余弦相似度搜索
- 持久化存储，数据保存在 `data/vector_db/` 目录

**支持的期刊/会议**:
- NeurIPS, CVPR, ICML, ICLR, AAAI (会议)
- IEEE, ACM, Nature (期刊)

### 2. KnowledgeBaseSearchTool 实现

**文件位置**: `src/autolatex/tools/knowledge_tools.py`

**接口定义** (由 A 同学定义):
```python
class KnowledgeBaseSearchTool(BaseTool):
    name: str = "LaTeX Template Knowledge Base Search"
    description: str = "根据期刊名称，从向量数据库中搜索最相关的 LaTeX 模板信息和排版建议。"
    
    def _run(self, journal_name: str) -> str:
        # 实现向量数据库搜索
```

**实现功能**:
- 接收期刊名称作为输入
- 在向量数据库中执行相似性搜索
- 返回格式化的搜索结果，包含：
  - 模板类型和文档类
  - 关键宏包列表
  - 详细的排版建议

### 3. FastAPI 后端服务

**文件位置**: `src/autolatex/api/main.py`

**API 端点**:

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 获取 API 基本信息 |
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/knowledge/search` | POST | 知识库搜索 |
| `/api/v1/paper/convert` | POST | 论文转换 |
| `/api/v1/paper/upload` | POST | 文件上传 |

**启动方式**:
```bash
python run_api.py
# 或
uvicorn autolatex.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**服务地址**: `http://localhost:8000`

### 4. Gradio Web UI

**文件位置**: `src/autolatex/web_ui.py`

**功能模块**:
1. **知识库搜索标签页**
   - 输入期刊名称
   - 显示搜索结果和相似度
   - 实时状态反馈

2. **论文转换标签页**
   - 文件上传功能
   - 期刊选择
   - 转换进度和结果展示

3. **使用说明标签页**
   - 详细的使用指南
   - API 端点说明
   - 注意事项

**启动方式**:
```bash
python run_ui.py
```

**访问地址**: `http://localhost:7860`

### 5. API 通信协议

**文档位置**: `docs/API_PROTOCOL.md`

**协议特点**:
- RESTful API 设计
- JSON 数据格式
- 统一的响应格式
- 完整的错误处理
- CORS 支持

**请求/响应示例**:
详见 `docs/API_PROTOCOL.md`

## 项目结构

```
AutoLatex-original/
├── src/
│   └── autolatex/
│       ├── api/
│       │   ├── __init__.py
│       │   └── main.py              # FastAPI 后端
│       ├── tools/
│       │   ├── vector_db.py         # 向量数据库
│       │   ├── knowledge_base.py    # 知识库管理
│       │   └── knowledge_tools.py   # 工具接口实现
│       ├── crew.py                  # 已更新：模板研究 Agent 使用知识库工具
│       └── web_ui.py                # Gradio Web UI
├── docs/
│   └── API_PROTOCOL.md              # API 协议文档
├── run_api.py                       # API 启动脚本
├── run_ui.py                        # UI 启动脚本
└── requirements.txt                 # 已更新依赖
```

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 FastAPI 后端

```bash
python run_api.py
```

后端服务将在 `http://localhost:8000` 启动。

### 3. 启动 Gradio Web UI

```bash
python run_ui.py
```

Web UI 将在 `http://localhost:7860` 启动。

### 4. 验证功能

1. 访问 Web UI: `http://localhost:7860`
2. 在"知识库搜索"标签页测试搜索功能
3. 在"论文转换"标签页测试文件上传和转换功能

## 测试 API

### 使用 curl

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 搜索知识库
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"journal_name": "NeurIPS"}'
```

### 使用 Python

```python
import requests

# 搜索知识库
response = requests.post(
    "http://localhost:8000/api/v1/knowledge/search",
    json={"journal_name": "CVPR"}
)
print(response.json())
```

## 与 A 同学的接口对接

### 已实现的接口

✅ **KnowledgeBaseSearchTool**
- 位置: `src/autolatex/tools/knowledge_tools.py`
- 接口: `_run(self, journal_name: str) -> str`
- 功能: 完整的向量数据库搜索实现

### 集成到 Crew

✅ **模板研究 Agent 已更新**
- 位置: `src/autolatex/crew.py`
- 变更: `template_researcher_agent` 现在使用 `KnowledgeBaseSearchTool()`

## 技术细节

### 向量数据库

- **存储**: ChromaDB 持久化存储
- **相似度算法**: 余弦相似度
- **嵌入模型**: ChromaDB 默认模型（可扩展）
- **数据位置**: `data/vector_db/`

### 知识库数据

知识库包含 8 个常见期刊/会议的模板信息：
- 文档类声明
- 关键宏包列表
- 格式要求
- 排版建议

### 错误处理

- API 统一错误响应格式
- 超时设置（搜索 10s，上传 30s，转换 300s）
- 详细的错误信息返回

## 后续扩展建议

1. **自定义嵌入模型**: 使用更专业的嵌入模型（如 sentence-transformers）
2. **知识库扩展**: 添加更多期刊模板和排版规则
3. **缓存机制**: 实现搜索结果缓存，提高响应速度
4. **用户认证**: 添加 API 密钥或用户认证
5. **批量处理**: 支持批量文件转换
6. **进度追踪**: WebSocket 实现实时转换进度

## 作者信息

**模块四：记忆与交互层**  
**实现者**: D同学（白钦宇）  
**完成时间**: 2024

## 联系方式

如有问题或建议，请联系项目团队。

