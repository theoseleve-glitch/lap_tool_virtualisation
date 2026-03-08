import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from trackreco_platform.domain.models import ArtifactReference, LayoutVersion
from trackreco_platform.storage.s3 import S3Storage


@dataclass(frozen=True)
class GeneratedAsset:
    artifact_type: str
    path: str
    checksum: str


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _base_path(layout_version: LayoutVersion) -> str:
    return f"layouts/{layout_version.layout_id}/versions/{layout_version.version}"


def generate_assets(layout_version: LayoutVersion, output_root: Path) -> dict[str, bytes]:
    payload = {
        "layout_version_id": layout_version.id,
        "version": layout_version.version,
        "immutable_hash": layout_version.immutable_hash,
    }
    geojson = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    svg = f"<svg data-layout-id='{layout_version.id}' data-version='{layout_version.version}'></svg>".encode()
    png = hashlib.md5(svg).hexdigest().encode()
    return {"geojson": geojson, "svg": svg, "thumbnail_png": png}


def persist_assets(db: Session, storage: S3Storage, layout_version: LayoutVersion, output_root: Path) -> list[GeneratedAsset]:
    base_path = _base_path(layout_version)
    files = generate_assets(layout_version, output_root)
    generated: list[GeneratedAsset] = []
    for artifact_type, content in files.items():
        object_key = f"{base_path}/{artifact_type}.{ 'png' if artifact_type.endswith('png') else artifact_type }"
        storage.put_bytes(object_key, content)
        checksum = _checksum(content)
        db.add(
            ArtifactReference(
                entity_type="layout_version",
                entity_id=layout_version.id,
                artifact_type=artifact_type,
                storage_path=object_key,
                checksum=checksum,
                created_by="system",
                updated_by="system",
            )
        )
        generated.append(GeneratedAsset(artifact_type=artifact_type, path=object_key, checksum=checksum))
    return generated
