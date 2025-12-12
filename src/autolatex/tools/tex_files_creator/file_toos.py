import os
from pathlib import Path
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SectionWriterInput(BaseModel):
    file_rel_path: str = Field(
        ..., 
        description="文件的相对路径，例如 'output/temp_source/sec/intro.tex'。"
    )
    content: str = Field(
        ..., 
        description="需要写入该文件的完整文本内容。"
    )

class SectionWriterTool(BaseTool):
    name: str = "Section Writer Tool"
    description: str = (
        "用于将文本内容写入项目中的指定文件。 "
        "输入路径是基于项目根目录的相对路径。"
    )
    args_schema: Type[BaseModel] = SectionWriterInput

    def _run(self, file_rel_path: str, content: str) -> str:
        """
        执行写入操作
        """
        project_root = None
        current_file = Path(__file__).resolve()

        try:
            # --- 1. 智能定位项目根目录 (最稳健的方法) ---
            # 策略：向上遍历父目录，找到那个包含 'src' 文件夹或 'pyproject.toml' 的目录
            # 这种方法比硬编码 parents[3] 更安全，哪怕你移动了脚本位置也能找到
            
            for parent in current_file.parents:
                # 检查特征：如果这个父目录下有 'src' 文件夹，且该 'src' 是个目录
                # 或者检查是否有 'pyproject.toml' (uv 项目的标准标志)
                if (parent / "src").exists() and (parent / "src").is_dir():
                    project_root = parent
                    break
                if (parent / "pyproject.toml").exists():
                    project_root = parent
                    break
            
            # 兜底：如果上面没找到，回退到硬编码逻辑 (基于你的路径结构 parents[3] 是对的)
            if project_root is None:
                # E:\...\autolatex\src\autolatex\tools\file_tools.py
                # [0]=tools, [1]=autolatex, [2]=src, [3]=ProjectRoot
                project_root = current_file.parents[3]

            print(f"DEBUG: [SectionWriter] 锁定项目根目录: {project_root}")

        except Exception as e:
            # 最后的防线：使用当前工作目录 (执行命令的地方)
            print(f"DEBUG: 路径定位出错，使用 cwd: {e}")
            project_root = Path(os.getcwd())

        # --- 2. 路径拼接 ---
        # 清洗路径，防止 Agent 传入 '/output/...' 开头的路径被识别为根目录绝对路径
        clean_rel_path = file_rel_path.strip("/").strip("\\")
        
        # 拼接：根目录 + 相对路径
        full_path = project_root / clean_rel_path

        # --- 3. 执行写入 ---
        try:
            # 确保父目录存在 (例如 'E:\...\output\temp_source\sec')
            os.makedirs(full_path.parent, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return f"SUCCESS: 已写入 {full_path}"

        except Exception as e:
            return f"ERROR: 写入文件失败。路径: {full_path}, 原因: {str(e)}"