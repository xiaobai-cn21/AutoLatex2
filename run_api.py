"""
启动 FastAPI 后端服务
"""
import sys
import os

# 添加 src 目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "autolatex.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )