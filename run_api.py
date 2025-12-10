"""
启动 FastAPI 后端服务
"""
import sys
import os

from dotenv import load_dotenv  # 新增：加载 .env 支持

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# 在项目根目录加载 .env（如果存在）
load_dotenv(os.path.join(project_root, ".env"), override=False)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "autolatex.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )