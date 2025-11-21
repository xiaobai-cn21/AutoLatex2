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
    from .latex_compiler import compile_latex_to_pdf, cleanup_temp_dir
    from .md_parser import parse_md_to_json
    from .schema_validator import load_document_schema, validate_parsed_document
    from .txt_parser import parse_txt_to_json
except ImportError:  # pragma: no cover
    from docx_parser import parse_docx_to_json  # type: ignore
    from latex_compiler import compile_latex_to_pdf, cleanup_temp_dir  # type: ignore
    from md_parser import parse_md_to_json  # type: ignore
    from schema_validator import (  # type: ignore
        load_document_schema,
        validate_parsed_document,
    )
    from txt_parser import parse_txt_to_json  # type: ignore

# ------------------- 接口定义 -------------------

class DocumentParserTool(BaseTool):
    name: str = "Document Parser Tool"
    description: str = "解析 Word, Markdown, 或 Txt 文件，返回其结构化的 JSON 内容。"

    def _run(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == ".docx":
            parsed_dict: Dict[str, Any] = parse_docx_to_json(file_path)
        elif ext == ".md":
            parsed_dict = parse_md_to_json(file_path)
        elif ext == ".txt":
            parsed_dict = parse_txt_to_json(file_path)
        else:
            raise NotImplementedError(f"当前版本暂不支持 {ext} 文件解析。")

        schema = load_document_schema()
        is_valid = validate_parsed_document(parsed_dict, schema)
        if not is_valid:
            raise ValueError("解析结果未能通过 Schema 验证，请检查文档结构。")

        return json.dumps(parsed_dict, ensure_ascii=False)


class LaTeXCompilerTool(BaseTool):
    name: str = "LaTeX Compiler and Debugger Tool"
    description: str = "编译一个 .tex 文件。如果成功，返回 PDF 路径；如果失败，返回完整的编译错误日志。"

    def _run(self, latex_content: str, journal_template_files_json: str = "{}") -> str:
        try:
            templates = json.loads(journal_template_files_json)
        except json.JSONDecodeError as exc:
            raise ValueError("journal_template_files_json 不是有效的 JSON 字符串。") from exc

        result = compile_latex_to_pdf(latex_content, templates)
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