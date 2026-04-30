from pathlib import Path

from pvi.app import is_hidden_or_noise_path


def test_hidden_checker_treats_noise_dirs_as_hidden(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    visible = project_dir / "main.py"
    visible.write_text("print('ok')\n", encoding="utf-8")

    noise_dir = project_dir / "__pycache__"
    noise_dir.mkdir()
    node_modules_dir = project_dir / "node_modules"
    node_modules_dir.mkdir()
    git_dir = project_dir / ".git"
    git_dir.mkdir()

    assert is_hidden_or_noise_path(visible) is False
    assert is_hidden_or_noise_path(noise_dir) is True
    assert is_hidden_or_noise_path(node_modules_dir) is True
    assert is_hidden_or_noise_path(git_dir) is True


def test_hidden_checker_recognizes_dot_names(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    hidden_file = project_dir / ".env"
    hidden_file.write_text("KEY=VALUE\n", encoding="utf-8")

    assert is_hidden_or_noise_path(hidden_file) is True
