#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from pathlib import Path

ALLOWED_FS = {"msdos", "exfat", "hfs", "apfs"}


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def fs_type_for_path(path: Path) -> str:
    proc = run(["df", "-T", str(path)])
    if proc.returncode != 0:
        return "unknown"
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if len(lines) < 2:
        return "unknown"
    cols = lines[1].split()
    if len(cols) < 3:
        return "unknown"
    return cols[2].lower()


def remove_macos_junk(dest: Path) -> None:
    for p in dest.rglob("._*"):
        if p.is_file():
            p.unlink(missing_ok=True)
    for p in dest.rglob(".DS_Store"):
        if p.is_file():
            p.unlink(missing_ok=True)


def sync_1_to_1(source: Path, dest: Path, dry_run: bool) -> int:
    rsync_cmd = [
        "rsync",
        "-avh",
        "--delete",
        "--progress",
        "--exclude",
        "._*",
        "--exclude",
        ".DS_Store",
        f"{source}/",
        f"{dest}/",
    ]
    if dry_run:
        rsync_cmd.insert(1, "--dry-run")
    proc = run(rsync_cmd)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    return proc.returncode


def count_audio(root: Path) -> int:
    exts = {".mp3", ".m4a", ".wav", ".aiff", ".flac"}
    return sum(1 for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="1:1 source->USB sync for Rekordbox prep with filesystem validation."
    )
    ap.add_argument("--source", required=True, help="Source folder, e.g. Desktop/2025 all songs")
    ap.add_argument("--usb-target", required=True, help="USB folder, e.g. /Volumes/NO NAME/2025/2025 all songs")
    ap.add_argument("--dry-run", action="store_true", help="Preview only")
    args = ap.parse_args()

    source = Path(args.source).expanduser().resolve()
    target = Path(args.usb_target).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Missing source folder: {source}")
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)

    fs = fs_type_for_path(target)
    print(f"USB filesystem detected: {fs}")
    if fs not in ALLOWED_FS:
        print("WARNING: Filesystem may not be Rekordbox-friendly.")
        print("Recommended: FAT32(msdos) for broadest CDJ compatibility, or exFAT for newer gear.")

    rc = sync_1_to_1(source, target, args.dry_run)
    if rc != 0:
        raise SystemExit(f"rsync failed with code {rc}")

    if not args.dry_run:
        remove_macos_junk(target)

    src_count = count_audio(source)
    dst_count = count_audio(target)
    print(f"Source audio files: {src_count}")
    print(f"USB audio files:    {dst_count}")
    if src_count == dst_count:
        print("OK: 1:1 audio count match.")
    else:
        print("WARNING: count mismatch. Run truth report next.")

    print("Next step: import/sync this USB in Rekordbox Export Mode to write Pioneer database files.")


if __name__ == "__main__":
    if not shutil.which("rsync"):
        raise SystemExit("rsync not found. Install or use a system with rsync.")
    main()
