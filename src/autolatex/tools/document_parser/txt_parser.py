"""TXT 文档解析器：使用启发式规则生成符合 document_schema 的数据。"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple, Optional


def _split_sections(text: str) -> Tuple[str, str]:
    """将文本分割为主体内容和参考文献部分。"""
    pattern = re.compile(r"^(?:参考文献|References)\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return text.strip(), ""
    return text[: match.start()].strip(), text[match.end() :].strip()


def _is_noise_line(line: str) -> bool:
    """判断是否是噪声行（页眉/页脚/页码等）。"""
    stripped = line.strip()
    
    # 空行
    if not stripped:
        return False
    
    # 只有页码
    if re.match(r"^\d+$", stripped):
        return True
    
    # 长分割线
    if re.match(r"^[-=_]{5,}$", stripped):
        return True
    
    # 包含期刊名+年份+页码的典型页眉格式
    if re.search(r"\b\d{4}\b.*\b\d+\s*$", stripped) and len(stripped) < 100:
        return True
    
    return False


def _parse_metadata(lines: List[str], full_text: str) -> Dict[str, Any]:
    """解析元数据，支持中英文双语摘要和关键词。"""
    metadata = {
        "title": "",
        "authors": [],
        "abstract": "",
        "abstract_zh": "",
        "abstract_en": "",
        "keywords": [],
        "keywords_zh": [],
        "keywords_en": []
    }
    
    if lines:
        metadata["title"] = lines[0].strip()

    # 解析作者
    author_line = ""
    for line in lines[1:5]:
        if any(key in line for key in ["作者", "Author", "Authors"]):
            author_line = line
            break
    if author_line:
        author_line = re.sub(r"(作者|Author|Authors)\s*[:：]", "", author_line).strip()
        names = [name.strip() for name in re.split(r"[;,，、]", author_line) if name.strip()]
        metadata["authors"] = [{"name": name, "affiliation": "", "email": ""} for name in names]

    # 解析中文摘要
    abstract_zh_match = re.search(
        r"(?:摘\s*要)\s*[:：]?\s*(.*?)(?:\n\s*\n|\n关键词|\nAbstract|\Z)",
        full_text,
        re.DOTALL,
    )
    if abstract_zh_match:
        metadata["abstract_zh"] = abstract_zh_match.group(1).strip()

    # 解析英文摘要
    abstract_en_match = re.search(
        r"(?:Abstract)\s*[:：]?\s*(.*?)(?:\n\s*\n|\nKeywords|\n关键词|\Z)",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if abstract_en_match:
        metadata["abstract_en"] = abstract_en_match.group(1).strip()

    # 合并摘要（优先使用英文）
    metadata["abstract"] = metadata["abstract_en"] or metadata["abstract_zh"]

    # 解析中文关键词
    keywords_zh_match = re.search(
        r"(?:关键词)\s*[:：]?\s*(.*?)(?:\n\s*\n|\nKeywords|\n\d+\.\s|\Z)",
        full_text,
        re.DOTALL,
    )
    if keywords_zh_match:
        keywords_str = keywords_zh_match.group(1).strip()
        metadata["keywords_zh"] = [kw.strip() for kw in re.split(r"[;,，、]", keywords_str) if kw.strip()]

    # 解析英文关键词
    keywords_en_match = re.search(
        r"(?:Keywords)\s*[:：]?\s*(.*?)(?:\n\s*\n|\n关键词|\n\d+\.\s|\Z)",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if keywords_en_match:
        keywords_str = keywords_en_match.group(1).strip()
        metadata["keywords_en"] = [kw.strip() for kw in re.split(r"[;,，、]", keywords_str) if kw.strip()]

    # 合并关键词
    metadata["keywords"] = metadata["keywords_en"] or metadata["keywords_zh"]

    return metadata


def _is_list_line(line: str) -> bool:
    """判断是否是列表项行。"""
    return bool(re.match(r"^\s*(?:[-*•]|\d+[\.\)]|\([0-9a-zA-Z]+\))\s+", line))


def _is_code_fence(line: str) -> bool:
    """判断是否是代码围栏标记。"""
    return line.strip().startswith("```")


def _extract_code_language(line: str) -> str:
    """从代码围栏行提取语言标识。"""
    match = re.match(r"^```(\w+)", line.strip())
    return match.group(1) if match else ""


def _is_caption(text: str) -> bool:
    """判断是否是图表标题。"""
    return bool(re.match(r"^\s*(?:Figure|Fig\.|Table|表|图)\s*\d+", text, re.IGNORECASE))


def _is_blockquote_line(line: str) -> bool:
    """判断是否是引用块行。"""
    return line.strip().startswith(">")


def _is_ascii_table(text: str) -> bool:
    """判断是否是ASCII表格。"""
    lines = text.split('\n')
    if len(lines) < 2:
        return False
    
    # 检查是否有多行包含竖线
    pipe_lines = sum(1 for line in lines if '|' in line)
    # 检查是否有分隔行（包含+和-）
    separator_lines = sum(1 for line in lines if '+' in line and '-' in line)
    
    return pipe_lines >= 2 and separator_lines >= 1


def _guess_heading_level(text: str) -> Tuple[bool, int, str]:
    """
    判断是否是标题，并推断层级和编号。
    返回: (是否是标题, 层级, 编号)
    """
    stripped = text.strip()
    
    # 检查数字编号标题（如：1.1 研究背景）
    number_match = re.match(r"^(\d+(?:\.\d+)*)\s+(.+)", stripped)
    if number_match:
        number = number_match.group(1)
        level = number.count(".") + 1
        return True, level, number
    
    # 检查罗马数字标题（如：I. INTRODUCTION）
    roman_match = re.match(r"^([IVX]+)\.\s+(.+)", stripped, re.IGNORECASE)
    if roman_match and stripped.isupper():
        return True, 1, roman_match.group(1)
    
    # 检查全大写短标题（如：INTRODUCTION）
    if len(stripped) < 80 and stripped.isupper() and not re.search(r"[.!?]$", stripped):
        return True, 1, ""
    
    return False, 0, ""


def _detect_formula_block(text: str) -> Optional[str]:
    """
    检测是否是块级公式，返回公式内容。
    """
    # 检查 $$ ... $$ 格式
    match = re.match(r"^\s*\$\$\s*(.*?)\s*\$\$\s*$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 检查 \[ ... \] 格式
    match = re.match(r"^\s*\\\[\s*(.*?)\s*\\\]\s*$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return None


def _extract_inline_formulas(text: str) -> List[str]:
    """提取行内公式（$...$格式）。"""
    # 匹配 $...$，但排除 $$
    formulas = re.findall(r"(?<!\$)\$(?!\$)([^$]+)\$(?!\$)", text)
    return [f.strip() for f in formulas]


def _extract_reference_markers(text: str) -> List[str]:
    """提取行内引用标记。"""
    markers = []
    
    # 数字型引用：[1], [1,2], [1-3]
    numeric_refs = re.findall(r"\[[0-9,\-\s]+\]", text)
    markers.extend(numeric_refs)
    
    # 作者-年份型引用：(Smith, 2020), (Smith et al., 2020)
    author_year_refs = re.findall(r"\([A-Z][A-Za-z\s,\.]+\d{4}[a-z]?\)", text)
    markers.extend(author_year_refs)
    
    return markers


def _parse_content(main_text: str) -> List[Dict[str, Any]]:
    """
    使用逐行状态机解析正文内容。
    支持：列表、代码块、ASCII表格、caption、blockquote、公式、标题等。
    """
    blocks: List[Dict[str, Any]] = []
    lines = main_text.split('\n')
    
    buffer: List[str] = []
    current_type: Optional[str] = None
    code_language: str = ""
    in_code_block: bool = False
    
    def flush_buffer():
        """将缓冲区内容转换为块并添加到结果中。"""
        nonlocal buffer, current_type, code_language
        
        if not buffer:
            return
        
        text = "\n".join(buffer).strip()
        if not text:
            buffer = []
            current_type = None
            return
        
        # 根据类型处理
        if current_type == "list_item":
            # 提取列表项内容（去除前导标记）
            items = []
            for line in buffer:
                # 去除 "1. ", "- ", "* " 等标记
                item_text = re.sub(r"^\s*(?:[-*•]|\d+[\.\)]|\([0-9a-zA-Z]+\))\s+", "", line)
                items.append(item_text)
            
            # 判断是有序还是无序列表
            first_line = buffer[0] if buffer else ""
            ordered = bool(re.match(r"^\s*\d+[\.\)]", first_line))
            
            blocks.append({"type": "list", "ordered": ordered, "items": items})
            
        elif current_type == "code":
            blocks.append({"type": "code", "language": code_language, "text": text})
            code_language = ""
            
        elif current_type == "blockquote":
            # 去除每行的 > 前缀
            quote_text = "\n".join(line.lstrip('>').strip() for line in buffer)
            blocks.append({"type": "quote", "text": quote_text})
            
        else:
            # 默认处理为段落，但需要进一步分类
            
            # 检查是否是ASCII表格
            if _is_ascii_table(text):
                blocks.append({"type": "table", "format": "ascii", "raw": text})
            
            # 检查是否是块级公式
            elif formula := _detect_formula_block(text):
                blocks.append({"type": "formula_block", "latex": formula})
            
            # 检查是否是caption
            elif _is_caption(text):
                blocks.append({"type": "caption", "text": text})
            
            # 检查是否是标题
            elif (is_heading := _guess_heading_level(text))[0]:
                _, level, number = is_heading
                blocks.append({
                    "type": "heading",
                    "level": level,
                    "number": number,
                    "text": text
                })
            
            # 普通段落
            else:
                blocks.append({"type": "paragraph", "text": text})
                
                # 提取行内公式
                inline_formulas = _extract_inline_formulas(text)
                for formula in inline_formulas:
                    blocks.append({"type": "formula_inline", "latex": formula})
                
                # 提取引用标记
                ref_markers = _extract_reference_markers(text)
                for marker in ref_markers:
                    blocks.append({"type": "reference_marker", "marker": marker})
        
        buffer = []
        current_type = None
    
    # 逐行扫描
    for line in lines:
        stripped = line.strip()
        
        # 过滤噪声行
        if _is_noise_line(line):
            continue
        
        # 处理代码块围栏
        if _is_code_fence(line):
            if in_code_block:
                # 结束代码块
                flush_buffer()
                in_code_block = False
            else:
                # 开始代码块
                flush_buffer()
                in_code_block = True
                current_type = "code"
                code_language = _extract_code_language(line)
            continue
        
        # 在代码块内部
        if in_code_block:
            buffer.append(line)
            continue
        
        # 处理空行（作为自然分隔符）
        if not stripped:
            flush_buffer()
            continue
        
        # 处理引用块
        if _is_blockquote_line(line):
            if current_type != "blockquote":
                flush_buffer()
                current_type = "blockquote"
            buffer.append(line)
            continue
        
        # 处理列表
        if _is_list_line(line):
            if current_type != "list_item":
                flush_buffer()
                current_type = "list_item"
            buffer.append(line)
            continue
        
        # 处理缩进代码块（4空格或Tab开头）
        if line.startswith("    ") or line.startswith("\t"):
            if current_type != "code":
                flush_buffer()
                current_type = "code"
                code_language = ""
            buffer.append(line)
            continue
        
        # 如果当前在处理列表或blockquote，但遇到非相关行，结束当前块
        if current_type in ["list_item", "blockquote"]:
            flush_buffer()
        
        # 普通文本行
        if current_type is None:
            current_type = "paragraph"
        buffer.append(line)
    
    # 处理最后剩余的内容
    flush_buffer()
    
    return blocks


def _parse_bibliography(text: str) -> List[Dict[str, Any]]:
    """
    解析参考文献，支持多种编号格式。
    """
    bibliography: List[Dict[str, Any]] = []
    if not text:
        return bibliography
    
    # 先尝试按空行分割
    items = re.split(r"\n\s*\n", text)
    
    # 如果只有一个条目但文本很长，说明没有空行分隔，需要按编号行分割
    if len(items) == 1 and len(text) > 100:
        # 按照参考文献编号的起始位置分割
        lines = text.split('\n')
        current_entry = []
        
        for line in lines:
            # 检查是否是新的参考文献条目的开始
            if re.match(r"^\[(\d+(?:[,\-]\d+)*)\]|^(\d+)[\.\)]|^\((\d+)\)", line.strip()):
                # 如果已经有累积的条目，先保存
                if current_entry:
                    items.append('\n'.join(current_entry))
                current_entry = [line]
            else:
                # 继续累积当前条目
                if current_entry or line.strip():  # 跳过开头的空行
                    current_entry.append(line)
        
        # 保存最后一个条目
        if current_entry:
            items.append('\n'.join(current_entry))
    
    # 解析每个条目
    for item in items:
        entry = item.strip()
        if not entry:
            continue
        
        bib_id = ""
        # 扩展的编号格式匹配：[1], 1., 1), (1)
        id_match = re.match(r"^\[(\d+(?:[,\-]\d+)*)\]|^(\d+)[\.\)]|^\((\d+)\)", entry)
        if id_match:
            # 取第一个非None的组
            bib_id = id_match.group(1) or id_match.group(2) or id_match.group(3)
        
        bibliography.append(
            {
                "id": bib_id,
                "type": "misc",
                "authors": [],
                "title": "",
                "venue": "",
                "year": "",
                "raw": entry,
            }
        )
    
    return bibliography


def parse_txt_to_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as txt_file:
        lines = txt_file.readlines()
    full_text = "".join(lines)

    metadata = _parse_metadata(lines, full_text)
    main_text, bibliography_text = _split_sections(full_text)
    content_blocks = _parse_content(main_text)
    bibliography = _parse_bibliography(bibliography_text)

    if not bibliography:
        bibliography.append(
            {
                "id": "",
                "type": "misc",
                "authors": [],
                "title": "",
                "venue": "",
                "year": "",
                "raw": "",
            }
        )

    return {"metadata": metadata, "content": content_blocks, "bibliography": bibliography}

