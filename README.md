# Folder Organizer

A small Python script that cleans up a messy folder, like your Downloads folder.

It looks at each file and moves it into the right folder:

- Documents (PDF, Word, Excel, text files)
- Images (JPG, PNG, GIF)
- Videos (MP4, MKV, MOV)
- Archives (ZIP, RAR, 7Z)
- Code (PY, JS, HTML, JSON)
- Others (anything else)

## What it does
- Makes the folders for you, only when it needs them.
- Never replaces a file. If a name is taken, it adds a number, like `report (1).pdf`.
- If a file is locked or can't be moved, it skips it and keeps going.
- Leaves alone files that are still downloading.
- Lets you preview first and undo afterwards.

## What you need
Python 3.8 or newer. You don't need to install anything else.

## How to use it

Clean your Downloads folder:
```
python organize.py
```

Clean a different folder:
```
python organize.py "C:\Users\You\Desktop"
```

See what would happen, without moving anything:
```
python organize.py --dry-run
```

Put everything back the way it was:
```
python organize.py --undo
```

## Change the folders
Open `organize.py` and edit the `CATEGORIES` list near the top. You can add new file types or new folders there.

## License
MIT