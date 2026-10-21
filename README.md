# hanzi-lint

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

中文文案排版检查与自动修复命令行工具。检查中英文之间的空格、中文里误用的半角标点、全角字母数字、重复标点等常见问题，可一键修复，适合放进 CI 和 pre-commit。

[English](#english)

## 安装

```bash
pip install git+https://github.com/aoyexiaoqi/hanzi-lint.git
```

需要 Python 3.9 及以上版本，除 Python 3.9/3.10 需要 `tomli` 外无其他依赖。

## 用法

```bash
hanzi-lint README.md docs/          # 检查文件或目录（默认 .md / .markdown / .txt）
hanzi-lint --fix docs/              # 就地修复
hanzi-lint --diff README.md         # 只显示修改差异，不改文件
hanzi-lint --json docs/             # JSON 输出，方便其他工具处理
echo "在LeTV上看视频" | hanzi-lint   # 从 stdin 读取
echo "在LeTV上看视频" | hanzi-lint --fix -   # 输出修复后的文本
hanzi-lint --disable space-cjk-latin,number-percent docs/
hanzi-lint --list-rules
```

输出格式为 `路径:行:列: [规则] 说明`：

```text
docs/intro.md:3:2: [space-cjk-latin] 中英文/数字之间缺少空格
```

退出码：`0` 没有问题；`1` 发现问题（`--fix` 后仍有无法修复的问题）；`2` 参数或配置错误。

Markdown 中的代码块（```` ``` ````、`~~~`、缩进代码）、行内代码、链接地址、URL、邮箱地址、HTML 标签和 YAML front matter 会被跳过。

## 规则

| 规则 | 说明 | 错误示例 | 修复后 |
| --- | --- | --- | --- |
| `space-cjk-latin` | 中文与英文字母、数字之间加空格 | `在LeTV上看3集` | `在 LeTV 上看 3 集` |
| `halfwidth-punct` | 中文语境中使用全角标点 | `你好,世界!` `看(这里)` | `你好，世界！` `看（这里）` |
| `fullwidth-alnum` | 字母和数字使用半角 | `ＡＢＣ１２３` | `ABC123` |
| `repeated-punct` | 不重复使用标点 | `太好了！！！` | `太好了！` |
| `space-fullwidth-punct` | 全角标点两侧不加空格 | `你好 ，世界` | `你好，世界` |
| `number-percent` | 数字与 `%`、`‰`、`°` 之间不加空格 | `增长 10 %` | `增长 10%` |
| `english-punct-spacing` | 英文标点后加空格、前不加空格 | `Hello,world .` | `Hello, world.` |

规则参考了 [中文文案排版指北](https://github.com/sparanoid/chinese-copywriting-guidelines)。

## 忽略

```markdown
这一行不检查 iPhone15 <!-- hanzi-lint-disable-line -->

<!-- hanzi-lint-disable-next-line -->
下一行不检查 iPhone15

<!-- hanzi-lint-disable -->
这一段都不检查
<!-- hanzi-lint-enable -->
```

纯文本文件中同样可以使用这些标记（例如 `# hanzi-lint-disable-line`）。

## 配置

在项目根目录（或任意上级目录）放置 `.hanzi-lint.toml`：

```toml
disable = ["english-punct-spacing"]
exclude = ["CHANGELOG.md", "vendor/*"]
extensions = [".md", ".txt"]
```

也可以写在 `pyproject.toml` 的 `[tool.hanzi-lint]` 中。可用 `--config` 指定路径。

## 在 CI 中使用

GitHub Actions：

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"
- run: pip install git+https://github.com/aoyexiaoqi/hanzi-lint.git
- run: hanzi-lint docs/ README.md
```

pre-commit（`.pre-commit-config.yaml`）：

```yaml
repos:
  - repo: https://github.com/aoyexiaoqi/hanzi-lint
    rev: v0.1.0
    hooks:
      - id: hanzi-lint        # 只检查
      # - id: hanzi-lint-fix  # 自动修复
```

## 路线图 / 欢迎贡献

以下是适合新贡献者的任务（good first issue）：

- [ ] 添加 GitHub Actions CI 工作流（运行 pytest，Python 3.9–3.13）
- [ ] 支持专有名词大小写检查（如 `github` → `GitHub`、`ios` → `iOS`），词表可配置
- [ ] 检查省略号与破折号用法（`...` → `……`、`--` → `——`）
- [ ] 支持 `.rst`、`.html` 文件中的文本提取
- [ ] 输出 GitHub Actions annotations 格式（`--format github`）
- [ ] 支持繁体中文与引号风格（「」与 “”）的偏好配置
- [ ] 为规则添加按文件 glob 的单独开关
- [ ] 发布到 PyPI 并提供 VS Code 插件

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## English

**hanzi-lint** is a CLI that lints and auto-fixes Chinese copywriting typography in Markdown and plain-text files: missing spaces between CJK and Latin characters, half-width punctuation inside Chinese text, full-width letters/digits, repeated punctuation, stray spaces around full-width punctuation, `10 %` style spacing, and English punctuation spacing.

```bash
pip install git+https://github.com/aoyexiaoqi/hanzi-lint.git
hanzi-lint docs/              # check; exits 1 if issues found (CI-friendly)
hanzi-lint --fix docs/        # fix in place
hanzi-lint --diff README.md   # show a unified diff
hanzi-lint --json docs/       # machine-readable output
cat file.md | hanzi-lint      # read from stdin
```

- Code blocks, inline code, URLs, link targets, HTML tags and front matter are skipped in Markdown.
- Ignore lines with `hanzi-lint-disable-line`, `hanzi-lint-disable-next-line`, or `hanzi-lint-disable` / `hanzi-lint-enable` blocks.
- Configure with `.hanzi-lint.toml` or `[tool.hanzi-lint]` in `pyproject.toml` (`disable`, `exclude`, `extensions`).
- Works as a [pre-commit](https://pre-commit.com) hook (`hanzi-lint`, `hanzi-lint-fix`).

See the rule table above for examples. Contributions are welcome — see the roadmap and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © aoyexiaoqi
