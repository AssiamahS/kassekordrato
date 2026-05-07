#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from mutagen import File as MutagenFile  # type: ignore
except Exception:
    MutagenFile = None

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aiff", ".flac"}


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def file_sha1(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


@dataclass
class Track:
    path: str
    filename: str
    extension: str
    artist: str
    title: str
    album: str
    genre: str
    sha1: str

    @property
    def key(self) -> str:
        return f"{normalize_text(self.artist)}::{normalize_text(self.title)}"


def read_tags(path: Path) -> Tuple[str, str, str, str]:
    artist = ""
    title = ""
    album = ""
    genre = ""
    if MutagenFile is None:
        return artist, title, album, genre
    try:
        mf = MutagenFile(path)
        if not mf or not getattr(mf, "tags", None):
            return artist, title, album, genre
        tags = mf.tags
        # Handle common tag key styles across formats.
        for k_artist in ("TPE1", "artist", "\xa9ART"):
            if k_artist in tags:
                v = tags[k_artist]
                artist = str(v[0] if isinstance(v, list) else v)
                break
        for k_title in ("TIT2", "title", "\xa9nam"):
            if k_title in tags:
                v = tags[k_title]
                title = str(v[0] if isinstance(v, list) else v)
                break
        for k_album in ("TALB", "album", "\xa9alb"):
            if k_album in tags:
                v = tags[k_album]
                album = str(v[0] if isinstance(v, list) else v)
                break
        for k_genre in ("TCON", "genre", "\xa9gen"):
            if k_genre in tags:
                v = tags[k_genre]
                genre = str(v[0] if isinstance(v, list) else v)
                break
    except Exception:
        pass
    return artist.strip(), title.strip(), album.strip(), genre.strip()


def iter_audio_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS and not p.name.startswith("._"):
            yield p


def parse_filename_fallback(path: Path) -> Tuple[str, str]:
    stem = path.stem
    if " - " in stem:
        left, right = stem.split(" - ", 1)
        return left.strip(), right.strip()
    return "", stem.strip()


def build_library(source_root: Path) -> List[Track]:
    tracks: List[Track] = []
    for audio_path in iter_audio_files(source_root):
        artist, title, album, genre = read_tags(audio_path)
        if not title:
            f_artist, f_title = parse_filename_fallback(audio_path)
            artist = artist or f_artist
            title = f_title
        tracks.append(
            Track(
                path=str(audio_path),
                filename=audio_path.name,
                extension=audio_path.suffix.lower(),
                artist=artist or "Unknown Artist",
                title=title or audio_path.stem,
                album=album,
                genre=genre,
                sha1=file_sha1(audio_path),
            )
        )
    return tracks


def find_duplicates(tracks: List[Track]) -> Dict[str, List[str]]:
    by_hash: Dict[str, List[str]] = {}
    for t in tracks:
        by_hash.setdefault(t.sha1, []).append(t.path)
    return {k: v for k, v in by_hash.items() if len(v) > 1}


def extract_text_from_binary(path: Path) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    # Keep printable ASCII-ish bytes and decode safely.
    filtered = bytes(b if 32 <= b < 127 else 10 for b in data)
    return filtered.decode("utf-8", errors="ignore")


def parse_serato_crates(crate_root: Path) -> Dict[str, Set[str]]:
    crates: Dict[str, Set[str]] = {}
    for crate in crate_root.rglob("*.crate"):
        text = extract_text_from_binary(crate)
        refs: Set[str] = set()
        for m in re.findall(r"([^\n\r]*\.(?:mp3|m4a|wav|aiff|flac))", text, flags=re.IGNORECASE):
            refs.add(m.strip())
        crates[str(crate)] = refs
    return crates


def parse_rekordbox_xml(xml_path: Path) -> Set[str]:
    refs: Set[str] = set()
    if not xml_path.exists():
        return refs
    text = xml_path.read_text(errors="ignore")
    for m in re.findall(r'Location="file://([^"]+)"', text):
        refs.add(m)
    return refs


def match_refs_to_library(
    crate_refs: Set[str], library_tracks: List[Track]
) -> Tuple[List[str], List[str]]:
    by_name = {t.filename.lower(): t.path for t in library_tracks}
    matched: List[str] = []
    unmatched: List[str] = []
    for ref in crate_refs:
        filename = Path(ref).name.lower()
        if filename in by_name:
            matched.append(ref)
        else:
            unmatched.append(ref)
    return matched, unmatched


def main():
    ap = argparse.ArgumentParser(description="Generate music truth report for crates and library.")
    ap.add_argument("--source", required=True, help="Source music folder (truth set).")
    ap.add_argument("--serato-subcrates", help="Path to Serato Subcrates folder.")
    ap.add_argument("--rekordbox-xml", help="Optional Rekordbox XML export path.")
    ap.add_argument(
        "--out",
        default="truth_report.json",
        help="Output JSON file path (default: truth_report.json).",
    )
    args = ap.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Missing source folder: {source}")

    tracks = build_library(source)
    dupes = find_duplicates(tracks)
    report: Dict[str, object] = {
        "source": str(source),
        "track_count": len(tracks),
        "duplicates_by_hash": dupes,
        "tracks": [asdict(t) for t in tracks],
    }

    if args.serato_subcrates:
        serato_root = Path(args.serato_subcrates).expanduser().resolve()
        crates = parse_serato_crates(serato_root)
        crate_report = {}
        for crate_file, refs in crates.items():
            matched, unmatched = match_refs_to_library(refs, tracks)
            crate_report[crate_file] = {
                "reference_count": len(refs),
                "matched_count": len(matched),
                "unmatched_count": len(unmatched),
                "unmatched_examples": unmatched[:25],
            }
        report["serato_crates"] = crate_report

    if args.rekordbox_xml:
        xml_path = Path(args.rekordbox_xml).expanduser().resolve()
        rb_refs = parse_rekordbox_xml(xml_path)
        matched, unmatched = match_refs_to_library(rb_refs, tracks)
        report["rekordbox"] = {
            "xml": str(xml_path),
            "reference_count": len(rb_refs),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "unmatched_examples": unmatched[:25],
        }

    out = Path(args.out).expanduser().resolve()
    out.write_text(json.dumps(report, indent=2))
    print(f"Wrote report: {out}")
    print(f"Tracks: {len(tracks)} | Duplicate groups: {len(dupes)}")


if __name__ == "__main__":
    main()
