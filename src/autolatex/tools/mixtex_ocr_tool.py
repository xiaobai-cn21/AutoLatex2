"""
MixTex OCR API 工具

通过 HTTP 调用本地/远程的 MixTex FastAPI `/predict` 接口，将图片转为 LaTeX。
"""

from __future__ import annotations

import os
import mimetypes
from typing import Type

import requests
from crewai.tools import BaseTool  # type: ignore
from pydantic import BaseModel, Field


class MixTexOCRToolInput(BaseModel):
    """MixTex OCR 工具输入参数。"""

    image_path: str = Field(
        ...,
        description="待识别图片的路径（绝对路径或相对项目根目录）",
    )
    max_length: int = Field(
        512,
        description="生成 LaTeX 的最大 token 长度，默认 512，可根据图片复杂度调大",
    )
    enhance: bool = Field(
        True,
        description="是否启用图片增强预处理，默认开启",
    )


class MixTexOCRTool(BaseTool):
    """
    调用已启动的 MixTex OCR FastAPI 服务，将图片转换为 LaTeX 代码。
    默认请求地址可通过环境变量 `MIXTEX_OCR_API_URL` 配置，未设置时使用
    `http://localhost:8001/predict`。
    """

    name: str = "MixTex OCR Tool"
    description: str = (
        "调用本地/远程 MixTex OCR FastAPI 的 /predict 接口，"
        "上传图片后返回识别得到的 LaTeX 代码。"
    )
    args_schema: Type[BaseModel] = MixTexOCRToolInput
    api_url: str = Field(
        default="http://localhost:8001/predict",
        description="OCR API 服务地址"
    )

    def __init__(self, api_url: str | None = None, **kwargs):
        # 确定 API URL：优先使用参数，其次环境变量，最后默认值
        final_api_url = (
            api_url
            or os.getenv("MIXTEX_OCR_API_URL")
            or "http://localhost:8001/predict"
        )
        super().__init__(api_url=final_api_url, **kwargs)

    def _run(self, image_path: str, max_length: int = 512, enhance: bool = True) -> str:
        abs_image_path = os.path.abspath(image_path)
        if not os.path.exists(abs_image_path):
            return f"错误：图片不存在 - {abs_image_path}"

        # FastAPI 对 form bool 使用 "true"/"false" 字符串即可正确解析
        form_data = {
            "max_length": str(max_length),
            "enhance": "true" if enhance else "false",
        }

        try:
            # 根据文件扩展名确定正确的 MIME 类型
            mime_type, _ = mimetypes.guess_type(abs_image_path)
            if not mime_type or not mime_type.startswith('image/'):
                # 如果无法识别，根据扩展名手动设置
                ext = os.path.splitext(abs_image_path)[1].lower()
                mime_map = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.bmp': 'image/bmp',
                    '.webp': 'image/webp',
                }
                mime_type = mime_map.get(ext, 'image/png')  # 默认使用 PNG
            
            with open(abs_image_path, "rb") as f:
                files = {
                    "file": (
                        os.path.basename(abs_image_path),
                        f,
                        mime_type,
                    )
                }
                resp = requests.post(self.api_url, data=form_data, files=files, timeout=60)
        except Exception as e:  # pragma: no cover - 主要用于运行时错误提示
            return f"调用 MixTex OCR API 失败：{e}"

        if resp.status_code != 200:
            return f"调用失败（HTTP {resp.status_code}）：{resp.text}"

        try:
            payload = resp.json()
        except ValueError:
            return f"API 返回非 JSON 内容：{resp.text}"

        if not payload.get("success", False):
            return f"识别失败：{payload.get('message', '未知错误')}"

        latex = payload.get("latex")
        if not latex:
            return "API 响应中未找到 LaTeX 字段。"

        return latex


