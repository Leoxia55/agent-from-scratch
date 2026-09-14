"""tools/_file_tools.py 单元测试：文件操作工具。"""

from __future__ import annotations

from scratchagent.tools import (
    delete_file,
    list_files,
    read_file,
    unzip_file,
)


# ---------------------------------------------------------------- read_file
class TestReadFile:
    def test_text_file(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("line1\nline2\n", encoding="utf-8")
        out = read_file(str(f))
        assert "line1" in out
        assert "line2" in out

    def test_line_range(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("1\n2\n3\n4\n", encoding="utf-8")
        out = read_file(str(f), start_line=2, end_line=3)
        assert "2" in out
        assert "4" not in out

    def test_not_found(self, tmp_path):
        assert "not found" in read_file(str(tmp_path / "missing.txt"))

    def test_csv(self, tmp_path):
        f = tmp_path / "a.csv"
        f.write_text("col1,col2\n1,2\n", encoding="utf-8")
        out = read_file(str(f))
        assert "col1" in out


# ---------------------------------------------------------------- list_files
class TestListFiles:
    def test_lists_files_and_dirs(self, tmp_path):
        (tmp_path / "file.txt").write_text("x")
        (tmp_path / "subdir").mkdir()
        out = list_files(str(tmp_path))
        assert "file.txt" in out
        assert "subdir/" in out

    def test_skips_hidden(self, tmp_path):
        (tmp_path / ".hidden").write_text("x")
        (tmp_path / "visible.txt").write_text("x")
        out = list_files(str(tmp_path))
        assert ".hidden" not in out
        assert "visible.txt" in out

    def test_not_found(self, tmp_path):
        assert "not found" in list_files(str(tmp_path / "missing"))

    def test_not_a_directory(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("x")
        assert "Not a directory" in list_files(str(f))


# ---------------------------------------------------------------- delete_file
class TestDeleteFile:
    def test_delete_file(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("x")
        assert "deleted" in delete_file(str(f))
        assert not f.exists()

    def test_delete_directory(self, tmp_path):
        d = tmp_path / "dir"
        d.mkdir()
        (d / "inner.txt").write_text("x")
        assert "deleted" in delete_file(str(d))
        assert not d.exists()

    def test_not_found(self, tmp_path):
        assert "not found" in delete_file(str(tmp_path / "missing"))


# ---------------------------------------------------------------- unzip_file
class TestUnzipFile:
    def test_unzip(self, tmp_path):
        import zipfile

        zip_path = tmp_path / "archive.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("inner.txt", "content")

        out = unzip_file(str(zip_path))
        assert "Extracted" in out
        assert "inner.txt" in out
        extracted_dir = tmp_path / "archive"
        assert (extracted_dir / "inner.txt").exists()

    def test_not_found(self, tmp_path):
        assert "not found" in unzip_file(str(tmp_path / "missing.zip"))
