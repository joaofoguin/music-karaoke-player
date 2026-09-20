from pathlib import Path
from typing import Callable

from models.track import Track
from core.metadata_reader import ler_metadados


class TrackLoader:
    """Concentra a validação e a criação de Track a partir de arquivos de áudio."""

    def __init__(
        self,
        audio_extensions,
        metadata_reader: Callable[[Path], dict] = ler_metadados,
    ):
        self.audio_extensions = {str(ext).lower() for ext in audio_extensions}
        self.metadata_reader = metadata_reader

    def set_audio_extensions(self, audio_extensions):
        self.audio_extensions = {str(ext).lower() for ext in audio_extensions}

    def carregar(self, caminho: Path) -> Track | None:
        caminho = Path(caminho)

        if not caminho.is_file() or caminho.suffix.lower() not in self.audio_extensions:
            return None

        metadados = self.metadata_reader(caminho)

        return Track(
            path=caminho,
            title=metadados["title"],
            artist=metadados["artist"],
            album=metadados["album"],
            cover=metadados["cover"],
            format=metadados["format"],
            duration=metadados["duration"],
        )
