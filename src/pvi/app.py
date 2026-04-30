from __future__ import annotations

import stat
from pathlib import Path
from typing import Callable

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.document._document import Selection
from textual.widgets import DirectoryTree, Footer, Header, Label, Markdown, TextArea

from pvi.modals import MarkdownPreviewModal, SearchModal, UnsavedChangesModal


NOISE_NAMES = {
    "__pycache__",
    "node_modules",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


def is_hidden_or_noise_path(path: Path) -> bool:
    if path.name in NOISE_NAMES:
        return True

    if path.name.startswith("."):
        return True

    try:
        st = path.stat()
    except OSError:
        return False

    file_attrs = getattr(st, "st_file_attributes", 0)
    hidden_mask = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0)
    return bool(file_attrs & hidden_mask)


class ToggleHiddenDirectoryTree(DirectoryTree):
    """支持运行时切换是否显示隐藏文件/目录。"""

    def __init__(self, path: str, show_hidden: bool = False, **kwargs):
        super().__init__(path, **kwargs)
        self.show_hidden = show_hidden

    def _is_hidden_path(self, path: Path) -> bool:
        return is_hidden_or_noise_path(path)

    def filter_paths(self, paths):
        if self.show_hidden:
            return paths
        return [path for path in paths if not self._is_hidden_path(path)]

    def set_show_hidden(self, show_hidden: bool) -> None:
        self.show_hidden = show_hidden
        self.reload()


class TuiVimLikeEditor(App):
    TITLE = "现代TUI编辑器 · 基础版"
    SUB_TITLE = "文件树 + 文本编辑 + 轻量语法高亮"

    # TextArea 内置高亮主题，按顺序轮换。
    THEMES = ["vscode_dark", "monokai", "dracula", "github_light", "css"]

    # 简单语言映射：用于 TextArea 内置语法高亮。
    LANGUAGE_BY_SUFFIX = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".json": "json",
        ".md": "markdown",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".html": "html",
        ".css": "css",
        ".sh": "bash",
        ".toml": "toml",
        ".xml": "xml",
    }

    # 当目标语言在当前 Textual 运行时不可用时，做轻量降级。
    LANGUAGE_FALLBACKS = {
        "typescript": "javascript",
        "tsx": "javascript",
    }

    HELP_TEXT = (
        "# 欢迎来到现代TUI编辑器\n\n"
        "- 左侧选择文件回车打开\n"
        "- Ctrl+N 新建 / Ctrl+S 保存\n"
        "- F1 显示帮助\n"
        "- F10 切换全屏（隐藏文件区）\n"
        "- F7 切换 Markdown 分栏预览\n"
        "- F9 显示/隐藏隐藏文件\n"
        "- Ctrl+Z 撤销 / Ctrl+Y 重做\n"
        "- Esc 聚焦文件树 / Ctrl+E 回到编辑区"
    )

    BINDINGS = [
        Binding("ctrl+n", "new_file", "新建", priority=True),
        Binding("ctrl+s", "save_file", "保存文件", priority=True),
        Binding("ctrl+f", "search", "搜索", priority=True),
        Binding("f1", "show_help", "帮助", priority=True, key_display="F1"),
        Binding("f3", "find_next", "下一个", priority=True, key_display="F3"),
        Binding("shift+f3", "find_prev", "上一个", priority=True, key_display="Shift+F3"),
        Binding("f6", "cycle_theme", "切换主题", priority=True, key_display="F6"),
        Binding("tab", "tab_key", "缩进/跳词", priority=True),
        Binding("shift+tab", "focus_tree", "回到文件树", priority=True),
        Binding("ctrl+z", "undo", "撤销", priority=True),
        Binding("ctrl+y", "redo", "重做", priority=True),
        Binding("ctrl+e", "focus_editor", "聚焦编辑区", priority=True),
        Binding("f10", "toggle_fullscreen", "全屏(隐藏文件区)", priority=True, key_display="F10"),
        Binding("f7", "toggle_markdown_split", "Markdown分栏", priority=True, key_display="F7"),
        Binding("f8", "preview_markdown", "预览Markdown", priority=True, key_display="F8"),
        Binding("f9", "toggle_hidden_files", "显示隐藏项", priority=True, key_display="F9"),
        Binding("escape", "focus_tree", "回到文件树", priority=True),
        Binding("ctrl+q", "quit", "退出", priority=True),
    ]

    CSS = """
    Screen {
        background: #0f1419;
    }
    .sidebar {
        width: 28%;
        background: #161b22;
        border: round #30363d;
        margin: 1;
    }
    .editor-pane {
        width: 100%;
        height: 1fr;
        background: #0d1117;
        border: round #30363d;
        margin: 1 1 0 1;
        color: #c9d1d9;
    }
    .editor-wrap {
        width: 72%;
        height: 100%;
    }
    .status-bar {
        height: 1;
        margin: 0 1 1 1;
        padding: 0 1;
        background: #161b22;
        color: #8b949e;
    }
    Header {
        background: #238636;
        color: white;
    }
    Footer {
        background: #161b22;
        color: #8b949e;
    }
    #editor-preview-layout {
        width: 100%;
        height: 1fr;
    }
    #preview-pane {
        display: none;
        width: 0;
        margin: 1 1 0 0;
        border: round #30363d;
        background: #0d1117;
        color: #c9d1d9;
    }
    #preview-title {
        width: 100%;
        padding: 0 1;
        color: #8b949e;
    }
    #preview-body {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    #preview-scroll {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        border: round #30363d;
        padding: 0 0 1 0;
    }
    .fullscreen-mode .sidebar {
        display: none;
    }
    .fullscreen-mode .editor-wrap {
        width: 100%;
    }
    .md-split-mode .sidebar {
        display: none;
    }
    .md-split-mode .editor-wrap {
        width: 100%;
    }
    .md-split-mode .editor-pane {
        width: 50%;
        margin: 1 0 0 1;
    }
    .md-split-mode #preview-pane {
        display: block;
        width: 50%;
    }
    """

    def __init__(
        self,
        open_path: Path | None = None,
        open_dir: Path | None = None,
        force_readonly: bool = False,
        startup_text: str | None = None,
        startup_language: str | None = None,
        startup_title: str | None = None,
        start_help_preview: bool = False,
        show_hidden_files: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.open_path = open_path
        self.open_dir = (open_dir or Path(".")).resolve()
        self.force_readonly = force_readonly
        self.startup_text = startup_text
        self.startup_language = startup_language
        self.startup_title = startup_title
        self.start_help_preview = start_help_preview
        self.show_hidden_files = show_hidden_files
        self.current_file: Path | None = None
        self._saved_text = ""
        self._dirty = False
        self.search_query = ""
        self._theme_index = 0
        self._tree_open_by_enter = False
        self._readonly = False
        self._fullscreen_mode = False
        self._fullscreen_before_markdown_split = False
        self._markdown_split_mode = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ToggleHiddenDirectoryTree(
                str(self.open_dir),
                id="file-tree",
                classes="sidebar",
                show_hidden=self.show_hidden_files,
            )
            with Vertical(classes="editor-wrap"):
                with Horizontal(id="editor-preview-layout"):
                    yield TextArea(
                        self.HELP_TEXT,
                        id="editor",
                        classes="editor-pane",
                        theme="vscode_dark",
                        show_line_numbers=True,
                    )
                    with Vertical(id="preview-pane"):
                        yield Label("Markdown 实时预览", id="preview-title")
                        with VerticalScroll(id="preview-scroll"):
                            yield Markdown(self.HELP_TEXT, id="preview-body")
                yield Label("未打开文件 | Ln 1, Col 1 | 已保存", id="status", classes="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        editor = self.query_one("#editor", TextArea)
        editor.focus()
        self._set_editor_language(editor, "markdown")
        self._saved_text = editor.text
        if self.open_path is not None:
            self._open_path(self.open_path, focus_editor=True)
            if self.force_readonly:
                self._set_readonly(True)
                self._update_status()
        elif self.startup_text is not None:
            self._set_readonly(False)
            editor.text = self.startup_text
            self._set_editor_language(editor, self.startup_language)
            editor.border_title = self.startup_title or "[只读帮助]"
            self.current_file = None
            self._saved_text = editor.text
            self._dirty = False
            self._set_readonly(True)
            self._update_status((0, 0))
        else:
            self._set_readonly(True)
        self._update_status()
        if self.start_help_preview:
            self.action_preview_markdown()

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter" and self.query_one("#file-tree").has_focus:
            self._tree_open_by_enter = True

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """选中文件后加载到编辑区"""
        path = Path(event.path)
        if path.is_dir():
            return
        focus_editor = self._tree_open_by_enter
        self._tree_open_by_enter = False
        self._confirm_before_leave(lambda: self._open_path(path, focus_editor=focus_editor))

    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self._tree_open_by_enter = False

    def _set_readonly(self, value: bool) -> None:
        self._readonly = value
        self.query_one("#editor", TextArea).read_only = value

    def _open_path(self, path: Path, focus_editor: bool = True) -> None:
        editor = self.query_one("#editor", TextArea)
        try:
            text = path.read_text(encoding="utf-8")
            editor.text = text
            editor.language = self._resolve_language(path, editor.available_languages)
            editor.border_title = str(path)
            self.current_file = path
            self._saved_text = text
            self._dirty = False
            self._set_readonly(False)
            self._update_status()
            if self._markdown_split_mode:
                self._update_markdown_preview()
                self._sync_preview_scroll(0)
        except UnicodeDecodeError:
            text = path.read_bytes().decode("utf-8", errors="replace")
            editor.text = text
            editor.language = None
            editor.border_title = f"{path} [二进制/只读]"
            self.current_file = None
            self._saved_text = text
            self._dirty = False
            self._set_readonly(True)
            self._update_status()
            self.notify(f"二进制文件，只读显示：{path.name}", severity="warning")
        except Exception as e:
            editor.text = f"无法读取文件：{path}\n错误：{str(e)}"
            editor.border_title = "错误 [只读]"
            self.current_file = None
            self._saved_text = editor.text
            self._dirty = False
            self._set_readonly(True)
            self._update_status()
            self.notify(f"打开失败：{path}", severity="error")
        if focus_editor:
            editor.focus()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self._dirty = event.text_area.text != self._saved_text
        if self._markdown_split_mode:
            self._update_markdown_preview()
        self._update_status()

    def on_text_area_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        if self._markdown_split_mode:
            self._sync_preview_scroll(event.selection.end[0])
        self._update_status(event.selection.end)

    def action_new_file(self) -> None:
        self._confirm_before_leave(self._create_new_buffer)

    def _create_new_buffer(self) -> None:
        editor = self.query_one("#editor", TextArea)
        self._set_readonly(False)
        editor.text = ""
        self._set_editor_language(editor, "python")
        editor.border_title = "[未命名文件]"
        self.current_file = None
        self._saved_text = ""
        self._dirty = False
        self._update_status((0, 0))
        editor.focus()
        self.notify("已创建未命名缓冲区", severity="information")

    def _confirm_before_leave(self, continue_action: Callable[[], None]) -> None:
        if self._readonly or not self._dirty:
            continue_action()
            return

        self.push_screen(
            UnsavedChangesModal(),
            callback=lambda choice: self._handle_unsaved_choice(choice, continue_action),
        )

    def _handle_unsaved_choice(self, choice: str | None, continue_action: Callable[[], None]) -> None:
        if choice == "save":
            self.action_save_file()
            if self._dirty:
                return
            continue_action()
            return

        if choice == "discard":
            continue_action()
            return

        self.notify("已取消操作", severity="information")

    def action_save_file(self) -> None:
        """保存当前文件"""
        editor = self.query_one("#editor", TextArea)
        if self._readonly:
            self.notify("当前为只读模式，无法保存", severity="warning")
            return
        if self.current_file is None:
            self.notify("当前是未命名文件，请先从左侧打开一个文件后再保存", severity="warning")
            return
        try:
            self.current_file.write_text(editor.text, encoding="utf-8")
            self._saved_text = editor.text
            self._dirty = False
            self._update_status()
            self.notify(f"文件已保存：{self.current_file}", severity="success")
        except Exception as e:
            self.notify(f"保存失败：{str(e)}", severity="error")

    def action_undo(self) -> None:
        self.query_one("#editor", TextArea).action_undo()

    def action_redo(self) -> None:
        self.query_one("#editor", TextArea).action_redo()

    def action_quit(self) -> None:
        if isinstance(self.screen, MarkdownPreviewModal):
            self.screen.dismiss(None)
            return
        self._confirm_before_leave(self.exit)

    def action_focus_tree(self) -> None:
        """焦点切回文件树"""
        if isinstance(self.screen, (SearchModal, MarkdownPreviewModal)):
            self.screen.dismiss(None)
            return
        if self._markdown_split_mode:
            self.notify("Markdown 分栏模式下已暂时隐藏文件树，按 F7 退出分栏", severity="information")
            return
        if self._fullscreen_mode:
            self.notify("全屏模式下已隐藏文件树，按 F10 退出全屏", severity="information")
            return
        self.query_one("#file-tree").focus()

    def action_focus_editor(self) -> None:
        self.query_one("#editor", TextArea).focus()

    def _load_help_markdown(self) -> str:
        help_file = Path(__file__).resolve().with_name("help.md")
        if help_file.is_file():
            try:
                return help_file.read_text(encoding="utf-8")
            except OSError:
                pass
        return self.HELP_TEXT

    def action_show_help(self) -> None:
        self.push_screen(MarkdownPreviewModal(self._load_help_markdown(), title="帮助文档"))

    def action_preview_markdown(self) -> None:
        editor = self.query_one("#editor", TextArea)
        is_markdown = (editor.language or "") == "markdown"
        if not is_markdown:
            self.notify("当前不是 Markdown 文档", severity="information")
            return
        title = str(self.current_file) if self.current_file else (self.startup_title or "Markdown 文档")
        self.push_screen(MarkdownPreviewModal(editor.text, title=title))

    def action_toggle_hidden_files(self) -> None:
        tree = self.query_one("#file-tree", ToggleHiddenDirectoryTree)
        self.show_hidden_files = not self.show_hidden_files
        tree.set_show_hidden(self.show_hidden_files)
        state_text = "显示" if self.show_hidden_files else "隐藏"
        self.notify(f"左侧文件树已{state_text}隐藏文件/目录", severity="information")

    def _apply_layout_mode(self) -> None:
        if self._markdown_split_mode:
            self.add_class("md-split-mode")
            self.remove_class("fullscreen-mode")
            return
        self.remove_class("md-split-mode")
        if self._fullscreen_mode:
            self.add_class("fullscreen-mode")
        else:
            self.remove_class("fullscreen-mode")

    def action_toggle_fullscreen(self) -> None:
        self._fullscreen_mode = not self._fullscreen_mode
        if self._markdown_split_mode:
            self._fullscreen_before_markdown_split = self._fullscreen_mode
            state_text = "开启" if self._fullscreen_mode else "关闭"
            self.notify(
                f"已{state_text}全屏（当前处于 Markdown 分栏，将在退出分栏后生效）",
                severity="information",
            )
            return
        self._apply_layout_mode()
        state_text = "开启" if self._fullscreen_mode else "关闭"
        self.notify(f"已{state_text}全屏（隐藏文件区）", severity="information")

    def action_toggle_markdown_split(self) -> None:
        editor = self.query_one("#editor", TextArea)
        is_markdown = (editor.language or "") == "markdown"
        if not is_markdown:
            self.notify("仅支持在 Markdown 文档中开启分栏模式", severity="warning")
            return

        self._markdown_split_mode = not self._markdown_split_mode
        if self._markdown_split_mode:
            self._fullscreen_before_markdown_split = self._fullscreen_mode
            self._apply_layout_mode()
            self._update_markdown_preview()
            self._sync_preview_scroll(editor.cursor_location[0])
            self.notify("已开启 Markdown 左右分栏（编辑+预览）", severity="information")
        else:
            self._fullscreen_mode = self._fullscreen_before_markdown_split
            self._apply_layout_mode()
            if self._fullscreen_mode:
                self.notify("已退出 Markdown 分栏，回到全屏（隐藏文件区）", severity="information")
            else:
                self.notify("已退出 Markdown 分栏模式", severity="information")

        editor.focus()

    def action_search(self) -> None:
        self.push_screen(SearchModal(), callback=self._on_search_submitted)

    def _on_search_submitted(self, query: str | None) -> None:
        if query is None:
            return
        self.search_query = query
        found = self._find_and_select(query, forward=True, wrap=True)
        if not found:
            self.notify(f"未找到: {query}", severity="warning")

    def action_find_next(self) -> None:
        if not self.search_query:
            self.notify("请先 Ctrl+F 输入搜索关键词", severity="information")
            return
        if not self._find_and_select(self.search_query, forward=True, wrap=True):
            self.notify(f"未找到: {self.search_query}", severity="warning")

    def action_find_prev(self) -> None:
        if not self.search_query:
            self.notify("请先 Ctrl+F 输入搜索关键词", severity="information")
            return
        if not self._find_and_select(self.search_query, forward=False, wrap=True):
            self.notify(f"未找到: {self.search_query}", severity="warning")

    def action_tab_key(self) -> None:
        editor = self.query_one("#editor", TextArea)
        if not editor.has_focus or self._readonly:
            return
        line, col = editor.cursor_location
        lines = editor.text.splitlines()
        if line < len(lines):
            line_text = lines[line]
            # 光标位于单词内部（当前字符是标识符），且满足以下之一：
            #   1. col==0（行首第一个单词）
            #   2. 前一个字符也是标识符（光标在单词中间/末尾）
            # 这样可以避免在 "abc.efg" 中，光标因 Textual 内部归一落到 'e'（col=4）后
            # 误判为"单词内部"而继续跳词。
            char_at = line_text[col] if col < len(line_text) else ""
            prev_is_word = col > 0 and (line_text[col - 1].isalnum() or line_text[col - 1] == "_")
            if char_at.isalnum() or char_at == "_":
                if col == 0 or prev_is_word:
                    end_col = col
                    while end_col < len(line_text) and (line_text[end_col].isalnum() or line_text[end_col] == "_"):
                        end_col += 1
                    editor.cursor_location = (line, end_col)
                    return
        editor.insert("    ")

    def action_cycle_theme(self) -> None:
        editor = self.query_one("#editor", TextArea)
        available_themes = editor.available_themes
        if not available_themes:
            self.notify("当前环境没有可用主题", severity="warning")
            return

        start = self._theme_index
        chosen = None
        for offset in range(1, len(self.THEMES) + 1):
            idx = (start + offset) % len(self.THEMES)
            candidate = self.THEMES[idx]
            if candidate in available_themes:
                self._theme_index = idx
                chosen = candidate
                break

        if chosen is None:
            chosen = sorted(available_themes)[0]

        editor.theme = chosen
        self._update_status()
        self.notify(f"主题: {chosen}", severity="information")

    def _resolve_language(self, file_path: Path, available_languages: set[str]) -> str | None:
        guessed = self.LANGUAGE_BY_SUFFIX.get(file_path.suffix.lower())
        if guessed is None:
            return None
        if guessed in available_languages:
            return guessed

        fallback = self.LANGUAGE_FALLBACKS.get(guessed)
        if fallback and fallback in available_languages:
            self.notify(
                f"当前环境不支持 {guessed}，已降级为 {fallback}",
                severity="information",
            )
            return fallback

        self.notify(
            f"当前环境不支持 {guessed}，将使用 plain 显示",
            severity="warning",
        )
        return None

    def _set_editor_language(self, editor: TextArea, language: str | None) -> str | None:
        if language is None:
            editor.language = None
            return None

        available_languages = editor.available_languages
        if language in available_languages:
            editor.language = language
            return language

        fallback = self.LANGUAGE_FALLBACKS.get(language)
        if fallback and fallback in available_languages:
            editor.language = fallback
            self.notify(
                f"当前环境不支持 {language}，已降级为 {fallback}",
                severity="information",
            )
            return fallback

        editor.language = None
        self.notify(
            f"当前环境不支持 {language}，将使用 plain 显示",
            severity="warning",
        )
        return None

    def _update_markdown_preview(self) -> None:
        editor = self.query_one("#editor", TextArea)
        preview = self.query_one("#preview-body", Markdown)
        preview.update(editor.text)
        self.call_after_refresh(lambda: self._sync_preview_scroll(editor.cursor_location[0]))

    def _sync_preview_scroll(self, editor_line: int) -> None:
        if not self._markdown_split_mode:
            return
        editor = self.query_one("#editor", TextArea)
        preview_scroll = self.query_one("#preview-scroll", VerticalScroll)
        total_lines = max(1, len(editor.text.splitlines()))
        ratio = min(1.0, max(0.0, editor_line / total_lines))
        preview_scroll.scroll_to(y=preview_scroll.max_scroll_y * ratio, animate=False)

    def _location_to_index(self, text: str, location: tuple[int, int]) -> int:
        line, col = location
        lines = text.splitlines(keepends=True)
        if line >= len(lines):
            return len(text)
        return min(sum(len(lines[i]) for i in range(line)) + col, len(text))

    def _index_to_location(self, text: str, index: int) -> tuple[int, int]:
        index = max(0, min(index, len(text)))
        before = text[:index]
        line = before.count("\n")
        if "\n" in before:
            col = len(before.rsplit("\n", 1)[-1])
        else:
            col = len(before)
        return (line, col)

    def _find_and_select(self, query: str, forward: bool, wrap: bool) -> bool:
        editor = self.query_one("#editor", TextArea)
        text = editor.text
        if not query:
            return False

        anchor = editor.selection.end
        anchor_index = self._location_to_index(text, anchor)

        if forward:
            idx = text.find(query, anchor_index)
            if idx == -1 and wrap:
                idx = text.find(query, 0)
        else:
            idx = text.rfind(query, 0, anchor_index)
            if idx == -1 and wrap:
                idx = text.rfind(query)

        if idx == -1:
            return False

        start = self._index_to_location(text, idx)
        end = self._index_to_location(text, idx + len(query))
        editor.selection = Selection(start, end)
        editor.scroll_cursor_visible()
        editor.focus()
        self._update_status(end)
        return True

    def _update_status(self, cursor: tuple[int, int] | None = None) -> None:
        editor = self.query_one("#editor", TextArea)
        is_markdown = (editor.language or "") == "markdown"
        if self._markdown_split_mode and not is_markdown:
            self._fullscreen_mode = self._fullscreen_before_markdown_split
            self._markdown_split_mode = False
            self._apply_layout_mode()
        if cursor is None:
            cursor = editor.cursor_location
        line, col = cursor
        path_text = str(self.current_file) if self.current_file else "未打开文件"
        dirty_text = "[只读]" if self._readonly else ("已修改" if self._dirty else "已保存")
        language = editor.language or "plain"
        theme = editor.theme or "default"
        self.query_one("#status", Label).update(
            f"{path_text} | Ln {line + 1}, Col {col + 1} | {language} | {theme} | {dirty_text}"
        )
