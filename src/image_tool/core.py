"""图片信息读取与编辑的核心函数。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


class ImageToolError(Exception):
    """用于表示可以直接展示给用户的错误。"""


# 常见颜色模式的友好名称，未列出的模式直接显示原始值。
_MODE_NAMES = {
    "1": "1 位位图 (1)",
    "L": "灰度 (L)",
    "LA": "灰度 + 透明 (LA)",
    "P": "调色板 (P)",
    "RGB": "RGB",
    "RGBA": "RGBA",
    "CMYK": "CMYK",
    "YCbCr": "YCbCr",
    "I": "32 位整型 (I)",
    "F": "32 位浮点 (F)",
}


@dataclass(frozen=True)
class ImageInfo:
    """图片的基础信息。"""

    filename: str
    format: str
    width: int
    height: int
    mode: str
    size_bytes: int

    @property
    def size_text(self) -> str:
        """文件大小的可读形式，保留两位小数。"""
        if self.size_bytes >= 1024 * 1024:
            return f"{self.size_bytes / (1024 * 1024):.2f} MB"
        return f"{self.size_bytes / 1024:.2f} KB"

    @property
    def mode_text(self) -> str:
        return _MODE_NAMES.get(self.mode, self.mode)


def _check_file(path: str | Path) -> Path:
    """检查路径存在且是普通文件，返回 Path 对象。"""
    file_path = Path(path)
    if not file_path.exists():
        raise ImageToolError(f"文件不存在：{file_path}")
    if not file_path.is_file():
        raise ImageToolError(f"路径不是文件：{file_path}")
    return file_path


def open_image(path: str | Path) -> Image.Image:
    """打开图片并完整读取，返回独立的 Pillow 图像对象。"""
    file_path = _check_file(path)
    try:
        with Image.open(file_path) as image:
            image.load()
            info = image.info.copy()
            result = image.copy()
        result.info.update(info)
        return result
    except UnidentifiedImageError as exc:
        raise ImageToolError(f"不是有效的图片文件：{file_path}") from exc
    except OSError as exc:
        raise ImageToolError(f"无法读取图片：{file_path}（{exc}）") from exc


def read_image_info(path: str | Path) -> ImageInfo:
    """读取图片的基础信息。"""
    file_path = _check_file(path)
    try:
        with Image.open(file_path) as image:
            image_format = image.format or file_path.suffix.lstrip(".").upper() or "未知"
            return ImageInfo(
                filename=file_path.name,
                format=image_format,
                width=image.width,
                height=image.height,
                mode=image.mode,
                size_bytes=file_path.stat().st_size,
            )
    except UnidentifiedImageError as exc:
        raise ImageToolError(f"不是有效的图片文件：{file_path}") from exc
    except OSError as exc:
        raise ImageToolError(f"无法读取图片：{file_path}（{exc}）") from exc
