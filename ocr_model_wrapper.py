"""
OCR 模型封装模块
用于加载和推理 MixTex 微调模型
"""
import os
import torch
from PIL import Image
from transformers import (
    VisionEncoderDecoderModel,
    AutoTokenizer,
    AutoImageProcessor,
)
from peft import PeftModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRModelWrapper:
    """OCR 模型封装类"""
    
    def __init__(self, checkpoint_dir: str, base_model_path: str = None, device: str = None):
        """
        初始化模型
        
        Args:
            checkpoint_dir: 微调模型 checkpoint 目录路径
            base_model_path: 基础模型路径（如果是 LoRA checkpoint 则必须提供）
            device: 设备 ('cuda' 或 'cpu')，默认自动检测
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = torch.device(device)
        logger.info(f"使用设备: {self.device}")
        
        # 加载模型
        self.model, self.tokenizer, self.image_processor = self._load_model(
            checkpoint_dir, base_model_path
        )
        logger.info("模型加载完成")
    
    def _load_model(self, checkpoint_dir: str, base_model_path: str = None):
        """加载模型和处理器"""
        logger.info(f"从 {checkpoint_dir} 加载模型...")
        
        # 检查是否是 LoRA checkpoint
        adapter_config_path = os.path.join(checkpoint_dir, "adapter_config.json")
        
        if os.path.exists(adapter_config_path):
            if not base_model_path:
                # 尝试使用默认的基础模型路径
                base_model_path = "MixTex/ZhEn-Latex-OCR"
                logger.warning(f"检测到 LoRA checkpoint，使用默认基础模型: {base_model_path}")
            
            logger.info(f"检测到 LoRA checkpoint，从基础模型 {base_model_path} 加载...")
            model = VisionEncoderDecoderModel.from_pretrained(base_model_path)
            tokenizer = AutoTokenizer.from_pretrained(base_model_path)
            image_processor = AutoImageProcessor.from_pretrained(base_model_path)
            
            logger.info("将 LoRA 适配器加载到 decoder ...")
            decoder_with_lora = PeftModel.from_pretrained(model.decoder, checkpoint_dir)
            decoder_with_lora = decoder_with_lora.merge_and_unload()  # 合并权重便于推理
            model.decoder = decoder_with_lora
        else:
            # 全量模型
            logger.info("检测到全量模型 checkpoint")
            model = VisionEncoderDecoderModel.from_pretrained(checkpoint_dir)
            tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)
            image_processor = AutoImageProcessor.from_pretrained(checkpoint_dir)
        
        model.to(self.device)
        model.eval()
        return model, tokenizer, image_processor
    
    def predict(self, image: Image.Image, max_length: int = 256) -> str:
        """
        对图片进行 OCR 识别
        
        Args:
            image: PIL Image 对象
            max_length: 生成的最大长度
        
        Returns:
            识别出的 LaTeX 代码字符串
        """
        # 确保图片是 RGB 格式
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # 预处理图片
        pixel_values = self.image_processor(
            images=[image], 
            return_tensors="pt"
        ).pixel_values.to(self.device)
        
        # 模型推理
        with torch.no_grad():
            generated_ids = self.model.generate(
                pixel_values, 
                max_length=max_length
            )
        
        # 解码
        latex_code = self.tokenizer.batch_decode(
            generated_ids, 
            skip_special_tokens=True
        )[0].strip()
        
        return latex_code



