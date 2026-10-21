import pytest
from hanzi_lint import check_text, fix_text


def rules(text, **kw):
    return [i.rule for i in check_text(text, **kw)]


@pytest.mark.parametrize("src,expected", [
    ("在LeTV上看视频", "在 LeTV 上看视频"),
    ("共3个", "共 3 个"),
    ("增长了10 %", "增长了 10%"),
    ("提升10%的效率", "提升 10% 的效率"),
    ("你好,世界", "你好，世界"),
    ("真的吗?", "真的吗？"),
    ("注意:这里", "注意：这里"),
    ("完成.", "完成。"),
    ("太好了!!", "太好了！"),
    ("真的！！！", "真的！"),
    ("看(这里)", "看（这里）"),
    ("ＡＢＣ１２３", "ABC123"),
    ("你好 ，世界", "你好，世界"),
    ("你好， 世界", "你好，世界"),
    ("Hello,world", "Hello, world"),
    ("Hello , world .", "Hello, world."),
    ("温度20 °", "温度 20°"),
])
def test_fix(src, expected):
    assert fix_text(src) == expected
    assert check_text(src)
    assert check_text(expected) == []


@pytest.mark.parametrize("ok", [
    "在 LeTV 上看视频。",
    "Version 1.2.3 and 1,000 items.",
    "e.g. this is fine.",
    "function(a, b)",
    "...",
    "纯中文句子，没有问题。",
])
def test_clean(ok):
    assert check_text(ok) == []


def test_skip_code_and_urls():
    md = "见 https://example.com/中文a 和 `代码a`\n```\n中文a,b\n```\n[链接](http://x.com/中文a)\n"
    assert check_text(md) == []
    assert fix_text(md) == md


def test_tilde_fence_and_indented_code():
    md = "~~~\n中文a\n~~~\n\n    中文a\n"
    assert check_text(md) == []


def test_txt_does_not_skip_backticks():
    assert "space-cjk-latin" in rules("`中文a`", markdown=False)


def test_front_matter_skipped():
    assert check_text("---\ntitle: 中文a\n---\n正文") == []


def test_ignore_comments():
    t = "中文a <!-- hanzi-lint-disable-line -->\n<!-- hanzi-lint-disable-next-line -->\n中文b\n中文c"
    issues = check_text(t)
    assert [i.line for i in issues] == [4]
    assert fix_text(t).endswith("中文 c")


def test_block_disable():
    t = "<!-- hanzi-lint-disable -->\n中文a\n<!-- hanzi-lint-enable -->\n中文b"
    assert [i.line for i in check_text(t)] == [4]


def test_disable_rule():
    assert check_text("中文a", disable=["space-cjk-latin"]) == []
    assert fix_text("中文a", disable=["space-cjk-latin"]) == "中文a"


def test_unknown_rule():
    with pytest.raises(ValueError):
        check_text("x", disable=["nope"])


def test_line_col():
    i = check_text("第一行\n你好a")[0]
    assert (i.line, i.col, i.rule) == (2, 3, "space-cjk-latin")


def test_fix_idempotent():
    t = "在LeTV上,看ＡＢＣ视频!!(很好)"
    once = fix_text(t)
    assert fix_text(once) == once
    assert check_text(once) == []
