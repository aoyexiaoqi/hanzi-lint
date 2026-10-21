import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

CONFIG_NAMES = (".hanzi-lint.toml", "hanzi-lint.toml")


def find_config(start: Path) -> Optional[Path]:
    start = start.resolve()
    for d in [start, *start.parents]:
        for n in CONFIG_NAMES:
            if (d / n).is_file():
                return d / n
        pp = d / "pyproject.toml"
        if pp.is_file():
            try:
                if "hanzi-lint" in tomllib.loads(pp.read_text("utf-8")).get("tool", {}):
                    return pp
            except Exception:
                pass
    return None


def load_config(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    data = tomllib.loads(Path(path).read_text("utf-8"))
    if Path(path).name == "pyproject.toml":
        data = data.get("tool", {}).get("hanzi-lint", {})
    return data
