#!/usr/bin/env python3
import argparse
import hashlib
import os
import re
import shutil
from pathlib import Path

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aiff", ".flac"}
MAX_BASENAME = 120


def safe_name(name: str) -> str:
    s = re.sub(r'[<>:"/\\|?*]+', '_', name).strip()
    s = re.sub(r'\s+', ' ', s)
    return s[:MAX_BASENAME].rstrip(' .') or 'untitled'


def sha1_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open('rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def iter_audio_files(root: Path):
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS and not p.name.startswith('._'):
            yield p


def unique_target_path(dest_dir: Path, stem: str, suffix: str) -> Path:
    candidate = dest_dir / f"{stem}{suffix}"
    i = 1
    while candidate.exists():
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        i += 1
    return candidate


def stage(source: Path, dest: Path, dry_run: bool = False):
    dest.mkdir(parents=True, exist_ok=True)
    seen_hashes = set()
    copied = 0
    skipped_dup = 0

    for src in iter_audio_files(source):
        try:
            digest = sha1_file(src)
        except Exception as e:
            print(f"ERROR hashing {src}: {e}")
            continue

        if digest in seen_hashes:
            skipped_dup += 1
            continue
        seen_hashes.add(digest)

        stem = safe_name(src.stem)
        out = unique_target_path(dest, stem, src.suffix.lower())
        if dry_run:
            print(f"DRYRUN copy: {src} -> {out}")
        else:
            shutil.copy2(src, out)
        copied += 1

    print(f"Done. copied={copied}, skipped_duplicates={skipped_dup}, destination={dest}")


def main():
    ap = argparse.ArgumentParser(description='Create clean Rekordbox staging folder (dedupe + safe filenames).')
    ap.add_argument('--source', required=True, help='Source music folder')
    ap.add_argument('--dest', required=True, help='Destination staging folder')
    ap.add_argument('--dry-run', action='store_true', help='Preview without copying')
    args = ap.parse_args()

    source = Path(args.source).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source folder not found: {source}")

    stage(source, dest, args.dry_run)


if __name__ == '__main__':
    main()
