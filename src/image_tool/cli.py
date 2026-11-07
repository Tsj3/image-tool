"""命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

from . import __version__
from .core import (
    ImageToolError,
    crop_image,
    flip_image,
    grayscale_image,
    open_image,
    read_image_info,
    resize_image,
    resolve_output_path,
    rotate_image,
    save_image,
)

# 格式名称与扩展名之间的对应关系，用于格式转换命令。
_TARGET_FORMATS = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WEBP",
    "bmp": "BMP",
}
_FORMAT_EXTENSIONS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "BMP": ".bmp",
}


def _add_output_argument(parser: argparse.ArgumentParser) -> None:
    """为子命令添加统一的输出文件参数。"""
    parser.add_argument(
        "-o",
        "--output",
        help="输出文件路径；不指定时在源文件旁生成新文件",
    )


def build_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="imagetool",
        description="读取图片信息并完成简单的图片编辑。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    info_parser = subparsers.add_parser("info", help="读取并显示图片信息")
    info_parser.add_argument("image", help="图片文件路径")
    info_parser.set_defaults(func=cmd_info)

    resize_parser = subparsers.add_parser("resize", help="缩放图片")
    resize_parser.add_argument("image", help="图片文件路径")
    resize_parser.add_argument("-w", "--width", type=int, help="目标宽度（像素）")
    resize_parser.add_argument("--height", type=int, help="目标高度（像素）")
    _add_output_argument(resize_parser)
    resize_parser.set_defaults(func=cmd_resize)

    crop_parser = subparsers.add_parser("crop", help="裁剪图片")
    crop_parser.add_argument("image", help="图片文件路径")
    crop_parser.add_argument("-l", "--left", type=int, required=True, help="裁剪区域左边界")
    crop_parser.add_argument("-t", "--top", type=int, required=True, help="裁剪区域上边界")
    crop_parser.add_argument("-r", "--right", type=int, required=True, help="裁剪区域右边界")
    crop_parser.add_argument("-b", "--bottom", type=int, required=True, help="裁剪区域下边界")
    _add_output_argument(crop_parser)
    crop_parser.set_defaults(func=cmd_crop)

    rotate_parser = subparsers.add_parser("rotate", help="旋转图片")
    rotate_parser.add_argument("image", help="图片文件路径")
    rotate_parser.add_argument(
        "-a",
        "--angle",
        type=int,
        required=True,
        help="顺时针旋转角度，例如 90、180、270",
    )
    _add_output_argument(rotate_parser)
    rotate_parser.set_defaults(func=cmd_rotate)

    flip_parser = subparsers.add_parser("flip", help="翻转图片")
    flip_parser.add_argument("image", help="图片文件路径")
    flip_parser.add_argument(
        "-d",
        "--direction",
        choices=("horizontal", "vertical", "both"),
        required=True,
        help="翻转方向：horizontal（水平）、vertical（垂直）、both（两者）",
    )
    _add_output_argument(flip_parser)
    flip_parser.set_defaults(func=cmd_flip)

    gray_parser = subparsers.add_parser("grayscale", help="把图片转换为灰度图")
    gray_parser.add_argument("image", help="图片文件路径")
    _add_output_argument(gray_parser)
    gray_parser.set_defaults(func=cmd_grayscale)

    convert_parser = subparsers.add_parser("convert", help="转换图片格式")
    convert_parser.add_argument("image", help="图片文件路径")
    convert_parser.add_argument(
        "--to",
        choices=tuple(_TARGET_FORMATS),
        required=True,
        help="目标格式",
    )
    _add_output_argument(convert_parser)
    convert_parser.set_defaults(func=cmd_convert)

    return parser


def cmd_info(args: argparse.Namespace) -> int:
    """显示图片的基础信息。"""
    info = read_image_info(args.image)
    print(f"文件名：{info.filename}")
    print(f"图片格式：{info.format}")
    print(f"宽度：{info.width} 像素")
    print(f"高度：{info.height} 像素")
    print(f"颜色模式：{info.mode_text}")
    print(f"文件大小：{info.size_text}（{info.size_bytes} 字节）")
    return 0


def _save_and_report(
    image,
    source: str,
    output: str | None,
    suffix: str,
) -> int:
    """保存处理结果并告诉用户保存位置。"""
    destination = resolve_output_path(source, output, suffix)
    saved_path = save_image(image, destination)
    print(f"已保存到：{saved_path.resolve()}")
    return 0


def cmd_resize(args: argparse.Namespace) -> int:
    """缩放图片。"""
    image = open_image(args.image)
    result = resize_image(image, width=args.width, height=args.height)
    return _save_and_report(result, args.image, args.output, "resized")


def cmd_crop(args: argparse.Namespace) -> int:
    """裁剪图片。"""
    image = open_image(args.image)
    result = crop_image(
        image,
        left=args.left,
        top=args.top,
        right=args.right,
        bottom=args.bottom,
    )
    return _save_and_report(result, args.image, args.output, "cropped")


def cmd_rotate(args: argparse.Namespace) -> int:
    """旋转图片。"""
    image = open_image(args.image)
    result = rotate_image(image, angle=args.angle)
    return _save_and_report(result, args.image, args.output, "rotated")


def cmd_flip(args: argparse.Namespace) -> int:
    """翻转图片。"""
    image = open_image(args.image)
    result = flip_image(image, direction=args.direction)
    return _save_and_report(result, args.image, args.output, "flipped")


def cmd_grayscale(args: argparse.Namespace) -> int:
    """把图片转换为灰度图。"""
    image = open_image(args.image)
    result = grayscale_image(image)
    return _save_and_report(result, args.image, args.output, "gray")


def cmd_convert(args: argparse.Namespace) -> int:
    """转换图片格式。"""
    target_format = _TARGET_FORMATS[args.to.lower()]

    # 如果用户显式指定了输出文件，检查扩展名与目标格式是否一致。
    if args.output:
        detected = Image.registered_extensions().get(Path(args.output).suffix.lower())
        if detected is not None and detected != target_format:
            raise ImageToolError(
                f"输出文件扩展名与目标格式不一致：{args.output} 对应 {detected}，"
                f"但 --to 指定的是 {target_format}。"
            )

    image = open_image(args.image)
    destination = resolve_output_path(
        args.image,
        args.output,
        "converted",
        extension=_FORMAT_EXTENSIONS[target_format],
    )
    saved_path = save_image(image, destination, target_format=target_format)
    print(f"已保存到：{saved_path.resolve()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """程序主入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except ImageToolError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
