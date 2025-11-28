"""
文档解析器模块

提供将不同格式的文档（DOCX、Markdown、TXT）解析为结构化 JSON 数据的功能。
"""

from .docx_parser import parse_docx_to_json
from .md_parser import parse_md_to_json
from .txt_parser import parse_txt_to_json

__all__ = [
    "parse_docx_to_json",
    "parse_md_to_json",
    "parse_txt_to_json",
]

