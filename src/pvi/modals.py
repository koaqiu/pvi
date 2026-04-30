from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Markdown


class SearchModal(ModalScreen[str | None]):
    """最小搜索输入弹窗。"""

    BINDINGS = [
        Binding("escape", "cancel", "取消", priority=True, show=False),
    ]

    CSS = """
    SearchModal {
        align: center middle;
    }
    #search-panel {
        width: 70%;
        max-width: 80;
        min-width: 44;
        height: auto;
        min-height: 7;
        border: round #3b82f6;
        background: #0d1117;
        padding: 1 2;
    }
    #search-input {
        width: 100%;
        margin-top: 1;
        border: round #238636;
        background: #161b22;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="search-panel"):
            yield Label("搜索: 输入关键词后回车，Esc 取消")
            yield Input(value="", placeholder="例如: def", id="search-input")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class UnsavedChangesModal(ModalScreen[str | None]):
    """未保存变更确认弹窗。"""

    BINDINGS = [
        Binding("escape", "cancel", "取消", priority=True, show=False),
    ]

    CSS = """
    UnsavedChangesModal {
        align: center middle;
    }
    #unsaved-panel {
        width: 70%;
        max-width: 84;
        min-width: 48;
        height: auto;
        min-height: 9;
        border: round #f59e0b;
        background: #0d1117;
        padding: 1 2;
    }
    #unsaved-actions {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    #unsaved-actions Button {
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="unsaved-panel"):
            yield Label("检测到未保存修改，是否先保存？")
            with Horizontal(id="unsaved-actions"):
                yield Button("保存并继续", id="save", variant="success")
                yield Button("不保存", id="discard", variant="warning")
                yield Button("取消", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#save", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def action_cancel(self) -> None:
        self.dismiss("cancel")


class MarkdownPreviewModal(ModalScreen[None]):
    """Markdown 预览弹层，关闭后回到编辑器。"""

    BINDINGS = [
        Binding("q,escape,ctrl+q", "close", "关闭帮助", priority=True, show=False),
    ]

    CSS = """
    MarkdownPreviewModal {
        align: center middle;
    }
    #markdown-preview-panel {
        width: 90%;
        height: 90%;
        border: round #3b82f6;
        background: #0d1117;
        padding: 1 2;
    }
    #markdown-preview {
        width: 100%;
        height: auto;
    }
    #markdown-preview-scroll {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        border: round #30363d;
        padding: 0 1;
    }
    #markdown-preview-tip {
        width: 100%;
        margin-top: 1;
        color: #8b949e;
    }
    """

    def __init__(self, markdown_text: str, title: str = "帮助文档", **kwargs):
        super().__init__(**kwargs)
        self.markdown_text = markdown_text
        self.title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="markdown-preview-panel"):
            yield Label(f"预览: {self.title}")
            with VerticalScroll(id="markdown-preview-scroll"):
                yield Markdown(self.markdown_text, id="markdown-preview")
            yield Label("按 Esc / Q 关闭预览并返回编辑器", id="markdown-preview-tip")

    def on_mount(self) -> None:
        self.query_one("#markdown-preview-scroll", VerticalScroll).focus()

    def on_key(self, event: Key) -> None:
        if event.key in {"escape", "q", "ctrl+q"}:
            event.stop()
            self.action_close()

    def action_close(self) -> None:
        self.dismiss(None)
