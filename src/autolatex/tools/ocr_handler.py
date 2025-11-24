# filename: src/autolatex/tools/ocr_handler.py
import os
import subprocess

# ==============================================================================
# --- 1. 重要配置区域 ---
# ==============================================================================
# 配置说明：
# 1. 如果使用独立的 deepseek-ocr conda 环境，请设置其 Python 路径
# 2. 如果使用当前 Python 环境，可以设置为 None 或当前 Python 解释器路径
# 3. 如果设置为 None，将使用当前 Python 解释器 (sys.executable)

# 方式1: 使用独立的 conda 环境（推荐，如果存在）
# DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH = "C:/Users/86138/.conda/envs/deepseek-ocr/python.exe"

# 方式2: 使用 LL-CLASS 环境（如果 OCR 依赖已安装在该环境）
# DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH = "C:/Users/86138/.conda/envs/LL-CLASS/python.exe"

# 方式3: 使用当前 Python 解释器（如果 OCR 依赖已安装在当前环境）
DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH = None  # None 表示使用当前 Python 解释器
# (这部分保持不变)
DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH = "C:/Users/Ding/anaconda3/envs/deepseek-ocr/python.exe"  # 确认这个路径是正确的

# --- (以下路径通常不需要修改) ---
OCR_SCRIPT_PATH = "vendor/DeepSeek-OCR/run_ocr.py"
OUTPUT_PATH = 'data/OCR_output'

# ==============================================================================
# --- 2. 检查配置有效性并确定最终使用的 Python 路径 ---
# ==============================================================================
import sys

# 如果未设置或设置为 None，使用当前 Python 解释器
if DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH is None:
    DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH = sys.executable
    print(f"[OCR Handler] 使用当前 Python 解释器: {DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH}")
elif not os.path.exists(DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH):
    print("=" * 60)
    print("!!!!!! 警告 in ocr_handler.py !!!!!!")
    print(f"指定的 Python 解释器路径不存在: {DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH}")
    print("将回退到使用当前 Python 解释器。")
    print("=" * 60)
    DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH = sys.executable
    print(f"[OCR Handler] 回退到当前 Python 解释器: {DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH}")
else:
    print(f"[OCR Handler] 使用指定的 Python 解释器: {DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH}")
# --- 2. 检查配置有效性 ---
# ==============================================================================
# (这部分保持不变)
if not os.path.exists(DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH):
    print("=" * 60)
    print("!!!!!! 严重配置错误 in ocr_handler.py !!!!!!")
    print(f"指定的 Python 解释器路径不存在: {DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH}")
    print("请按照文件内的注释，正确设置 DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH 变量。")
    print("=" * 60)


# ==============================================================================
# --- 3. 可供外部导入的核心工具函数 ---
# ==============================================================================

def recognize_image_to_latex(image_path: str) -> str:
    """
    通过调用一个在独立Conda环境中的外部脚本来执行OCR，并返回LaTeX代码字符串。
    具有缓存功能，如果.mmd输出文件已存在，则直接读取。
    """
    # --- 步骤 1: 路径准备和缓存检查 ---
    # (这部分保持不变)
    image_base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_mmd_path = os.path.join(OUTPUT_PATH, f"{image_base_name}.mmd")

    if os.path.exists(output_mmd_path):
        print(f"  - [OCR Cache] 命中缓存，直接读取: {output_mmd_path}")
        with open(output_mmd_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    # ====================== 开始修改 ======================
    # --- 步骤 2: 将所有相对路径转换为绝对路径，然后构造命令 ---

    # 获取当前脚本所在目录的项目根目录 (AutoLatex 文件夹)
    # 通常假设我们是从项目根目录运行的，os.getcwd() 就可以。
    # 为了更健壮，我们可以用 os.path.abspath()

    # 将所有路径转换为绝对路径
    abs_ocr_script_path = os.path.abspath(OCR_SCRIPT_PATH)
    abs_image_path = os.path.abspath(image_path)
    abs_output_path = os.path.abspath(OUTPUT_PATH)

    # 检查转换后的路径是否存在，便于调试
    if not os.path.exists(abs_ocr_script_path):
        print(f"  - 错误：无法找到OCR执行脚本: {abs_ocr_script_path}")
        return ""
    if not os.path.exists(abs_image_path):
        print(f"  - 错误：无法找到输入图片: {abs_image_path}")
        return ""

    command = [
        DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH,
        abs_ocr_script_path,
        "--input_image", abs_image_path,
        "--output_dir", abs_output_path
    ]
    # ====================== 修改结束 ======================

    print(f"  - [OCR Handler] 调用外部进程执行OCR...")
    try:
        os.makedirs(abs_output_path, exist_ok=True)  # 使用绝对路径确保目录被正确创建
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            # 设置工作目录，可以进一步增强稳定性
            cwd=os.path.abspath(".")  # cwd = Current Working Directory
        )
        print("  - [OCR Handler] 外部进程成功执行。")

    except FileNotFoundError:
        # (这部分保持不变)
        print("=" * 60)
        print("!!!!!! 严重配置错误 in ocr_handler.py !!!!!!")
        print(f"无法找到 Python 解释器: {DEEPSEEK_OCR_CONDA_ENV_PYTHON_PATH}")
        print("=" * 60)
        return ""
    except subprocess.CalledProcessError as e:
        # (这部分保持不变)
        print(f"!!!!!! [OCR Handler] 外部OCR脚本执行失败 !!!!!!")
        print(f"  - 命令: {' '.join(e.cmd)}")
        print(f"  - 返回码: {e.returncode}")
        print("  - STDOUT (标准输出):\n", e.stdout)
        print("  - STDERR (标准错误):\n", e.stderr)
        return ""

    # --- 步骤 3: 读取外部脚本生成的结果文件 ---
    # (这部分保持不变, 但用绝对路径检查更可靠)
    abs_output_mmd_path = os.path.abspath(output_mmd_path)
    if os.path.exists(abs_output_mmd_path):
        with open(abs_output_mmd_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        print(f"  - 错误：OCR脚本执行成功，但未找到预期的输出文件 {abs_output_mmd_path}")
        return ""