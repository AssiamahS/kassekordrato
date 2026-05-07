# kassekordrato

Version: `0.2.0`

Desktop-first Rekordbox/USB music workflow with truth reporting.

## What works now
- Folder ingest from desktop source.
- Truth report (tracks, duplicates, crate-match audit).
- 1:1 USB mirror sync for music folders.
- Optional USB format helper for Rekordbox compatibility.
- Desktop UI to run the flow without memorizing commands.

## Run app
```bash
cd /Users/djsly/kassekordrato
python3 app/desktop_manager.py
```

## Core workflow
1. Choose source folder (example: `Desktop/2025/2025 all songs`).
2. Choose USB target folder (example: `/Volumes/NO NAME/2025/2025 all songs`).
3. Run Truth Report.
4. Run 1:1 Sync to USB.
5. Open Rekordbox Export Mode and sync playlists to USB (writes Pioneer DB/cue metadata).

## Rekordbox truth
- File copy alone is not full Rekordbox export.
- Rekordbox must write its own database on the USB.

## USB formatting guidance
- `MS-DOS (FAT32)` for widest legacy CDJ compatibility.
- `ExFAT` for newer Pioneer devices/firmware.

Use `tools/format_usb_macos.py` only when you intentionally want to erase and reformat a drive.

## Project layout
- `app/desktop_manager.py` desktop GUI launcher
- `tools/music_truth_report.py` metadata + crate matching report
- `tools/usb_rekordbox_sync.py` 1:1 source->USB sync (`--delete` mirror)
- `tools/format_usb_macos.py` explicit macOS formatting helper
- `ios-companion/` iOS companion plan

## Next upgrades
- Real Serato crate binary parser for high-fidelity references.
- Rekordbox XML writer and playlist generation.
- Signed desktop app packaging.
- Cloud build and release artifacts.
