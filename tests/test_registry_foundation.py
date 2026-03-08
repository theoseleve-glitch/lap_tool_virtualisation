from trackreco_platform.imagery.fetcher import ImageryFetcher


def test_fetcher_is_deterministic():
    fetcher = ImageryFetcher()
    a = fetcher.fetch("https://example.org/a.tif")
    b = fetcher.fetch("https://example.org/a.tif")
    assert a.payload == b.payload
    assert a.metadata["checksum_hint"] == b.metadata["checksum_hint"]


def test_fetcher_changes_with_uri():
    fetcher = ImageryFetcher()
    a = fetcher.fetch("u1")
    b = fetcher.fetch("u2")
    assert a.metadata["checksum_hint"] != b.metadata["checksum_hint"]
