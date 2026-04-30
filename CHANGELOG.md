# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-30

### Added

- 基于 [Textual](https://github.com/Textualize/textual) 的 TUI 编辑器，命令 `pvi` 启动
- 左侧文件树浏览，支持目录与文件导航
- 文本编辑区域，带语法高亮（依赖 `textual[syntax]` / tree-sitter）
- Markdown 实时预览：`F7` 切换左右分栏模式（左编辑、右预览）
- 隐藏文件与缓存目录过滤（`__pycache__`、`node_modules`、`.git` 等），`F9` 运行时切换
- 搜索功能（模态对话框）
- 未保存更改提示对话框
- CLI 参数支持：
  - `pvi [path]`：打开目录树或直接打开指定文件
  - `pvi --version` / `pvi -v`：输出版本后退出
  - `pvi --help`：只读打开内置帮助文档
  - `pvi --show-hidden`：启动时显示隐藏文件与缓存目录
- PyInstaller 单文件打包，支持 Windows、Linux、macOS 三平台
- GitHub Actions CI/CD：tag 触发三平台自动构建与发布

[0.1.0]: https://github.com/koaqiu/pvi/releases/tag/v0.1.0
