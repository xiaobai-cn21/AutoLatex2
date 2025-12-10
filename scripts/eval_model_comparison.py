"""
模型评估对比脚本
从 linxy/LaTeX_OCR 测试集中随机选择50个样本，对比本地微调模型和DeepSeek-OCR的表现

支持使用本地部署的 DeepSeek-OCR：
1. 通过 HTTP API: --deepseekocr-api-url http://localhost:8000
2. 通过 subprocess: --deepseekocr-path <path> --deepseekocr-conda-env deepseek-ocr

示例：
  # 使用本地 DeepSeek-OCR (subprocess)
  python scripts/eval_model_comparison.py \\
    --checkpoint-dir checkpoints/mixtex_qlora_final_attempt/epoch_5 \\
    --deepseekocr-path vendor/DeepSeek-OCR \\
    --deepseekocr-conda-env deepseek-ocr

  # 使用本地 DeepSeek-OCR (HTTP API)
  python scripts/eval_model_comparison.py \\
    --checkpoint-dir checkpoints/mixtex_qlora_final_attempt/epoch_5 \\
    --deepseekocr-api-url http://localhost:8000
"""
import argparse
import base64
import json
import os
import random
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
from io import BytesIO

import torch
from PIL import Image
import requests
from datasets import load_dataset
from dotenv import load_dotenv
from transformers import (
    VisionEncoderDecoderModel,
    AutoTokenizer,
    AutoImageProcessor,
    GenerationConfig,
)
from peft import PeftModel
from tqdm.auto import tqdm

# 加载环境变量
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_OUTPUT_DIR = PROJECT_ROOT / "evaluation_results"
IMAGES_DIR = EVAL_OUTPUT_DIR / "eval_images"
PREDICTIONS_DIR = EVAL_OUTPUT_DIR / "predictions"


def load_model_and_tokenizer(checkpoint_dir: str, device: torch.device, base_model_path: str = None):
    """加载微调后的模型（支持LoRA和全量模型）"""
    print(f"从 {checkpoint_dir} 加载模型...")
    
    # 检查是否是LoRA checkpoint
    adapter_config_path = os.path.join(checkpoint_dir, "adapter_config.json")
    
    if os.path.exists(adapter_config_path):
        if not base_model_path:
            # 使用默认基础模型
            base_model_path = "MixTex/ZhEn-Latex-OCR"
            print(f"检测到LoRA checkpoint，使用默认基础模型: {base_model_path}")
        
        print(f"从基础模型 {base_model_path} 加载...")
        model = VisionEncoderDecoderModel.from_pretrained(base_model_path)
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        image_processor = AutoImageProcessor.from_pretrained(base_model_path)
        
        print("将 LoRA 适配器加载到 decoder ...")
        decoder_with_lora = PeftModel.from_pretrained(model.decoder, checkpoint_dir)
        decoder_with_lora = decoder_with_lora.merge_and_unload()
        model.decoder = decoder_with_lora
    else:
        # 全量模型
        model = VisionEncoderDecoderModel.from_pretrained(checkpoint_dir)
        tokenizer = AutoTokenizer.from_pretrained(checkpoint_dir)
        image_processor = AutoImageProcessor.from_pretrained(checkpoint_dir)
    
    model.to(device)
    model.eval()
    return model, tokenizer, image_processor


def predict_with_local_model(
    model,
    tokenizer,
    image_processor,
    image: Image.Image,
    device: torch.device,
) -> tuple[str, float]:
    """使用本地模型进行预测，返回预测结果和处理时间"""
    start_time = time.time()
    
    with torch.no_grad():
        pixel_values = image_processor(images=[image], return_tensors="pt").pixel_values.to(device)
        # 使用简单、与 eval_finetuned_model 一致的生成方式，并显式提供 pad/eos，避免配置丢失导致乱码
        pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id
        eos_id = tokenizer.eos_token_id
        generated_ids = model.generate(
            pixel_values,
            max_length=256,
            pad_token_id=pad_id,
            eos_token_id=eos_id,
        )
        pred_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    
    elapsed_time = time.time() - start_time
    return pred_text, elapsed_time


def predict_with_deepseek_api(
    image: Image.Image,
    api_key: str,
    base_url: str = "https://api.deepseek.com",
) -> tuple[str, float, Optional[float]]:
    """
    使用DeepSeek API进行预测，返回预测结果、处理时间和成本（如果可用）
    注意：DeepSeek Chat API目前不支持图片输入（vision功能），此函数将返回空结果
    """
    if not api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY")
    
    start_time = time.time()
    
    # 将图片转换为base64
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # 构建请求
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 尝试使用vision API格式（DeepSeek API目前不支持，但保留代码以便将来支持时使用）
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张图片中的数学公式，并将其转换为LaTeX代码。只返回LaTeX代码，不要包含任何解释或注释。如果图片中没有公式，请返回空字符串。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 512
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        # 检查响应状态
        if response.status_code == 400:
            # 尝试解析错误信息
            try:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "未知错误")
                # 检查是否是vision不支持的错误
                if "image_url" in error_msg.lower() or "unknown variant" in error_msg.lower():
                    # 只在第一次遇到时打印警告，避免重复输出
                    if not hasattr(predict_with_deepseek_api, '_vision_warning_printed'):
                        print(f"  [警告] DeepSeek API不支持图片输入（vision功能）: {error_msg}")
                        print(f"  [提示] 将跳过DeepSeek API评估，或考虑使用支持vision的其他API（如OpenAI GPT-4V）")
                        predict_with_deepseek_api._vision_warning_printed = True
                else:
                    print(f"  [警告] DeepSeek API返回400错误: {error_msg}")
            except:
                if not hasattr(predict_with_deepseek_api, '_vision_warning_printed'):
                    print(f"  [警告] DeepSeek API返回400错误，可能不支持图片输入")
                    predict_with_deepseek_api._vision_warning_printed = True
            return "", 0.0, None
        elif response.status_code == 401:
            print("  [错误] DeepSeek API认证失败，请检查API密钥是否正确")
            return "", 0.0, None
        elif response.status_code == 402:
            print("  [错误] DeepSeek API余额不足")
            return "", 0.0, None
        elif response.status_code == 429:
            print("  [错误] DeepSeek API请求频率过高，请稍后重试")
            return "", 0.0, None
        
        response.raise_for_status()
        data = response.json()
        
        # 提取响应内容
        content = data["choices"][0]["message"]["content"].strip()
        
        # 尝试提取LaTeX代码块（如果有）
        if "```" in content:
            parts = content.split("```")
            if len(parts) >= 3:
                latex_part = parts[1]
                if latex_part.startswith("latex"):
                    latex_part = latex_part[5:].strip()
                elif latex_part.startswith("math"):
                    latex_part = latex_part[4:].strip()
                content = latex_part.strip()
        
        # 移除可能的markdown格式
        content = content.strip().strip("$").strip()
        
        elapsed_time = time.time() - start_time
        
        # 尝试获取成本信息（如果API返回）
        cost = None
        if "usage" in data:
            usage = data["usage"]
            total_tokens = usage.get("total_tokens", 0)
            # DeepSeek Chat API定价：约每1000 tokens 0.0014元（需要根据实际定价调整）
            # 这里使用一个估算值
            cost = (total_tokens / 1000) * 0.0014
        
        return content, elapsed_time, cost
        
    except requests.exceptions.RequestException as e:
        print(f"  DeepSeek API调用失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"  错误详情: {error_data}")
            except:
                print(f"  响应状态码: {e.response.status_code}")
        return "", 0.0, None


def save_image(image: Image.Image, image_id: str, output_dir: Path):
    """保存图片到指定目录"""
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{image_id}.png"
    image.save(image_path)
    return image_path


def predict_with_local_deepseekocr(
    image: Image.Image,
    deepseekocr_path: Optional[str] = None,
    conda_env: Optional[str] = None,
    api_url: Optional[str] = None,
    timeout: int = 1800,
) -> tuple[str, float]:
    """
    使用本地部署的 DeepSeek-OCR 进行预测
    
    支持两种方式：
    1. 通过 HTTP API 调用（如果 api_url 提供）
    2. 通过 subprocess 调用 run_ocr.py（如果 deepseekocr_path 和 conda_env 提供）
    
    Args:
        image: PIL Image 对象
        deepseekocr_path: DeepSeek-OCR 项目路径（包含 run_ocr.py）
        conda_env: Conda 环境名称（如 'deepseek-ocr'）
        api_url: DeepSeek-OCR HTTP API 地址（如 'http://localhost:8000'）
    
    Returns:
        (预测结果, 处理时间)
    """
    start_time = time.time()
    
    # 方式1: 通过 HTTP API 调用
    if api_url:
        try:
            # 将图片保存到临时文件
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                image.save(tmp_file.name, format="PNG")
                tmp_path = tmp_file.name
            
            try:
                # 发送请求
                with open(tmp_path, "rb") as f:
                    files = {"file": (os.path.basename(tmp_path), f, "image/png")}
                    response = requests.post(f"{api_url}/predict", files=files, timeout=120)
                
                if response.status_code == 200:
                    result = response.json()
                    latex_code = result.get("latex", "").strip()
                    elapsed_time = time.time() - start_time
                    return latex_code, elapsed_time
                else:
                    print(f"  [警告] DeepSeek-OCR API返回错误: {response.status_code} - {response.text}")
                    return "", 0.0
            finally:
                # 清理临时文件
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            print(f"  [错误] DeepSeek-OCR API调用失败: {e}")
            return "", 0.0
    
    # 方式2: 通过 subprocess 调用 run_ocr.py
    if deepseekocr_path and conda_env:
        try:
            # 将路径转换为绝对路径，避免路径重复问题
            deepseekocr_path = os.path.abspath(deepseekocr_path)
            
            # 准备临时目录和文件
            with tempfile.TemporaryDirectory() as tmp_dir:
                # 保存图片到临时目录
                input_image_path = os.path.join(tmp_dir, "input.png")
                image.save(input_image_path, format="PNG")
                
                # 构建命令 - 使用绝对路径
                run_ocr_script = os.path.join(deepseekocr_path, "run_ocr.py")
                run_ocr_script = os.path.abspath(run_ocr_script)  # 确保是绝对路径
                
                if not os.path.exists(run_ocr_script):
                    print(f"  [错误] 找不到 run_ocr.py: {run_ocr_script}")
                    return "", 0.0
                
                # 使用 conda run 命令（更可靠的方式）
                # 使用绝对路径，不设置 cwd，避免路径重复问题
                shell_cmd = [
                    'conda', 'run', '-n', conda_env,
                    'python', run_ocr_script,
                    '--input_image', input_image_path,
                    '--output_dir', tmp_dir
                ]
                
                # 添加进度提示（DeepSeek-OCR 每次调用都会加载模型，可能很慢）
                if not hasattr(predict_with_local_deepseekocr, '_first_call_done'):
                    print(f"  [提示] DeepSeek-OCR 首次调用，正在加载模型...")
                    print(f"  [提示] 注意：每次调用都会重新加载模型，可能需要 {timeout//60} 分钟")
                    print(f"  [提示] 建议：如果可能，使用 HTTP API 方式（--deepseekocr-api-url）以避免重复加载模型")
                    predict_with_local_deepseekocr._first_call_done = True
                
                # 执行命令 - 不设置 cwd，使用绝对路径
                # 使用可配置的超时时间（默认30分钟，因为每次调用都需要加载模型）
                result = subprocess.run(
                    shell_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                
                if result.returncode == 0:
                    # 读取输出文件（.mmd 文件）
                    output_mmd = os.path.join(tmp_dir, "input.mmd")
                    if os.path.exists(output_mmd):
                        with open(output_mmd, "r", encoding="utf-8") as f:
                            latex_code = f.read().strip()
                        # 清理可能的 markdown 格式
                        latex_code = latex_code.strip().strip("$").strip()
                        elapsed_time = time.time() - start_time
                        return latex_code, elapsed_time
                    else:
                        print(f"  [警告] DeepSeek-OCR 未生成输出文件")
                        return "", 0.0
                else:
                    print(f"  [错误] DeepSeek-OCR 执行失败: {result.stderr}")
                    return "", 0.0
        except subprocess.TimeoutExpired:
            timeout_minutes = timeout // 60
            print(f"  [错误] DeepSeek-OCR 执行超时（>{timeout_minutes}分钟）")
            print(f"  [提示] 每次调用都会重新加载模型，这可能需要很长时间")
            print(f"  [建议] 1. 增加超时时间：--deepseekocr-timeout 3600（60分钟）")
            print(f"  [建议] 2. 使用 HTTP API 方式（如果可能）：--deepseekocr-api-url http://localhost:8000")
            print(f"  [建议] 3. 检查 DeepSeek-OCR 环境是否正确配置")
            return "", 0.0
        except Exception as e:
            print(f"  [错误] DeepSeek-OCR 调用失败: {e}")
            return "", 0.0
    
    # 如果既没有 API URL 也没有路径，返回空
    print(f"  [错误] 未提供 DeepSeek-OCR 配置（需要 api_url 或 deepseekocr_path+conda_env）")
    return "", 0.0


def save_prediction(prediction: str, image_id: str, model_name: str, output_dir: Path):
    """保存预测结果到文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    pred_file = output_dir / f"{image_id}_{model_name}.txt"
    with open(pred_file, "w", encoding="utf-8") as f:
        f.write(prediction)
    return pred_file


def main():
    parser = argparse.ArgumentParser(description="模型评估对比脚本")
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        required=True,
        help="微调后的模型 checkpoint 目录",
    )
    parser.add_argument(
        "--base-model-path",
        type=str,
        default=None,
        help="LoRA模型的基础模型路径（如果checkpoint是LoRA适配器）",
    )
    parser.add_argument(
        "--subset-name",
        type=str,
        default="small",
        help="数据集子集名称 (small, full, ...)",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=50,
        help="随机选择的样本数量",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="设备 (cpu, cuda)",
    )
    parser.add_argument(
        "--include-baseline",
        action="store_true",
        help="是否包含基线模型（原始MixTex）的评估",
    )
    parser.add_argument(
        "--baseline-model-path",
        type=str,
        default="MixTex/ZhEn-Latex-OCR",
        help="基线模型路径（默认: MixTex/ZhEn-Latex-OCR）",
    )
    parser.add_argument(
        "--skip-deepseek",
        action="store_true",
        help="跳过DeepSeek API评估（DeepSeek API目前不支持图片输入）",
    )
    parser.add_argument(
        "--deepseekocr-path",
        type=str,
        default=None,
        help="本地 DeepSeek-OCR 项目路径（包含 run_ocr.py），用于通过 subprocess 调用",
    )
    parser.add_argument(
        "--deepseekocr-conda-env",
        type=str,
        default=None,
        help="DeepSeek-OCR 的 Conda 环境名称（如 'deepseek-ocr'）",
    )
    parser.add_argument(
        "--deepseekocr-api-url",
        type=str,
        default=None,
        help="DeepSeek-OCR HTTP API 地址（如 'http://localhost:8000'），如果已启动服务",
    )
    parser.add_argument(
        "--deepseekocr-timeout",
        type=int,
        default=1800,
        help="DeepSeek-OCR 调用超时时间（秒），默认 1800 秒（30分钟）。首次调用需要加载模型，可能需要较长时间",
    )
    
    args = parser.parse_args()
    
    # 设置随机种子
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # 创建输出目录
    EVAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载模型
    # 自动检测 GPU 可用性
    if args.device == "cuda":
        if not torch.cuda.is_available():
            print("警告: 请求使用 CUDA，但系统未检测到可用的 GPU")
            print("      将自动切换到 CPU")
            device = torch.device("cpu")
        else:
            device = torch.device("cuda")
            print(f"使用设备: {device}")
            print(f"GPU 名称: {torch.cuda.get_device_name(0)}")
            print(f"CUDA 版本: {torch.version.cuda}")
    else:
        device = torch.device(args.device)
        print(f"使用设备: {device}")
    
    # 加载微调模型
    print("\n[1/2] 加载微调模型...")
    model, tokenizer, image_processor = load_model_and_tokenizer(
        args.checkpoint_dir,
        device,
        base_model_path=args.base_model_path
    )
    
    # 加载基线模型（如果需要）
    baseline_model = None
    baseline_tokenizer = None
    baseline_image_processor = None
    if args.include_baseline:
        print("\n[2/2] 加载基线模型...")
        try:
            baseline_model = VisionEncoderDecoderModel.from_pretrained(args.baseline_model_path)
            baseline_tokenizer = AutoTokenizer.from_pretrained(args.baseline_model_path)
            baseline_image_processor = AutoImageProcessor.from_pretrained(args.baseline_model_path)
            baseline_model.to(device)
            baseline_model.eval()
            print(f"基线模型加载成功: {args.baseline_model_path}")
        except Exception as e:
            print(f"警告: 基线模型加载失败: {e}")
            print("将跳过基线模型评估")
            args.include_baseline = False
    else:
        print("\n[2/2] 跳过基线模型加载（使用 --include-baseline 可启用）")
    
    # 加载测试集
    print(f"\n加载测试集: linxy/LaTeX_OCR, name={args.subset_name}, split=test")
    try:
        ds = load_dataset("linxy/LaTeX_OCR", name=args.subset_name, split="test")
    except Exception as e:
        print(f"在线加载失败: {e}")
        print("请确保网络连接正常")
        return
    
    # 随机选择样本
    total_samples = len(ds)
    if args.num_samples > total_samples:
        print(f"警告: 请求的样本数 ({args.num_samples}) 大于测试集大小 ({total_samples})，将使用全部样本")
        selected_indices = list(range(total_samples))
    else:
        selected_indices = random.sample(range(total_samples), args.num_samples)
    
    print(f"从 {total_samples} 个测试样本中随机选择了 {len(selected_indices)} 个样本")
    
    # 配置 DeepSeek-OCR（本地或 API）
    use_local_deepseekocr = False
    deepseekocr_path = args.deepseekocr_path
    deepseekocr_conda_env = args.deepseekocr_conda_env or os.getenv("DEEPSEEKOCR_CONDA_ENV", "deepseek-ocr")
    deepseekocr_api_url = args.deepseekocr_api_url or os.getenv("DEEPSEEKOCR_API_URL")
    
    api_key = None
    if args.skip_deepseek:
        print("提示: 已设置 --skip-deepseek，将跳过DeepSeek API评估")
        print("      （DeepSeek API目前不支持图片输入/vision功能）")
    elif deepseekocr_api_url or (deepseekocr_path and deepseekocr_conda_env):
        # 使用本地 DeepSeek-OCR
        use_local_deepseekocr = True
        if deepseekocr_api_url:
            print(f"提示: 将使用本地 DeepSeek-OCR HTTP API: {deepseekocr_api_url}")
        else:
            print(f"提示: 将使用本地 DeepSeek-OCR (路径: {deepseekocr_path}, Conda环境: {deepseekocr_conda_env})")
    else:
        # 尝试使用 DeepSeek API（但可能不支持）
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("警告: 未找到 DEEPSEEK_API_KEY，将跳过DeepSeek API评估")
            print("      提示: 可以使用 --deepseekocr-path 和 --deepseekocr-conda-env 来使用本地 DeepSeek-OCR")
        else:
            print("提示: DeepSeek API目前不支持图片输入（vision功能），评估可能会失败")
            print("      建议: 使用 --deepseekocr-path 和 --deepseekocr-conda-env 来使用本地 DeepSeek-OCR")
    
    # 评估结果
    results: List[Dict] = []
    total_deepseek_cost = 0.0
    
    print("\n开始评估...")
    for idx, sample_idx in enumerate(tqdm(selected_indices, desc="评估进度")):
        sample = ds[sample_idx]
        
        # 获取图片和Ground Truth
        image = sample["image"]
        if not isinstance(image, Image.Image):
            image = Image.fromarray(image)
        image = image.convert("RGB")
        ground_truth = sample["text"].strip()
        
        # 生成图片ID
        image_id = f"test_{sample_idx:05d}"
        
        # 保存图片
        image_path = save_image(image, image_id, IMAGES_DIR)
        
        # 使用微调模型预测
        local_pred, local_time = predict_with_local_model(
            model, tokenizer, image_processor, image, device
        )
        save_prediction(local_pred, image_id, "finetuned_model", PREDICTIONS_DIR)
        
        # 使用基线模型预测（如果需要）
        baseline_pred = ""
        baseline_time = 0.0
        if args.include_baseline and baseline_model:
            try:
                baseline_pred, baseline_time = predict_with_local_model(
                    baseline_model, baseline_tokenizer, baseline_image_processor, image, device
                )
                save_prediction(baseline_pred, image_id, "baseline_model", PREDICTIONS_DIR)
            except Exception as e:
                print(f"\n样本 {image_id} 的基线模型预测失败: {e}")
                baseline_pred = "[预测失败]"
        
        # 使用 DeepSeek-OCR 或 DeepSeek API 预测
        deepseek_pred = ""
        deepseek_time = 0.0
        deepseek_cost = None
        if use_local_deepseekocr:
            # 使用本地 DeepSeek-OCR
            try:
                if idx == 0:  # 第一个样本时给出提示
                    print(f"\n[提示] 正在调用 DeepSeek-OCR 处理样本 {image_id}...")
                    print(f"       （首次调用需要加载模型，可能需要几分钟，请耐心等待）")
                deepseek_pred, deepseek_time = predict_with_local_deepseekocr(
                    image,
                    deepseekocr_path=deepseekocr_path,
                    conda_env=deepseekocr_conda_env,
                    api_url=deepseekocr_api_url,
                    timeout=args.deepseekocr_timeout
                )
                if deepseek_pred:
                    save_prediction(deepseek_pred, image_id, "deepseekocr_local", PREDICTIONS_DIR)
                else:
                    deepseek_pred = "[调用失败]"
                    save_prediction(deepseek_pred, image_id, "deepseekocr_local", PREDICTIONS_DIR)
            except Exception as e:
                print(f"\n样本 {image_id} 的本地 DeepSeek-OCR 调用失败: {e}")
                deepseek_pred = f"[调用失败: {str(e)}]"
                save_prediction(deepseek_pred, image_id, "deepseekocr_local", PREDICTIONS_DIR)
        elif api_key:
            # 使用 DeepSeek API（可能不支持）
            try:
                deepseek_pred, deepseek_time, deepseek_cost = predict_with_deepseek_api(
                    image, api_key
                )
                if deepseek_cost:
                    total_deepseek_cost += deepseek_cost
                if deepseek_pred:
                    save_prediction(deepseek_pred, image_id, "deepseek_api", PREDICTIONS_DIR)
                else:
                    # API调用失败，保存错误信息
                    deepseek_pred = "[API调用失败]"
                    save_prediction(deepseek_pred, image_id, "deepseek_api", PREDICTIONS_DIR)
            except Exception as e:
                print(f"\n样本 {image_id} 的DeepSeek API调用失败: {e}")
                deepseek_pred = f"[API调用失败: {str(e)}]"
                save_prediction(deepseek_pred, image_id, "deepseek_api", PREDICTIONS_DIR)
        else:
            # 跳过DeepSeek评估
            deepseek_pred = "[已跳过]"
            save_prediction(deepseek_pred, image_id, "deepseek_api", PREDICTIONS_DIR)
        
        # 记录结果
        result = {
            "image_id": image_id,
            "image_path": str(image_path),
            "ground_truth": ground_truth,
            "finetuned_model_pred": local_pred,
            "finetuned_model_time": local_time,
            "deepseek_pred": deepseek_pred,
            "deepseek_time": deepseek_time,
            "deepseek_cost": deepseek_cost,
        }
        
        if args.include_baseline:
            result["baseline_model_pred"] = baseline_pred
            result["baseline_model_time"] = baseline_time
        
        results.append(result)
    
    # 保存结果到JSON文件
    results_file = EVAL_OUTPUT_DIR / "evaluation_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {results_file}")
    
    # 生成Excel格式的CSV文件（方便导入Excel）
    csv_file = EVAL_OUTPUT_DIR / "evaluation_results.csv"
    import csv
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        # 写入表头
        header = [
            "Image ID",
            "Ground Truth LaTeX",
        ]
        
        if args.include_baseline:
            header.extend([
                "基线模型-预测",
                "基线模型-质量(1-5)",
                "基线模型-耗时(秒)",
            ])
        
        # 根据使用的 DeepSeek 类型设置列名
        if use_local_deepseekocr:
            deepseek_name = "DeepSeek-OCR(本地)"
        elif api_key:
            deepseek_name = "DeepSeek-API"
        else:
            deepseek_name = "DeepSeek"
        
        header.extend([
            "微调模型-预测",
            f"{deepseek_name}-预测",
            "微调模型-质量(1-5)",
            f"{deepseek_name}-质量(1-5)",
            "微调模型-耗时(秒)",
            f"{deepseek_name}-耗时(秒)",
            "备注"
        ])
        
        writer.writerow(header)
        
        # 写入数据
        for r in results:
            row = [
                r["image_id"],
                r["ground_truth"],
            ]
            
            if args.include_baseline:
                row.extend([
                    r.get("baseline_model_pred", ""),
                    "",  # 质量评分需要人工填写
                    f"{r.get('baseline_model_time', 0.0):.3f}",
                ])
            
            row.extend([
                r["finetuned_model_pred"],
                r["deepseek_pred"],
                "",  # 质量评分需要人工填写
                "",  # 质量评分需要人工填写
                f"{r['finetuned_model_time']:.3f}",
                f"{r['deepseek_time']:.3f}",
                ""  # 备注需要人工填写
            ])
            
            writer.writerow(row)
    print(f"CSV文件已保存到: {csv_file}")
    
    # 打印统计信息
    print("\n" + "="*60)
    print("评估完成！")
    print("="*60)
    print(f"总样本数: {len(results)}")
    print(f"微调模型平均耗时: {sum(r['finetuned_model_time'] for r in results) / len(results):.3f} 秒")
    if args.include_baseline:
        baseline_times = [r.get('baseline_model_time', 0.0) for r in results if r.get('baseline_model_time', 0.0) > 0]
        if baseline_times:
            print(f"基线模型平均耗时: {sum(baseline_times) / len(baseline_times):.3f} 秒")
    if use_local_deepseekocr:
        deepseek_times = [r['deepseek_time'] for r in results if r['deepseek_time'] > 0]
        if deepseek_times:
            print(f"DeepSeek-OCR(本地)平均耗时: {sum(deepseek_times) / len(deepseek_times):.3f} 秒")
    elif api_key:
        deepseek_times = [r['deepseek_time'] for r in results if r['deepseek_time'] > 0]
        if deepseek_times:
            print(f"DeepSeek API平均耗时: {sum(deepseek_times) / len(deepseek_times):.3f} 秒")
        if total_deepseek_cost > 0:
            print(f"DeepSeek API总成本（估算）: {total_deepseek_cost:.4f} 元")
    print(f"\n图片保存在: {IMAGES_DIR}")
    print(f"预测结果保存在: {PREDICTIONS_DIR}")
    print(f"\n请打开 {csv_file} 进行人工评估，填写质量评分和备注")
    print("="*60)


if __name__ == "__main__":
    main()

