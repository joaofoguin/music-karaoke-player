from dataclasses import dataclass
from pathlib import Path


@dataclass
class Track:
    path: Path
    title: str
    artist: str = ""
    album: str = ""
    cover: bytes | None = None
    format: str = ""
    duration: float = 0.0