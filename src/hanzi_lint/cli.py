import argparse
import difflib
import fnmatch
import json
import sys
from pathlib import Path
from typing import Iterator, List, Optional

from . import __version__
from .config import find_config, load_config
from .core import check_text, fix_text
from .rules import RULES

DEFAULT_EXT = (".md", ".markdown", ".txt")


def _iter_files(paths: List[str], exts, exclude) -> Iterator[Path]:
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for f in sorted(path.rglob("*")):
                if f.is_file() and f.suffix.lower() in exts and not any(
                        part.startswith(".") for part in f.relative_to(path).parts) and not _excluded(f, exclude):
                    yield f
        elif path.is_file():
            if not _excluded(path, exclude):
                yield path
        else:
            raise FileNotFoundError(p)


def _excluded(f: Path, patterns) -> bool:
    s = f.as_posix()
    return any(fnmatch.fnmatch(s, pat) or fnmatch.fnmatch(f.name, pat) for pat in patterns)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hanzi-lint", description="中文文案排版检查工具 / Chinese copywriting linter")
    p.add_argument("paths", nargs="*", help="文件或目录；省略或 '-' 表示从 stdin 读取")
    p.add_argument("--fix", action="store_true", help="就地修复文件（stdin 时输出修复结果）")
    p.add_argument("--diff", action="store_true", help="输出修复前后的 unified diff，不修改文件")
    p.add_argument("--json", action="store_true", help="以 JSON 输出问题")
    p.add_argument("--disable", action="append", default=[], metavar="RULE", help="禁用规则（可重复，逗号分隔）")
    p.add_argument("--config", help="配置文件路径（默认自动查找 .hanzi-lint.toml / pyproject.toml）")
    p.add_argument("--format", choices=["auto", "markdown", "text"], default="auto", help="输入格式")
    p.add_argument("--list-rules", action="store_true", help="列出所有规则")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_rules:
        for r in RULES.values():
            print(f"{r.id:24} {r.description}")
        return 0
    cfg_path = Path(args.config) if args.config else find_config(Path.cwd())
    try:
        cfg = load_config(cfg_path)
    except Exception as e:
        print(f"hanzi-lint: 无法读取配置 {cfg_path}: {e}", file=sys.stderr)
        return 2
    disable = list(cfg.get("disable", []))
    for d in args.disable:
        disable += [x.strip() for x in d.split(",") if x.strip()]
    exts = tuple(cfg.get("extensions", DEFAULT_EXT))
    exclude = cfg.get("exclude", [])
    unknown = set(disable) - set(RULES)
    if unknown:
        print(f"hanzi-lint: 未知规则: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    sources = []
    if not args.paths or args.paths == ["-"]:
        sources.append(("<stdin>", None, sys.stdin.read()))
    else:
        try:
            for f in _iter_files(args.paths, exts, exclude):
                try:
                    sources.append((str(f), f, f.read_text("utf-8")))
                except UnicodeDecodeError:
                    print(f"hanzi-lint: 跳过非 UTF-8 文件 {f}", file=sys.stderr)
        except FileNotFoundError as e:
            print(f"hanzi-lint: 找不到路径 {e}", file=sys.stderr)
            return 2

    all_issues = []
    for name, f, text in sources:
        md = args.format == "markdown" or (args.format == "auto" and (f is None or f.suffix.lower() in (".md", ".markdown")))
        issues = check_text(text, name, markdown=md, disable=disable)
        all_issues += issues
        if args.diff or args.fix:
            fixed = fix_text(text, markdown=md, disable=disable)
            if args.diff and fixed != text:
                sys.stdout.writelines(difflib.unified_diff(
                    text.splitlines(True), fixed.splitlines(True), f"a/{name}", f"b/{name}"))
            if args.fix:
                if f is None:
                    sys.stdout.write(fixed)
                elif fixed != text:
                    f.write_text(fixed, "utf-8")
                    print(f"已修复 {name}", file=sys.stderr)
    if args.fix or args.diff:
        if args.fix:
            # report what remains unfixable
            remaining = []
            for name, f, text in sources:
                if f is not None:
                    md = args.format == "markdown" or (args.format == "auto" and f.suffix.lower() in (".md", ".markdown"))
                    remaining += check_text(f.read_text("utf-8"), name, markdown=md, disable=disable)
            return 1 if remaining else 0
        return 1 if all_issues else 0
    if args.json:
        print(json.dumps([i.to_dict() for i in all_issues], ensure_ascii=False, indent=2))
    else:
        for i in all_issues:
            print(f"{i.path}:{i.line}:{i.col}: [{i.rule}] {i.message}")
        if all_issues:
            print(f"\n发现 {len(all_issues)} 个问题，可使用 --fix 自动修复。", file=sys.stderr)
    return 1 if all_issues else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
