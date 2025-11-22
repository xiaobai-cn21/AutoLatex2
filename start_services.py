"""
启动 AutoLaTeX 所有服务
同时启动 FastAPI 后端和 Gradio Web UI
"""
import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def start_api():
    """启动 FastAPI 后端"""
    print("🚀 正在启动 FastAPI 后端服务...")
    subprocess.run([sys.executable, "run_api.py"])

def start_ui():
    """启动 Gradio Web UI"""
    # 等待 API 启动
    time.sleep(3)
    print("🎨 正在启动 Gradio Web UI...")
    subprocess.run([sys.executable, "run_ui.py"])

def main():
    """主函数"""
    print("=" * 50)
    print("AutoLaTeX 服务启动器")
    print("=" * 50)
    
    # 创建必要的目录
    os.makedirs("data/vector_db", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    print("\n📁 目录结构已准备就绪")
    print("\n⚠️  注意：")
    print("   - FastAPI 后端将在 http://localhost:8000 启动")
    print("   - Gradio Web UI 将在 http://localhost:7860 启动")
    print("   - 请确保端口 8000 和 7860 未被占用")
    print("\n" + "=" * 50 + "\n")
    
    # 启动 API（在后台线程）
    api_thread = Thread(target=start_api, daemon=True)
    api_thread.start()
    
    # 启动 UI（主线程）
    start_ui()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
        sys.exit(0)

