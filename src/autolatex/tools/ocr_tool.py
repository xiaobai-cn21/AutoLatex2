"""DeepSeek OCR工具包装类，供CrewAI Agent调用。"""

from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool  # type: ignore
from pydantic import BaseModel, Field

try:
    from .ocr_handler import recognize_image_to_latex
except ImportError:  # pragma: no cover
    from ocr_handler import recognize_image_to_latex  # type: ignore


class DeepSeekOCRToolInput(BaseModel):
    """DeepSeek OCR工具的输入Schema。"""

    image_path: str = Field(
        ..., description="图片文件路径（绝对路径或相对于项目根目录的路径）"
    )


class DeepSeekOCRTool(BaseTool):
    """使用DeepSeek-OCR模型识别图片中的数学公式或表格，并转换为LaTeX代码。"""

    name: str = "DeepSeek OCR Tool"
    description: str = (
        "使用DeepSeek-OCR模型识别图片中的数学公式或表格，"
        "并将其转换为LaTeX代码。输入图片路径，返回LaTeX字符串。"
        "如果图片路径不存在或OCR识别失败，返回错误信息。"
    )
    args_schema: Type[BaseModel] = DeepSeekOCRToolInput

    def _run(self, image_path: str) -> str:
        """调用OCR处理函数并返回LaTeX代码。"""
        result = recognize_image_to_latex(image_path)
        if not result:
            return "OCR识别失败：无法从图片中提取LaTeX代码。请检查图片路径是否正确，或图片是否包含可识别的数学公式/表格。"
        return result

