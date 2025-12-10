## 启动
```powershell
cd C:\Users\Ding\Desktop\NLP\AutoLatex
# 如需自定义端口/设备可加环境变量，否则用默认
# $env:OCR_CHECKPOINT_DIR="checkpoints\mixtex_lora_10k_final_tuned\epoch_2"
# $env:OCR_DEVICE="cuda"  # 或 cpu
uvicorn ocr_api:app --host 0.0.0.0 --port 8001
```

## 识别图片
```powershell
curl -X POST "http://127.0.0.1:8001/predict" `
  -H "accept: application/json" `
  -F "file=@C:\path\to\image.png;type=image/png"
```
返回 JSON 中的 `latex` 字段即为识别结果。 

