import json
import os
from typing import Any, Dict

try:
    from crewai_tools import BaseTool  # type: ignore
except ImportError:  # pragma: no cover
    class BaseTool:  # type: ignore
        """Fallback BaseTool 用于本地测试。"""

        name: str = ""
        description: str = ""

        def __init__(self, *args, **kwargs):
            pass

        def _run(self, *args, **kwargs):
            raise NotImplementedError("BaseTool fallback does not implement _run.")

try:
    from .docx_parser import parse_docx_to_json
    from .schema_validator import load_document_schema, validate_parsed_document
except ImportError:  # pragma: no cover
    from docx_parser import parse_docx_to_json  # type: ignore
    from schema_validator import (  # type: ignore
        load_document_schema,
        validate_parsed_document,
    )

# ------------------- 接口定义 -------------------

class DocumentParserTool(BaseTool):
    name: str = "Document Parser Tool"
    description: str = "解析 Word, Markdown, 或 Txt 文件，返回其结构化的 JSON 内容。"

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext != ".docx":
            raise NotImplementedError("当前版本仅支持 .docx 文件解析。")

        parsed_dict: Dict[str, Any] = parse_docx_to_json(file_path)

        schema = load_document_schema()
        is_valid = validate_parsed_document(parsed_dict, schema)
        if not is_valid:
            raise ValueError("解析结果未能通过 Schema 验证，请检查文档结构。")

        return json.dumps(parsed_dict, ensure_ascii=False)


class LaTeXCompilerTool(BaseTool):
    name: str = "LaTeX Compiler and Debugger Tool"
    description: str = "编译一个 .tex 文件。如果成功，返回 PDF 路径；如果失败，返回完整的编译错误日志。"

    def _run(self, latex_file_path: str) -> str:
        # 这是 B 同学需要实现的部分
        # 1. 准备一个安全的 Docker 沙箱环境
        # 2. 将 latex_file_path 和相关模板文件挂载到容器中
        # 3. 在容器内执行 pdflatex 或 xelatex 命令
        # 4. 检查返回值。如果成功 (返回码 0)，找到 .pdf 文件并返回其路径
        # 5. 如果失败，读取 .log 文件的内容并返回
        
        # 示例实现:
        print(f"--- [工具模拟] 正在编译: {latex_file_path} ---")
        # 模拟编译失败的情况
        return "编译错误: ! Undefined control sequence. l.15 \\includegraphics"