# pvi

[![CI](https://github.com/koaqiu/pvi/actions/workflows/onefile-build.yml/badge.svg)](https://github.com/koaqiu/pvi/actions/workflows/onefile-build.yml)
[![Release](https://github.com/koaqiu/pvi/actions/workflows/release.yml/badge.svg)](https://github.com/koaqiu/pvi/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)

基于 Textual 的终端编辑器（TUI），通过 `pvi` 命令启动，支持文件树浏览、文本编辑、语法高亮和 Markdown 预览。

发布说明：PyPI 发布名为 `pvi-editor`，安装后命令仍为 `pvi`。

## 功能与 CLI 用法

当前入口为 `src/pvi/cli.py`，可通过以下方式启动：

> 命名说明：`pvi` 中 `p` 表示 Python，`vi` 表示 vi-like 的使用体验；当前项目强调“类 vi 的工具定位”，而非完整 vi 键位与行为兼容实现。

- `pvi`：启动编辑器，默认打开当前目录。
- `pvi <path>`：`path` 为目录时打开目录树；为文件时直接打开该文件。
- `pvi -v` / `pvi --version`：输出版本后退出。
- `pvi --help`：启动编辑器并只读打开随程序分发的帮助文档；开发环境下若包内帮助不存在，则回退到 `README.md` 或内置帮助文本。
- `pvi --show-hidden`：启动时显示左侧文件树中的隐藏文件与已知缓存目录。

### 参数总览

| 参数 | 默认值 | 说明 | 示例 |
| --- | --- | --- | --- |
| `path` | 空 | 要打开的文件或目录路径 | `pvi src/pvi` |
| `-v`, `--version` | `false` | 输出版本并退出 | `pvi --version` |
| `--help` | `false` | 只读打开帮助文档 | `pvi --help` |
| `--show-hidden` | `false` | 显示隐藏文件与缓存目录（如 `__pycache__`、`node_modules`、`.git`） | `pvi --show-hidden` |

### 编辑器内相关开关

- `F9`：切换左侧文件树“显示/隐藏隐藏项与缓存目录”。
- `F7`：Markdown 左右分栏（左编辑、右预览）。

语法高亮依赖说明：

- 本项目使用 `textual[syntax]`，会自动安装 `tree-sitter` 和 `tree-sitter-languages`。
- 若编辑器出现纯文本降级，可在本地虚拟环境中执行：`.\\.venv\\Scripts\\python.exe -m pip install -e .[dev]`。

## Python 版本建议

- 运行兼容范围：Python 3.9+
- 本地开发推荐：Python 3.11

选择 3.11 的原因：

- 已满足依赖要求（3.9+）
- 相比 3.12/3.13，第三方库兼容性通常更稳
- 工具链和 CI 生态成熟，适合作为 CLI 项目的默认开发版本

## 初始化本地虚拟环境

本项目使用 **pyenv-win** 管理 Python 版本，虚拟环境与 conda 完全无关。

Windows PowerShell:

```powershell
pyenv install 3.11.9   # 若已安装可跳过
pyenv local 3.11.9     # 写入 .python-version（已包含在仓库中）
pyenv exec python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

说明：当前机器默认 `python` 指向 3.13，必须通过 `pyenv exec python` 或激活 `.venv` 来使用 3.11.9。

## 常用命令

```powershell
.\.venv\Scripts\python.exe -m pvi --help
.\.venv\Scripts\python.exe -m pvi -v
.\.venv\Scripts\python.exe -m pvi --show-hidden
.\.venv\Scripts\python.exe -m pvi .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## 单文件打包

当前仓库已提供 [build_onefile.py](build_onefile.py)，使用 PyInstaller 生成单文件可执行程序。

限制说明：

- PyInstaller 不能跨平台交叉打包。
- Windows 产物必须在 Windows 上构建。
- Linux 产物必须在 Linux 上构建。
- macOS 产物必须在 macOS 上构建。

### Windows

```powershell
.\.venv\Scripts\python.exe -m pip install -e .[bundle]
.\.venv\Scripts\python.exe build_onefile.py --target-platform windows
```

输出文件：`dist/windows/pvi.exe`

### Linux

```bash
./.venv/bin/python -m pip install -e .[bundle]
./.venv/bin/python build_onefile.py --target-platform linux
```

输出文件：`dist/linux/pvi`

### macOS

```bash
./.venv/bin/python -m pip install -e .[bundle]
./.venv/bin/python build_onefile.py --target-platform macos
```

输出文件：`dist/macos/pvi`

### 打包说明

- 构建脚本会自动把 `src/pvi/help.md` 一并打进单文件程序，确保 `pvi --help` 在打包后仍可用。
- 入口使用仓库根目录的 `__main__.py`，并通过 `--paths src` 指向 `src` 布局源码。
- 如果需要同时产出 Windows、Linux、macOS 版本，应分别在对应平台机器或 CI Job 中执行上述命令。
- 仓库内置 [onefile-build.yml](.github/workflows/onefile-build.yml)：用于日常 CI（main、PR）测试与三平台构建产物校验。
- 仓库内置 [release.yml](.github/workflows/release.yml)：用于 tag 发版（`vX.Y.Z`），自动构建三平台并创建 GitHub Release 上传产物。

## 版本管理建议

建议采用“`pyproject.toml` 为版本真源 + Git Tag 作为发布锚点”的组合：

- 日常开发：以 `pyproject.toml` 的 `[project].version` 作为唯一真实版本号。
- 正式发布：打 `vX.Y.Z` 的 Git tag（例如 `v0.2.0`）。
- CI 约束：当触发 tag 构建时，工作流会校验 tag 与 `pyproject.toml` 版本完全一致。

这样做的原因：

- 规范：符合 Python 包生态（版本写在项目元数据中）。
- 实用：Git tag 适合发布追踪、回滚和生成 release artifact。
- 可审计：代码版本、构建产物、发布记录可以一一对应。

## 项目结构

```text
build_onefile.py
src/
  pvi/
    __init__.py
    __main__.py
    app.py
    cli.py
    help.md
    modals.py
tests/
  test_build_onefile.py
  test_cli.py
.github/
  workflows/
    onefile-build.yml
.vscode/
pyproject.toml
README.md
```

## 变更同步约定

- 若修改了目录或文件结构（新增、删除、重命名），需同步更新本节“项目结构”和项目级记忆。
- 若新增或变更用户可见功能，需同步更新本文档的“功能与 CLI 用法”说明。
- 若新增或变更命令行参数，需同步更新“参数总览”和“常用命令”示例。
