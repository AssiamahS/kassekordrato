#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def list_external_disks() -> str:
    p = run(["diskutil", "list", "external"])
    return p.stdout if p.returncode == 0 else p.stderr


def main() -> None:
    ap = argparse.ArgumentParser(description="Format USB for Rekordbox use on macOS.")
    ap.add_argument("--disk", required=True, help="Disk identifier, e.g. disk4")
    ap.add_argument("--name", required=True, help="Volume name, e.g. REKORDBOX")
    ap.add_argument(
        "--fs",
        required=True,
        choices=["MS-DOS", "ExFAT"],
        help="MS-DOS(FAT32) for widest compatibility, ExFAT for newer devices.",
    )
    ap.add_argument("--yes-i-understand-erase", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.yes_i_understand_erase:
        raise SystemExit("Refusing to format without --yes-i-understand-erase")

    disk = args.disk.strip()
    if not disk.startswith("disk"):
        raise SystemExit("Disk must look like diskN, e.g. disk4")

    print("External disks:")
    print(list_external_disks())
    cmd = ["diskutil", "eraseDisk", args.fs, args.name, "MBRFormat", f"/dev/{disk}"]
    print("Command:", " ".join(cmd))
    if args.dry_run:
        print("Dry run only. No changes made.")
        return

    proc = run(cmd)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr)
        raise SystemExit(proc.returncode)
    print("Format complete.")


if __name__ == "__main__":
    main()
