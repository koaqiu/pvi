from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pvi import __version__
from pvi.app import TuiVimLikeEditor


def parse_startup_path(argv: list[str]) -> Path | None:
    """解析启动参数，返回原始路径（若存在）。"""
    return Path(argv[0]).expanduser().resolve() if argv else None


def get_help_file_path() -> Path:
    """返回帮助文件路径，优先使用包内资源以兼容单文件打包。"""
    bundled_help = Path(__file__).resolve().with_name("help.md")
    if bundled_help.is_file():
        return bundled_help
    return Path(__file__).resolve().parents[2] / "README.md"


def get_fallback_help_text() -> str:
    """当 README 不存在时使用的内置帮助文本。"""
    return (
        "# pvi help\n\n"
        "README.md 不存在，已回退到内置帮助。\n\n"
        "## 基本操作\n"
        "- 左侧文件树选择文件后回车打开\n"
        "- Ctrl+N 新建缓冲区\n"
        "- Ctrl+S 保存当前文件\n"
        "- F1 显示帮助\n"
        "- F10 切换全屏（隐藏文件区）\n"
        "- Ctrl+F 搜索，F3/Shift+F3 跳转\n"
        "- F6 切换主题\n"
        "- Ctrl+Q 退出\n"
    )


def read_markdown_file(path: Path) -> str:
    """读取 Markdown 文件内容。"""
    return path.read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pvi",
        description="pvi TUI editor",
        add_help=False,
    )
    parser.add_argument("path", nargs="?", help="要打开的文件或目录路径")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本并退出")
    parser.add_argument("--help", action="store_true", dest="show_help", help="打开帮助文件")
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="在左侧文件树中显示隐藏文件和目录",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.show_help:
        help_file = get_help_file_path()
        if help_file.is_file():
            TuiVimLikeEditor(
                open_path=help_file,
                open_dir=help_file.parent,
                start_help_preview=True,
                show_hidden_files=args.show_hidden,
            ).run()
        else:
            TuiVimLikeEditor(
                startup_text=get_fallback_help_text(),
                startup_language="markdown",
                startup_title="[内置帮助]",
                start_help_preview=True,
                show_hidden_files=args.show_hidden,
            ).run()
        return 0

    path = parse_startup_path([args.path] if args.path else [])
    if path is None:
        TuiVimLikeEditor(show_hidden_files=args.show_hidden).run()
        return 0
    elif path.is_dir():
        TuiVimLikeEditor(open_dir=path, show_hidden_files=args.show_hidden).run()
        return 0
    elif path.is_file():
        TuiVimLikeEditor(
            open_path=path,
            open_dir=path.parent,
            show_hidden_files=args.show_hidden,
        ).run()
        return 0
    else:
        print(f"错误：路径不存在: {path}", file=sys.stderr)
        return 1
