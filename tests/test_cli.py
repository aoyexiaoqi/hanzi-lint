import io
import json
from hanzi_lint.cli import main


def test_clean_file_exit0(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text("你好，世界。\n", "utf-8")
    assert main([str(f)]) == 0


def test_issue_exit1_and_output(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text("你好a\n", "utf-8")
    assert main([str(f)]) == 1
    out = capsys.readouterr().out
    assert f"{f}:1:3: [space-cjk-latin]" in out


def test_json(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("你好a", "utf-8")
    assert main(["--json", str(f)]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data[0]["rule"] == "space-cjk-latin" and data[0]["line"] == 1


def test_fix_in_place(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("你好a,b", "utf-8")
    assert main(["--fix", str(f)]) == 0
    assert f.read_text("utf-8") == "你好 a, b"


def test_diff_does_not_modify(tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text("你好a\n", "utf-8")
    assert main(["--diff", str(f)]) == 1
    out = capsys.readouterr().out
    assert "-你好a" in out and "+你好 a" in out
    assert f.read_text("utf-8") == "你好a\n"


def test_directory_and_extensions(tmp_path, capsys):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.md").write_text("你好a", "utf-8")
    (tmp_path / "b.py").write_text("你好a", "utf-8")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "c.md").write_text("你好a", "utf-8")
    assert main([str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "a.md" in out and "b.py" not in out and "c.md" not in out


def test_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("你好a"))
    assert main([]) == 1
    monkeypatch.setattr("sys.stdin", io.StringIO("你好a"))
    main(["--fix", "-"])
    assert capsys.readouterr().out.endswith("你好 a")


def test_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".hanzi-lint.toml").write_text('disable = ["space-cjk-latin"]\nexclude = ["skip*.md"]\n', "utf-8")
    (tmp_path / "a.md").write_text("你好a", "utf-8")
    (tmp_path / "skip1.md").write_text("你好,", "utf-8")
    assert main(["."]) == 0


def test_pyproject_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[tool.hanzi-lint]\ndisable = ["space-cjk-latin"]\n', "utf-8")
    (tmp_path / "a.md").write_text("你好a", "utf-8")
    assert main(["a.md"]) == 0


def test_cli_disable_and_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.md").write_text("你好a", "utf-8")
    assert main(["--disable", "space-cjk-latin", "a.md"]) == 0
    assert main(["--disable", "bogus", "a.md"]) == 2


def test_missing_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["nope.md"]) == 2


def test_list_rules(capsys):
    assert main(["--list-rules"]) == 0
    assert "halfwidth-punct" in capsys.readouterr().out


def test_bad_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad.toml").write_text("=[", "utf-8")
    assert main(["--config", "bad.toml", "-"]) == 2
