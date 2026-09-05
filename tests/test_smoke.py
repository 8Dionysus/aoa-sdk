from inspect import getfile
import os
from pathlib import Path
import subprocess
import sys

import pytest

from aoa_sdk import AoASDK


def test_import() -> None:
    assert AoASDK is not None
    source_root = Path(__file__).resolve().parents[1] / "src" / "aoa_sdk"
    assert Path(getfile(AoASDK)).resolve().is_relative_to(source_root)


def test_leaf_import_does_not_load_the_entire_sdk() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src"
    environment = dict(os.environ, PYTHONPATH=str(source_root))
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, aoa_sdk; "
            "assert 'AoASDK' in dir(aoa_sdk); "
            "import aoa_sdk.titans.appserver_bridge; "
            "assert 'aoa_sdk.api' not in sys.modules",
        ],
        env=environment,
        check=True,
    )


def test_public_export_keeps_identity_and_unknown_names_fail() -> None:
    import aoa_sdk
    from aoa_sdk.api import AoASDK as DirectAoASDK

    assert aoa_sdk.AoASDK is AoASDK is DirectAoASDK
    assert aoa_sdk.__all__ == ["AoASDK"]
    with pytest.raises(AttributeError, match="has no attribute 'unknown_sdk_export'"):
        getattr(aoa_sdk, "unknown_sdk_export")
