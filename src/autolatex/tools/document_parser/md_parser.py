"""Markdown 文档解析器，将 .md 内容转换为符合 document_schema 的结构。"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

import markdown
import yaml
from bs4 import BeautifulSoup, NavigableString, Tag

IMAGES_DIR = os.path.join(os.getcwd(), "parsed_images")


def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _resolve_image_path(image_src: str, base_dir: str) -> str:
    """将 Markdown 图片源解析为本地路径（暂不下载远程资源）。"""
    if not image_src:
        return ""
    if image_src.startswith(("http://", "https://")):
        return image_src
    return os.path.normpath(os.path.join(base_dir, image_src))


def _parse_metadata_from_md(md_text: str) -> Tuple[Dict[str, Any], str]:
    metadata = {"title": "", "authors": [], "abstract": "", "keywords": []}
    if md_text.startswith("---"):
        parts = md_text.split("---", 2)
        if len(parts) > 2:
            front_matter_str = parts[1].strip()
            remaining_md_text = parts[2].strip()
            try:
                front_matter = yaml.safe_load(front_matter_str)
                if isinstance(front_matter, dict):
                    metadata["title"] = front_matter.get("title", "") or ""
                    authors_data = front_matter.get("authors", [])
                    if isinstance(authors_data, list):
                        for item in authors_data:
                            if isinstance(item, str):
                                metadata["authors"].append(
                                    {"name": item, "affiliation": "", "email": ""}
                                )
                            elif isinstance(item, dict):
                                metadata["authors"].append(
                                    {
                                        "name": item.get("name", ""),
                                        "affiliation": item.get("affiliation", ""),
                                        "email": item.get("email", ""),
                                    }
                                )
                    metadata["abstract"] = front_matter.get("abstract", "") or ""
                    keywords_data = front_matter.get("keywords", [])
                    if isinstance(keywords_data, str):
                        metadata["keywords"] = [
                            kw.strip() for kw in keywords_data.split(",") if kw.strip()
                        ]
                    elif isinstance(keywords_data, list):
                        metadata["keywords"] = [
                            str(kw).strip() for kw in keywords_data if str(kw).strip()
                        ]
            except yaml.YAMLError as exc:  # pragma: no cover - log warning
                print(f"Warning: Error parsing YAML Front Matter: {exc}")
            return metadata, remaining_md_text
    return metadata, md_text


def _detect_formula_block(text: str) -> Optional[str]:
    """检测是否是块级公式，返回公式内容。"""
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
    """提取行内引用标记，支持更多格式。"""
    markers = []
    
    # 数字型引用：[1], [1,2], [1-3]
    # 排除任务列表标记 [ ] 和 [x]
    numeric_refs = re.findall(r"\[(?![\sxX]\])[0-9,\-\s]+\]", text)
    markers.extend(numeric_refs)
    
    # 作者-年份型引用：(Smith, 2020), (Smith et al., 2020)
    author_year_refs = re.findall(r"\([A-Z][A-Za-z\s,\.]+\d{4}[a-z]?\)", text)
    markers.extend(author_year_refs)
    
    return markers


def _paragraph_with_references(text: str) -> List[Dict[str, Any]]:
    """
    解析段落文本，提取引用标记和公式。
    """
    blocks: List[Dict[str, Any]] = []
    
    # 检查是否是块级公式
    formula = _detect_formula_block(text)
    if formula:
        blocks.append({"type": "formula_block", "latex": formula})
        return blocks
    
    # 普通段落
    blocks.append({"type": "paragraph", "text": text})
    
    # 提取行内公式
    inline_formulas = _extract_inline_formulas(text)
    for formula in inline_formulas:
        blocks.append({"type": "formula_inline", "latex": formula})
    
    # 提取引用标记
    ref_markers = _extract_reference_markers(text)
    for marker in ref_markers:
        blocks.append({"type": "reference_marker", "marker": marker})
    
    return blocks


def _parse_heading(h_tag: Tag) -> List[Dict[str, Any]]:
    """解析标题，提取层级、编号和文本。"""
    level = int(h_tag.name[1])
    text = h_tag.get_text(strip=True)
    number = ""
    
    # 提取前缀编号（如 1.1 研究背景）
    m = re.match(r"^(\d+(?:\.\d+)*)\s+(.*)$", text)
    if m:
        number = m.group(1)
        pure_text = m.group(2)
    else:
        pure_text = text
    
    return [{
        "type": "heading",
        "level": level,
        "number": number,
        "text": pure_text,
    }]


def _parse_paragraph(p_tag: Tag) -> List[Dict[str, Any]]:
    """解析段落，处理引用标记和公式。"""
    text = p_tag.get_text(strip=True)
    if not text:
        return []
    return _paragraph_with_references(text)


def _parse_list(list_tag: Tag) -> List[Dict[str, Any]]:
    """
    递归解析列表，支持有序/无序/任务列表和嵌套。
    """
    ordered = (list_tag.name == "ol")
    items = []
    
    for li in list_tag.find_all("li", recursive=False):
        # 提取 li 主体文本（去掉内部子列表）
        sub_lists = li.find_all(["ul", "ol"], recursive=False)
        for sub in sub_lists:
            sub.extract()
        
        text = li.get_text(" ", strip=True)
        
        # 任务列表：[ ] / [x]
        checked = None
        m = re.match(r"^\s*\[(?P<flag>[ xX])\]\s*(.+)$", text)
        if m:
            checked = (m.group("flag").lower() == "x")
            text = m.group(2)
        
        # 递归处理子列表
        children = []
        for sub in sub_lists:
            child_list = _parse_list(sub)
            if child_list:
                children.extend(child_list)
        
        items.append({
            "text": text,
            "checked": checked,
            "children": children,
        })
    
    return [{
        "type": "list",
        "ordered": ordered,
        "items": items,
    }]


def _parse_code_block(pre_tag: Tag) -> List[Dict[str, Any]]:
    """从 <pre><code> 提取代码块，包含语言和内容。"""
    code = pre_tag.code or pre_tag.find("code")
    if not code:
        # 如果没有 code 标签，直接取 pre 内容
        text = pre_tag.get_text()
        return [{"type": "code", "language": "", "text": text}]
    
    # 提取语言标识
    classes = code.get("class", []) or []
    language = ""
    for c in classes:
        m = re.match(r"language-(\w+)", c)
        if m:
            language = m.group(1)
            break
    
    text = code.get_text()
    return [{
        "type": "code",
        "language": language,
        "text": text,
    }]


def _parse_table(table_tag: Tag) -> List[Dict[str, Any]]:
    """
    解析表格，区分表头和数据行。
    """
    headers: List[str] = []
    rows: List[List[str]] = []
    caption = ""
    
    # 提取 caption
    caption_tag = table_tag.find("caption")
    if caption_tag:
        caption = caption_tag.get_text(strip=True)
    
    # 提取表头
    thead = table_tag.find("thead")
    if thead:
        header_row = thead.find("tr")
        if header_row:
            headers = [cell.get_text(strip=True)
                      for cell in header_row.find_all(["th", "td"])]
    else:
        # 如果没有 thead，尝试从第一行提取
        first_row = table_tag.find("tr")
        if first_row:
            headers = [cell.get_text(strip=True)
                      for cell in first_row.find_all(["th", "td"])]
    
    # 提取数据行
    if table_tag.tbody:
        body_rows = table_tag.tbody.find_all("tr")
    else:
        all_rows = table_tag.find_all("tr")
        # 如果第一行是表头，跳过它
        body_rows = all_rows[1:] if headers and len(all_rows) > 1 else all_rows
    
    for row in body_rows:
        cells = [cell.get_text(strip=True)
                for cell in row.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    
    return [{
        "type": "table",
        "caption": caption,
        "headers": headers,
        "rows": rows,
    }]


def _parse_image(img_tag: Tag, base_dir: str) -> List[Dict[str, Any]]:
    """解析图片，提取路径和标题。"""
    src = img_tag.get("src", "")
    if not src:
        return []
    
    path = _resolve_image_path(src, base_dir)
    alt = img_tag.get("alt", "").strip()
    
    return [{
        "type": "figure",
        "path": path,
        "caption": alt,
    }]


def _parse_blockquote(bq_tag: Tag, base_dir: str) -> List[Dict[str, Any]]:
    """
    解析引用块，保留引用语义并递归解析内部内容。
    """
    children_blocks: List[Dict[str, Any]] = []
    
    for child in bq_tag.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                children_blocks.append({"type": "paragraph", "text": text})
            continue
        
        blocks = _parse_block_element(child, base_dir)
        if blocks:
            children_blocks.extend(blocks)
    
    if not children_blocks:
        return []
    
    return [{
        "type": "blockquote",
        "children": children_blocks,
    }]


def _parse_hr() -> List[Dict[str, Any]]:
    """解析水平分隔线。"""
    return [{"type": "separator"}]


def _parse_block_element(element: Tag, base_dir: str) -> List[Dict[str, Any]]:
    """
    根据 HTML 标签类型分发到具体的解析函数。
    这是核心分发器。
    """
    if not hasattr(element, "name") or not element.name:
        return []
    
    tag = element.name.lower()
    
    # 标题
    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        return _parse_heading(element)
    
    # 段落
    elif tag == "p":
        return _parse_paragraph(element)
    
    # 列表
    elif tag in {"ul", "ol"}:
        return _parse_list(element)
    
    # 代码块
    elif tag == "pre":
        return _parse_code_block(element)
    
    # 表格
    elif tag == "table":
        return _parse_table(element)
    
    # 图片
    elif tag == "img":
        return _parse_image(element, base_dir)
    
    # 引用块
    elif tag == "blockquote":
        return _parse_blockquote(element, base_dir)
    
    # 分隔线
    elif tag == "hr":
        return _parse_hr()
    
    # 其他标签，尝试作为段落处理
    else:
        text = element.get_text(strip=True)
        if text:
            return [{"type": "paragraph", "text": text}]
        return []


def _parse_content_from_md(md_text: str, base_dir: str) -> List[Dict[str, Any]]:
    """
    解析 Markdown 正文内容，使用分发器模式处理各种块级元素。
    """
    content_list: List[Dict[str, Any]] = []
    
    html_content = markdown.markdown(
        md_text, extensions=["fenced_code", "tables", "toc", "codehilite"]
    )
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body or soup
    
    for element in body.children:
        if isinstance(element, NavigableString):
            continue
        
        blocks = _parse_block_element(element, base_dir)
        if blocks:
            content_list.extend(blocks)
    
    return content_list


def _split_content_and_bibliography(md_text: str) -> Tuple[str, str]:
    pattern = re.compile(r"^(#+\s+(?:References|参考文献))", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(md_text)
    if match:
        split_idx = match.start()
        return md_text[:split_idx].strip(), md_text[split_idx:].strip()
    return md_text, ""


def _parse_bibliography_from_md(md_text: str) -> List[Dict[str, Any]]:
    """
    解析参考文献，支持多种编号格式。
    """
    bibliography: List[Dict[str, Any]] = []
    if not md_text:
        return bibliography
    
    html_content = markdown.markdown(md_text)
    soup = BeautifulSoup(html_content, "html.parser")
    references_heading = soup.find(
        ["h1", "h2", "h3", "h4", "h5", "h6"],
        string=re.compile(r"references|参考文献", re.IGNORECASE),
    )
    
    if not references_heading:
        return bibliography
    
    current = references_heading.find_next_sibling()
    all_items: List[str] = []
    
    # 收集所有条目文本
    while current:
        if getattr(current, "name", "") in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            break
        
        if current.name in {"ul", "ol"}:
            all_items.extend([li.get_text().strip() for li in current.find_all("li")])
        elif current.name == "p":
            text = current.get_text().strip()
            # 如果段落包含多个条目（每行一个），需要分割
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and re.match(r"^\[(\d+(?:[,\-]\d+)*)\]|^(\d+)[\.\)]|^\((\d+)\)", line):
                    all_items.append(line)
                elif line:
                    # 如果不是以编号开头，可能是上一条的continuation
                    if all_items:
                        all_items[-1] += " " + line
                    else:
                        all_items.append(line)
        
        current = current.find_next_sibling()
    
    # 解析每个条目
    for item in all_items:
        if not item:
            continue
        
        bib_id = ""
        # 扩展的编号格式匹配：[1], 1., 1), (1), [1-3], [1,2,5]
        id_match = re.match(r"^\[(\d+(?:[,\-]\d+)*)\]|^(\d+)[\.\)]|^\((\d+)\)", item)
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
                "raw": item,
            }
        )
    
    return bibliography


def _split_keywords_text(text: str) -> List[str]:
    return [kw.strip() for kw in re.split(r"[,\n，、;；]", text) if kw.strip()]


def _extract_keywords_from_body(md_text: str) -> List[str]:
    heading_pattern = re.compile(r"^#+\s*(keywords|关键词)\s*$", re.IGNORECASE | re.MULTILINE)
    match = heading_pattern.search(md_text)
    if match:
        section_start = match.end()
        following = md_text[section_start:]
        next_heading = re.search(r"^#+\s", following, re.MULTILINE)
        keywords_block = following[: next_heading.start()].strip() if next_heading else following.strip()
        if keywords_block:
            return _split_keywords_text(keywords_block)

    inline_pattern = re.compile(r"(?:Keywords|关键词)\s*[:：]\s*(.+)")
    inline_match = inline_pattern.search(md_text)
    if inline_match:
        return _split_keywords_text(inline_match.group(1))
    return []


def parse_md_to_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as md_file:
        md_text = md_file.read()

    metadata, remaining_md = _parse_metadata_from_md(md_text)
    if not metadata["keywords"]:
        metadata["keywords"] = _extract_keywords_from_body(remaining_md)
    content_md, bibliography_md = _split_content_and_bibliography(remaining_md)

    parsed_data: Dict[str, Any] = {
        "metadata": metadata,
        "content": _parse_content_from_md(content_md, os.path.dirname(file_path)),
        "bibliography": _parse_bibliography_from_md(bibliography_md),
    }

    if not parsed_data["bibliography"]:
        parsed_data["bibliography"].append(
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

    return parsed_data

