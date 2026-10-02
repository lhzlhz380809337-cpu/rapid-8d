"""Offline backup/restore. Stop the API before invoking; archives contain private data."""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def backup(source: Path, archive: Path):
    source = source.resolve()
    if not source.is_dir():
        raise ValueError("Data directory does not exist")
    if archive.resolve().is_relative_to(source):
        raise ValueError("Backup must be outside the data directory")
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as out:
        for item in sorted(source.rglob("*")):
            if item.is_symlink():
                raise ValueError("Symlinks are not supported")
            if item.is_file():
                name = item.relative_to(source).as_posix()
                payload = item.read_bytes()
                manifest[name] = hashlib.sha256(payload).hexdigest()
                out.writestr(name, payload)
        out.writestr("BACKUP-MANIFEST.json", json.dumps(manifest, indent=2))


def restore(archive: Path, target: Path):
    target = target.resolve()
    if target.exists() and any(target.iterdir()):
        raise ValueError("Restore target must be empty; existing data will never be overwritten")
    with zipfile.ZipFile(archive) as source:
        manifest = json.loads(source.read("BACKUP-MANIFEST.json"))
        # Verify the entire archive before writing any file.
        for name, digest in manifest.items():
            destination = (target / name).resolve()
            if not destination.is_relative_to(target) or "\\" in name or ":" in name:
                raise ValueError("Unsafe backup path")
            if hashlib.sha256(source.read(name)).hexdigest() != digest:
                raise ValueError("Backup integrity check failed")
        for name in manifest:
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read(name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("data", type=Path)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.action == "backup":
        backup(args.data, args.archive)
    else:
        restore(args.archive, args.data)
    print("Completed. Keep backup files private and apply your retention policy.")
