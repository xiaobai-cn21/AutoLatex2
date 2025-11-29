"""
文档解析工具模块

提供将不同格式的文档（DOCX、Markdown、TXT）解析为结构化 JSON 的功能。
"""

import json
import os
from typing import Any, Callable, Dict

from crewai.tools import BaseTool  # type: ignore

try:
    from .document_parser import parse_docx_to_json, parse_md_to_json, parse_txt_to_json
    from .schema_validator import load_document_schema, validate_parsed_document
except ImportError:  # pragma: no cover
    from document_parser import parse_docx_to_json, parse_md_to_json, parse_txt_to_json  # type: ignore
    from schema_validator import (  # type: ignore
        load_document_schema,
        validate_parsed_document,
    )


# 文件扩展名到解析函数的映射
_PARSER_MAP: Dict[str, Callable[[str], Dict[str, Any]]] = {
    ".docx": parse_docx_to_json,
    ".md": parse_md_to_json,
    ".txt": parse_txt_to_json,
}


class DocumentParserTool(BaseTool):
    """文档解析工具，支持 DOCX、Markdown 和 TXT 格式。"""

    name: str = "Document Parser Tool"
    description: str = "解析 Word, Markdown, 或 Txt 文件，返回其结构化的 JSON 内容。"

    def _run(self, file_path: str) -> str:
        """
        解析文档文件并返回结构化的 JSON 字符串。

        Args:
            file_path: 文档文件的路径

        Returns:
            解析后的 JSON 字符串

        Raises:
            FileNotFoundError: 文件不存在
            NotImplementedError: 不支持的文件格式
            ValueError: 解析结果未能通过 Schema 验证
        """
        # 统一将传入路径转换为绝对路径，避免相对路径导致的 File Not Found 问题
        file_path = os.path.abspath(file_path)
        print(f"[DocumentParserTool] 正在处理文件: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # 根据扩展名动态选择解析函数
        parser_func = _PARSER_MAP.get(ext)
        if parser_func is None:
            raise NotImplementedError(f"当前版本暂不支持 {ext} 文件解析。")

        # 调用对应的解析函数
        parsed_dict: Dict[str, Any] = parser_func(file_path)

        # 验证解析结果
        schema = load_document_schema()
        is_valid = validate_parsed_document(parsed_dict, schema)
        if not is_valid:
            raise ValueError("解析结果未能通过 Schema 验证，请检查文档结构。")

        return json.dumps(parsed_dict, ensure_ascii=False)