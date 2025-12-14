import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from crewai.tools import BaseTool

# 辅助函数：执行命令
def run_command(cmd, work_dir):
    return subprocess.run(
        cmd,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

class LaTeXCompilerTool(BaseTool):
    name: str = "LaTeX Compiler and Debugger Tool"
    description: str = (
        "编译 LaTeX 项目。自动从 'output/temp_source' 读取源代码，"
        "并结合模版和图片资源进行编译。"
        "Args: template_dir_path (模版文件夹名称)"
    )

    def _run(self, template_dir_path: Optional[str] = None, **kwargs) -> str:
        """
        Args:
            template_dir_path: 模版子文件夹名称
            **kwargs: 吞掉 Agent 可能错误传入的 latex_content 参数
        """
        
        # ================= 1. 动态路径配置 =================
        try:
            # 定位项目根目录
            current_file = Path(__file__).resolve()
            project_root = current_file.parents[3] 
            
            # 定义关键路径
            BASE_TEMPLATE_ROOT = str(project_root / "模板")
            PROJECT_OUTPUT_DIR = str(project_root / "output")
            SOURCE_CODE_ROOT = str(project_root / "output" / "temp_source")
            # 🔥 新增：图片资源目录
            IMAGES_SOURCE_ROOT = str(project_root / "parsed_images")
            
        except Exception as e:
            return f"System Error: 路径配置失败 - {str(e)}"
        # ==================================================

        print(f"\n--- [LaTeX Tool] 开始编译任务 ---")
        
        # 2. 解析模版路径
        abs_template_path = None
        if template_dir_path:
            clean_name = template_dir_path.replace("/", "\\").strip("\\").strip()
            if clean_name.lower().startswith("templates\\"):
                clean_name = clean_name.replace("templates\\", "")
            
            candidate = os.path.join(BASE_TEMPLATE_ROOT, clean_name)
            abs_template_path = os.path.abspath(candidate)
            
            if not os.path.exists(abs_template_path):
                return f"Error: 找不到模版 '{clean_name}' (路径: {abs_template_path})"

        # 3. 创建临时编译沙盒
        job_id = str(uuid.uuid4())[:8]
        work_dir = os.path.join(tempfile.gettempdir(), f"autotex_build_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            # ================= 4. 文件搬运 (模版 + 源码 + 图片) =================
            
            # A. 复制模版
            if abs_template_path:
                print(f"DEBUG: 加载模版文件...")
                shutil.copytree(abs_template_path, work_dir, dirs_exist_ok=True)
            
            # B. 复制源码 (覆盖)
            if os.path.exists(SOURCE_CODE_ROOT):
                print(f"DEBUG: 加载生成的源代码...")
                shutil.copytree(SOURCE_CODE_ROOT, work_dir, dirs_exist_ok=True)
            else:
                # 兼容 Agent 依然通过参数传代码的情况 (兜底)
                fallback_content = kwargs.get('latex_content')
                if fallback_content:
                    with open(os.path.join(work_dir, "main.tex"), "w", encoding="utf-8") as f:
                        f.write(fallback_content)
                else:
                    return "Error: 找不到源代码，请先运行生成任务。"

            # C. 🔥 关键修复：复制图片文件夹
            if os.path.exists(IMAGES_SOURCE_ROOT):
                print(f"DEBUG: 加载图片资源 ({IMAGES_SOURCE_ROOT})...")
                # 在编译目录下创建 parsed_images 文件夹，并把图片拷进去
                target_img_dir = os.path.join(work_dir, "parsed_images")
                shutil.copytree(IMAGES_SOURCE_ROOT, target_img_dir, dirs_exist_ok=True)
            else:
                print("DEBUG: ⚠️ 未找到 parsed_images 文件夹，若文档包含图片将编译失败。")

            # D. 自动修复路径错误 (防止 Agent 写错 bibliography 路径)
            main_tex_path = os.path.join(work_dir, "main.tex")
            if os.path.exists(main_tex_path):
                with open(main_tex_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 自动修正引用路径错误
                if "output/temp_source/main" in content:
                    print("DEBUG: 自动修复 bibliography 路径...")
                    content = content.replace("output/temp_source/main", "main")
                    with open(main_tex_path, "w", encoding="utf-8") as f:
                        f.write(content)

            # ================= 5. 执行完整编译链 =================
            
            if not os.path.exists(os.path.join(work_dir, "main.tex")):
                return "Error: 编译目录下缺少 main.tex 文件。"

            cmd_pdflatex = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", "main.tex"]
            cmd_bibtex = ["bibtex", "main"]

            print("DEBUG: [1/4] pdflatex...")
            run_command(cmd_pdflatex, work_dir)

            if os.path.exists(os.path.join(work_dir, "main.bib")):
                print("DEBUG: [2/4] bibtex...")
                run_command(cmd_bibtex, work_dir)
                print("DEBUG: [3/4] pdflatex (link)...")
                run_command(cmd_pdflatex, work_dir)
                print("DEBUG: [4/4] pdflatex (fix)...")
                result = run_command(cmd_pdflatex, work_dir)
            else:
                print("DEBUG: 无参考文献，跳过 bibtex。")
                result = run_command(cmd_pdflatex, work_dir)
            
            # ================= 6. 结果处理 =================
            
            pdf_filename = "main.pdf"
            pdf_full_path = os.path.join(work_dir, pdf_filename)
            
            if os.path.exists(pdf_full_path):
                os.makedirs(PROJECT_OUTPUT_DIR, exist_ok=True)
                final_pdf_path = os.path.join(PROJECT_OUTPUT_DIR, f"result_{job_id}.pdf")
                shutil.copy(pdf_full_path, final_pdf_path)
                
                msg = f"SUCCESS: 编译成功！PDF 已保存: {final_pdf_path}"
                if result.returncode != 0:
                    msg += f"\n(Note: 编译含警告 ReturnCode={result.returncode})"
                return msg
            else:
                # 失败尸检
                os.makedirs(PROJECT_OUTPUT_DIR, exist_ok=True)
                failed_src_path = os.path.join(PROJECT_OUTPUT_DIR, f"debug_failed_{job_id}.tex")
                if os.path.exists(main_tex_path):
                    shutil.copy(main_tex_path, failed_src_path)
                
                logs = result.stdout.splitlines()[-20:]
                return f"COMPILATION FAILED.\nLogs:\n...{chr(10).join(logs)}"

        except Exception as e:
            return f"System Error: {str(e)}"
            
        finally:
            # pass
            shutil.rmtree(work_dir, ignore_errors=True)