"""Safe temporary materialization for compact routing shadow fixture archives."""

from __future__ import annotations

import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PART_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = PART_ROOT / "fixtures" / "routing-shadow"
ALLOWED_ARCHIVES = {
    "canonical-generated",
    "inputs",
    "producer-inputs",
}


def validated_members(
    archive: tarfile.TarFile,
    target: Path,
) -> list[tarfile.TarInfo]:
    members = archive.getmembers()
    target = target.resolve()
    for member in members:
        member_path = Path(member.name)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise RuntimeError(f"unsafe fixture archive path: {member.name}")
        if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
            raise RuntimeError(f"unsupported fixture archive member: {member.name}")
        resolved = (target / member_path).resolve()
        try:
            resolved.relative_to(target)
        except ValueError as exc:
            raise RuntimeError(f"fixture archive path escapes target: {member.name}") from exc
    return members


@contextmanager
def materialized_fixture_archive(name: str) -> Iterator[Path]:
    if name not in ALLOWED_ARCHIVES:
        raise ValueError(f"unknown routing shadow fixture archive: {name}")
    archive_path = ARCHIVE_ROOT / f"{name}.tar.gz"
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    with tempfile.TemporaryDirectory(prefix=f"aoa-routing-{name}-") as temp_dir:
        target = Path(temp_dir) / name
        target.mkdir()
        with tarfile.open(archive_path, mode="r:gz") as archive:
            for member in validated_members(archive, target):
                archive.extract(member, path=target)
        yield target
