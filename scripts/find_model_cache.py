"""快速查找 HuggingFace 模型缓存位置的工具"""
import os
from pathlib import Path
from huggingface_hub import HfFolder

def find_model_cache(model_name: str):
    """查找指定模型的本地缓存路径"""
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    
    # 将模型名转换为缓存目录名格式
    # 例如: "MixTex/ZhEn-Latex-OCR" -> "models--MixTex--ZhEn-Latex-OCR"
    cache_model_name = f"models--{model_name.replace('/', '--')}"
    model_cache_path = cache_dir / cache_model_name
    
    print(f"模型: {model_name}")
    print(f"缓存目录: {cache_dir}")
    print(f"模型缓存路径: {model_cache_path}")
    print(f"是否存在: {model_cache_path.exists()}")
    
    if model_cache_path.exists():
        # 查找实际的模型文件（通常在 snapshots 子目录下）
        snapshots = model_cache_path / "snapshots"
        if snapshots.exists():
            snapshots_list = list(snapshots.iterdir())
            if snapshots_list:
                latest_snapshot = max(snapshots_list, key=lambda p: p.stat().st_mtime)
                print(f"\n[OK] 找到模型文件！")
                print(f"完整路径: {latest_snapshot}")
                print(f"\n使用方式:")
                print(f'  --local-model-path "{latest_snapshot}"')
                return str(latest_snapshot)
    
    print(f"\n[ERROR] 模型尚未下载到本地缓存")
    return None

if __name__ == "__main__":
    import sys
    model_name = sys.argv[1] if len(sys.argv) > 1 else "MixTex/ZhEn-Latex-OCR"
    find_model_cache(model_name)

