from types import SimpleNamespace

from trackreco_platform.services.asset_generation import generate_assets


def test_deterministic_asset_generation():
    version = SimpleNamespace(id="lv-1", layout_id="l1", version=7, immutable_hash="abc")
    first = generate_assets(version, output_root=None)
    second = generate_assets(version, output_root=None)
    assert first == second
    assert sorted(first.keys()) == ["geojson", "svg", "thumbnail_png"]
