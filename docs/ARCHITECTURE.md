# Architecture

## Inputs
- Source music directory (example: Desktop/2025 all songs)
- USB target directory (example: /Volumes/NO NAME/2025/2025 all songs)
- Crate backup directories (Serato/Rekordbox exports)

## Pipeline
1. Scan source + target + crates.
2. Build canonical track IDs (hash + normalized tags).
3. Validate 1:1 source->USB sync.
4. Detect duplicates by audio/content hash.
5. Resolve filename safety issues (length + illegal characters).
6. Parse crate membership and map tracks.
7. Emit truth report:
   - matched crate tracks
   - unmatched crate references
   - orphan songs
8. Optional apply mode (safe, logged, reversible).

## Rekordbox integration
- Prefer Rekordbox XML export/import for deterministic mapping.
- Preserve cue/playlist identity where possible.

## Safety
- Dry-run default.
- Every change logged.
- Optional backup snapshots before apply mode.
