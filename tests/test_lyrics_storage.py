from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import QCoreApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from models.track import Track
from core.config_manager import ConfigManager
from core.lyrics_storage import (
    get_central_lyrics_dir,
    get_lyrics_filename,
    get_save_lyrics_path,
    resolve_lyrics_path,
    sanitize_filename,
)


def test_sanitize_filename():
    assert sanitize_filename("Arctic Monkeys / R U Mine?") == "Arctic Monkeys _ R U Mine_"
    assert sanitize_filename("A < B > C: D | E * F") == "A _ B _ C_ D _ E _ F"
    assert sanitize_filename("") == ""


def test_get_lyrics_filename():
    assert get_lyrics_filename("Queen", "Bohemian Rhapsody") == "Queen - Bohemian Rhapsody.lrc"
    assert get_lyrics_filename("", "Bohemian Rhapsody") == "Bohemian Rhapsody.lrc"
    assert get_lyrics_filename("Queen", "") == "Queen - track.lrc"
    assert get_lyrics_filename("", "", fallback_stem="musica123") == "musica123.lrc"


def test_resolve_and_save_lyrics_path():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        cm = ConfigManager(organization="TestLyricsOrg", application="TestLyricsStorage")
        cm.set("karaoke/lyrics_directory", str(temp_path))

        track = Track(
            path=Path("C:/Musicas/Rock/01_Song.mp3"),
            title="Song Title",
            artist="Artist Name",
        )

        # Destino padrão
        save_path = get_save_lyrics_path(track, cm)
        assert save_path.parent == temp_path
        assert save_path.name == "Artist Name - Song Title.lrc"

        # Antes de criar o arquivo, resolve_lyrics_path retorna None
        assert resolve_lyrics_path(track, cm) is None

        # Cria o arquivo na pasta central
        save_path.write_text("[00:01.00]Teste", encoding="utf-8")

        # Agora resolve_lyrics_path deve encontrar
        resolved = resolve_lyrics_path(track, cm)
        assert resolved == save_path
