import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from crewai.tools import BaseTool

class LaTeXCompilerTool(BaseTool):
    name: str = "LaTeX Compiler and Debugger Tool"
    description: str = (
        "编译 LaTeX 项目。注意：不再接受代码字符串。"
        "它会自动从 'output/temp_source' 读取上一步生成的源代码，"
        "并结合指定的模版进行编译。"
        "Args: template_dir_path (模版文件夹名称，如 'CVPR')"
    )

    def _run(self, template_dir_path: Optional[str] = None, **kwargs) -> str:
        """
        Args:
            template_dir_path: 模版子文件夹名称
            **kwargs: 吞掉 Agent 可能错误传入的 latex_content 参数，防止报错
        """
        
        # ================= 1. 动态路径配置 =================
        try:
            # 定位项目根目录 (E:\Python项目\NLP3\autolatex)
            current_file = Path(__file__).resolve()
            # 根据文件结构 src/autolatex/tools/latex_tools.py 回溯
            project_root = current_file.parents[3] 
            
            # 定义关键路径 (全部转为 str 以防兼容性问题)
            BASE_TEMPLATE_ROOT = str(project_root / "模板")
            PROJECT_OUTPUT_DIR = str(project_root / "output")
            SOURCE_CODE_ROOT = str(project_root / "output" / "temp_source") # Agent 写代码的地方
            
        except Exception as e:
            return f"System Error: 路径配置失败 - {str(e)}"
        # ==================================================

        print(f"\n--- [LaTeX Tool] 开始编译任务 ---")
        
        # 2. 解析模版路径 (如果有)
        abs_template_path = None
        if template_dir_path:
            clean_name = template_dir_path.replace("/", "\\").strip("\\").strip()
            # 容错：去除可能的前缀
            if clean_name.lower().startswith("templates\\"):
                clean_name = clean_name.replace("templates\\", "")
            
            candidate = os.path.join(BASE_TEMPLATE_ROOT, clean_name)
            abs_template_path = os.path.abspath(candidate)
            
            if not os.path.exists(abs_template_path):
                return f"Error: 找不到模版 '{clean_name}' (路径: {abs_template_path})"

        # 3. 创建临时编译沙盒 (Temp Dir)
        job_id = str(uuid.uuid4())[:8]
        work_dir = os.path.join(tempfile.gettempdir(), f"autotex_build_{job_id}")
        os.makedirs(work_dir, exist_ok=True)
        
        try:
            # ================= 4. 文件准备 (合并模版与源码) =================
            
            # A. 先复制模版 (底座)
            if abs_template_path:
                print(f"DEBUG: 加载模版文件: {abs_template_path}")
                shutil.copytree(abs_template_path, work_dir, dirs_exist_ok=True)
            
            # B. 再复制生成的源码 (覆盖)
            # 这是关键！Agent 写的 main.tex 和 sec/ 文件夹在 SOURCE_CODE_ROOT 里
            if os.path.exists(SOURCE_CODE_ROOT) and os.listdir(SOURCE_CODE_ROOT):
                print(f"DEBUG: 加载生成的源代码: {SOURCE_CODE_ROOT}")
                shutil.copytree(SOURCE_CODE_ROOT, work_dir, dirs_exist_ok=True)
            else:
                # 如果硬盘里没代码，检查是否 Agent 依然通过参数传了 (兼容旧逻辑)
                fallback_content = kwargs.get('latex_content')
                if fallback_content:
                    print("DEBUG: ⚠️ 警告：使用参数传入的代码 (建议改用硬盘写入)")
                    with open(os.path.join(work_dir, "main.tex"), "w", encoding="utf-8") as f:
                        f.write(fallback_content)
                else:
                    return "Error: 找不到源代码！请确保 latex_generation_task 已成功写入 output/temp_source。"

            # ================= 5. 执行完整编译链 (关键修改) =================
            
            # 定义基础命令
            cmd_pdflatex = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", "main.tex"]
            cmd_bibtex = ["bibtex", "main"] # 注意：bibtex 不需要加 .tex 或 .aux 后缀

            print("DEBUG: [Pass 1/4] 初次编译 pdflatex...")
            run_command(cmd_pdflatex, work_dir)

            # 检查是否有参考文献文件 main.bib
            # 如果有，才执行 bibtex 链条
            if os.path.exists(os.path.join(work_dir, "main.bib")):
                print("DEBUG: [Pass 2/4] 检测到 main.bib，执行 bibtex...")
                bib_result = run_command(cmd_bibtex, work_dir)
                
                # 如果 bibtex 报错，记录一下但不强制退出（有时候有警告也能出结果）
                if bib_result.returncode != 0:
                    print(f"Warning: Bibtex warning/error: {bib_result.stdout}")

                print("DEBUG: [Pass 3/4] 再次编译 pdflatex (以此链接参考文献)...")
                run_command(cmd_pdflatex, work_dir)

                print("DEBUG: [Pass 4/4] 最终编译 pdflatex (修正引用序号)...")
                final_result = run_command(cmd_pdflatex, work_dir)
            else:
                print("DEBUG: 未检测到 main.bib，跳过参考文献处理。")
                final_result = run_command(cmd_pdflatex, work_dir) # 再跑一次确保页码正确

            # 将最后一次的结果赋值给 result，供后续检查使用
            result = final_result
            
            # ================= 6. 结果处理 (宽容模式) =================
            
            pdf_filename = "main.pdf"
            pdf_full_path = os.path.join(work_dir, pdf_filename)
            
            # 只要 PDF 存在，就视为成功
            if os.path.exists(pdf_full_path):
                os.makedirs(PROJECT_OUTPUT_DIR, exist_ok=True)
                final_pdf_name = f"result_{job_id}.pdf"
                final_pdf_path = os.path.join(PROJECT_OUTPUT_DIR, final_pdf_name)
                
                shutil.copy(pdf_full_path, final_pdf_path)
                
                msg = f"SUCCESS: 编译成功！PDF 已保存: {final_pdf_path}"
                if result.returncode != 0:
                    msg += f"\n(Note: 编译含警告 ReturnCode={result.returncode}，但不影响阅读)"
                return msg
            
            else:
                # ================= 7. 失败尸检 (保存源码) =================
                os.makedirs(PROJECT_OUTPUT_DIR, exist_ok=True)
                failed_src_path = os.path.join(PROJECT_OUTPUT_DIR, f"debug_failed_{job_id}.tex")
                
                # 尝试保存 main.tex 供调试
                src_main = os.path.join(work_dir, "main.tex")
                if os.path.exists(src_main):
                    shutil.copy(src_main, failed_src_path)
                    saved_msg = f"源码已保存至: {failed_src_path}"
                else:
                    saved_msg = "无法保存源码"

                logs = result.stdout.splitlines()[-20:]
                log_str = "\n".join(logs)
                
                return f"COMPILATION FAILED (No PDF). {saved_msg}\nLogs:\n{log_str}"

        except Exception as e:
            return f"System Error: {str(e)}"
            
        finally:
            # 调试时可注释掉清理
            # shutil.rmtree(work_dir, ignore_errors=True)
            pass


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