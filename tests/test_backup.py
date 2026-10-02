import hashlib
import json
import zipfile
import pytest
from scripts.backup import backup, restore

def test_backup_restore_checksums_and_no_overwrite(tmp_path):
    root = tmp_path / "data"; root.mkdir()
    (root / "project.json").write_text('{"title":"报告"}', encoding="utf-8")
    archive = tmp_path / "backup.zip"
    backup(root, archive)
    restored = tmp_path / "restored"
    restore(archive, restored)
    assert (root / "project.json").read_bytes() == (restored / "project.json").read_bytes()
    with pytest.raises(ValueError):
        restore(archive, restored)

def test_restore_rejects_traversal_before_writing(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive,"w") as out:
        out.writestr("../outside", b"bad")
        out.writestr("BACKUP-MANIFEST.json", json.dumps({"../outside":hashlib.sha256(b"bad").hexdigest()}))
    with pytest.raises(ValueError):
        restore(archive,tmp_path / "restore")
    assert not (tmp_path / "outside").exists()
