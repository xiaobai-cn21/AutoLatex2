"""快速查找 HuggingFace 数据集缓存位置的工具"""
import os
from pathlib import Path

def find_dataset_cache(dataset_name: str, subset_name: str = None):
    """查找指定数据集的本地缓存路径"""
    cache_dir = Path.home() / ".cache" / "huggingface" / "datasets"
    
    # 将数据集名转换为缓存目录名格式
    # 例如: "linxy/LaTeX_OCR" -> "linxy___LaTeX_OCR"
    cache_dataset_name = dataset_name.replace("/", "___")
    dataset_cache_path = cache_dir / cache_dataset_name
    
    print(f"数据集: {dataset_name}")
    if subset_name:
        print(f"子集: {subset_name}")
    print(f"缓存目录: {cache_dir}")
    print(f"数据集缓存路径: {dataset_cache_path}")
    print(f"是否存在: {dataset_cache_path.exists()}")
    
    if dataset_cache_path.exists():
        # 查找实际的缓存文件
        subdirs = [d for d in dataset_cache_path.iterdir() if d.is_dir()]
        if subdirs:
            print(f"\n[OK] 找到数据集缓存！")
            print(f"缓存目录: {dataset_cache_path}")
            print(f"\n提示：")
            print(f"  如果遇到网络连接问题，可以尝试：")
            print(f"  1. 设置环境变量: set HF_DATASETS_OFFLINE=1")
            print(f"  2. 或使用 --local-dataset-path 参数（如果支持）")
            return str(dataset_cache_path)
    
    print(f"\n[ERROR] 数据集尚未下载到本地缓存")
    print(f"提示：需要先在线下载一次数据集，之后才能使用本地缓存")
    return None

if __name__ == "__main__":
    import sys
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else "linxy/LaTeX_OCR"
    subset_name = sys.argv[2] if len(sys.argv) > 2 else None
    find_dataset_cache(dataset_name, subset_name)






