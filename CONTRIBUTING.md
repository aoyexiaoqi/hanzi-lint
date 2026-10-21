# 贡献指南 / Contributing

感谢你愿意参与！Thanks for contributing!

## 开发环境

```bash
git clone https://github.com/aoyexiaoqi/hanzi-lint.git
cd hanzi-lint
python -m venv .venv && . .venv/bin/activate
pip install -e '.[test]'
pytest --cov=hanzi_lint
```

## 新增规则

1. 在 `src/hanzi_lint/rules.py` 中写一个生成 `(start, end, replacement, message)` 的函数，并注册到 `RULES`。
2. 在 `tests/test_rules.py` 中添加错误示例、修复结果和不应误报的正例。
3. 在 README 的规则表中补充说明。

## 提交 PR

- 保持每个 PR 聚焦一件事，附上测试。
- 确保 `pytest` 全部通过，并用 `hanzi-lint README.md` 检查文档。
- 报告误报时，请附上原文片段和期望结果。

Bug reports and PRs in English are equally welcome.
