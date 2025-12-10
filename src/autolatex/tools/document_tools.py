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
    description: str = "解析文档文件，将完整内容保存为JSON文件，并返回文件路径和元数据摘要。"

    def _run(self, file_path: str) -> str:
        """
        解析文档 -> 保存 JSON 到磁盘 -> 返回路径。
        避免直接返回巨大的字符串给 LLM。
        """
        # 1. 路径处理
        file_path = os.path.abspath(file_path)
        print(f"[DocumentParserTool] 正在处理文件: {file_path}")

        if not os.path.exists(file_path):
            return f"Error: 文件不存在: {file_path}"

        # 2. 获取扩展名并选择解析器
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        parser_func = _PARSER_MAP.get(ext)
        
        if parser_func is None:
            return f"Error: 当前版本暂不支持 {ext} 文件解析。"

        try:
            # 3. 执行解析 (这里会生成巨大的字典)
            parsed_dict: Dict[str, Any] = parser_func(file_path)

            # 4. 验证 Schema (可选，建议保留)
            # schema = load_document_schema()
            # if not validate_parsed_document(parsed_dict, schema):
            #     return "Error: 解析结果未能通过 Schema 验证。"

            # 5. 【关键步骤】：将结果保存到文件，而不是直接返回
            # 生成输出文件名：原文件名_parsed.json
            dir_name = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(dir_name, f"{base_name}_parsed.json")

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_dict, f, ensure_ascii=False, indent=2)

            print(f"[DocumentParserTool] 解析结果已保存至: {output_path}")

            # 6. 【关键步骤】：构造轻量级的返回信息
            # 只返回路径和元数据，Token 占用极小
            response = {
                "status": "success",
                "message": "文档解析成功，内容过长已保存为独立文件。",
                "saved_json_path": output_path, # Agent 需要这个路径
                "metadata": parsed_dict.get("metadata", {}) # 让 Agent 知道标题和摘要即可
            }

            return json.dumps(response, ensure_ascii=False)

        except Exception as e:
            return f"Error: 解析过程中发生错误: {str(e)}"