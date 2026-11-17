# Folder Organizer

This is a Python script that cleans up a messy folder, like your Downloads folder.

It looks at each file and moves it into the right folder:

- Documents (PDF, Word, Excel, text files)
- Images (JPG, PNG, GIF)
- Videos (MP4, MKV, MOV)
- Archives (ZIP, RAR, 7Z)
- Code (PY, JS, HTML, JSON)
- Others (anything else)

## What it does
- Finds exact duplicate files and moves the extra copies to a Duplicates folder.
- Makes the folders for you, only when it needs them.
- Never replaces a file. If a name is taken, it adds a number, like `report (1).pdf`.
- If a file is locked or can't be moved, it skips it and keeps going.
- Leaves alone files that are still downloading.
- Lets you preview first and undo afterwards.

## What you need
Python 3.8 or newer. You don't need to install anything else.
e
## How to use it
Move exact duplicate files into a Duplicates folder (nothing is deleted):
```
python3 organize.py --dedupe

Put images and videos into month folders (like Images/2026-03):
```
python3 organize.py --by-date
```
```

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
## Run it automatically
You can make your computer clean a folder every day with cron (Linux).

1. Open your schedule: `crontab -e`
2. Add this line (change the paths to match your computer). It runs every day at 9 am:
```
0 9 * * * /usr/bin/python3 /home/YOUR_NAME/organize.py /home/YOUR_NAME/Downloads --by-date >> /home/YOUR_NAME/organize-cron.log 2>&1
```
3. Save and exit. To see what it did, open `organize-cron.log`.

Your computer needs to be on at that time.
MIT