import re
from dataclasses import dataclass, asdict
from typing import Iterable, List, Optional, Set, Tuple

from .rules import RULES

DISABLE_LINE = "hanzi-lint-disable-line"
DISABLE_NEXT = "hanzi-lint-disable-next-line"
DISABLE_BLOCK = "hanzi-lint-disable"
ENABLE_BLOCK = "hanzi-lint-enable"

_URL = r"(?:https?|ftp)://[^\s<>()（）\]]+|www\.[^\s<>()（）\]]+|[\w.+-]+@[\w-]+\.[\w.-]+"
_MD_INLINE = re.compile(r"(`+).+?\1|\]\([^)]*\)|<[^>\n]+>|" + _URL)
_TXT_INLINE = re.compile(_URL)
_FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass
class Issue:
    path: str
    line: int
    col: int
    rule: str
    message: str

    def to_dict(self):
        return asdict(self)


def _protected(line: str, markdown: bool) -> List[Tuple[int, int]]:
    pat = _MD_INLINE if markdown else _TXT_INLINE
    return [(m.start(), m.end()) for m in pat.finditer(line)]


def _overlaps(s: int, e: int, spans) -> bool:
    for a, b in spans:
        if s == e:
            if a < s < b:
                return True
        elif s < b and a < e:
            return True
    return False


def _skip_lines(lines: List[str], markdown: bool) -> Set[int]:
    skip: Set[int] = set()
    in_fence = None
    disabled = False
    for i, line in enumerate(lines):
        if markdown:
            m = _FENCE.match(line)
            if in_fence:
                skip.add(i)
                if m and m.group(1) == in_fence:
                    in_fence = None
                continue
            if m:
                in_fence = m.group(1)
                skip.add(i)
                continue
            if line.startswith("    ") or line.startswith("\t"):
                # indented code block (only when previous line blank or also code)
                if i == 0 or not lines[i - 1].strip() or (i - 1) in skip:
                    skip.add(i)
                    continue
        if ENABLE_BLOCK in line and DISABLE_BLOCK not in line.replace(ENABLE_BLOCK, ""):
            disabled = False
            skip.add(i)
            continue
        if re.search(DISABLE_BLOCK + r"(?![-\w])", line):
            disabled = True
        if disabled or DISABLE_LINE in line:
            skip.add(i)
        if DISABLE_NEXT in line:
            skip.add(i)
            skip.add(i + 1)
    # front matter
    if markdown and lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            skip.add(0)
            skip.add(j)
            if lines[j].strip() == "---":
                break
    return skip


def _line_matches(line: str, rules: Iterable[str], markdown: bool):
    spans = _protected(line, markdown)
    for rid in rules:
        for s, e, rep, msg in RULES[rid].finder(line):
            if not _overlaps(s, e, spans):
                yield rid, s, e, rep, msg


def _active(disable: Optional[Iterable[str]]) -> List[str]:
    disable = set(disable or ())
    unknown = disable - set(RULES)
    if unknown:
        raise ValueError(f"未知规则: {', '.join(sorted(unknown))}")
    return [r for r in RULES if r not in disable]


def check_text(text: str, path: str = "<stdin>", markdown: bool = True,
               disable: Optional[Iterable[str]] = None) -> List[Issue]:
    rules = _active(disable)
    lines = text.split("\n")
    skip = _skip_lines(lines, markdown)
    issues = []
    for i, line in enumerate(lines):
        if i in skip:
            continue
        for rid, s, _e, _rep, msg in _line_matches(line, rules, markdown):
            issues.append(Issue(path, i + 1, s + 1, rid, msg))
    issues.sort(key=lambda x: (x.line, x.col, x.rule))
    return issues


def _fix_line(line: str, rules: List[str], markdown: bool) -> str:
    for _ in range(5):  # iterate to a fixed point
        before = line
        for rid in rules:
            edits = [(s, e, rep) for r, s, e, rep, _m in _line_matches(line, [rid], markdown)]
            # apply right-to-left, dropping overlaps
            edits.sort(key=lambda x: (x[0], x[1]))
            out, last = [], len(line) + 1
            for s, e, rep in reversed(edits):
                if e > last or (e == last and s == e and out and out[-1][0] == s):
                    continue
                out.append((s, e, rep))
                last = s
            for s, e, rep in out:
                line = line[:s] + rep + line[e:]
        if line == before:
            break
    return line


def fix_text(text: str, markdown: bool = True, disable: Optional[Iterable[str]] = None) -> str:
    rules = _active(disable)
    lines = text.split("\n")
    skip = _skip_lines(lines, markdown)
    return "\n".join(l if i in skip else _fix_line(l, rules, markdown) for i, l in enumerate(lines))
