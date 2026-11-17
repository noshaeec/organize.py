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

    def test_unfinished_downloads_are_skipped(tmp_path):
       (tmp_path / "movie.crdownload").write_text("x")
       organize(tmp_path)
       assert (tmp_path / "movie.crdownload").exists()


def test_duplicate_goes_to_duplicates_folder(tmp_path):
    (tmp_path / "report.pdf").write_text("same content")
    (tmp_path / "report (1).pdf").write_text("same content")
    organize(tmp_path, dedupe=True)
    assert len(list((tmp_path / "Documents").iterdir())) == 1
    assert len(list((tmp_path / "Duplicates").iterdir())) == 1


def test_different_files_with_same_size_are_not_duplicates(tmp_path):
    (tmp_path / "a.txt").write_text("aaaa")
    (tmp_path / "b.txt").write_text("bbbb")
    organize(tmp_path, dedupe=True)
    assert not (tmp_path / "Duplicates").exists()


def test_copy_of_already_sorted_file_is_caught(tmp_path):
    (tmp_path / "Documents").mkdir()
    (tmp_path / "Documents" / "cv.pdf").write_text("my cv")
    (tmp_path / "cv copy.pdf").write_text("my cv")
    organize(tmp_path, dedupe=True)
    assert (tmp_path / "Duplicates" / "cv copy.pdf").exists()


def test_without_dedupe_flag_copies_are_kept(tmp_path):
    (tmp_path / "a.pdf").write_text("same")
    (tmp_path / "b.pdf").write_text("same")
    organize(tmp_path)
    assert not (tmp_path / "Duplicates").exists()

