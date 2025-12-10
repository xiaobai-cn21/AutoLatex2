"""
OCR API 服务
提供 HTTP 接口用于图片转 LaTeX
"""
import os
import io
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
from ocr_model_wrapper import OCRModelWrapper

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(
    title="MixTex OCR API",
    description="基于 MixTex 微调模型的 LaTeX OCR API 服务"
)

# 全局模型实例
model_wrapper = None


class OCRResponse(BaseModel):
    """API 响应模型"""
    latex: str
    success: bool = True
    message: str = "识别成功"


@app.on_event("startup")
async def startup_event():
    """应用启动时加载模型"""
    global model_wrapper
    
    # 从环境变量或默认值获取配置
    checkpoint_dir = os.getenv(
        "OCR_CHECKPOINT_DIR",
        # 默认加载最新的全量训练 LoRA 结果
        "checkpoints/mixtex_lora_10k_final_tuned/epoch_2"
    )
    # 优先使用用户指定的基础模型；默认直接使用 HuggingFace 名称便于交付
    base_model_path = os.getenv("OCR_BASE_MODEL_PATH", "MixTex/ZhEn-Latex-OCR")
    device = os.getenv("OCR_DEVICE", None)  # None 表示自动检测
    
    logger.info(f"加载模型 checkpoint: {checkpoint_dir}")
    if base_model_path:
        logger.info(f"基础模型路径: {base_model_path}")
    
    try:
        model_wrapper = OCRModelWrapper(
            checkpoint_dir=checkpoint_dir,
            base_model_path=base_model_path,
            device=device
        )
        logger.info("模型加载成功，API 服务就绪")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise


@app.post("/predict", response_model=OCRResponse)
async def predict_latex(file: UploadFile = File(...)):
    """
    接收图片文件，返回识别出的 LaTeX 代码
    
    Args:
        file: 上传的图片文件
    
    Returns:
        JSON 响应，包含识别出的 LaTeX 代码
    """
    if model_wrapper is None:
        raise HTTPException(status_code=503, detail="模型未加载，请稍后重试")
    
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="上传的文件必须是图片格式")
    
    try:
        # 读取图片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 进行 OCR 识别
        logger.info(f"正在识别图片: {file.filename}")
        latex_code = model_wrapper.predict(image)
        logger.info(f"识别结果: {latex_code[:100]}...")  # 只打印前100个字符
        
        return OCRResponse(
            latex=latex_code,
            success=True,
            message="识别成功"
        )
    
    except Exception as e:
        logger.error(f"处理图片时发生错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"服务器内部错误: {str(e)}"
        )


@app.get("/")
def read_root():
    """根路径，用于健康检查"""
    return {
        "message": "MixTex OCR API 服务运行中",
        "status": "ready" if model_wrapper is not None else "loading",
        "endpoints": {
            "predict": "/predict (POST) - 上传图片进行 OCR 识别"
        }
    }


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy" if model_wrapper is not None else "unhealthy",
        "model_loaded": model_wrapper is not None
    }


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取端口，默认 8000
    port = int(os.getenv("OCR_API_PORT", 8000))
    host = os.getenv("OCR_API_HOST", "0.0.0.0")
    
    logger.info(f"启动 OCR API 服务，地址: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)



