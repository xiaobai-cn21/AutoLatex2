"""
Gradio Web UI for AutoLaTeX
提供知识库搜索和论文转换的用户界面
"""
import gradio as gr
import requests
import os
from typing import Optional

# API 基础 URL
API_BASE_URL = "http://localhost:8000"

def get_available_journals() -> list:
    """
    获取所有可用的期刊/会议名称列表
    
    Returns:
        期刊名称列表
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/knowledge/journals",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data.get("journals", [])
        return []
    except Exception:
        # 如果 API 不可用，返回硬编码的列表作为后备
        return [
            "AAAI", "ACL", "ACM", "CVPR", "ICLR", "ICML", "IEEE", "KDD", 
            "Nature", "NeurIPS", "SIGGRAPH", "WWW",
            "CCF", "计算机学报", "软件学报", "中国科学", "自动化学报", 
            "电子学报", "通信学报", "计算机研究与发展", "中文信息学报", 
            "模式识别与人工智能"
        ]

def search_knowledge_base(journal_name: str) -> str:
    """
    搜索知识库
    
    Args:
        journal_name: 期刊名称
        
    Returns:
        搜索结果字符串
    """
    if not journal_name or not journal_name.strip():
        return "⚠️ 请输入期刊名称"
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/knowledge/search",
            json={"journal_name": journal_name.strip()},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            return data.get("results", "未找到相关结果")
        else:
            return f"❌ 搜索失败: {data.get('message', '未知错误')}"
    except requests.exceptions.ConnectionError:
        return "❌ 无法连接到 API 服务器，请确保 FastAPI 后端正在运行 (http://localhost:8000)"
    except requests.exceptions.Timeout:
        return "❌ 请求超时，请稍后重试"
    except Exception as e:
        return f"❌ 发生错误: {str(e)}"

def upload_and_convert(file, journal_name: str, topic: Optional[str] = None) -> str:
    """
    上传文件并转换论文
    
    Args:
        file: 上传的文件对象
        journal_name: 期刊名称
        topic: 可选的主题
        
    Returns:
        转换结果消息
    """
    if file is None:
        return "⚠️ 请先上传文件"
    
    if not journal_name or not journal_name.strip():
        return "⚠️ 请输入期刊名称"
    
    try:
        # 第一步：上传文件
        with open(file.name, 'rb') as f:
            files = {'file': (os.path.basename(file.name), f, 'application/octet-stream')}
            upload_response = requests.post(
                f"{API_BASE_URL}/api/v1/paper/upload",
                files=files,
                timeout=60
            )
            upload_response.raise_for_status()
            upload_data = upload_response.json()
            
            if not upload_data.get("success"):
                return f"❌ 文件上传失败: {upload_data.get('message', '未知错误')}"
            
            file_path = upload_data.get("file_path")
        
        # 第二步：转换论文
        convert_response = requests.post(
            f"{API_BASE_URL}/api/v1/paper/convert",
            json={
                "file_path": file_path,
                "journal_name": journal_name.strip(),
                "topic": topic or None
            },
            timeout=300  # 5分钟超时
        )
        convert_response.raise_for_status()
        convert_data = convert_response.json()
        
        if convert_data.get("success"):
            output_path = convert_data.get("output_path", "output/draft.tex")
            return f"✅ 转换成功！\n\n输出文件: {output_path}\n\n{convert_data.get('message', '')}"
        else:
            error_msg = convert_data.get("error", convert_data.get("message", "未知错误"))
            return f"❌ 转换失败: {error_msg}"
            
    except requests.exceptions.ConnectionError:
        return "❌ 无法连接到 API 服务器，请确保 FastAPI 后端正在运行 (http://localhost:8000)"
    except requests.exceptions.Timeout:
        return "❌ 请求超时，转换可能需要较长时间，请稍后重试"
    except Exception as e:
        return f"❌ 发生错误: {str(e)}"

def create_ui() -> gr.Blocks:
    """
    创建 Gradio Web UI
    
    Returns:
        Gradio Blocks 对象
    """
    # 获取可用的期刊列表
    available_journals = get_available_journals()
    
    # 自定义 CSS
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-header {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 30px;
    }
    """
    
    with gr.Blocks(title="AutoLaTeX - LaTeX智能排版专家") as demo:
        # 标题
        gr.Markdown(
            """
            # 📝 AutoLaTeX - LaTeX智能排版专家
            
            将 Word/Txt/Markdown 格式的论文自动转换为符合期刊要求的 LaTeX 格式
            """,
            elem_classes=["main-header"]
        )
        
        # 标签页
        with gr.Tabs():
            # 标签页1：知识库搜索
            with gr.Tab("🔍 知识库搜索"):
                gr.Markdown("### 搜索期刊模板信息")
                gr.Markdown("输入期刊或会议名称，搜索相关的 LaTeX 模板信息和排版要求。")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        journal_input = gr.Dropdown(
                            label="期刊/会议名称",
                            choices=available_journals,
                            value=None,
                            allow_custom_value=True,
                            info="从下拉列表中选择或输入自定义期刊名称"
                        )
                        search_btn = gr.Button("🔍 搜索", variant="primary")
                    
                search_output = gr.Textbox(
                    label="搜索结果",
                    lines=15,
                    interactive=False,
                    placeholder="搜索结果将显示在这里..."
                )
                
                search_btn.click(
                    fn=search_knowledge_base,
                    inputs=journal_input,
                    outputs=search_output
                )
                
                # 示例
                gr.Markdown("### 💡 支持的期刊/会议示例")
                gr.Markdown("""
                - **国际会议**: NeurIPS, CVPR, ICML, ICLR, AAAI, KDD, ACL, WWW, SIGGRAPH
                - **国际期刊**: IEEE, ACM, Nature
                - **中文期刊**: 计算机学报, 软件学报, 中国科学, 自动化学报, 电子学报, 通信学报
                """)
            
            # 标签页2：论文转换
            with gr.Tab("📄 论文转换"):
                gr.Markdown("### 上传并转换论文")
                gr.Markdown("上传您的 Word/Txt/Markdown 格式论文，选择目标期刊，系统将自动转换为 LaTeX 格式。")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(
                            label="上传论文文件",
                            file_types=[".docx", ".txt", ".md"],
                            type="filepath"
                        )
                        journal_input_convert = gr.Dropdown(
                            label="目标期刊/会议名称",
                            choices=available_journals,
                            value=None,
                            allow_custom_value=True,
                            info="从下拉列表中选择或输入自定义期刊名称"
                        )
                        topic_input = gr.Textbox(
                            label="论文主题（可选）",
                            placeholder="例如: 深度学习, 计算机视觉",
                            value=""
                        )
                        convert_btn = gr.Button("🚀 开始转换", variant="primary")
                    
                convert_output = gr.Textbox(
                    label="转换结果",
                    lines=10,
                    interactive=False,
                    placeholder="转换结果将显示在这里..."
                )
                
                convert_btn.click(
                    fn=upload_and_convert,
                    inputs=[file_input, journal_input_convert, topic_input],
                    outputs=convert_output
                )
                
                gr.Markdown("### ⚠️ 注意事项")
                gr.Markdown("""
                - 支持的文件格式: `.docx`, `.txt`, `.md`
                - 转换过程可能需要几分钟，请耐心等待
                - 确保 FastAPI 后端服务正在运行
                - 转换结果将保存在 `output/` 目录
                """)
            
            # 标签页3：使用说明
            with gr.Tab("📖 使用说明"):
                gr.Markdown("### AutoLaTeX 使用指南")
                
                gr.Markdown("""
                ## 🎯 功能说明
                
                AutoLaTeX 是一个智能论文排版系统，可以将 Word/Txt/Markdown 格式的论文自动转换为符合各种期刊要求的 LaTeX 格式。
                
                ## 📋 主要功能
                
                ### 1. 知识库搜索
                - 搜索各种期刊和会议的 LaTeX 模板信息
                - 查看模板的文档类、关键宏包、格式要求等
                - 支持中英文期刊/会议
                
                ### 2. 论文转换
                - 上传 Word/Txt/Markdown 格式的论文文件
                - 选择目标期刊/会议
                - 自动转换为符合要求的 LaTeX 格式
                
                ## 🔧 API 端点
                
                ### 知识库搜索
                ```
                POST /api/v1/knowledge/search
                Body: {"journal_name": "期刊名称"}
                ```
                
                ### 论文转换
                ```
                POST /api/v1/paper/convert
                Body: {
                    "file_path": "文件路径",
                    "journal_name": "期刊名称",
                    "topic": "论文主题（可选）"
                }
                ```
                
                ### 文件上传
                ```
                POST /api/v1/paper/upload
                Form Data: file (文件)
                ```
                
                ## 🚀 启动服务
                
                ### 方式1：使用启动脚本（推荐）
                ```bash
                python start_services.py
                ```
                
                ### 方式2：分别启动
                ```bash
                # 终端1：启动 FastAPI 后端
                python run_api.py
                
                # 终端2：启动 Gradio Web UI
                python run_ui.py
                ```
                
                ## 📍 服务地址
                
                - **FastAPI 后端**: http://localhost:8000
                - **Gradio Web UI**: http://localhost:7860
                - **API 文档**: http://localhost:8000/docs
                
                ## ⚠️ 注意事项
                
                1. 确保端口 8000 和 7860 未被占用
                2. 首次运行会自动初始化知识库（可能需要几秒钟）
                3. 转换过程可能需要较长时间，请耐心等待
                4. 确保已安装所有依赖: `pip install -r requirements.txt`
                
                ## 📚 支持的期刊/会议
                
                ### 国际会议
                - NeurIPS, CVPR, ICML, ICLR, AAAI
                - KDD, ACL, WWW, SIGGRAPH
                
                ### 国际期刊
                - IEEE, ACM, Nature
                
                ### 中文期刊
                - 计算机学报, 软件学报, 中国科学
                - 自动化学报, 电子学报, 通信学报
                - 计算机研究与发展, 中文信息学报
                - 模式识别与人工智能
                
                ## 🐛 问题排查
                
                1. **无法连接到 API**: 确保 FastAPI 后端正在运行
                2. **文件上传失败**: 检查文件格式和大小
                3. **转换失败**: 查看错误信息，检查文件内容格式
                4. **知识库搜索无结果**: 尝试使用不同的期刊名称或缩写
                """)
        
        # 页脚
        gr.Markdown(
            """
            ---
            **AutoLaTeX** - LaTeX智能排版专家 | 版本 1.0.0
            """,
            elem_classes=["footer"]
        )
    
    return demo
