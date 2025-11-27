# AutoLaTeX API 通信协议文档

本文档定义了 AutoLaTeX 系统前端与 FastAPI 后端的 API 通信协议。

## 基础信息

- **API 基础 URL**: `http://localhost:8000`
- **API 版本**: `v1`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

所有 API 响应都遵循以下格式：

```json
{
  "success": true/false,
  "message": "状态消息",
  "data": {} // 具体数据（可选）
}
```

## API 端点

### 1. 根端点

**GET** `/`

获取 API 基本信息。

**响应示例**:
```json
{
  "service": "AutoLaTeX API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "knowledge_search": "/api/v1/knowledge/search",
    "paper_convert": "/api/v1/paper/convert",
    "health": "/api/v1/health"
  }
}
```

---

### 2. 健康检查

**GET** `/api/v1/health`

检查 API 服务状态。

**响应示例**:
```json
{
  "status": "healthy",
  "service": "AutoLaTeX API"
}
```

---

### 3. 知识库搜索

**POST** `/api/v1/knowledge/search`

根据期刊名称搜索 LaTeX 模板信息。

**请求体**:
```json
{
  "journal_name": "NeurIPS"
}
```

**响应示例**:
```json
{
  "success": true,
  "journal_name": "NeurIPS",
  "results": "【结果 1】相似度: 95.23%\n期刊: NeurIPS\n...",
  "message": "搜索成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "journal_name": "",
  "results": "",
  "message": "错误信息"
}
```

---

### 4. 论文转换

**POST** `/api/v1/paper/convert`

将论文文件转换为 LaTeX 格式。

**请求体**:
```json
{
  "file_path": "data/uploads/sample_paper.docx",
  "journal_name": "CVPR",
  "topic": "深度学习" // 可选
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "论文转换成功",
  "output_path": "output/draft.tex"
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "论文转换失败",
  "error": "详细错误信息"
}
```

---

### 5. 文件上传

**POST** `/api/v1/paper/upload`

上传论文文件到服务器。

**请求格式**: `multipart/form-data`

**请求参数**:
- `file`: 文件对象（支持 .docx, .txt, .md）

**响应示例**:
```json
{
  "success": true,
  "message": "文件上传成功",
  "file_path": "data/uploads/sample_paper.docx",
  "filename": "sample_paper.docx"
}
```

**错误响应**:
```json
{
  "detail": "错误信息"
}
```

---

## 状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 错误处理

所有错误响应都包含 `detail` 字段，描述具体的错误信息。

**示例**:
```json
{
  "detail": "期刊名称不能为空"
}
```

## CORS 配置

API 支持跨域请求（CORS），允许来自任何域名的请求。生产环境应限制为特定域名。

## 超时设置

- 知识库搜索: 10 秒
- 文件上传: 30 秒
- 论文转换: 300 秒（5 分钟）

## 使用示例

### Python 示例

```python
import requests

# 搜索知识库
response = requests.post(
    "http://localhost:8000/api/v1/knowledge/search",
    json={"journal_name": "NeurIPS"}
)
data = response.json()
print(data["results"])

# 上传文件
with open("paper.docx", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/api/v1/paper/upload",
        files=files
    )
    data = response.json()
    file_path = data["file_path"]

# 转换论文
response = requests.post(
    "http://localhost:8000/api/v1/paper/convert",
    json={
        "file_path": file_path,
        "journal_name": "NeurIPS"
    }
)
data = response.json()
print(data["message"])
```

### JavaScript 示例

```javascript
// 搜索知识库
fetch('http://localhost:8000/api/v1/knowledge/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ journal_name: 'NeurIPS' })
})
.then(response => response.json())
.then(data => console.log(data.results));

// 上传文件
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/v1/paper/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data.file_path));
```

---

**文档版本**: 1.0.0  
**最后更新**: 2024  
**维护者**: D同学（白钦宇）- 模块四：记忆与交互层

