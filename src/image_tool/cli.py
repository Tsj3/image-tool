"""命令行入口。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import ImageToolError, read_image_info


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
