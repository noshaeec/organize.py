from organize import categorize, organize
from pathlib import Path


def test_categorize():
    assert categorize(Path("a.PDF")) == "Documents"
    assert categorize(Path("a.png")) == "Images"
    assert categorize(Path("a.xyz")) == "Others"


def test_files_move_to_right_folders(tmp_path):
    (tmp_path / "a.pdf").write_text("x")
    (tmp_path / "b.png").write_text("x")
    organize(tmp_path)
    assert (tmp_path / "Documents" / "a.pdf").exists()
    assert (tmp_path / "Images" / "b.png").exists()


def test_name_collision_keeps_both_files(tmp_path):
    (tmp_path / "Documents").mkdir()
    (tmp_path / "Documents" / "a.pdf").write_text("old")
    (tmp_path / "a.pdf").write_text("new")
    organize(tmp_path)
    assert (tmp_path / "Documents" / "a.pdf").read_text() == "old"
    assert (tmp_path / "Documents" / "a (1).pdf").read_text() == "new"


def test_dry_run_moves_nothing(tmp_path):
    (tmp_path / "a.pdf").write_text("x")
    organize(tmp_path, dry_run=True)
    assert (tmp_path / "a.pdf").exists()
    assert not (tmp_path / "Documents").exists()


def test_unfinished_downloads_are_skipped(tmp_path):
    (tmp_path / "movie.crdownload").write_text("x")
    organize(tmp_path)
    assert (tmp_path / "movie.crdownload").exists()