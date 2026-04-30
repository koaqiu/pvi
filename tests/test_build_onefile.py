from pathlib import Path

import pytest

import build_onefile


def test_build_command_uses_windows_data_separator(tmp_path: Path) -> None:
    command = build_onefile.build_pyinstaller_command(
        tmp_path,
        "windows",
        python_executable=Path("C:/Python/python.exe"),
    )

    add_data_value = command[command.index("--add-data") + 1]

    assert add_data_value.endswith("help.md;pvi")


def test_build_command_uses_linux_data_separator(tmp_path: Path) -> None:
    command = build_onefile.build_pyinstaller_command(
        tmp_path,
        "linux",
        python_executable=Path("/usr/bin/python3"),
    )

    add_data_value = command[command.index("--add-data") + 1]

    assert add_data_value.endswith("help.md:pvi")


def test_build_command_uses_macos_data_separator(tmp_path: Path) -> None:
    command = build_onefile.build_pyinstaller_command(
        tmp_path,
        "macos",
        python_executable=Path("/usr/bin/python3"),
    )

    add_data_value = command[command.index("--add-data") + 1]

    assert add_data_value.endswith("help.md:pvi")


def test_cross_platform_build_is_rejected() -> None:
    with pytest.raises(SystemExit, match="不能跨平台交叉构建"):
        build_onefile.ensure_native_build("windows", host_platform="linux")


def test_normalize_platform_supports_macos() -> None:
    assert build_onefile.normalize_platform("Darwin") == "macos"


def test_build_command_includes_tree_sitter_hidden_imports(tmp_path: Path) -> None:
    command = build_onefile.build_pyinstaller_command(tmp_path, "windows")

    assert "--hidden-import" in command
    assert "tree_sitter_markdown" in command
    assert "tree_sitter_python" in command


def test_build_command_collects_textual_and_tree_sitter_assets(tmp_path: Path) -> None:
    command = build_onefile.build_pyinstaller_command(tmp_path, "windows")

    assert "--collect-all" in command
    assert "textual" in command
    assert "tree_sitter" in command