# Quickstart: Put Songs Into Rekordbox First

## Desktop App (easy mode)

```bash
python3 app/desktop_manager.py
```

Flow:
1. Choose source folder (your 2025 folder).
2. Choose USB target folder.
3. Run Truth Report.
4. Run 1:1 USB Sync.
5. Open Rekordbox Export Mode and sync playlists to write Pioneer database data.

## A) 1:1 Desktop Folder -> USB (Rekordbox Prep)

This is the safe replacement for messy manual copy:

```bash
python3 tools/usb_rekordbox_sync.py \
  --source "/Users/djsly/Desktop/2025/2025 all songs" \
  --usb-target "/Volumes/NO NAME/2025/2025 all songs"
```

Preview first:

```bash
python3 tools/usb_rekordbox_sync.py \
  --source "/Users/djsly/Desktop/2025/2025 all songs" \
  --usb-target "/Volumes/NO NAME/2025/2025 all songs" \
  --dry-run
```

Recommended USB format:
- `FAT32 (msdos)` for widest CDJ compatibility.
- `exFAT` for newer Pioneer players/firmware.

After sync, open Rekordbox in Export Mode and sync playlists to that USB so Rekordbox writes Pioneer DB files.

Important:
- iOS alone cannot reliably copy full desktop music folders to arbitrary USB and write Rekordbox/Pioneer database structures.
- The correct reliable core is desktop (Mac/PC). iOS can be a companion/remote trigger later.

## B) Optional clean staging folder

1. Build clean staging folder:

```bash
python3 tools/rekordbox_staging.py \
  --source "/Users/djsly/Desktop/2025/2025 all songs" \
  --dest "/Users/djsly/Desktop/rekordbox_import_staging"
```

2. Open Rekordbox.
3. Drag `rekordbox_import_staging` into Rekordbox collection/playlists.
4. After import is correct, run crate/playlist mapping step.

Use `--dry-run` first if needed.

## Truth Report (Before Any Crate Edits)

Run this to prove what matches and what does not:

```bash
python3 tools/music_truth_report.py \
  --source "/Users/djsly/Desktop/2025/2025 all songs" \
  --serato-subcrates "/Users/djsly/Music/_Serato_Backup/Subcrates" \
  --out "/Users/djsly/Desktop/truth_report.json"
```

Optional Rekordbox XML:

```bash
python3 tools/music_truth_report.py \
  --source "/Users/djsly/Desktop/2025/2025 all songs" \
  --serato-subcrates "/Users/djsly/Music/_Serato_Backup/Subcrates" \
  --rekordbox-xml "/path/to/rekordbox_export.xml" \
  --out "/Users/djsly/Desktop/truth_report.json"
```
