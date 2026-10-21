"""hanzi-lint: 中文文案排版检查与自动修复工具。"""
from .core import Issue, check_text, fix_text
from .rules import RULES

__all__ = ["Issue", "check_text", "fix_text", "RULES"]
__version__ = "0.1.0"
