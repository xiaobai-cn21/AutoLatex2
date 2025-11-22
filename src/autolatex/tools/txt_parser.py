"""TXT 文档解析器：使用启发式规则生成符合 document_schema 的数据。"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple


def _split_sections(text: str) -> Tuple[str, str]:
    pattern = re.compile(r"^(?:参考文献|References)\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return text.strip(), ""
    return text[: match.start()].strip(), text[match.end() :].strip()


def _parse_metadata(lines: List[str], full_text: str) -> Dict[str, Any]:
    metadata = {"title": "", "authors": [], "abstract": "", "keywords": []}
    if lines:
        metadata["title"] = lines[0].strip()

    author_line = ""
    for line in lines[1:5]:
        if any(key in line for key in ["作者", "Author", "Authors"]):
            author_line = line
            break
    if author_line:
        author_line = re.sub(r"(作者|Author|Authors)\s*[:：]", "", author_line).strip()
        names = [name.strip() for name in re.split(r"[;,，、]", author_line) if name.strip()]
        metadata["authors"] = [{"name": name, "affiliation": "", "email": ""} for name in names]

    abstract_match = re.search(
        r"(?:摘要|Abstract)\s*[:：]?\s*(.*?)(?:\n\s*\n|\n关键词|\nKeywords|\Z)",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if abstract_match:
        metadata["abstract"] = abstract_match.group(1).strip()

    keywords_match = re.search(
        r"(?:关键词|Keywords)\s*[:：]?\s*(.*?)(?:\n\s*\n|\n\d+\.\s|\Z)",
        full_text,
        re.IGNORECASE | re.DOTALL,
    )
    if keywords_match:
        keywords_str = keywords_match.group(1).strip()
        metadata["keywords"] = [kw.strip() for kw in re.split(r"[;,，、]", keywords_str) if kw.strip()]

    return metadata


def _parse_content(main_text: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    paragraphs = re.split(r"\n\s*\n", main_text)
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) < 80 and (para.isupper() or re.match(r"^\d+(\.\d+)*\s", para)):
            level = para.count(".") + 1 if "." in para else 1
            blocks.append({"type": "heading", "level": level, "text": para})
        else:
            blocks.append({"type": "paragraph", "text": para})
    return blocks


def _parse_bibliography(text: str) -> List[Dict[str, Any]]:
    bibliography: List[Dict[str, Any]] = []
    if not text:
        return bibliography
    items = re.split(r"\n\s*\n", text)
    for item in items:
        entry = item.strip()
        if not entry:
            continue
        bib_id = ""
        id_match = re.match(r"^\[(\d+)\]|^(\d+)\.", entry)
        if id_match:
            bib_id = id_match.group(1) or id_match.group(2)
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

