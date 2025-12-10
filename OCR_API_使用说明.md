# OCR API 使用说明

## 概述

这是一个基于 MixTex 微调模型的 LaTeX OCR API 服务，提供 HTTP 接口用于将公式图片转换为 LaTeX 代码。

## 文件说明

- `ocr_model_wrapper.py`: 模型封装模块，负责加载和推理
- `ocr_api.py`: FastAPI 服务主文件
- `test_ocr_api.py`: 测试脚本

## 快速开始

### 1. 启动 API 服务

```bash
# 使用默认配置启动（默认使用 checkpoints/mixtex_qlora_lr_test_2e-5/epoch_3）
python ocr_api.py
```

### 2. 通过环境变量配置模型路径

```bash
# Windows PowerShell
$env:OCR_CHECKPOINT_DIR="checkpoints/mixtex_qlora_final_attempt/epoch_5"
$env:OCR_BASE_MODEL_PATH="C:\Users\Ding\.cache\huggingface\hub\models--MixTex--ZhEn-Latex-OCR\snapshots\37da0497956ac97f0a81f4da001f000d5295b77c"
python ocr_api.py

# Linux/Mac
export OCR_CHECKPOINT_DIR="checkpoints/mixtex_qlora_final_attempt/epoch_5"
export OCR_BASE_MODEL_PATH="/path/to/base/model"
python ocr_api.py
```

### 3. 测试 API

```bash
# 使用测试脚本
python test_ocr_api.py test_image.png

# 或使用 curl
curl -X POST "http://localhost:8000/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.png"
```

## API 接口说明

### POST /predict

上传图片进行 OCR 识别。

**请求:**
- Content-Type: `multipart/form-data`
- 参数: `file` (图片文件)

**响应:**
```json
{
  "latex": "\\frac{a}{b}",
  "success": true,
  "message": "识别成功"
}
```

### GET /health

健康检查接口，检查模型是否已加载。

**响应:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### GET /

根路径，返回服务信息。

## 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OCR_CHECKPOINT_DIR` | 微调模型 checkpoint 目录 | `checkpoints/mixtex_qlora_lr_test_2e-5/epoch_3` |
| `OCR_BASE_MODEL_PATH` | 基础模型路径（LoRA 模型需要） | `None`（自动使用 `MixTex/ZhEn-Latex-OCR`） |
| `OCR_DEVICE` | 设备 (`cuda` 或 `cpu`) | `None`（自动检测） |
| `OCR_API_PORT` | API 服务端口 | `8000` |
| `OCR_API_HOST` | API 服务主机 | `0.0.0.0` |

## 模型切换

当最终模型训练完成后，只需修改环境变量 `OCR_CHECKPOINT_DIR` 指向新的 checkpoint 目录即可：

```bash
# 使用最终训练好的模型
$env:OCR_CHECKPOINT_DIR="checkpoints/mixtex_qlora_final_attempt/epoch_5"
python ocr_api.py
```

## 注意事项

1. **首次启动**: 如果使用 HuggingFace Hub 上的模型，首次启动时会自动下载模型权重，可能需要一些时间。

2. **LoRA 模型**: 如果 checkpoint 是 LoRA 适配器（包含 `adapter_config.json`），需要提供基础模型路径。如果不提供，会默认使用 `MixTex/ZhEn-Latex-OCR`。

3. **GPU 支持**: 如果有 CUDA GPU，模型会自动使用 GPU 加速。否则会使用 CPU（速度较慢）。

4. **内存要求**: 
   - GPU: 建议至少 4GB 显存
   - CPU: 建议至少 8GB 内存

## 集成到 Agent

A 同学可以通过 HTTP 请求调用此 API：

```python
import requests

def ocr_image(image_path: str, api_url: str = "http://localhost:8000"):
    """调用 OCR API"""
    with open(image_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{api_url}/predict", files=files)
    return response.json()["latex"]
```

## 故障排查

1. **模型加载失败**: 检查 checkpoint 目录路径是否正确，确保包含必要的模型文件。

2. **CUDA 错误**: 如果没有 GPU 或 CUDA 配置有问题，设置 `OCR_DEVICE=cpu` 使用 CPU。

3. **端口被占用**: 修改 `OCR_API_PORT` 环境变量使用其他端口。

4. **内存不足**: 如果使用 CPU，可能需要减少并发请求数量。



