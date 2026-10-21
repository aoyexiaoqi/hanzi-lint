"""Rule definitions. Each rule yields (start, end, replacement, message) on a single line."""
import re
from dataclasses import dataclass
from typing import Callable, Iterator, Tuple

# CJK ideographs + kana; extension ranges kept practical
CJK = r"\u2e80-\u2eff\u2f00-\u2fdf\u3040-\u309f\u30a0-\u30ff\u3100-\u312f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK_RE = re.compile(f"[{CJK}]")

Match = Tuple[int, int, str, str]


@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    finder: Callable[[str], Iterator[Match]]


def _space_cjk_latin(line: str) -> Iterator[Match]:
    for m in re.finditer(f"(?<=[{CJK}])(?=[A-Za-z0-9])|(?<=[A-Za-z0-9%‰])(?=[{CJK}])", line):
        yield m.start(), m.start(), " ", "中英文/数字之间缺少空格"


HALF_TO_FULL = {",": "，", "!": "！", "?": "？", ";": "；", ":": "：", ".": "。"}


def _halfwidth_punct(line: str) -> Iterator[Match]:
    # punctuation directly after a CJK char
    for m in re.finditer(f"(?<=[{CJK}])([,!?;:]+|\\.(?!\\.)(?=\\s|$|[{CJK}]))", line):
        ch = m.group(1)
        full = "".join(HALF_TO_FULL[c] for c in ch)
        yield m.start(), m.end(), full, f"中文语境中使用了半角标点 “{ch}”，应为 “{full}”"
    # parentheses whose content contains CJK
    for m in re.finditer(r"\(([^()]*)\)", line):
        if CJK_RE.search(m.group(1)):
            yield m.start(), m.end(), f"（{m.group(1)}）", "中文语境中使用了半角括号，应为全角 “（）”"


def _fullwidth_alnum(line: str) -> Iterator[Match]:
    for m in re.finditer(r"[\uff10-\uff19\uff21-\uff3a\uff41-\uff5a]+", line):
        s = "".join(chr(ord(c) - 0xFEE0) for c in m.group())
        yield m.start(), m.end(), s, f"使用了全角字母/数字 “{m.group()}”，应为半角 “{s}”"


def _repeated_punct(line: str) -> Iterator[Match]:
    for m in re.finditer(r"([！？。，、；：])\1+", line):
        yield m.start(), m.end(), m.group(1), f"重复使用标点 “{m.group()}”"


def _space_fullwidth_punct(line: str) -> Iterator[Match]:
    p = "，。！？；：、（）【】《》「」『』"
    for m in re.finditer(f"(?<=\\S)[ \\t]+(?=[{p}])|(?<=[{p}])[ \\t]+(?=\\S)", line):
        yield m.start(), m.end(), "", "全角标点两侧不应有空格"


def _number_percent(line: str) -> Iterator[Match]:
    for m in re.finditer(r"(?<=\d)[ \t]+(?=%|‰|°)", line):
        yield m.start(), m.end(), "", "数字与 %/‰/° 之间不应有空格"


def _english_punct_spacing(line: str) -> Iterator[Match]:
    for m in re.finditer(r"(?<=[a-zA-Z])([,;!?])(?=[A-Za-z])", line):
        yield m.end(), m.end(), " ", f"英文标点 “{m.group(1)}” 后缺少空格"
    for m in re.finditer(r"(?<=[A-Za-z])[ \t]+(?=[,;!?.](?:\s|$))", line):
        yield m.start(), m.end(), "", "英文标点前不应有空格"


RULES = {r.id: r for r in [
    Rule("space-cjk-latin", "中文与英文字母/数字之间加空格", _space_cjk_latin),
    Rule("halfwidth-punct", "中文语境中使用全角标点", _halfwidth_punct),
    Rule("fullwidth-alnum", "字母和数字使用半角", _fullwidth_alnum),
    Rule("repeated-punct", "不重复使用标点", _repeated_punct),
    Rule("space-fullwidth-punct", "全角标点两侧不加空格", _space_fullwidth_punct),
    Rule("number-percent", "数字与 %、‰、° 之间不加空格", _number_percent),
    Rule("english-punct-spacing", "英文标点后加空格、前不加空格", _english_punct_spacing),
]}
