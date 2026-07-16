from inspect import getfile
from pathlib import Path

from aoa_sdk import AoASDK


def test_import() -> None:
    assert AoASDK is not None
    source_root = Path(__file__).resolve().parents[1] / "src" / "aoa_sdk"
    assert Path(getfile(AoASDK)).resolve().is_relative_to(source_root)
