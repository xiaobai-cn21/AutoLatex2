from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal

# ==========================================
# 1. 元数据部分 (Metadata)
# ==========================================

class Author(BaseModel):
    name: str = Field(..., description="作者姓名")
    affiliation: Optional[str] = Field(None, description="作者单位")
    email: Optional[str] = Field(None, description="作者邮箱")

class Metadata(BaseModel):
    title: str = Field(..., description="文档标题")
    authors: List[Author] = Field(..., description="作者列表")
    abstract: str = Field(..., description="摘要正文")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")

# ==========================================
# 2. 内容块部分 (Content Blocks)
# ==========================================

class HeadingBlock(BaseModel):
    type: Literal["heading"] = "heading"
    level: int = Field(..., ge=1, le=6, description="标题级别（1级为最高）")
    text: str = Field(..., description="标题文本")

class ParagraphBlock(BaseModel):
    type: Literal["paragraph"] = "paragraph"
    text: str = Field(..., description="段落文本")

class EquationBlock(BaseModel):
    type: Literal["equation"] = "equation"
    format: Literal["inline", "display"] = Field(..., description="行内公式或独立公式")
    # 这里的逻辑是：DocParser 填 image_path，OCR Agent 填 latex
    latex: Optional[str] = Field(None, description="LaTeX公式代码（OCR识别后填入）")
    image_path: Optional[str] = Field(None, description="公式图片路径（OCR识别前填入）")

class TableBlock(BaseModel):
    type: Literal["table"] = "table"
    caption: Optional[str] = Field(None, description="表格标题")
    latex: Optional[str] = Field(None, description="表格LaTeX代码")
    image_path: Optional[str] = Field(None, description="表格图片路径")
    data: Optional[List[List[str]]] = Field(None, description="表格数据二维数组")

class FigureBlock(BaseModel):
    type: Literal["figure"] = "figure"
    caption: Optional[str] = Field(None, description="图标题")
    image_path: str = Field(..., description="图片文件路径")

class CodeBlock(BaseModel):
    type: Literal["code"] = "code"
    language: Optional[str] = Field(None, description="编程语言")
    content: str = Field(..., description="代码内容")

class ReferenceBlock(BaseModel):
    type: Literal["reference"] = "reference"
    marker: str = Field(..., description="引用标记，如 '[1]'")

# 定义联合类型：这就是你 JSON Schema 里的 oneOf
ContentBlock = Union[
    HeadingBlock, 
    ParagraphBlock, 
    EquationBlock, 
    TableBlock, 
    FigureBlock, 
    CodeBlock, 
    ReferenceBlock
]

# ==========================================
# 3. 参考文献部分 (Bibliography)
# ==========================================

class BibEntry(BaseModel):
    id: str = Field(..., description="引用ID")
    type: Optional[str] = Field(None, description="文献类型")
    authors: Optional[List[str]] = Field(None, description="作者列表")
    title: Optional[str] = Field(None, description="文献标题")
    venue: Optional[str] = Field(None, description="期刊/会议名称")
    year: Optional[str] = Field(None, description="年份")
    raw: str = Field(..., description="原始参考文献文本")

# ==========================================
# 4. 根文档对象 (对应 Task 0 输出)
# ==========================================

class DocumentStructure(BaseModel):
    metadata: Metadata = Field(..., description="文档元信息")
    content_file_path: str = Field(description="解析后的完整内容 JSON 文件保存的本地绝对路径") 
    summary: str = Field(description="论文内容的简要概述")
    bibliography: List[BibEntry] = Field(..., description="参考文献列表")


class ParsedResultPath(BaseModel):
    file_path: str = Field(..., description="解析后的完整数据（Metadata+Content）所在的JSON文件绝对路径")

# ==========================================
# 5. 辅助对象 (对应 Task 1 输出)
# ==========================================

class LatexSnippet(BaseModel):
    # 这个 ID 对应 DocumentStructure.content 列表的索引（0, 1, 2...）
    # 或者对应原文中的图片文件名
    block_index: int = Field(..., description="该公式在 content 列表中的索引位置")
    latex_code: str = Field(..., description="识别后的LaTeX代码")

class EquationList(BaseModel):
    snippets: List[LatexSnippet] = Field(..., description="所有识别出的公式列表")

