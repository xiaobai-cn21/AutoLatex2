import os
import shutil
import subprocess
import tempfile
import uuid
from typing import Optional
from crewai.tools import BaseTool
from pathlib import Path

class LaTeXCompilerTool(BaseTool):
    name: str = "LaTeX Compiler and Debugger Tool"
    description: str = (
        "编译 LaTeX 代码为 PDF。如果需要模版，请提供模版文件夹名称（例如 'CVPR'）。"
        "工具会自动处理模版文件的加载和编译。"
    )

    def _run(self, latex_content: str, template_dir_path: str = None) -> str:
        """
        Args:
            latex_content: 需要编译的 .tex 源代码
            template_dir_path: 模版子文件夹名称 (例如 "CVPR" 或 "IEEE")
        """
        
        # ================= 配置区域 =================
        # 1. 锁定你的项目模版根目录 (这是你的物理路径)
    

        current_file = Path(__file__).resolve()
        project_root = current_file.parents[3]
        _base_path_obj = project_root / "模板"

        
        # 3. 拼接出 "模板" 目录
        BASE_TEMPLATE_ROOT = str(_base_path_obj)
        _output_file = project_root/"output"
        OUTPUT_FILE = str(_output_file)
        # ===========================================

        print(f"\n--- [LaTeX Tool] 开始编译任务 ---")
        
        # 2. 智能解析模版路径
        abs_template_path = None
        
        if template_dir_path:
            # 清洗输入：去掉 Agent 可能误传的 / 或 \ 以及空格
            # 比如 Agent 传了 "/templates/CVPR"，我们清理成 "templates/CVPR"
            clean_name = template_dir_path.replace("/", "\\").strip("\\").strip()
            
            # 容错处理：如果 Agent 传了 "templates\CVPR"，我们要把 "templates" 去掉
            # 因为我们的根目录已经是 "...\模板" 了
            if clean_name.lower().startswith("templates\\"):
                clean_name = clean_name.replace("templates\\", "")
            
            # 拼接绝对路径
            candidate_path = os.path.join(BASE_TEMPLATE_ROOT, clean_name)
            abs_template_path = os.path.abspath(candidate_path)
            
            print(f"DEBUG: Agent输入='{template_dir_path}' -> 解析路径='{abs_template_path}'")

            # 3. 安全与存在性检查
            if not os.path.exists(abs_template_path):
                return f"Error: 找不到模版文件夹: {abs_template_path}。请确认 B 同学已经将模版放入 'E:\\Python项目\\NLP3\\autolatex\\模板' 目录中。"
            
            # 防止路径逃逸（防止 Agent 访问 E:\ 或 C:\）
            if BASE_TEMPLATE_ROOT not in abs_template_path:
                return "Error: 安全警告！禁止访问模版目录以外的路径。"

        # 4. 创建临时编译工作区 (在系统临时目录下)
        # 使用 UUID 防止文件夹冲突
        job_id = str(uuid.uuid4())[:8]
        work_dir = os.path.join(tempfile.gettempdir(), f"autotex_build_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            # 5. 复制模版文件 (如果存在)
            if abs_template_path:
                print(f"DEBUG: 正在复制模版文件...")
                # copytree 要求目标目录必须不存在，或者使用 dirs_exist_ok=True (Python 3.8+)
                shutil.copytree(abs_template_path, work_dir, dirs_exist_ok=True)
            
            # 6. 写入 main.tex
            tex_file_path = os.path.join(work_dir, "main.tex")
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(latex_content)
                
            print(f"DEBUG: 已写入 LaTeX 源码到 {tex_file_path}")

            # 7. 执行编译 (调用系统 pdflatex)
            # -interaction=nonstopmode: 出错不卡住
            # -file-line-error: 显示详细行号错误
            cmd = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", "main.tex"]
            
            # 运行命令
            result = subprocess.run(
                cmd,
                cwd=work_dir,       # 关键：在临时目录下运行
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',    # Windows 上如果乱码，可以尝试改用 'gbk'
                errors='replace'     # 防止解码错误导致崩溃
            )
            
            # 8. 检查结果
            pdf_filename = "main.pdf"
            pdf_full_path = os.path.join(work_dir, pdf_filename)
            
            # ================= 修改开始 =================
            # 8. 检查结果 (宽容模式)
            pdf_filename = "main.pdf"
            pdf_full_path = os.path.join(work_dir, pdf_filename)
            
            # 只要文件存在，就认为成功，忽略 returncode
            if os.path.exists(pdf_full_path):
                # 确保输出目录存在
                project_output_dir = project_root / "output"
                os.makedirs(project_output_dir, exist_ok=True)
                
                final_pdf_path = project_output_dir / f"result_{job_id}.pdf"
                shutil.copy(pdf_full_path, final_pdf_path)
                
                status_msg = f"SUCCESS: PDF 已生成并保存至: {final_pdf_path}"
                
                # 如果 returncode 不为 0，加个警告提示给 Agent
                if result.returncode != 0:
                    status_msg += f"\n(Warning: 编译过程有非致命错误，返回码 {result.returncode}，请检查 PDF 内容)"
                
                return status_msg
            else:
                # 真的没生成 PDF 才是失败
                logs = result.stdout.splitlines()[-20:]
                log_str = "\n".join(logs)
                return f"COMPILATION FAILED (No PDF generated).\nReturn Code: {result.returncode}\nError Logs:\n...{log_str}"
            # ================= 修改结束 =================

        except Exception as e:
            return f"System Error during compilation: {str(e)}"
            
        finally:
            # 9. 清理临时目录 (可选：调试阶段可以注释掉这一行，方便去临时目录看尸体)
            # shutil.rmtree(work_dir, ignore_errors=True)
            pass