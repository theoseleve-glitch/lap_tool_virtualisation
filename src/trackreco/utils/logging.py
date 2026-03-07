from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(slots=True)
class StageLog:
    ts: str
    stage: str
    status: str
    message: str
    details: dict


class JsonlLogger:
    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file
        output_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: StageLog) -> None:
        with self.output_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
