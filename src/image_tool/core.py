"""图片信息读取与编辑的核心函数。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# 兼容不同版本的 Pillow。
try:
    _LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # Pillow < 9.1
    _LANCZOS = Image.LANCZOS


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


def resize_image(
    image: Image.Image,
    width: int | None = None,
    height: int | None = None,
) -> Image.Image:
    """缩放图片；只指定宽或高时按原比例计算另一边。"""
    if width is None and height is None:
        raise ImageToolError("请至少指定宽度（--width）或高度（--height）中的一个。")
    if width is not None and width <= 0:
        raise ImageToolError("宽度必须大于 0。")
    if height is not None and height <= 0:
        raise ImageToolError("高度必须大于 0。")

    if width is None:
        width = round(image.width * height / image.height)
    elif height is None:
        height = round(image.height * width / image.width)

    # 按比例计算后至少保留 1 像素，避免出现 0 尺寸。
    width = max(1, width)
    height = max(1, height)
    return image.resize((width, height), resample=_LANCZOS)


def crop_image(
    image: Image.Image,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> Image.Image:
    """按左、上、右、下坐标裁剪图片，并检查区域是否越界。"""
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ImageToolError(
            "裁剪区域不合法："
            f"left={left}, top={top}, right={right}, bottom={bottom}，"
            f"图片尺寸为 {image.width}x{image.height}。"
            f"要求 0 <= left < right <= {image.width} 且 0 <= top < bottom <= {image.height}。"
        )
    return image.crop((left, top, right, bottom))


def _same_path(first: Path, second: Path) -> bool:
    """判断两个路径是否指向同一个文件。"""
    return first.expanduser().resolve() == second.expanduser().resolve()


def resolve_output_path(
    source: str | Path,
    output: str | Path | None,
    suffix: str,
) -> Path:
    """确定输出路径，默认在源文件旁生成不重名的新文件。"""
    source_path = Path(source)
    if output is not None:
        destination = Path(output).expanduser()
        if destination.exists() and destination.is_dir():
            raise ImageToolError(f"输出路径是一个目录，请输入文件名：{destination}")
        if _same_path(destination, source_path):
            raise ImageToolError("输出文件不能与原图相同，请换一个文件名。")
        if not destination.parent.exists():
            raise ImageToolError(f"输出目录不存在：{destination.parent}")
        return destination

    extension = source_path.suffix
    if not extension:
        raise ImageToolError("源文件没有扩展名，无法确定输出格式，请用 -o 指定输出文件。")

    destination = source_path.with_name(f"{source_path.stem}_{suffix}{extension}")
    index = 1
    while destination.exists():
        destination = source_path.with_name(f"{source_path.stem}_{suffix}_{index}{extension}")
        index += 1
    return destination


def _prepare_for_jpeg(image: Image.Image) -> Image.Image:
    """将图片转换为适合保存为 JPEG 的 RGB 模式。"""
    # 调色板图片可能通过 info 携带透明色，先展开成 RGBA。
    if image.mode == "P" and "transparency" in image.info:
        image = image.convert("RGBA")

    # 带透明通道的图片放到白色背景上，避免透明区域变黑。
    if image.mode in ("RGBA", "LA"):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    if image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image


def save_image(
    image: Image.Image,
    destination: str | Path,
    target_format: str | None = None,
) -> Path:
    """保存图片；根据扩展名推断格式，并处理透明通道转 JPEG 的情况。"""
    destination_path = Path(destination)
    image_format = target_format or Image.registered_extensions().get(
        destination_path.suffix.lower()
    )
    if image_format is None:
        raise ImageToolError(
            f"无法根据扩展名确定图片格式：{destination_path.suffix or '（无扩展名）'}。"
            "支持的格式包括 .png、.jpg、.jpeg、.webp、.bmp 等。"
        )

    prepared = _prepare_for_jpeg(image) if image_format == "JPEG" else image
    try:
        prepared.save(destination_path, format=image_format)
    except OSError as exc:
        raise ImageToolError(f"保存图片失败：{destination_path}（{exc}）") from exc
    return destination_path
