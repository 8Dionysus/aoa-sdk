#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[0]
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aoa_sdk.closeout import CloseoutAPI  # noqa: E402
from aoa_sdk.workspace.discovery import Workspace  # noqa: E402


UNIT_NAMES = ("aoa-closeout-inbox.service", "aoa-closeout-inbox.path")
DEFAULT_USER_UNIT_DIR = Path.home() / ".config" / "systemd" / "user"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install and optionally enable the aoa-sdk closeout inbox user units."
    )
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="Workspace root used for federation discovery.",
    )
    parser.add_argument(
        "--user-unit-dir",
        default=str(DEFAULT_USER_UNIT_DIR),
        help="Target directory for user-level systemd units.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing unit files when their contents differ.",
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Enable and start the path unit after installation.",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start the path unit after installation without enabling it.",
    )
    return parser.parse_args(argv)


def install_units(*, user_unit_dir: Path, overwrite: bool) -> list[Path]:
    installed_paths: list[Path] = []
    source_dir = REPO_ROOT / "systemd"
    user_unit_dir.mkdir(parents=True, exist_ok=True)
    for unit_name in UNIT_NAMES:
        source_path = source_dir / unit_name
        target_path = user_unit_dir / unit_name
        source_text = source_path.read_text(encoding="utf-8")
        if target_path.exists():
            target_text = target_path.read_text(encoding="utf-8")
            if target_text == source_text:
                installed_paths.append(target_path)
                continue
            if not overwrite:
                raise FileExistsError(
                    f"{target_path} already exists with different contents; rerun with --overwrite"
                )
        shutil.copyfile(source_path, target_path)
        installed_paths.append(target_path)
    return installed_paths


def ensure_queue_dirs(*, root: Path) -> list[Path]:
    workspace = Workspace.discover(root)
    closeout = CloseoutAPI(workspace)
    queue_paths = closeout.default_queue_paths()
    ensured: list[Path] = []
    for key in ("root", "requests", "manifests", "inbox", "processed", "failed", "reports"):
        path = queue_paths[key]
        path.mkdir(parents=True, exist_ok=True)
        ensured.append(path)
    return ensured


def run_systemctl(*args: str) -> None:
    subprocess.run(["systemctl", "--user", *args], check=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    user_unit_dir = Path(args.user_unit_dir).expanduser().resolve()

    installed_paths = install_units(user_unit_dir=user_unit_dir, overwrite=args.overwrite)
    ensured_paths = ensure_queue_dirs(root=root)

    run_systemctl("daemon-reload")
    if args.enable:
        run_systemctl("enable", "--now", "aoa-closeout-inbox.path")
    elif args.start:
        run_systemctl("start", "aoa-closeout-inbox.path")

    print(f"[ok] installed {len(installed_paths)} user units into {user_unit_dir}")
    for path in installed_paths:
        print(f"[unit] {path}")
    print(f"[ok] ensured {len(ensured_paths)} closeout queue directories exist")
    for path in ensured_paths:
        print(f"[queue] {path}")
    if args.enable:
        print("[status] aoa-closeout-inbox.path enabled and started")
    elif args.start:
        print("[status] aoa-closeout-inbox.path started")
    else:
        print("[status] units installed; run systemctl --user enable --now aoa-closeout-inbox.path when ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
