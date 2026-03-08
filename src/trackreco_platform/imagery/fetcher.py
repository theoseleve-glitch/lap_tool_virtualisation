from dataclasses import dataclass
import hashlib


@dataclass
class FetchedImagery:
    payload: bytes
    metadata: dict


class ImageryFetcher:
    def fetch(self, source_uri: str) -> FetchedImagery:
        payload = source_uri.encode("utf-8")
        checksum = hashlib.sha256(payload).hexdigest()
        return FetchedImagery(payload=payload, metadata={"source_uri": source_uri, "checksum_hint": checksum})
