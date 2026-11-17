#!/usr/bin/env python3
"""
organize.py - Sort a cluttered directory (e.g. Downloads) into category folders.

Usage:
    python organize.py                      # organizes ~/Downloads
    python organize.py /path/to/folder      # organizes a specific folder
    python organize.py --dry-run            # preview only, nothing is moved
    python organize.py --undo               # reverse the last run in that folder
"""

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
import hashlib
from collections import Counter

CATEGORIES = {
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx",
                  ".csv", ".ppt", ".pptx", ".md", ".epub"},
    "Images":    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff",
                  ".ico", ".heic"},
    "Videos":    {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm", ".m4v"},
    "Archives":  {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"},
    "Code":      {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".go",
                  ".rs", ".html", ".css", ".json", ".xml", ".sh", ".sql", ".yml", ".yaml"},
                      "Installers": {".deb", ".rpm", ".appimage", ".exe", ".msi", ".jar"},
}
FALLBACK = "Others"  # unknown extensions; set to None to leave them in place
PARTIAL_DOWNLOADS = {".crdownload", ".part", ".tmp", ".download"}
UNDO_LOG = ".organize_log.json"
DUPLICATES = "Duplicates"
DATE_SORTED = {"Images", "Videos"}  # these get month folders with --by-date

# Reverse lookup: extension -> category
EXT_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}


def categorize(path: Path):
    return EXT_MAP.get(path.suffix.lower(), FALLBACK)


def unique_destination(dest: Path) -> Path:
    """Return a non-colliding path: report.pdf -> report (1).pdf -> report (2).pdf"""
    if not dest.exists():
        return dest
    counter = 1
    while True:
        candidate = dest.with_name(f"{dest.stem} ({counter}){dest.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1

def sha256_of(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash a file's contents in chunks, so big files don't fill up memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


class DuplicateFinder:
    """Spots files with exactly the same content, even if the names differ."""

    def __init__(self, root: Path, candidates):
        self.sizes = Counter()
        self.known = {}  # content hash -> the file we are keeping

        existing = []
        for category in list(CATEGORIES) + [FALLBACK]:
            folder = root / category if category else None
            if folder and folder.is_dir():
               existing += [p for p in folder.rglob("*") if p.is_file()]

        for path in existing + list(candidates):
            try:
                self.sizes[path.stat().st_size] += 1
            except OSError:
                pass

        for path in existing:
            self.is_duplicate(path)  # registers it as an original

    def is_duplicate(self, path: Path) -> bool:
        try:
            size = path.stat().st_size
            if size == 0 or self.sizes[size] < 2:
                return False  # empty or unique size: can't be a copy
            digest = sha256_of(path)
        except OSError as exc:
            logging.warning("Could not check %s for duplicates: %s", path.name, exc)
            return False
        if digest in self.known:
            return True
        self.known[digest] = path
        return False
    
def date_folder(path: Path) -> str:
    """Month folder like 2026-11, taken from the file's last-modified date."""
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m")

def _age_order(entry):
    """Oldest first; on a tie the shorter name wins."""
    try:
        mtime = entry.stat(follow_symlinks=False).st_mtime
    except OSError:
        mtime = 0.0
    return (mtime, len(entry.name), entry.name)

def organize(root: Path, dry_run: bool = False,dedupe: bool = False, by_date: bool = False) -> dict:
    stats = {"moved": 0, "skipped": 0, "errors": 0}
    moves = []  # (source, destination) pairs for undo
    script_path = Path(__file__).resolve()

    try:
        entries = list(os.scandir(root))
    except PermissionError:
        logging.error("No permission to read %s", root)
        stats["errors"] += 1
        return stats
    
    finder = None
    if dedupe:
        entries.sort(key=_age_order)  # oldest file is kept as the original
        files = [Path(e.path) for e in entries if e.is_file(follow_symlinks=False)]
        finder = DuplicateFinder(root, files)

    for entry in entries:
        path = Path(entry.path)

        # Only regular files at the top level; never touch folders or symlinks
        if not entry.is_file(follow_symlinks=False):
            continue
        if path.name.startswith(".") or path.resolve() == script_path:
            stats["skipped"] += 1
            continue
        if path.suffix.lower() in PARTIAL_DOWNLOADS:
            logging.info("Skipping in-progress download: %s", path.name)
            stats["skipped"] += 1
            continue

        category = categorize(path)
        if finder and finder.is_duplicate(path):
            category = DUPLICATES
        if category is None:
            stats["skipped"] += 1
            continue

        subfolder = date_folder(path) if by_date and category in DATE_SORTED else ""
        target_dir = root / category / subfolder
        dest = unique_destination(target_dir / path.name)

        if dry_run:
            logging.info("[DRY RUN] %s -> %s/%s", path.name, target_dir.relative_to(root), dest.name)
            stats["moved"] += 1
            continue

        try:
            target_dir.mkdir(parents=True, exist_ok=True)  # created only when needed
            shutil.move(str(path), str(dest))
            moves.append((str(path), str(dest)))
            logging.info("Moved %s -> %s/%s", path.name, target_dir.relative_to(root), dest.name)
            stats["moved"] += 1
        except PermissionError:
            logging.warning("Permission denied (file locked/in use?): %s", path.name)
            stats["errors"] += 1
        except OSError as exc:
            logging.warning("Could not move %s: %s", path.name, exc)
            stats["errors"] += 1

    if moves:
        save_log(root, moves)
    return stats


def save_log(root: Path, moves):
    log_file = root / UNDO_LOG
    try:
        log_file.write_text(json.dumps(
            {"time": datetime.now().isoformat(timespec="seconds"), "moves": moves},
            indent=2))
    except OSError as exc:
        logging.warning("Could not write undo log: %s", exc)


def undo(root: Path):
    log_file = root / UNDO_LOG
    if not log_file.exists():
        logging.error("No undo log found in %s", root)
        return
    data = json.loads(log_file.read_text())
    restored = 0
    for src, dest in reversed(data["moves"]):
        try:
            if Path(dest).exists():
                shutil.move(dest, unique_destination(Path(src)))
                restored += 1
        except OSError as exc:
            logging.warning("Could not restore %s: %s", dest, exc)
    log_file.unlink(missing_ok=True)
    logging.info("Restored %d file(s).", restored)


def main():
    parser = argparse.ArgumentParser(description="Organize a directory by file type.")
    parser.add_argument("directory", nargs="?", default=str(Path.home() / "Downloads"))
    parser.add_argument("--dry-run", action="store_true", help="preview without moving")
    parser.add_argument("--undo", action="store_true", help="reverse the last run")
    parser.add_argument("--dedupe", action="store_true",
                        help="move exact duplicate files into a Duplicates folder")
    parser.add_argument("--by-date", action="store_true",
                        help="put Images and Videos into month folders like 2026-11")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Not a directory: {root}")

    if args.undo:
        undo(root)
        return
    

    stats = organize(root, dry_run=args.dry_run, dedupe=args.dedupe, by_date=args.by_date)
    logging.info("Done. Moved: %(moved)d | Skipped: %(skipped)d | Errors: %(errors)d", stats)
    
if __name__ == "__main__":
    main()
