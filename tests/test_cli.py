from pathlib import Path

from pvi import __version__
from pvi import cli


def test_main_prints_version_with_short_flag(capsys) -> None:
    exit_code = cli.main(["-v"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == __version__


def test_main_prints_version_with_long_flag(capsys) -> None:
    exit_code = cli.main(["--version"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == __version__


def test_get_help_file_path_prefers_bundled_help(monkeypatch, tmp_path) -> None:
    fake_cli_file = tmp_path / "cli.py"
    fake_cli_file.write_text("# test", encoding="utf-8")
    bundled_help = tmp_path / "help.md"
    bundled_help.write_text("# bundled", encoding="utf-8")

    monkeypatch.setattr(cli, "__file__", str(fake_cli_file))

    assert cli.get_help_file_path() == bundled_help.resolve()


def test_main_help_launches_readonly_help_file(monkeypatch) -> None:
    called: dict[str, object] = {}

    class FakeEditor:
        def __init__(self, **kwargs):
            called.update(kwargs)

        def run(self) -> None:
            called["ran"] = True

    monkeypatch.setattr(cli, "TuiVimLikeEditor", FakeEditor)
    monkeypatch.setattr(cli, "get_help_file_path", lambda: Path("README.md").resolve())

    exit_code = cli.main(["--help"])

    assert exit_code == 0
    assert called["ran"] is True
    assert called["open_path"] == Path("README.md").resolve()
    assert called["start_help_preview"] is True


def test_main_help_falls_back_to_builtin_text(monkeypatch) -> None:
    called: dict[str, object] = {}

    class FakeEditor:
        def __init__(self, **kwargs):
            called.update(kwargs)

        def run(self) -> None:
            called["ran"] = True

    monkeypatch.setattr(cli, "TuiVimLikeEditor", FakeEditor)
    monkeypatch.setattr(cli, "get_help_file_path", lambda: Path("missing-readme-xyz.md"))

    exit_code = cli.main(["--help"])

    assert exit_code == 0
    assert called["ran"] is True
    assert "startup_text" in called
    assert "README.md 不存在" in str(called["startup_text"])
    assert called["startup_language"] == "markdown"
    assert called["start_help_preview"] is True


def test_main_missing_path_returns_error(capsys) -> None:
    exit_code = cli.main(["not-exists-123456"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "路径不存在" in captured.err


def test_main_hides_hidden_files_by_default(monkeypatch) -> None:
    called: dict[str, object] = {}

    class FakeEditor:
        def __init__(self, **kwargs):
            called.update(kwargs)

        def run(self) -> None:
            called["ran"] = True

    monkeypatch.setattr(cli, "TuiVimLikeEditor", FakeEditor)

    exit_code = cli.main([])

    assert exit_code == 0
    assert called["ran"] is True
    assert called["show_hidden_files"] is False


def test_main_can_show_hidden_files_by_flag(monkeypatch) -> None:
    called: dict[str, object] = {}

    class FakeEditor:
        def __init__(self, **kwargs):
            called.update(kwargs)

        def run(self) -> None:
            called["ran"] = True

    monkeypatch.setattr(cli, "TuiVimLikeEditor", FakeEditor)

    exit_code = cli.main(["--show-hidden"])

    assert exit_code == 0
    assert called["ran"] is True
    assert called["show_hidden_files"] is True