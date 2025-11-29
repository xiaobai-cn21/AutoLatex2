"""Markdown 文档解析器，将 .md 内容转换为符合 document_schema 的结构。"""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import markdown
import yaml
from bs4 import BeautifulSoup

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


def _paragraph_with_references(text: str) -> List[Dict[str, Any]]:
    markers = re.findall(r"\[[0-9]+\]|\([A-Za-z]+, \d{4}\)", text)
    blocks: List[Dict[str, Any]] = []
    blocks.append({"type": "paragraph", "text": text})
    for marker in markers:
        blocks.append({"type": "reference", "marker": marker})
    return blocks


def _parse_content_from_md(md_text: str, base_dir: str) -> List[Dict[str, Any]]:
    content_list: List[Dict[str, Any]] = []
    html_content = markdown.markdown(
        md_text, extensions=["fenced_code", "tables", "toc", "codehilite"]
    )
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body or soup
    for element in body.children:
        if getattr(element, "name", None) is None:
            continue
        tag = element.name.lower()
        text = element.get_text().strip()
        if not text and tag not in {"img", "table", "pre"}:
            continue
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(tag[1])
            content_list.append({"type": "heading", "level": level, "text": text})
        elif tag == "p":
            content_list.extend(_paragraph_with_references(text))
        elif tag in {"ul", "ol"}:
            for li in element.find_all("li", recursive=False):
                li_text = li.get_text().strip()
                if li_text:
                    content_list.append({"type": "paragraph", "text": li_text})
        elif tag == "table":
            caption = element.find("caption")
            caption_text = caption.get_text().strip() if caption else ""
            table_data: List[List[str]] = []
            for row in element.find_all("tr"):
                row_data = [
                    cell.get_text().strip() for cell in row.find_all(["th", "td"])
                ]
                if row_data:
                    table_data.append(row_data)
            content_list.append(
                {
                    "type": "table",
                    "caption": caption_text or "未识别表格标题",
                    "latex": "",
                    "image_path": "",
                    "data": table_data,
                }
            )
        elif tag == "pre":
            code_tag = element.find("code")
            if code_tag:
                class_attr = code_tag.get("class") or []
                language = ""
                for css_class in class_attr:
                    match = re.match(r"language-(\w+)", css_class)
                    if match:
                        language = match.group(1)
                        break
                content_list.append(
                    {
                        "type": "code",
                        "language": language,
                        "content": code_tag.get_text().strip(),
                    }
                )
        elif tag == "img":
            src = element.get("src", "")
            caption = element.get("alt", "") or ""
            image_path = _resolve_image_path(src, base_dir)
            content_list.append(
                {
                    "type": "figure",
                    "caption": caption or "未识别图片标题",
                    "image_path": image_path,
                }
            )
        elif tag == "blockquote":
            content_list.append({"type": "paragraph", "text": text})
        else:
            content_list.append({"type": "paragraph", "text": text})
    return content_list


def _split_content_and_bibliography(md_text: str) -> Tuple[str, str]:
    pattern = re.compile(r"^(#+\s+(?:References|参考文献))", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(md_text)
    if match:
        split_idx = match.start()
        return md_text[:split_idx].strip(), md_text[split_idx:].strip()
    return md_text, ""


def _parse_bibliography_from_md(md_text: str) -> List[Dict[str, Any]]:
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
    while current:
        if getattr(current, "name", "") in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            break
        items: List[str] = []
        if current.name in {"ul", "ol"}:
            items = [li.get_text().strip() for li in current.find_all("li")]
        elif current.name == "p":
            items = [current.get_text().strip()]
        for item in items:
            if not item:
                continue
            bib_id = ""
            id_match = re.match(r"^\[(\d+)\]", item)
            if id_match:
                bib_id = id_match.group(1)
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
        current = current.find_next_sibling()
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

