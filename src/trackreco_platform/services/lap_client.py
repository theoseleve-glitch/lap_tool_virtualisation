from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class LapLayoutContract:
    contract_version: str
    layout_id: str
    layout_version_id: str
    version: int
    canonical_geometry: dict


class LapRegistryClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def fetch_layout(self, venue_id: str, version: int | None = None) -> LapLayoutContract:
        params = {"version": version} if version is not None else None
        response = requests.get(f"{self.base_url}/api/v1/lap/venues/{venue_id}/layout", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        return LapLayoutContract(**payload)
