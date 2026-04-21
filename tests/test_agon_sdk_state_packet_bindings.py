from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_sdk_state_packet_bindings_are_current():
    build = load_module(ROOT / 'scripts' / 'build_agon_sdk_state_packet_bindings.py', 'build_agon_sdk_state_packet_bindings')
    expected = build.build(build.load_json(build.CONFIG))
    current = build.load_json(build.OUT)
    assert current == expected


def test_sdk_state_packet_binding_validation():
    validate = load_module(ROOT / 'scripts' / 'validate_agon_sdk_state_packet_bindings.py', 'validate_agon_sdk_state_packet_bindings')
    validate.validate()
