"""
FastAPI 后端服务
提供 AutoLaTeX 的 RESTful API 接口
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
from urllib.parse import quote

# 添加 src 目录到路径（从 api/main.py 向上两级到 src）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from autolatex.tools.knowledge_base import knowledge_base_search, initialize_knowledge_base, get_all_journal_names
from autolatex.crew import Autolatex

app = FastAPI(
    title="AutoLaTeX API",
    description="AutoLaTeX 论文自动转换服务 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化知识库
print("正在初始化知识库...")
try:
    initialize_knowledge_base()
    print("知识库初始化完成")
except Exception as e:
    print(f"知识库初始化失败: {e}")

# ==================== 请求/响应模型 ====================

class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    journal_name: str

class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应"""
    success: bool
    journal_name: str
    results: str
    message: Optional[str] = None

class PaperConvertRequest(BaseModel):
    """论文转换请求"""
    file_path: str
    journal_name: str
    topic: Optional[str] = None

class PaperConvertResponse(BaseModel):
    """论文转换响应"""
    success: bool
    message: str
    output_path: Optional[str] = None
    pdf_filename: Optional[str] = None
    pdf_url: Optional[str] = None
    error: Optional[str] = None

# ==================== API 端点 ====================

@app.get("/")
async def root():
    """根端点，返回 API 信息"""
    return {
        "service": "AutoLaTeX API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "knowledge_search": "/api/v1/knowledge/search",
            "knowledge_journals": "/api/v1/knowledge/journals",
            "paper_convert": "/api/v1/paper/convert",
            "health": "/api/v1/health"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "AutoLaTeX API"
    }

@app.get("/api/v1/knowledge/journals")
async def get_journals():
    """
    获取所有可用的期刊/会议名称列表
    
    返回知识库中所有支持的期刊和会议名称
    """
    try:
        journal_names = get_all_journal_names()
        return {
            "success": True,
            "journals": journal_names,
            "count": len(journal_names),
            "message": "获取成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取期刊列表失败: {str(e)}")

@app.post("/api/v1/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(request: KnowledgeSearchRequest):
    """
    搜索知识库
    
    根据期刊名称在向量数据库中搜索相关的 LaTeX 模板信息
    """
    try:
        journal_name = request.journal_name.strip()
        if not journal_name:
            raise HTTPException(status_code=400, detail="期刊名称不能为空")
        
        # 执行搜索
        results = knowledge_base_search(journal_name=journal_name, n_results=3)
        
        return KnowledgeSearchResponse(
            success=True,
            journal_name=journal_name,
            results=results,
            message="搜索成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/api/v1/paper/convert", response_model=PaperConvertResponse)
async def convert_paper(request: PaperConvertRequest):
    """
    转换论文
    
    将上传的论文文件转换为 LaTeX 格式
    """
    try:
        # 将文件路径转换为绝对路径并验证
        file_path = os.path.abspath(request.file_path)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 准备输入参数
        from datetime import datetime
        inputs = {
            'topic': request.topic or '自动将word、txt、markdown格式论文转化为Latex格式论文',
            'current_year': str(datetime.now().year),
            'file_path': file_path,
            'journal_name': request.journal_name,
        }
        
        # 运行 Crew
        crew = Autolatex().crew()
        result = crew.kickoff(inputs=inputs)
        
        # 提取输出路径（根据实际 Crew 输出调整）
        output_path = None
        if hasattr(result, 'output_path'):
            output_path = result.output_path
        elif isinstance(result, dict) and 'output_path' in result:
            output_path = result['output_path']

        # 查找最新生成的 PDF（存放于项目 output 目录）
        output_dir = os.path.join(project_root, "output")
        latest_pdf = None
        if os.path.isdir(output_dir):
            pdf_files = [
                f for f in os.listdir(output_dir)
                if f.lower().endswith(".pdf")
            ]
            if pdf_files:
                pdf_files.sort(
                    key=lambda fname: os.path.getmtime(os.path.join(output_dir, fname)),
                    reverse=True,
                )
                latest_pdf = pdf_files[0]
        
        pdf_url = None
        if latest_pdf:
            pdf_url = f"/api/v1/paper/download?filename={quote(latest_pdf)}"
        
        return PaperConvertResponse(
            success=True,
            message="论文转换成功",
            output_path=output_path or "output/draft.tex",
            pdf_filename=latest_pdf,
            pdf_url=pdf_url,
        )
    except Exception as e:
        return PaperConvertResponse(
            success=False,
            message="论文转换失败",
            error=str(e)
        )

@app.post("/api/v1/paper/upload")
async def upload_paper(file: UploadFile = File(...)):
    """
    上传论文文件
    
    接收用户上传的论文文件并保存到临时目录
    """
    try:
        # 创建上传目录（使用项目根目录下的绝对路径，避免相对路径引发的 File Not Found 问题）
        upload_dir = os.path.join(project_root, "data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件并返回绝对路径
        file_path = os.path.abspath(os.path.join(upload_dir, file.filename))
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "message": "文件上传成功",
            "file_path": file_path,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.get("/api/v1/paper/download")
async def download_pdf(filename: str):
    """
    下载生成的 PDF 文件（仅允许 output 目录下的 .pdf）
    """
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持下载 PDF 文件")
    
    output_dir = os.path.join(project_root, "output")
    target_path = os.path.abspath(os.path.join(output_dir, filename))
    
    # 路径安全校验，防止目录穿越
    if not target_path.startswith(os.path.abspath(output_dir)):
        raise HTTPException(status_code=400, detail="非法的文件路径")
    
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        target_path,
        media_type="application/pdf",
        filename=filename
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

