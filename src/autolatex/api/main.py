"""
FastAPI 后端服务
提供 AutoLaTeX 的 RESTful API 接口
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import uuid
import re
import zipfile
import shutil
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
    image_paths: Optional[List[str]] = None

class PaperConvertResponse(BaseModel):
    """论文转换响应"""
    success: bool
    message: str
    output_path: Optional[str] = None
    pdf_filename: Optional[str] = None
    pdf_url: Optional[str] = None
    tex_zip_url: Optional[str] = None
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
        
        # 如果有图片路径，添加到输入参数中
        if request.image_paths:
            inputs['image_paths'] = request.image_paths
            print(f"[API] 转换请求包含 {len(request.image_paths)} 张图片")
        
        # 设置 formula_position 为 equation 文件夹的路径
        # 从 file_path 推断出 equation 文件夹路径（例如：data/ex2/equation）
        file_dir = os.path.dirname(file_path)
        equation_folder = os.path.join(file_dir, 'equation')
        
        # 转换为相对于项目根目录的路径
        try:
            # 计算相对路径
            equation_folder_rel = os.path.relpath(equation_folder, project_root)
            # 将路径分隔符统一为正斜杠（跨平台兼容）
            formula_position = equation_folder_rel.replace(os.sep, '/')
        except ValueError:
            # 如果无法计算相对路径（在不同驱动器上），使用绝对路径
            formula_position = equation_folder.replace(os.sep, '/')
        
        inputs['formula_position'] = formula_position
        print(f"[API] formula_position 设置为: {formula_position}")
        
        # 运行 Crew
        print(f"[API] 开始执行 Crew，输入参数: {inputs}")
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
        
        # 检查 temp_source 文件夹是否存在，如果存在则提供下载链接
        temp_source_dir = os.path.join(project_root, "output", "temp_source")
        tex_zip_url = None
        if os.path.exists(temp_source_dir) and os.path.isdir(temp_source_dir):
            tex_zip_url = "/api/v1/paper/download-tex"
        
        return PaperConvertResponse(
            success=True,
            message="论文转换成功",
            output_path=output_path or "output/draft.tex",
            pdf_filename=latest_pdf,
            pdf_url=pdf_url,
            tex_zip_url=tex_zip_url,
        )
    except HTTPException:
        # 重新抛出 HTTPException，让 FastAPI 处理
        raise
    except Exception as e:
        # 记录完整的错误堆栈
        import traceback
        error_trace = traceback.format_exc()
        error_message = str(e)
        
        # 打印到控制台以便调试
        print(f"[API] 论文转换失败: {error_message}")
        print(f"[API] 错误堆栈:\n{error_trace}")
        
        # 返回详细的错误信息
        return PaperConvertResponse(
            success=False,
            message="论文转换失败",
            error=f"{error_message}\n\n详细错误信息请查看服务器日志。"
        )

@app.post("/api/v1/paper/upload")
async def upload_paper(request: Request):
    """
    上传论文文件和图片
    
    接收用户上传的论文文件以及公式图片（image_0, image_1, ...），并保存到临时目录
    """
    try:
        # 解析 multipart/form-data
        form = await request.form()
        
        # 调试：打印所有接收到的字段
        print(f"[API] 接收到的表单字段: {list(form.keys())}")
        
        # 获取文档文件
        file_item = None
        if "file" in form:
            file_item = form["file"]
        elif hasattr(form, 'get'):
            file_item = form.get("file")
        
        if not file_item:
            all_keys = list(form.keys()) if hasattr(form, 'keys') else []
            raise HTTPException(status_code=400, detail=f"缺少文档文件。接收到的字段: {all_keys}")
        
        # 检查是否是 UploadFile 对象（通过检查是否有 read 方法）
        if not hasattr(file_item, 'read'):
            raise HTTPException(status_code=400, detail=f"文件字段格式错误，类型: {type(file_item)}")
        
        file = file_item
        if not file.filename:
            raise HTTPException(status_code=400, detail="文档文件名不能为空")
        
        # 从文件名提取文件夹名（不含扩展名）
        file_name_without_ext = os.path.splitext(file.filename)[0]
        # 清理文件名，移除可能导致问题的字符
        safe_folder_name = re.sub(r'[<>:"/\\|?*]', '_', file_name_without_ext)
        if not safe_folder_name or safe_folder_name.strip() == '':
            safe_folder_name = "uploaded_file"
        
        # 创建以文件名命名的文件夹结构
        # data/文件名/文件名.扩展名
        # data/文件名/equation/原始图片文件名.png
        file_folder = os.path.join(project_root, "data", safe_folder_name)
        equation_folder = os.path.join(file_folder, "equation")
        
        # 创建必要的目录
        os.makedirs(file_folder, exist_ok=True)
        os.makedirs(equation_folder, exist_ok=True)
        
        print(f"[API] 创建文件夹: {file_folder}")
        print(f"[API] 创建公式文件夹: {equation_folder}")
        
        # 保存文档文件到文件文件夹中
        file_path = os.path.abspath(os.path.join(file_folder, file.filename))
        file_content = await file.read()
        with open(file_path, "wb") as f:
            f.write(file_content)
        print(f"[API] 保存文档: {file.filename} -> {file_path}")
        
        # 获取并保存所有图片文件到 equation 文件夹
        saved_image_paths = []
        image_keys = sorted([key for key in form.keys() if key.startswith("image_")])
        print(f"[API] 找到图片字段: {image_keys}")
        
        for image_key in image_keys:
            image_item = form.get(image_key)
            print(f"[API] 图片字段 {image_key} 类型: {type(image_item)}")
            
            # 检查是否是 UploadFile 对象
            if image_item and hasattr(image_item, 'read') and hasattr(image_item, 'filename'):
                image_file = image_item
                if image_file.filename:
                    # 验证文件扩展名必须是 PNG
                    file_ext = os.path.splitext(image_file.filename)[1].lower()
                    if file_ext != ".png":
                        raise HTTPException(
                            status_code=400, 
                            detail=f"图片格式错误：只接受 PNG 格式。当前文件: {image_file.filename}"
                        )
                    
                    # 使用原始文件名保存图片
                    original_filename = image_file.filename
                    image_path = os.path.abspath(os.path.join(equation_folder, original_filename))
                    
                    # 如果文件已存在，添加数字后缀避免覆盖
                    base_name, ext = os.path.splitext(original_filename)
                    counter = 1
                    while os.path.exists(image_path):
                        new_filename = f"{base_name}_{counter}{ext}"
                        image_path = os.path.abspath(os.path.join(equation_folder, new_filename))
                        counter += 1
                    
                    # 保存图片
                    image_content = await image_file.read()
                    with open(image_path, "wb") as img_f:
                        img_f.write(image_content)
                    
                    saved_image_paths.append(image_path)
                    print(f"[API] 保存图片: {image_file.filename} -> {image_path}")
        
        response_data = {
            "success": True,
            "message": "文件上传成功",
            "file_path": file_path,
            "filename": file.filename,
            "image_paths": saved_image_paths
        }
        
        if saved_image_paths:
            response_data["message"] = f"文件上传成功，已保存 {len(saved_image_paths)} 张图片"
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API] 上传错误: {error_trace}")
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

@app.get("/api/v1/paper/download-tex")
async def download_tex_zip():
    """
    下载 temp_source 文件夹中的所有 tex 文件（打包为 zip）
    """
    temp_source_dir = os.path.join(project_root, "output", "temp_source")
    
    if not os.path.exists(temp_source_dir):
        raise HTTPException(status_code=404, detail="temp_source 文件夹不存在")
    
    # 创建临时 zip 文件
    zip_filename = "latex_source.zip"
    temp_zip_path = os.path.join(project_root, "output", zip_filename)
    
    try:
        # 创建 zip 文件
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 遍历 temp_source 目录中的所有文件
            for root, dirs, files in os.walk(temp_source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径（相对于 temp_source 目录）
                    arcname = os.path.relpath(file_path, temp_source_dir)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            temp_zip_path,
            media_type="application/zip",
            filename=zip_filename,
            headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
        )
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
        raise HTTPException(status_code=500, detail=f"创建 zip 文件失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

