"""
模板检索工具模块

提供从模板管理器检索期刊模板文件的功能。
"""

from crewai.tools import BaseTool  # type: ignore

from .template_manager import get_journal_template_files


class TemplateRetrievalTool(BaseTool):
    """模板检索工具，支持从期刊模板文件夹或单个模板文件读取。"""

    name: str = "期刊模板读取工具"
    description: str = "根据模板名称（例如 'ieee_conference' 或 'cvpr'），读取并返回对应的LaTeX模板文件。支持单个文件或整个模板文件夹。"

    def _run(self, template_name: str) -> str:
        """
        读取模板文件或模板文件夹。
        
        Args:
            template_name: 模板名称，应该是期刊名称（如 'cvpr', 'ieee' 等）
                          -> 从 src/autolatex/templates/journals/ 读取
        
        Returns:
            模板文件内容字符串，如果是文件夹则返回主要文件内容
        """
        # 尝试作为期刊文件夹模板读取
        try:
            template_files = get_journal_template_files(template_name)
            if template_files:
                # 如果有多个文件，优先返回主文件（main.tex, _main.tex 等）
                for key in ["_main.tex", "main.tex", "cvpr_header.tex"]:
                    if key in template_files:
                        return template_files[key]
                # 如果没有主文件，返回第一个文件
                return list(template_files.values())[0]
        except FileNotFoundError:
            pass
        
        # 如果找不到模板，返回错误信息
        return f"错误：找不到名为 {template_name} 的模板目录。请确保模板存在于 src/autolatex/templates/journals/{template_name}/"


# 向后兼容：保留 TemplateTools 作为别名
TemplateTools = TemplateRetrievalTool