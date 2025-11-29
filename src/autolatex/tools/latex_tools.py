"""
LaTeX 编译工具模块

提供将 LaTeX 内容编译为 PDF 的 CrewAI 工具接口。
"""

import json
import os

from crewai.tools import BaseTool  # type: ignore

from .latex_compiler import compile_latex_to_pdf, cleanup_temp_dir


class LaTeXCompilerTool(BaseTool):
    """LaTeX 编译和调试工具。"""

    name: str = "LaTeX Compiler and Debugger Tool"
    description: str = "编译一个 .tex 文件。如果成功，返回 PDF 路径；如果失败，返回完整的编译错误日志。"

    def _run(self, latex_content: str, template_dir_path: str) -> str:
        """
        编译 LaTeX 内容为 PDF。

        Args:
            latex_content: LaTeX 源代码内容
            template_dir_path: 宿主机上的模板文件夹绝对路径，将被复制到编译环境中

        Returns:
            JSON 字符串，包含编译结果：
            - 成功时：{"message": "PDF 编译成功。", "pdf_path": "...", "temp_dir": "..."}
            - 失败时：{"message": "LaTeX 编译失败", "error_log": "..."}

        Raises:
            ValueError: template_dir_path 为空或不是绝对路径
            FileNotFoundError: 模板目录不存在
        """
        if not template_dir_path:
            raise ValueError("template_dir_path 不能为空。")
        if not os.path.isabs(template_dir_path):
            raise ValueError("template_dir_path 必须是宿主机上的绝对路径。")
        if not os.path.isdir(template_dir_path):
            raise FileNotFoundError(f"模板目录不存在: {template_dir_path}")

        result = compile_latex_to_pdf(latex_content, template_dir_path)
        if result.success:
            response = {
                "message": "PDF 编译成功。",
                "pdf_path": result.pdf_path,
                "temp_dir": result.temp_dir,
            }
            return json.dumps(response, ensure_ascii=False)

        if result.temp_dir:
            cleanup_temp_dir(result.temp_dir)
        return json.dumps(
            {"message": "LaTeX 编译失败", "error_log": result.error_log},
            ensure_ascii=False,
        )

