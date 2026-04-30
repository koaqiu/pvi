from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


SUPPORTED_PLATFORMS = {
    "Windows": "windows",
    "Linux": "linux",
    "Darwin": "macos",
}

TREE_SITTER_HIDDEN_IMPORTS = [
    "tree_sitter_bash",
    "tree_sitter_css",
    "tree_sitter_go",
    "tree_sitter_html",
    "tree_sitter_java",
    "tree_sitter_javascript",
    "tree_sitter_json",
    "tree_sitter_markdown",
    "tree_sitter_python",
    "tree_sitter_regex",
    "tree_sitter_rust",
    "tree_sitter_sql",
    "tree_sitter_toml",
    "tree_sitter_xml",
    "tree_sitter_yaml",
]

COLLECT_ALL_PACKAGES = [
    "textual",
    "tree_sitter",
    *TREE_SITTER_HIDDEN_IMPORTS,
]


def normalize_platform(name: str) -> str:
    if name not in SUPPORTED_PLATFORMS:
        raise ValueError(f"不支持的平台: {name}")
    return SUPPORTED_PLATFORMS[name]


def current_platform() -> str:
    return normalize_platform(platform.system())


def ensure_native_build(target_platform: str, host_platform: str | None = None) -> None:
    host = host_platform or current_platform()
    if target_platform != host:
        raise SystemExit(
            f"PyInstaller 不能跨平台交叉构建。当前主机为 {host}，目标为 {target_platform}，"
            "请在目标平台上执行打包。"
        )


def build_pyinstaller_command(
    project_root: Path,
    target_platform: str,
    python_executable: Path | None = None,
) -> list[str]:
    entry_file = project_root / "__main__.py"
    help_file = project_root / "src" / "pvi" / "help.md"
    dist_dir = project_root / "dist" / target_platform
    work_dir = project_root / "build" / "pyinstaller" / target_platform
    data_separator = ";" if target_platform == "windows" else ":"

    python_bin = python_executable or Path(sys.executable)

    return [
        str(python_bin),
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "pvi",
        "--paths",
        str(project_root / "src"),
        "--add-data",
        f"{help_file}{data_separator}pvi",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir),
        *[
            item
            for package in COLLECT_ALL_PACKAGES
            for item in ("--collect-all", package)
        ],
        *[
            item
            for module in TREE_SITTER_HIDDEN_IMPORTS
            for item in ("--hidden-import", module)
        ],
        str(entry_file),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="构建 pvi 单文件可执行程序")
    parser.add_argument(
        "--target-platform",
        choices=["windows", "linux", "macos"],
        default=current_platform(),
        help="目标平台；PyInstaller 不支持跨平台交叉构建",
    )
    args = parser.parse_args(argv)

    ensure_native_build(args.target_platform)

    project_root = Path(__file__).resolve().parent
    command = build_pyinstaller_command(project_root, args.target_platform)
    subprocess.run(command, cwd=project_root, check=True)

    output_name = "pvi.exe" if args.target_platform == "windows" else "pvi"
    print(project_root / "dist" / args.target_platform / output_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())